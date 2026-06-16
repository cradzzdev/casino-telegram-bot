import sqlite3
import os
import json
import threading

DB_PATH = os.path.join(os.path.dirname(__file__), "taixiu.db")
_db_lock = threading.Lock()

_conn = None

def get_db():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA busy_timeout=30000")
    return _conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 10000,
            total_bets INTEGER DEFAULT 0,
            total_wins INTEGER DEFAULT 0,
            total_losses INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            exp INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            bet_type TEXT,
            bet_amount INTEGER,
            detail TEXT,
            result TEXT,
            win INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS game_config (
            key TEXT PRIMARY KEY,
            value REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS giftcodes (
            code TEXT PRIMARY KEY,
            amount INTEGER NOT NULL,
            max_uses INTEGER DEFAULT 1,
            used_count INTEGER DEFAULT 0,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        );
    """)
    conn.commit()

    # ── MIGRATION: add missing columns ──
    existing_cols = [c["name"] for c in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "level" not in existing_cols:
        conn.execute("ALTER TABLE users ADD COLUMN level INTEGER DEFAULT 1")
    if "exp" not in existing_cols:
        conn.execute("ALTER TABLE users ADD COLUMN exp INTEGER DEFAULT 0")
    conn.commit()


def get_user(user_id, username=None):
    with _db_lock:
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not user:
            conn.execute(
                "INSERT INTO users (user_id, username, balance) VALUES (?, ?, 10000)",
                (user_id, username),
            )
            conn.commit()
            user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        elif username:
            conn.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
            conn.commit()
        return dict(user)


def place_bet(user_id, bet_type, bet_amount, detail, result, win_amount):
    """detail: any JSON-serializable data (dict/list) about the bet."""
    with _db_lock:
        conn = get_db()
        conn.execute(
            "UPDATE users SET balance = balance + ?, total_bets = total_bets + 1, "
            "total_wins = total_wins + ?, total_losses = total_losses + ? WHERE user_id = ?",
            (
                win_amount - bet_amount,
                1 if win_amount > 0 else 0,
                1 if win_amount == 0 else 0,
                user_id,
            ),
        )
        conn.execute(
            "INSERT INTO history (user_id, bet_type, bet_amount, detail, result, win) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, bet_type, bet_amount, json.dumps(detail, ensure_ascii=False), result, win_amount),
        )
        conn.commit()


def get_history(user_id, limit=10):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def get_top_users(limit=10):
    conn = get_db()
    rows = conn.execute(
        "SELECT user_id, username, balance, total_wins, total_losses "
        "FROM users ORDER BY balance DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_all_users():
    conn = get_db()
    rows = conn.execute(
        "SELECT user_id, username, balance, total_bets, total_wins, total_losses "
        "FROM users ORDER BY balance DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def admin_set_balance(user_id, amount):
    with _db_lock:
        conn = get_db()
        conn.execute("UPDATE users SET balance = ? WHERE user_id = ?", (amount, user_id))
        conn.commit()


def admin_reset_user(user_id):
    with _db_lock:
        conn = get_db()
        conn.execute(
            "UPDATE users SET balance = 10000, total_bets = 0, total_wins = 0, total_losses = 0 "
            "WHERE user_id = ?",
            (user_id,),
        )
        conn.execute("DELETE FROM history WHERE user_id = ?", (user_id,))
        conn.commit()


def admin_delete_user(user_id):
    with _db_lock:
        conn = get_db()
        conn.execute("DELETE FROM history WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()


def admin_get_stats():
    conn = get_db()
    total_users = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()["cnt"]
    total_bets = conn.execute("SELECT COALESCE(SUM(total_bets), 0) as s FROM users").fetchone()["s"]
    total_balance = conn.execute("SELECT COALESCE(SUM(balance), 0) as s FROM users").fetchone()["s"]
    return {"total_users": total_users, "total_bets": total_bets, "total_balance": total_balance}


# ═══════════════════════════════════════════════════════════
# LEVEL SYSTEM
# ═══════════════════════════════════════════════════════════
MAX_LEVEL = 1000

def get_exp_needed(level):
    """EXP cần để lên level tiếp. Level 1-10: 10, 11-20: 15, 21-30: 20..."""
    return 10 + (level // 10) * 5

def get_level_rewards():
    """Quà tặng mỗi 10 level. Returns dict {level: amount}."""
    rewards = {}
    base = 10000
    for lv in range(10, MAX_LEVEL + 1, 10):
        # Level 10: 10k, 20: 25k, 30: 50k, 40: 100k...
        multiplier = 1 + (lv // 10 - 1) * 0.5
        rewards[lv] = int(base * multiplier)
    return rewards

LEVEL_REWARDS = get_level_rewards()

def add_exp(user_id, amount=1):
    """Thêm EXP, tự động level up. Returns list of (new_level, reward_amount) for each level up."""
    with _db_lock:
        conn = get_db()
        user = conn.execute("SELECT level, exp FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not user:
            return []
        level = user["level"]
        exp = user["exp"]
        level_ups = []

        exp += amount
        while level < MAX_LEVEL:
            needed = get_exp_needed(level)
            if exp >= needed:
                exp -= needed
                level += 1
                reward = LEVEL_REWARDS.get(level, 0)
                level_ups.append((level, reward))
                if reward > 0:
                    conn.execute(
                        "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                        (reward, user_id)
                    )
            else:
                break

        if level >= MAX_LEVEL:
            exp = 0

        conn.execute(
            "UPDATE users SET level = ?, exp = ? WHERE user_id = ?",
            (level, exp, user_id)
        )
        conn.commit()
        return level_ups


# ═══════════════════════════════════════════════
# GIFTCODE SYSTEM
# ═══════════════════════════════════════════════

def create_giftcode(code, amount, max_uses=1, created_by=None, expires_at=None):
    """Tạo giftcode mới. Returns True if success."""
    with _db_lock:
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO giftcodes (code, amount, max_uses, created_by, expires_at) VALUES (?, ?, ?, ?, ?)",
                (code.upper(), amount, max_uses, created_by, expires_at)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Code already exists


def redeem_giftcode(code, user_id):
    """Đổi giftcode. Returns (success, amount_or_msg)."""
    with _db_lock:
        conn = get_db()
        gc = conn.execute("SELECT * FROM giftcodes WHERE code = ?", (code.upper(),)).fetchone()
        if not gc:
            return False, "Giftcode không tồn tại!"
        
        gc = dict(gc)
        
        # Check if expired
        if gc["expires_at"]:
            from datetime import datetime
            try:
                exp = datetime.fromisoformat(gc["expires_at"])
                if datetime.now() > exp:
                    return False, "Giftcode đã hết hạn!"
            except:
                pass
        
        # Check max uses
        if gc["used_count"] >= gc["max_uses"]:
            return False, "Giftcode đã hết lượt sử dụng!"
        
        # Apply
        conn.execute("UPDATE giftcodes SET used_count = used_count + 1 WHERE code = ?", (code.upper(),))
        conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (gc["amount"], user_id))
        conn.commit()
        return True, gc["amount"]


def get_giftcode_list():
    """Lấy danh sách giftcode (admin)."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM giftcodes ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def delete_giftcode(code):
    """Xóa giftcode."""
    with _db_lock:
        conn = get_db()
        conn.execute("DELETE FROM giftcodes WHERE code = ?", (code.upper(),))
        conn.commit()


# ═══════════════════════════════════════
# GAME CONFIG
# ═══════════════════════════════════════

DEFAULT_GAME_CONFIG = {
    "taixiu_mult": 2.0,
    "xocdia_mult": 2.0,
    "roulette_color_mult": 2.0,
    "roulette_number_mult": 35.0,
    "slot_jackpot_mult": 10.0,
    "slot_pair_mult": 2.0,
    "bj_normal_mult": 2.0,
    "bj_blackjack_mult": 3.0,
    "bj_push_return": 1.0,
}

def get_game_config():
    """Lấy config hiện tại. Returns dict."""
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM game_config").fetchall()
    cfg = dict(DEFAULT_GAME_CONFIG)
    for r in rows:
        cfg[r["key"]] = r["value"]
    return cfg

def set_game_config(key, value):
    """Set 1 config. Tạo mới hoặc update."""
    with _db_lock:
        conn = get_db()
        conn.execute(
            "INSERT INTO game_config (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, float(value))
        )
        conn.commit()

def reset_game_config():
    """Reset tất cả về default."""
    with _db_lock:
        conn = get_db()
        conn.execute("DELETE FROM game_config")
        conn.commit()


def admin_set_level(user_id, level, exp=0):
    """Admin set level + exp cho user."""
    with _db_lock:
        conn = get_db()
        conn.execute(
            "UPDATE users SET level = ?, exp = ? WHERE user_id = ?",
            (int(level), int(exp), user_id)
        )
        conn.commit()
