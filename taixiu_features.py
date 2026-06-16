"""
taixiu_features.py — Ranking & Payback system
Thêm vào mà KHÔNG sửa 1 dòng code cũ nào.
Tự hook vào Application.process_update để gửi payback sau ván thua.
"""
import time
import json
from taixiu_db import add_exp, get_exp_needed, MAX_LEVEL, LEVEL_REWARDS

# ═══════════════════════════════════════════════════════════
# RANK SYSTEM
# ═══════════════════════════════════════════════════════════
# (min_balance, emoji, title)
RANKS = [
    (0,         "🥚", "Tân Binh"),
    (2000000,   "🃏", "Mới Chơi"),
    (5000000,   "🎲", "Tay Chơi"),
    (10000000,  "👑", "Cao Thủ"),
    (20000000,  "💎", "Triệu Phú"),
    (50000000,  "🏆", "Bá Chủ"),
]

def get_rank(balance):
    e, t = RANKS[0][1], RANKS[0][2]
    for th, em, ti in RANKS:
        if balance >= th: e, t = em, ti
    return e, t

def get_rank_display(balance):
    e, t = get_rank(balance)
    return f"{e} **{t}**"

def get_next_rank_info(balance):
    for th, em, ti in RANKS:
        if balance < th: return em, ti, th - balance
    return None

def get_rank_progress(balance):
    for i in range(len(RANKS) - 1):
        low, high = RANKS[i][0], RANKS[i+1][0]
        if low <= balance < high:
            pct = (balance - low) / (high - low) * 100
            next_e, next_t = RANKS[i+1][1], RANKS[i+1][2]
            bars = "▓" * int(pct // 10) + "░" * (10 - int(pct // 10))
            return f"{bars} {pct:.0f}% → {next_e} {next_t}"
    return None

# ═══════════════════════════════════════════════════════════
# LEVEL SYSTEM
# ═══════════════════════════════════════════════════════════

def get_level_display(level, exp):
    """Hiển thị level + progress bar."""
    needed = get_exp_needed(level)
    pct = (exp / needed * 100) if needed > 0 else 0
    bars = "▓" * int(pct // 10) + "░" * (10 - int(pct // 10))
    return f"Lv.{level} {bars} {exp}/{needed} EXP"

def get_next_reward_info(level):
    """Quà tiếp theo ở level nào, cần bao nhiêu level nữa."""
    for lv in sorted(LEVEL_REWARDS.keys()):
        if lv > level:
            return lv, LEVEL_REWARDS[lv]
    return None, None

# ═══════════════════════════════════════════════════════════
# PAYBACK SYSTEM
# ═══════════════════════════════════════════════════════════

COOLDOWN = 1800  # 30 phút

MILESTONES = {
    5:  (5000,  "💊 **Payback!** Thua 5 ván liên tiếp! Nhận **5,000đ** an ủi 🫂"),
    10: (15000, "💊 **Payback x3!** Thua 10 ván liên tiếp! Nhận **15,000đ** 🫂"),
    15: (25000, "💊 **Payback x5!** Thua 15 ván liên tiếp! Nhận **25,000đ** 🫂"),
    20: (50000, "💊 **Payback x10!** Thua 20 ván liên tiếp! Nhận **50,000đ** 🫂"),
}

def check_payback(user_id, won, balance, total_bets):
    """Returns list of (message, amount) paybacks."""
    import taixiu_bot as bot
    s = bot._get_session(user_id)
    now = time.time()
    results = []

    if "pb_losses" not in s: s["pb_losses"] = 0
    if "pb_last_ms" not in s: s["pb_last_ms"] = 0
    if "pb_last_em" not in s: s["pb_last_em"] = 0

    if not won:
        s["pb_losses"] += 1
        losses = s["pb_losses"]

        if total_bets >= 5:
            # Milestone payback
            if losses in MILESTONES and losses > s["pb_last_ms"]:
                bonus, msg = MILESTONES[losses]
                if now - s["pb_last_ms"] >= COOLDOWN:
                    results.append((msg, bonus))
                    s["pb_last_ms"] = now

            # Emergency
            if balance < 1000 and losses >= 3:
                if now - s["pb_last_em"] >= COOLDOWN:
                    results.append((
                        "🆘 **Cứu trợ!** Số dư quá thấp! Nhận **3,000đ** để gỡ gạc 🎯",
                        3000
                    ))
                    s["pb_last_em"] = now
    else:
        s["pb_losses"] = 0  # Reset on win

    return results


# ═══════════════════════════════════════════════════════════
# HOOKING — monkey-patch existing bot functions
# ═══════════════════════════════════════════════════════════

import sys
# Fix: Khi taixiu_bot chạy dạng __main__, import taixiu_bot tạo bản copy riêng.
# Dùng sys.modules để patch đúng instance thật.
bot = sys.modules.get('taixiu_bot') or sys.modules.get('__main__')
if bot is None:
    import taixiu_bot as bot

from taixiu_db import get_user
from telegram.ext import Application

# ── 1. PATCH: _menu_text to include rank ──

_orig_menu_text = bot._menu_text

def _patched_menu_text(user_id, first_name=""):
    text = _orig_menu_text(user_id, first_name)
    db = get_user(user_id)
    rank_line = f"🏅 {get_rank_display(db['balance'])}"
    prog = get_rank_progress(db['balance'])
    if prog:
        rank_line += f"\n     {prog}"

    level = db.get("level", 1)
    exp = db.get("exp", 0)
    level_line = f"⭐ {get_level_display(level, exp)}"

    lines = text.split("\n")
    new_lines = []
    for line in lines:
        new_lines.append(line)
        if line.strip().startswith("📈 Win rate:") or "win rate:" in line.lower():
            new_lines.append(rank_line)
            new_lines.append(level_line)
    return "\n".join(new_lines)

bot._menu_text = _patched_menu_text

# ── 2. PATCH: place_bet to track consecutive losses + give payback ──

_orig_place_bet = bot.place_bet

def _patched_place_bet(user_id, bet_type, bet_amount, detail, result, win_amount):
    import logging
    logging.getLogger(__name__).info(f"PATCHED place_bet called: uid={user_id} type={bet_type} amt={bet_amount}")
    _orig_place_bet(user_id, bet_type, bet_amount, detail, result, win_amount)
    # +1 EXP per game
    try:
        level_ups = add_exp(user_id, 1)
    except Exception as e:
        logging.getLogger(__name__).error(f"add_exp FAILED for {user_id}: {e}")
        level_ups = []
    if level_ups:
        s = bot._get_session(user_id)
        if "level_rewards" not in s:
            s["level_rewards"] = []
        for new_lv, reward in level_ups:
            s["level_rewards"].append((new_lv, reward))
        s["pb_pending_level"] = level_ups
    # If loss, store pending payback info in session
    if win_amount == 0:
        db = get_user(user_id)
        pbs = check_payback(user_id, False, db["balance"], db["total_bets"])
        if pbs:
            s = bot._get_session(user_id)
            s["pb_pending"] = pbs  # Will be sent by hook below

bot.place_bet = _patched_place_bet

# ── 3. HOOK: After each update, send pending payback ──

_orig_process_update = Application.process_update

async def _patched_process_update(self, update):
    await _orig_process_update(self, update)
    # After processing, check if any user has pending payback
    # We need to find the user_id from the update
    try:
        user = update.effective_user
        if user:
            s = bot._get_session(user.id)
            # Send level-up notifications
            pending_level = s.pop("pb_pending_level", None)
            if pending_level:
                chat_id = update.effective_chat.id
                for new_lv, reward in pending_level:
                    if reward > 0:
                        text = f"⬆️ **LEVEL UP!** Level {new_lv} 🎉\n🎁 Nhận **{reward:,}đ** thưởng!"
                    else:
                        text = f"⬆️ **LEVEL UP!** Level {new_lv} 🎉"
                    await self.bot.send_message(
                        chat_id=chat_id, text=text, parse_mode="Markdown"
                    )
            # Send payback notifications
            pbs = s.pop("pb_pending", None)
            if pbs:
                chat_id = update.effective_chat.id
                for msg_text, amount in pbs:
                    # Apply payback bonus
                    from taixiu_db import get_db
                    db_conn = get_db()
                    db_conn.execute(
                        "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                        (amount, user.id)
                    )
                    db_conn.commit()
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=msg_text,
                        parse_mode="Markdown"
                    )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Payback hook error: {e}")

Application.process_update = _patched_process_update


# ═══════════════════════════════════════════════════════════
# COMMAND: /rank
# ═══════════════════════════════════════════════════════════

async def rank_cmd(update, context):
    user = update.effective_user
    db = get_user(user.id, user.username or user.first_name)
    bal = db["balance"]

    e, title = get_rank(bal)
    next_info = get_next_rank_info(bal)
    s = bot._get_session(user.id)

    lines = [
        f"🏅 **CẤP BẬC CỦA BẠN**",
        f"━━━━━━━━━━━━━━━━━━",
        f"          {e}",
        f"   **{title}**",
        f"━━━━━━━━━━━━━━━━━━",
        f"💰 **{bal:,} VNĐ**",
        f"📊 {db['total_bets']} ván (W{db['total_wins']}/L{db['total_losses']})",
    ]

    if next_info:
        next_e, next_t, needed = next_info
        prog = get_rank_progress(bal)
        lines.append(f"━━━━━━━━━━━━━━━━━━")
        lines.append(f"🎯 Cấp tiếp: {next_e} **{next_t}**")
        lines.append(f"📈 Cần thêm **{needed:,}đ**")
        if prog: lines.append(f"{prog}")
    else:
        lines.append(f"━━━━━━━━━━━━━━━━━━")
        lines.append(f"✨ **CAO NHẤT!** ✨")

    losses = s.get("pb_losses", 0)
    lines.append(f"━━━━━━━━━━━━━━━━━━")
    lines.append(f"🔥 Thua liên tiếp: **{losses}** ván" if losses else "🔥 Chuỗi: sạch sẽ ✅")

    await update.message.reply_text(
        "\n".join(lines), parse_mode="Markdown",
        reply_markup=bot.kb_back(),
    )

# ═══════════════════════════════════════════════════════════
# COMMAND: /level
# ═══════════════════════════════════════════════════════════

async def level_cmd(update, context):
    user = update.effective_user
    db = get_user(user.id, user.username or user.first_name)
    level = db.get("level", 1)
    exp = db.get("exp", 0)
    needed = get_exp_needed(level)
    next_rlv, next_ramt = get_next_reward_info(level)

    lines = [
        f"⭐ **LEVEL SYSTEM**",
        f"━━━━━━━━━━━━━━━━━━",
        f"📊 {get_level_display(level, exp)}",
        f"",
        f"📈 EXP cần để lên level: **{needed}**",
        f"🎯 Mỗi ván: **+1 EXP**",
    ]

    if next_rlv:
        lines.append(f"")
        lines.append(f"🎁 **Quà tiếp theo:**")
        lines.append(f"   Level {next_rlv} → **{next_ramt:,}đ**")
        lines.append(f"   Còn **{next_rlv - level}** level nữa")
    else:
        lines.append(f"")
        lines.append(f"✨ **ĐÃ ĐẠT MAX LEVEL!** ✨")

    # Show recent rewards
    s = bot._get_session(user.id)
    recent_rewards = s.get("level_rewards", [])
    if recent_rewards:
        lines.append(f"")
        lines.append(f"🏆 **Quà đã nhận:**")
        for rl, ra in recent_rewards[-5:]:
            lines.append(f"   Lv.{rl} → +{ra:,}đ")

    await update.message.reply_text(
        "\n".join(lines), parse_mode="Markdown",
        reply_markup=bot.kb_back(),
    )


# ── 4. /rank, /level handlers registered in taixiu_bot.py main() ──

# Also need to inject the /rank command help into /start
# Patch start_cmd to add /rank to first message
_orig_start_cmd = bot.start_cmd

async def _patched_start_cmd(update, context):
    await _orig_start_cmd(update, context)
    # The start_cmd already sends a welcome message.
    # We just send a follow-up if user never saw rank info before.
    user = update.effective_user
    s = bot._get_session(user.id)
    if not s.get("pb_rank_intro"):
        s["pb_rank_intro"] = True
        db = get_user(user.id, user.username or user.first_name)
        rank_display = get_rank_display(db["balance"])
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"💡 Gõ /rank để xem cấp bậc chi tiết!\n"
                 f"🏅 Cấp hiện tại: {rank_display}",
            parse_mode="Markdown"
        )

bot.start_cmd = _patched_start_cmd


# ═══════════════════════════════════════════════════════════
# ── 5. Register /rank, /level handlers in taixiu_bot.py main() ──


# ═══════════════════════════════════════════════════════════
print("✅ taixiu_features loaded — Rank, Level & Payback system active!")
print("   🏅 /rank — Xem cấp bậc")
print("   ⭐ /level — Xem level + EXP")
print("   💊 Payback tự động khi thua liên tiếp")
