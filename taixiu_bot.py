#!/usr/bin/env python3
import sys
import random
import asyncio
import logging
import base64
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, BotCommandScopeDefault
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from taixiu_db import init_db, get_db, get_user, place_bet, get_history, get_top_users, get_all_users, admin_set_balance, admin_reset_user, admin_delete_user, admin_get_stats, create_giftcode, redeem_giftcode, get_giftcode_list, delete_giftcode, get_game_config, set_game_config, reset_game_config, admin_set_level
from new_anims import (anim_taixiu, anim_baucla, anim_xocdia, anim_roulette, anim_slot, anim_blackjack,
                       DICE_EMOJIS, BAUCLA_EMOJI_ANIM, BAUCLA_NAMES_ANIM, RL_RED_SET,
                       SLOT_SYMS_ANIM, SLOT_WEIGHTS_ANIM, CARD_BACK, _edit_safe)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Token
def _load_token():
    try:
        token_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "token.txt")
        with open(token_path) as f:
            t = f.read().strip()
        if t and ":" in t:
            return t
    except:
        pass
    return "YOUR_TELEGRAM_TOKEN_BOT"

TOKEN = _load_token()

# ═══════════════ VERSION ═══════════════
BOT_VERSION = "1.0"

# ═══════════════ CONSTANTS ═══════════════
ADMIN_PASSWORD = "PASSWORD"
ADMIN_ID = "UID_TELEGRAM"

# ═══════════════ SESSION ═══════════════
_sessions = {}

def _get_session(user_id):
    if user_id not in _sessions:
        _sessions[user_id] = {}
    return _sessions[user_id]

# ═══════════════════════════════════════════════════════════
# KEYBOARDS
# ═══════════════════════════════════════════════════════════

LIST_GAMENAMES = [
    ("🎲 Tài Xỉu", "game_taixiu"),
    ("🦀 Bầu Cua", "game_baucua"),
    ("🪙 Xóc Đĩa", "game_xocdia"),
    ("🃏 Blackjack", "game_blackjack"),
    ("🎡 Roulette", "game_roulette"),
    ("🎰 Slot", "game_slot"),
]

def kb_main_menu():
    buttons = []
    row = []
    for i, (label, cb) in enumerate(LIST_GAMENAMES):
        row.append(InlineKeyboardButton(label, callback_data=cb))
        if i % 2 == 1:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([
        InlineKeyboardButton("🏅 Cấp bậc", callback_data="show_rank"),
        InlineKeyboardButton("⭐ Level", callback_data="show_level"),
    ])
    buttons.append([
        InlineKeyboardButton("📊 Lịch sử", callback_data="show_history"),
        InlineKeyboardButton("🏆 Xếp hạng", callback_data="leaderboard"),
    ])
    buttons.append([
        InlineKeyboardButton("❓ Trợ giúp", callback_data="help"),
    ])
    return InlineKeyboardMarkup(buttons)

def kb_back():
    return InlineKeyboardMarkup([[InlineKeyboardButton("← Menu chính", callback_data="menu")]])


# ── Quick-bet keyboards ──
QB_AMOUNTS = [10_000, 25_000, 50_000, 100_000, 200_000, 500_000]

def _kb_qb_amounts(game):
    """Amount selection buttons for quick-bet."""
    buttons = []
    row = []
    for i, amt in enumerate(QB_AMOUNTS):
        row.append(InlineKeyboardButton(f"{amt//1000}k", callback_data=f"qb_{game}_amt_{amt}"))
        if i % 3 == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("← Menu", callback_data="menu")])
    return InlineKeyboardMarkup(buttons)

def _kb_qb_back(game):
    """Back to amount selection for this game."""
    return InlineKeyboardMarkup([[InlineKeyboardButton("← Mức cược", callback_data=f"game_{game}")]])

def _kb_qb_taixiu(amount):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 Tài", callback_data=f"qb_taixiu_tai_{amount}"),
         InlineKeyboardButton("🎲 Xỉu", callback_data=f"qb_taixiu_xiu_{amount}")],
        [InlineKeyboardButton("← Mức cược", callback_data="game_taixiu")],
    ])

def _kb_qb_baucua(amount):
    items = [("🍐 Bầu","bau"),("🦀 Cua","cua"),("🦐 Tôm","tom"),
             ("🐟 Cá","ca"),("🐔 Gà","ga"),("🦌 Nai","nai")]
    buttons = []
    row = []
    for label, key in items:
        row.append(InlineKeyboardButton(label, callback_data=f"qb_baucua_{key}_{amount}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("← Mức cược", callback_data="game_baucua")])
    return InlineKeyboardMarkup(buttons)

def _kb_qb_xocdia(amount):
    buttons = []
    row = []
    for n in range(5):
        row.append(InlineKeyboardButton(str(n), callback_data=f"qb_xocdia_{n}_{amount}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("← Mức cược", callback_data="game_xocdia")])
    return InlineKeyboardMarkup(buttons)

def _kb_qb_roulette(amount):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔴 Đỏ", callback_data=f"qb_roulette_red_{amount}"),
         InlineKeyboardButton("⚫ Đen", callback_data=f"qb_roulette_black_{amount}")],
        [InlineKeyboardButton("👻 Lẻ", callback_data=f"qb_roulette_odd_{amount}"),
         InlineKeyboardButton("👻 Chẵn", callback_data=f"qb_roulette_even_{amount}")],
        [InlineKeyboardButton("← Mức cược", callback_data="game_roulette")],
    ])

def _kb_qb_blackjack(amount):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🃏 Chơi Blackjack", callback_data=f"qb_bj_{amount}")],
        [InlineKeyboardButton("← Mức cược", callback_data="game_blackjack")],
    ])

def _kb_qb_slot(amount):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎰 Quay Slot", callback_data=f"qb_slot_{amount}")],
        [InlineKeyboardButton("← Mức cược", callback_data="game_slot")],
    ])

# ── Format a history row: Game - Kết quả chơi - Kết quả cược ──
GAME_NAMES = {
    "taixiu": "🎲 Tài Xỉu",
    "baucla": "🦀 Bầu Cua",
    "xocdia": "🪙 Xóc Đĩa",
    "blackjack": "🃏 Blackjack",
    "roulette": "🎡 Roulette",
    "slot": "🎰 Slot",
}

def _fmt_hist(r):
    wl = "✅" if r["win"] > 0 else "❌"
    bt = r["bet_type"]
    if bt.startswith("taixiu"):
        game = "🎲 Tài Xỉu"
    elif bt == "blackjack":
        game = "🃏 Blackjack"
    elif bt == "slot":
        game = "🎰 Slot"
    else:
        game = GAME_NAMES.get(bt.split("_")[0], bt.replace("_", "·"))
    result_str = (r.get("result", "") or "").replace("_", "·").replace("*", "·")
    profit = r["win"] - r["bet_amount"]
    b_r = f"+{profit:,}đ" if profit > 0 else f"-{r['bet_amount']:,}đ"
    return f"{wl} {game} - {result_str} - **{b_r}**"

# ═══════════════════════════════════════════════════════════
# MENU TEXT — profile + history summary
def _esc_md(text):
    """Escape Markdown special characters."""
    for c in ["_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"]:
        text = text.replace(c, f"\\{c}")
    return text

def _menu_text(user_id, first_name=""):
    db = get_user(user_id)
    w = db["total_wins"]
    l = db["total_losses"]
    total = db["total_bets"]
    bal = db["balance"]
    wr = f"{w/(w+l)*100:.0f}%" if (w+l) > 0 else "N/A"

    # Last 3 games history
    h = get_history(user_id, 3)
    hist_lines = []

    if h:
        hist_lines = [_fmt_hist(r) for r in h]
        hist_str = "\n".join(hist_lines)
    else:
        hist_str = "  Chưa có ván nào"

    # Update log
    update_log = (
        "\n📋 **UPDATE LOG**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ **V{BOT_VERSION}** (16/06/2026)\n"
        "  • 🎰 6 trò chơi: Tài Xỉu, Bầu Cua, Xóc Đĩa, Blackjack, Roulette, Slot Machine\n"
        "  • 🏅 Hệ thống cấp bậc (Rank) & Level (EXP)\n"
        "  • 💊 Payback tự động khi thua liên tiếp\n"
        "  • 🎟️ Giftcode (Admin tạo / người chơi nhập)\n"
        "  • 📊 Thống kê, Lịch sử, Bảng xếp hạng\n"
        "  • ⚙️ Admin có thể đặt Level & thay đổi tỷ lệ\n"
    )

    safe_name = _esc_md(first_name or db.get('username') or f'User {user_id}')
    text = (
        "🎰 **CRADZZ'S CASINO** 🎰\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"\n👤 **{safe_name}**"
        f"\n💰 **Số dư: {bal:,}đ**\n"
        f"\n📊 **THỐNG KÊ**"
        f"\n  🎲 **{total}** ván  ·  ✅ **{w}** thắng  ·  ❌ **{l}** thua"
        f"\n  📈 Win rate: **{wr}**"
        f"\n"
        f"\n📋 **3 VÁN GẦN NHẤT:**"
        f"\n{hist_str}"
        f"\n"
        f"{update_log}"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎮 **CHỌN TRÒ CHƠI:** 👇"
    )
    return text


# ═══════════════════════════════════════════════════════════
# ADMIN KEYBOARDS
# ═══════════════════════════════════════════════════════════

def kb_admin():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Thống kê", callback_data="adm_stats")],
        [InlineKeyboardButton("👥 Danh sách User", callback_data="adm_users")],
        [InlineKeyboardButton("💰 Set Balance", callback_data="adm_setbal"),
         InlineKeyboardButton("🔄 Reset User", callback_data="adm_reset")],
        [InlineKeyboardButton("🗑️ Xóa User", callback_data="adm_del"),
         InlineKeyboardButton("🔍 Tra cứu", callback_data="adm_search")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="adm_broadcast"),
         InlineKeyboardButton("🎁 Tặng tất cả", callback_data="adm_gift_all")],
        [InlineKeyboardButton("⭐ Set Level", callback_data="adm_setlevel"),
         InlineKeyboardButton("⚙️ Tỷ lệ", callback_data="adm_odds")],
        [InlineKeyboardButton("🎟️ Giftcode", callback_data="adm_giftcode")],
        [InlineKeyboardButton("❌ Đóng", callback_data="menu")],
    ])


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def _game_rules(game_name):
    rules = {
        "taixiu": "🎲 **TÀI XỈU**\n━━━━━━━━━━━━━━━━━━\n• Đoán tổng 3 viên xúc xắc\n• **Tài** (11-17) hoặc **Xỉu** (4-10)\n• Thắng x2 tiền cược\n• VD: `/tai 10k` hoặc `/xiu 10k`",
        "baucua": "🦀 **BẦU CUA**\n━━━━━━━━━━━━━━━━━━\n• Đoán mặt sẽ ra: Bầu, Cua, Tôm, Cá, Gà, Nai\n• 3 viên xúc xắc, mỗi mặt 1 con vật\n• Trúng → x3, Trúng 2 → x2\n• VD: `/bau cua 10k`",
        "xocdia": "🪙 **XÓC ĐĨA**\n━━━━━━━━━━━━━━━━━━\n• Đoán số đồng xu ngửa (0-4)\n• Thắng x2 nếu đoán đúng\n• VD: `/xoc 2 10k` (đoán 2 ngửa)",
        "blackjack": "🃏 **BLACKJACK**\n━━━━━━━━━━━━━━━━━━\n• Càng gần 21 càng tốt, không quá 21\n• BLACKJACK (21 từ 2 lá đầu) x2.5\n• Thắng thường x2, Hòa hoàn tiền\n• **HIT**: lấy thêm bài\n• **STAND**: giữ bài\n• **DOUBLE**: gấp đôi cược, lấy 1 lá\n• Dealer: Hit < 17, Stand ≥ 17\n• VD: `/bj 10k`",
        "roulette": "🎡 **ROULETTE**\n━━━━━━━━━━━━━━━━━━\n• Cược Đỏ/Đen/Lẻ/Chẵn x2\n• Cược số cụ thể x35\n• VD: `/ru red 10k`, `/ru 7 10k`",
        "slot": "🎰 **SLOT MACHINE**\n━━━━━━━━━━━━━━━━━━\n• 3 reel quay ngẫu nhiên\n• 3 biểu tượng giống nhau → JACKPOT (x10)\n• 2 giống nhau → x2\n• VD: `/slot 10k`",
    }
    return rules.get(game_name, "❌ Không có thông tin.")


# ═══════════════════════════════════════════════════════════
# ANIMATIONS — Imported from new_anims.py
# ═══════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════
# GAME LOGIC
# ═══════════════════════════════════════════════════════════

TAIXIU_SIDES = ["tai", "xiu"]

def _roll_dice(count=3, sides=6):
    return [random.randint(1, sides) for _ in range(count)]


async def _play_taixiu(update, context, side, amount):
    user = update.effective_user
    user_id = user.id
    db = get_user(user_id, user.username or user.first_name)
    if amount > db["balance"]:
        await update.message.reply_text(f"❌ Số dư không đủ! Bạn có {db['balance']:,}đ")
        return
    label = "TÀI" if side == "tai" else "XỈU"
    try:
        await update.message.delete()
    except:
        pass
    dice, anim_msg = await anim_taixiu(context, update.message.chat_id)
    total = sum(dice)
    win_side = "tai" if 11 <= total <= 17 else "xiu"
    is_win = side == win_side
    win_amt = amount * 2 if is_win else 0
    sys.modules[__name__].place_bet(user_id, f"taixiu{side}", amount, {"dice": dice, "total": total}, win_side, win_amt)
    new_bal = get_user(user_id)["balance"]
    de = ["⚀⚁⚂⚃⚄⚅"[d - 1] for d in dice]
    result_text = f"🏆 **THẮNG +{amount:,}đ**" if is_win else f"💀 **THUA -{amount:,}đ**"
    try:
        await anim_msg.delete()
    except:
        pass
    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text=(
            f"🎲 **TÀI XỈU**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"  {de[0]}  {de[1]}  {de[2]} = **{total}**\n"
            f"  Kết quả: **{win_side.upper()}** | Cược: **{label}** {amount:,}đ\n\n"
            f"{result_text}\n"
            f"💰 Số dư: **{new_bal:,}đ**"
        ),
        parse_mode="Markdown",
        reply_markup=kb_back()
    )


# ═══════════════════════════════════════════════════════════
# BAU CUA
# ═══════════════════════════════════════════════════════════

BAUCUA_NAMES = ["bau", "cua", "tom", "ca", "ga", "nai"]
BAUCUA_EMOJIS = {"bau": "🍐", "cua": "🦀", "tom": "🦐", "ca": "🐟", "ga": "🐔", "nai": "🦌"}


async def _play_baucua(update, context, bet_name, amount):
    user = update.effective_user
    user_id = user.id
    db = get_user(user_id, user.username or user.first_name)
    if amount > db["balance"]:
        await update.message.reply_text(f"❌ Số dư không đủ! Bạn có {db['balance']:,}đ")
        return
    bet_name = bet_name.lower()
    if bet_name not in BAUCUA_NAMES:
        await update.message.reply_text("❌ Chọn: bầu, cua, tôm, cá, gà, nai")
        return
    bet_emoji = BAUCUA_EMOJIS.get(bet_name, "❓")
    try:
        await update.message.delete()
    except:
        pass
    rolled, anim_msg = await anim_baucla(context, update.message.chat_id)
    count = rolled.count(BAUCUA_NAMES.index(bet_name))
    if count == 3:
        win_amt = amount * 3
    elif count == 2:
        win_amt = amount * 2
    elif count == 1:
        win_amt = amount * 1
    else:
        win_amt = 0
    sys.modules[__name__].place_bet(user_id, f"baucla_{bet_name}", amount, {"dice": [x+1 for x in rolled], "rolled": rolled}, " ".join(BAUCLA_EMOJI_ANIM[r] for r in rolled), win_amt)
    new_bal = get_user(user_id)["balance"]
    emojis = " ".join(BAUCLA_EMOJI_ANIM[r] for r in rolled)
    names = " • ".join(BAUCLA_NAMES_ANIM[r] for r in rolled)
    res = f"🏆 TRÚNG {matches}! +{win_amt:,}đ (x{matches+1})" if count > 0 else f"💀 KHÔNG TRÚNG -{amount:,}đ"
    try:
        await anim_msg.delete()
    except:
        pass
    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text=(
            f"🦀 **BẦU CUA**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"  {emojis}\n"
            f"  {names}\n\n"
            f"Cược: {bet_emoji} {bet_name} — {amount:,}đ\n"
            f"{res}\n\n"
            f"💰 Số dư: **{new_bal:,}đ**"
        ),
        parse_mode="Markdown",
        reply_markup=kb_back()
    )


# ═══════════════════════════════════════════════════════════
# XÓC ĐĨA
# ═══════════════════════════════════════════════════════════

async def _play_xocdia(update, context, pick, amount):
    user = update.effective_user
    user_id = user.id
    db = get_user(user_id, user.username or user.first_name)
    if amount > db["balance"]:
        await update.message.reply_text(f"❌ Số dư không đủ! Bạn có {db['balance']:,}đ")
        return
    if pick not in (0, 1, 2, 3, 4):
        await update.message.reply_text("❌ Chọn 0-4 (số đồng xu ngửa)!")
        return
    try:
        await update.message.delete()
    except:
        pass
    coins, anim_msg = await anim_xocdia(context, update.message.chat_id)
    actual = sum(coins)
    is_win = actual == pick
    win_amt = amount * 2 if is_win else 0
    sys.modules[__name__].place_bet(user_id, f"xocdia_{pick}", amount, {"coins": coins, "actual": actual}, f"{actual} ngửa", win_amt)
    new_bal = get_user(user_id)["balance"]
    coin_str = " ".join("🔴" if c else "⚫" for c in coins)
    res = f"🏆 TRÚNG! +{amount:,}đ" if is_win else f"💀 SAI -{amount:,}đ"
    try:
        await anim_msg.delete()
    except:
        pass
    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text=(
            f"🪙 **XÓC ĐĨA**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"  {coin_str}\n"
            f"  Số ngửa: **{actual}**\n\n"
            f"Cược: {pick} NGỬA — {amount:,}đ\n"
            f"{res}\n\n"
            f"💰 Số dư: **{new_bal:,}đ**"
        ),
        parse_mode="Markdown",
        reply_markup=kb_back()
    )


# ═══════════════════════════════════════════════════════════
# BLACKJACK
# ═══════════════════════════════════════════════════════════

CARDS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
SUITS = ["♠", "♥", "♦", "♣"]


def _draw_card():
    return random.choice(CARDS) + random.choice(SUITS)


def _hand_value(hand):
    val = 0
    aces = 0
    for c in hand:
        r = c[:-1]
        if r in ("J", "Q", "K"):
            val += 10
        elif r == "A":
            aces += 1
            val += 11
        else:
            val += int(r)
    while val > 21 and aces:
        val -= 10
        aces -= 1
    return val


def _hand_str(hand):
    return " ".join(hand)


def _is_soft(hand):
    """Check if hand contains an Ace counted as 11."""
    val = 0
    aces = 0
    for c in hand:
        r = c[:-1]
        if r == "A":
            aces += 1
            val += 11
        elif r in ("J", "Q", "K"):
            val += 10
        else:
            val += int(r)
    # If we have aces and haven't needed to reduce any, it's soft
    return aces > 0 and val <= 21


async def _play_blackjack(update, context, amount):
    user = update.effective_user
    user_id = user.id
    db = get_user(user_id, user.username or user.first_name)
    if amount > db["balance"]:
        await update.message.reply_text(f"❌ Số dư không đủ! Bạn có {db['balance']:,}đ")
        return
    try:
        await update.message.delete()
    except:
        pass

    # Deal initial cards
    player = [_draw_card(), _draw_card()]
    dealer = [_draw_card(), _draw_card()]
    pv = _hand_value(player)
    dv = _hand_value(dealer)

    # Check for immediate blackjack
    if pv == 21 and dv == 21:
        # Both blackjack - push
        sys.modules[__name__].place_bet(user_id, "blackjack", amount, {"player": _hand_str(player), "dealer": _hand_str(dealer), "pt": pv, "dt": dv}, "push", amount)
        new_bal = get_user(user_id)["balance"]
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text=(
                f"🃏 **BLACKJACK**\n━━━━━━━━━━━━━━━━━━\n"
                f"👤 Bạn: {_hand_str(player)} = **{pv}**\n"
                f"🤖 Dealer: {_hand_str(dealer)} = **{dv}**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🔄 **CẢ HAI BLACKJACK - HÒA**\n"
                f"💰 Số dư: **{new_bal:,}đ**"
            ),
            parse_mode="Markdown"
        )
        return
    elif pv == 21:
        # Player blackjack - win 3:2
        win_amt = int(amount * 2.5)
        sys.modules[__name__].place_bet(user_id, "blackjack", amount, {"player": _hand_str(player), "dealer": _hand_str(dealer), "pt": pv, "dt": dv}, "blackjack", win_amt)
        new_bal = get_user(user_id)["balance"]
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text=(
                f"🃏 **BLACKJACK**\n━━━━━━━━━━━━━━━━━━\n"
                f"👤 Bạn: {_hand_str(player)} = **{pv}**\n"
                f"🤖 Dealer: {_hand_str(dealer)} = **{dv}**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🎉 **BLACKJACK! +{win_amt:,}đ**\n"
                f"💰 Số dư: **{new_bal:,}đ**"
            ),
            parse_mode="Markdown"
        )
        return
    elif dv == 21:
        # Dealer blackjack - player loses
        sys.modules[__name__].place_bet(user_id, "blackjack", amount, {"player": _hand_str(player), "dealer": _hand_str(dealer), "pt": pv, "dt": dv}, "dealer_blackjack", 0)
        new_bal = get_user(user_id)["balance"]
        await context.bot.send_message(
            chat_id=update.message.chat_id,
            text=(
                f"🃏 **BLACKJACK**\n━━━━━━━━━━━━━━━━━━\n"
                f"👤 Bạn: {_hand_str(player)} = **{pv}**\n"
                f"🤖 Dealer: {_hand_str(dealer)} = **{dv}**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💀 **DEALER BLACKJACK! -{amount:,}đ**\n"
                f"💰 Số dư: **{new_bal:,}đ**"
            ),
            parse_mode="Markdown"
        )
        return

    # No blackjack - play the game
    # Show initial state with dealer's upcard
    dealer_upcard = dealer[1]  # Second card is upcard
    dealer_hidden = "❓"
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👆 HIT", callback_data=f"bj_hit_{amount}"),
            InlineKeyboardButton("✋ STAND", callback_data=f"bj_stand_{amount}")
        ],
        [
            InlineKeyboardButton(f"💰 DOUBLE ({amount * 2:,}đ)", callback_data=f"bj_double_{amount}")
        ]
    ])
    msg = await context.bot.send_message(
        chat_id=update.message.chat_id,
        text=(
            f"🃏 **BLACKJACK**\n━━━━━━━━━━━━━━━━━━\n"
            f"👤 Bạn: {_hand_str(player)} = **{pv}**\n"
            f"🤖 Dealer: {dealer[0]} {dealer_hidden}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Chọn: **HIT** (lấy thêm) / **STAND** (đủ) / **DOUBLE** (gấp đôi)"
        ),
        parse_mode="Markdown",
        reply_markup=kb
    )

    # Store game state in session
    s = _get_session(user_id)
    s["bj_game"] = {
        "player": player,
        "dealer": dealer,
        "amount": amount,
        "msg_id": msg.message_id,
        "chat_id": update.message.chat_id
    }


async def bj_hit_callback(query, context, user_id, amount):
    """Player chooses to HIT."""
    s = _get_session(user_id)
    game = s.get("bj_game")
    if not game:
        await query.edit_message_text("❌ Phiên đã hết hạn. Chơi lại với /bj")
        return

    player = game["player"]
    dealer = game["dealer"]
    original_amount = game["amount"]

    # Draw one card
    player.append(_draw_card())
    pv = _hand_value(player)

    if pv > 21:
        # Player busts
        sys.modules[__name__].place_bet(user_id, "blackjack", original_amount, {"player": _hand_str(player), "dealer": _hand_str(dealer), "pt": pv, "dt": _hand_value(dealer)}, "bust", 0)
        new_bal = get_user(user_id)["balance"]
        try:
            await query.message.delete()
        except:
            pass
        await context.bot.send_message(
            chat_id=game["chat_id"],
            text=(
                f"🃏 **BLACKJACK**\n━━━━━━━━━━━━━━━━━━\n"
                f"👤 Bạn: {_hand_str(player)} = **{pv}** 💥\n"
                f"🤖 Dealer: {_hand_str(dealer)} = **{_hand_value(dealer)}**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💀 **BUST! -{original_amount:,}đ**\n"
                f"💰 Số dư: **{new_bal:,}đ**"
            ),
            parse_mode="Markdown"
        )
        s.pop("bj_game", None)
        return

    # Check if player has 21
    if pv == 21:
        # Auto stand on 21
        await _dealer_play(query, context, user_id, game)
        return

    # Show updated hand, allow more hits
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👆 HIT", callback_data=f"bj_hit_{original_amount}"),
            InlineKeyboardButton("✋ STAND", callback_data=f"bj_stand_{original_amount}")
        ],
        [
            InlineKeyboardButton(f"💰 DOUBLE ({original_amount * 2:,}đ)", callback_data=f"bj_double_{original_amount}")
        ]
    ])
    await query.edit_message_text(
        text=(
            f"🃏 **BLACKJACK**\n━━━━━━━━━━━━━━━━━━\n"
            f"👤 Bạn: {_hand_str(player)} = **{pv}**\n"
            f"🤖 Dealer: {dealer[0]} ❓\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Chọn: **HIT** / **STAND** / **DOUBLE**"
        ),
        parse_mode="Markdown",
        reply_markup=kb
    )


async def bj_stand_callback(query, context, user_id, amount):
    """Player chooses to STAND."""
    s = _get_session(user_id)
    game = s.get("bj_game")
    if not game:
        await query.edit_message_text("❌ Phiên đã hết hạn. Chơi lại với /bj")
        return

    await _dealer_play(query, context, user_id, game)


async def bj_double_callback(query, context, user_id, amount):
    """Player chooses to DOUBLE DOWN."""
    s = _get_session(user_id)
    game = s.get("bj_game")
    if not game:
        await query.edit_message_text("❌ Phiên đã hết hạn. Chơi lại với /bj")
        return

    player = game["player"]
    dealer = game["dealer"]
    original_amount = game["amount"]

    # Check if player has enough balance
    db = get_user(user_id)
    if original_amount > db["balance"]:
        await query.edit_message_text(f"❌ Số dư không đủ để DOUBLE! Bạn có {db['balance']:,}đ")
        return

    # Double the bet
    game["amount"] = original_amount * 2

    # Draw exactly one card
    player.append(_draw_card())
    pv = _hand_value(player)

    if pv > 21:
        # Player busts after double
        sys.modules[__name__].place_bet(user_id, "blackjack", original_amount * 2, {"player": _hand_str(player), "dealer": _hand_str(dealer), "pt": pv, "dt": _hand_value(dealer), "doubled": True}, "bust", 0)
        new_bal = get_user(user_id)["balance"]
        try:
            await query.message.delete()
        except:
            pass
        await context.bot.send_message(
            chat_id=game["chat_id"],
            text=(
                f"🃏 **BLACKJACK** (DOUBLE)\n━━━━━━━━━━━━━━━━━━\n"
                f"👤 Bạn: {_hand_str(player)} = **{pv}** 💥\n"
                f"🤖 Dealer: {_hand_str(dealer)} = **{_hand_value(dealer)}**\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💀 **BUST! -{original_amount * 2:,}đ**\n"
                f"💰 Số dư: **{new_bal:,}đ**"
            ),
            parse_mode="Markdown"
        )
        s.pop("bj_game", None)
        return

    # Auto stand after double
    await _dealer_play(query, context, user_id, game)


async def _dealer_play(query, context, user_id, game):
    """Dealer plays according to rules: hit on 16 or less, stand on 17+."""
    player = game["player"]
    dealer = game["dealer"]
    amount = game["amount"]

    pv = _hand_value(player)

    # Dealer hits on 16 or less, stands on 17+
    while _hand_value(dealer) < 17:
        dealer.append(_draw_card())

    dv = _hand_value(dealer)

    # Determine winner
    if dv > 21:
        result = "dealer_bust"
        win_amt = amount * 2
        result_text = f"🏆 **THẮNG! +{win_amt:,}đ**"
    elif pv > dv:
        result = "win"
        win_amt = amount * 2
        result_text = f"🏆 **THẮNG! +{win_amt:,}đ**"
    elif pv == dv:
        result = "push"
        win_amt = amount
        result_text = f"🔄 **HÒA**"
    else:
        result = "lose"
        win_amt = 0
        result_text = f"💀 **THUA! -{amount:,}đ**"

    sys.modules[__name__].place_bet(user_id, "blackjack", amount, {"player": _hand_str(player), "dealer": _hand_str(dealer), "pt": pv, "dt": dv}, result, win_amt)
    new_bal = get_user(user_id)["balance"]

    try:
        await query.message.delete()
    except:
        pass

    await context.bot.send_message(
        chat_id=game["chat_id"],
        text=(
            f"🃏 **BLACKJACK**\n━━━━━━━━━━━━━━━━━━\n"
            f"👤 Bạn: {_hand_str(player)} = **{pv}**\n"
            f"🤖 Dealer: {_hand_str(dealer)} = **{dv}**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"{result_text}\n"
            f"💰 Số dư: **{new_bal:,}đ**"
        ),
        parse_mode="Markdown"
    )
    _get_session(user_id).pop("bj_game", None)


# ═══════════════════════════════════════════════════════════
# ROULETTE
# ═══════════════════════════════════════════════════════════

RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}


async def _play_roulette(update, context, bet_type, amount):
    user = update.effective_user
    user_id = user.id
    db = get_user(user_id, user.username or user.first_name)
    if amount > db["balance"]:
        await update.message.reply_text(f"❌ Số dư không đủ! Bạn có {db['balance']:,}đ")
        return
    bt = bet_type.lower()
    number, anim_msg = await anim_roulette(context, update.message.chat_id)
    col = "green" if number == 0 else ("red" if number in RED_NUMBERS else "black")
    col_e = "🟢" if col == "green" else ("🔴" if col == "red" else "⚫")
    col_name = "XANH" if col == "green" else ("ĐỎ" if col == "red" else "ĐEN")

    try:
        bet_num = int(bet_type)
        is_win = number == bet_num
        mult = 35
    except:
        if bt in ("red", "do"):
            is_win = col == "red"
        elif bt in ("black", "den"):
            is_win = col == "black"
        elif bt in ("odd", "le"):
            is_win = number % 2 == 1 and number != 0
        elif bt in ("even", "chan"):
            is_win = number % 2 == 0 and number != 0
        else:
            is_win = False
        mult = 1

    win_amt = amount * (mult + 1) if is_win else 0
    sys.modules[__name__].place_bet(user_id, f"roulette_{bt}", amount, {"number": number, "color": col}, f"{col_e} {number}", win_amt)
    new_bal = get_user(user_id)["balance"]
    labels = {"red": "🔴 Đỏ", "black": "⚫ Đen", "odd": "🔢 Lẻ", "even": "🟡 Chẵn"}
    res = f"🏆 THẮNG +{win_amt:,}đ" if is_win else f"💀 THUA -{amount:,}đ"
    try:
        await anim_msg.delete()
    except:
        pass
    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text=(
            f"🎡 **ROULETTE**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"  {col_e} **{number}** ({col_name})\n\n"
            f"Cược: {labels.get(bt, bt)} — {amount:,}đ\n"
            f"{res}\n\n"
            f"💰 Số dư: **{new_bal:,}đ**"
        ),
        parse_mode="Markdown",
        reply_markup=kb_back()
    )


# ═══════════════════════════════════════════════════════════
# SLOT MACHINE
# ═══════════════════════════════════════════════════════════

SLOT_SYMBOLS = ["🍒", "🍋", "🍊", "🍇", "🔔", "💎", "7️⃣", "⭐"]


async def _play_slot(update, context, amount):
    user = update.effective_user
    user_id = user.id
    db = get_user(user_id, user.username or user.first_name)
    if amount > db["balance"]:
        await update.message.reply_text(f"❌ Số dư không đủ! Bạn có {db['balance']:,}đ")
        return
    try:
        await update.message.delete()
    except:
        pass
    result, anim_msg = await anim_slot(context, update.message.chat_id)
    if result[0] == result[1] == result[2]:
        win_amt = amount * 10
        wt = "🎰 JACKPOT! x10 🎰"
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        win_amt = amount * 2
        wt = "✨ TRÚNG 2! x2 ✨"
    else:
        win_amt = 0
        wt = "💀 Không trúng"
    sys.modules[__name__].place_bet(user_id, "slot", amount, {"reels": result}, " ".join(result), win_amt)
    new_bal = get_user(user_id)["balance"]
    try:
        await anim_msg.delete()
    except:
        pass
    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text=(
            f"🎰 **SLOT MACHINE**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"  {result[0]}  {result[1]}  {result[2]}\n\n"
            f"Cược: {amount:,}đ\n"
            f"{wt}\n"
            f"{'+' if win_amt > 0 else '-'}{win_amt:,}đ\n\n"
            f"💰 Số dư: **{new_bal:,}đ**"
        ),
        parse_mode="Markdown",
        reply_markup=kb_back()
    )


# ── Quick-bet execution (from inline callbacks) ──

async def _qb_play_taixiu(query, context, side, amount):
    user = query.from_user
    user_id = user.id
    db = get_user(user_id, user.username or user.first_name)
    if amount > db["balance"]:
        await query.edit_message_text(f"❌ Số dư không đủ! Bạn có {db['balance']:,}đ", reply_markup=_kb_qb_back("taixiu"))
        return
    label = "TÀI" if side == "tai" else "XỈU"
    dice, anim_msg = await anim_taixiu(context, query.message.chat_id)
    total = sum(dice)
    win_side = "tai" if 11 <= total <= 17 else "xiu"
    is_win = side == win_side
    win_amt = amount * 2 if is_win else 0
    sys.modules[__name__].place_bet(user_id, f"taixiu{side}", amount, {"dice": dice, "total": total}, win_side, win_amt)
    new_bal = get_user(user_id)["balance"]
    de = ["⚀⚁⚂⚃⚄⚅"[d - 1] for d in dice]
    result_text = f"🏆 **THẮNG +{amount:,}đ**" if is_win else f"💀 **THUA -{amount:,}đ**"
    try:
        await anim_msg.delete()
    except:
        pass
    await query.edit_message_text(
        f"🎲 **TÀI XỈU**\n━━━━━━━━━━━━━━━━━━\n"
        f"  {de[0]}  {de[1]}  {de[2]} = **{total}**\n"
        f"  Kết quả: **{win_side.upper()}** | Cược: **{label}** {amount:,}đ\n\n"
        f"{result_text}\n"
        f"💰 Số dư: **{new_bal:,}đ**",
        parse_mode="Markdown", reply_markup=kb_back())

async def _qb_play_baucua(query, context, bet_name, amount):
    user = query.from_user
    user_id = user.id
    db = get_user(user_id, user.username or user.first_name)
    if amount > db["balance"]:
        await query.edit_message_text(f"❌ Số dư không đủ! Bạn có {db['balance']:,}đ", reply_markup=_kb_qb_back("baucua"))
        return
    # Run animation
    rolled, anim_msg = await anim_baucla(context, query.message.chat_id)
    count = rolled.count(BAUCUA_NAMES.index(bet_name))
    if count == 3:
        win_amt = amount * 3
    elif count == 2:
        win_amt = amount * 2
    elif count == 1:
        win_amt = amount * 1
    else:
        win_amt = 0
    sys.modules[__name__].place_bet(user_id, f"baucla_{bet_name}", amount, {"dice": [x+1 for x in rolled], "rolled": rolled}, " ".join(BAUCLA_EMOJI_ANIM[r] for r in rolled), win_amt)
    emojis = " ".join(BAUCLA_EMOJI_ANIM[r] for r in rolled)
    new_bal = get_user(user_id)["balance"]
    result_text = f"✅ **THẮNG +{win_amt:,}đ**" if win_amt > 0 else f"❌ **THUA -{amount:,}đ**"
    try:
        await anim_msg.delete()
    except:
        pass
    await query.edit_message_text(
        f"🦀 **BẦU CUA**\n━━━━━━━━━━━━━━━━━━\n"
        f"{emojis}\n"
        f"Cược: **{bet_name}** x **{amount:,}đ**\n"
        f"Xuất hiện **{count}** lần\n\n"
        f"{result_text}\n"
        f"💰 Số dư: **{new_bal:,}đ**",
        parse_mode="Markdown", reply_markup=kb_back())
    await query.message.reply_text(
        f"🦀 Bầu Cua | {'✅ THẮNG' if win_amt > 0 else '❌ THUA'} **{win_amt:,}đ**",
        parse_mode="Markdown")

async def _qb_play_xocdia(query, context, pick, amount):
    user = query.from_user
    user_id = user.id
    db = get_user(user_id, user.username or user.first_name)
    if amount > db["balance"]:
        await query.edit_message_text(f"❌ Số dư không đủ! Bạn có {db['balance']:,}đ", reply_markup=_kb_qb_back("xocdia"))
        return
    # Run animation
    coins, anim_msg = await anim_xocdia(context, query.message.chat_id)
    actual = sum(coins)
    is_win = actual == pick
    win_amt = amount * 2 if is_win else 0
    sys.modules[__name__].place_bet(user_id, f"xocdia_{pick}", amount, {"coins": coins, "actual": actual}, f"{actual} ngửa", win_amt)
    coin_str = " ".join(["🔴" if c else "⚫" for c in coins])
    ngua_bar = "🔴" * actual + "⚫" * (4 - actual)
    new_bal = get_user(user_id)["balance"]
    result_text = f"✅ **THẮNG +{win_amt:,}đ**" if is_win else f"❌ **THUA -{amount:,}đ**"
    try:
        await anim_msg.delete()
    except:
        pass
    await query.edit_message_text(
        f"🪙 **XÓC ĐĨA**\n━━━━━━━━━━━━━━━━━━\n"
        f"{coin_str} → **{actual}** ngửa {ngua_bar}\n"
        f"Cược: **{pick}** ngửa x **{amount:,}đ**\n\n"
        f"{result_text}\n"
        f"💰 Số dư: **{new_bal:,}đ**",
        parse_mode="Markdown", reply_markup=kb_back())
    await query.message.reply_text(
        f"🪙 Xóc Đĩa | {'✅ THẮNG' if is_win else '❌ THUA'} **{win_amt:,}đ**",
        parse_mode="Markdown")

async def _qb_play_roulette(query, context, bet_type, amount):
    user = query.from_user
    user_id = user.id
    db = get_user(user_id, user.username or user.first_name)
    if amount > db["balance"]:
        await query.edit_message_text(f"❌ Số dư không đủ! Bạn có {db['balance']:,}đ", reply_markup=_kb_qb_back("roulette"))
        return
    # Run animation
    number, anim_msg = await anim_roulette(context, query.message.chat_id)
    col = "red" if number in RED_NUMBERS else ("black" if number != 0 else "green")
    col_e = "🔴" if col == "red" else ("⚫" if col == "black" else "🟢")
    bt = bet_type.lower()
    if bt in ("red",):
        is_win = col == "red"
    elif bt in ("black",):
        is_win = col == "black"
    elif bt in ("odd",):
        is_win = number % 2 == 1 and number != 0
    elif bt in ("even",):
        is_win = number % 2 == 0 and number != 0
    else:
        is_win = False
    win_amt = amount * 2 if is_win else 0
    sys.modules[__name__].place_bet(user_id, f"roulette_{bt}", amount, {"number": number, "color": col}, f"{col_e} {number}", win_amt)
    new_bal = get_user(user_id)["balance"]
    result_text = f"✅ **THẮNG +{win_amt:,}đ**" if is_win else f"❌ **THUA -{amount:,}đ**"
    try:
        await anim_msg.delete()
    except:
        pass
    await query.edit_message_text(
        f"🎡 **ROULETTE**\n━━━━━━━━━━━━━━━━━━\n"
        f"Kết quả: {col_e} **{number}**\n"
        f"Cược: **{bt}** x **{amount:,}đ**\n\n"
        f"{result_text}\n"
        f"💰 Số dư: **{new_bal:,}đ**",
        parse_mode="Markdown", reply_markup=kb_back())
    await query.message.reply_text(
        f"🎡 Roulette | {'✅ THẮNG' if is_win else '❌ THUA'} **{win_amt:,}đ**",
        parse_mode="Markdown")

async def _qb_play_bj(query, context, amount):
    user = query.from_user
    user_id = user.id
    db = get_user(user_id, user.username or user.first_name)
    if amount > db["balance"]:
        await query.edit_message_text(f"❌ Số dư không đủ! Bạn có {db['balance']:,}đ", reply_markup=_kb_qb_back("blackjack"))
        return

    # Deal initial cards
    player = [_draw_card(), _draw_card()]
    dealer = [_draw_card(), _draw_card()]
    pv = _hand_value(player)
    dv = _hand_value(dealer)

    # Check for immediate blackjack
    if pv == 21 and dv == 21:
        sys.modules[__name__].place_bet(user_id, "blackjack", amount, {"player": _hand_str(player), "dealer": _hand_str(dealer), "pt": pv, "dt": dv}, "push", amount)
        new_bal = get_user(user_id)["balance"]
        await query.edit_message_text(
            f"🃏 **BLACKJACK**\n━━━━━━━━━━━━━━━━━━\n"
            f"👤 Bạn: {_hand_str(player)} = **{pv}**\n"
            f"🤖 Dealer: {_hand_str(dealer)} = **{dv}**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔄 **CẢ HAI BLACKJACK - HÒA**\n"
            f"💰 Số dư: **{new_bal:,}đ**",
            parse_mode="Markdown", reply_markup=kb_back())
        return
    elif pv == 21:
        win_amt = int(amount * 2.5)
        sys.modules[__name__].place_bet(user_id, "blackjack", amount, {"player": _hand_str(player), "dealer": _hand_str(dealer), "pt": pv, "dt": dv}, "blackjack", win_amt)
        new_bal = get_user(user_id)["balance"]
        await query.edit_message_text(
            f"🃏 **BLACKJACK**\n━━━━━━━━━━━━━━━━━━\n"
            f"👤 Bạn: {_hand_str(player)} = **{pv}**\n"
            f"🤖 Dealer: {_hand_str(dealer)} = **{dv}**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎉 **BLACKJACK! +{win_amt:,}đ**\n"
            f"💰 Số dư: **{new_bal:,}đ**",
            parse_mode="Markdown", reply_markup=kb_back())
        return
    elif dv == 21:
        sys.modules[__name__].place_bet(user_id, "blackjack", amount, {"player": _hand_str(player), "dealer": _hand_str(dealer), "pt": pv, "dt": dv}, "dealer_blackjack", 0)
        new_bal = get_user(user_id)["balance"]
        await query.edit_message_text(
            f"🃏 **BLACKJACK**\n━━━━━━━━━━━━━━━━━━\n"
            f"👤 Bạn: {_hand_str(player)} = **{pv}**\n"
            f"🤖 Dealer: {_hand_str(dealer)} = **{dv}**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💀 **DEALER BLACKJACK! -{amount:,}đ**\n"
            f"💰 Số dư: **{new_bal:,}đ**",
            parse_mode="Markdown", reply_markup=kb_back())
        return

    # No blackjack - play the game interactively
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👆 HIT", callback_data=f"bj_hit_{amount}"),
            InlineKeyboardButton("✋ STAND", callback_data=f"bj_stand_{amount}")
        ],
        [
            InlineKeyboardButton(f"💰 DOUBLE ({amount * 2:,}đ)", callback_data=f"bj_double_{amount}")
        ],
        [
            InlineKeyboardButton("← Mức cược", callback_data="game_blackjack")
        ]
    ])
    await query.edit_message_text(
        f"🃏 **BLACKJACK**\n━━━━━━━━━━━━━━━━━━\n"
        f"👤 Bạn: {_hand_str(player)} = **{pv}**\n"
        f"🤖 Dealer: {dealer[0]} ❓\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Chọn: **HIT** (lấy thêm) / **STAND** (đủ) / **DOUBLE** (gấp đôi)",
        parse_mode="Markdown",
        reply_markup=kb
    )

    # Store game state in session
    s = _get_session(user_id)
    s["bj_game"] = {
        "player": player,
        "dealer": dealer,
        "amount": amount,
        "msg_id": query.message.message_id,
        "chat_id": query.message.chat_id
    }

async def _qb_play_slot(query, context, amount):
    user = query.from_user
    user_id = user.id
    db = get_user(user_id, user.username or user.first_name)
    if amount > db["balance"]:
        await query.edit_message_text(f"❌ Số dư không đủ! Bạn có {db['balance']:,}đ", reply_markup=_kb_qb_back("slot"))
        return
    # Run animation
    result, anim_msg = await anim_slot(context, query.message.chat_id)
    is_jackpot = result[0] == result[1] == result[2]
    is_pair = not is_jackpot and (result[0] == result[1] or result[1] == result[2] or result[0] == result[2])
    if is_jackpot:
        win_amt = amount * 10
    elif is_pair:
        win_amt = amount * 2
    else:
        win_amt = 0
    sys.modules[__name__].place_bet(user_id, "slot", amount, {"reels": result}, " ".join(result), win_amt)
    label = "✅ JACKPOT!" if is_jackpot else ("✅ TRÚNG 2!" if is_pair else "❌ THUA")
    new_bal = get_user(user_id)["balance"]
    try:
        await anim_msg.delete()
    except:
        pass
    await query.edit_message_text(
        f"🎰 **SLOT MACHINE**\n━━━━━━━━━━━━━━━━━━\n"
        f"│ {' │ '.join(result)} │\n"
        f"Cược: **{amount:,}đ**\n\n"
        f"→ **{label}** **{win_amt:,}đ**\n"
        f"💰 Số dư: **{new_bal:,}đ**",
        parse_mode="Markdown", reply_markup=kb_back())
    await query.message.reply_text(
        f"🎰 Slot | {label} **{win_amt:,}đ**",
        parse_mode="Markdown")


# ═══════════════════════════════════════════════════════════
# CALLBACK HANDLERS
# ═══════════════════════════════════════════════════════════

async def callback_router(update, context):
    query = update.callback_query
    user = update.effective_user
    user_id = user.id
    data = query.data

    # ── Menu chính ──
    if data == "menu":
        await query.edit_message_text(_menu_text(user_id, user.first_name), parse_mode="Markdown", reply_markup=kb_main_menu())

    # ── Game callbacks (quick-bet + command) ──
    elif data == "game_taixiu":
        s = _get_session(user_id)
        s["awaiting_game"] = "taixiu"
        await query.edit_message_text(
            "🎲 **TÀI XỈU**\n━━━━━━━━━━━━━━━━━━\n"
            "Chọn mức cược nhanh bên dưới, hoặc gõ lệnh:\n"
            "`/tai 10k` / `/xiu 10k`\n\n"
            "Gõ /cancel để hủy.",
            parse_mode="Markdown", reply_markup=_kb_qb_amounts("taixiu"))

    elif data == "game_baucua":
        s = _get_session(user_id)
        s["awaiting_game"] = "baucua"
        await query.edit_message_text(
            "🦀 **BẦU CUA**\n━━━━━━━━━━━━━━━━━━\n"
            "Chọn mức cược nhanh bên dưới, hoặc gõ lệnh:\n"
            "`/bau cua 10k`\n\n"
            "Gõ /cancel để hủy.",
            parse_mode="Markdown", reply_markup=_kb_qb_amounts("baucua"))

    elif data == "game_xocdia":
        s = _get_session(user_id)
        s["awaiting_game"] = "xocdia"
        await query.edit_message_text(
            "🪙 **XÓC ĐĨA**\n━━━━━━━━━━━━━━━━━━\n"
            "Chọn mức cược nhanh bên dưới, hoặc gõ lệnh:\n"
            "`/xoc 2 10k` (đoán số ngửa 0-4)\n\n"
            "Gõ /cancel để hủy.",
            parse_mode="Markdown", reply_markup=_kb_qb_amounts("xocdia"))

    elif data == "game_blackjack":
        s = _get_session(user_id)
        s["awaiting_game"] = "blackjack"
        await query.edit_message_text(
            "🃏 **BLACKJACK**\n━━━━━━━━━━━━━━━━━━\n"
            "Chọn mức cược nhanh bên dưới, hoặc gõ lệnh:\n"
            "`/bj 10k`\n\n"
            "Gõ /cancel để hủy.",
            parse_mode="Markdown", reply_markup=_kb_qb_amounts("bj"))

    elif data == "game_roulette":
        s = _get_session(user_id)
        s["awaiting_game"] = "roulette"
        await query.edit_message_text(
            "🎡 **ROULETTE**\n━━━━━━━━━━━━━━━━━━\n"
            "Chọn mức cược nhanh bên dưới, hoặc gõ lệnh:\n"
            "`/ru red 10k`\n"
            "Cược: red/black/odd/even hoặc số 0-36\n\n"
            "Gõ /cancel để hủy.",
            parse_mode="Markdown", reply_markup=_kb_qb_amounts("roulette"))

    elif data == "game_slot":
        s = _get_session(user_id)
        s["awaiting_game"] = "slot"
        await query.edit_message_text(
            "🎰 **SLOT MACHINE**\n━━━━━━━━━━━━━━━━━━\n"
            "Chọn mức cược nhanh bên dưới, hoặc gõ lệnh:\n"
            "`/slot 10k`\n\n"
            "Gõ /cancel để hủy.",
            parse_mode="Markdown", reply_markup=_kb_qb_amounts("slot"))

    # ── Rank ──
    elif data == "show_rank":
        db = get_user(user_id)
        bal = db["balance"]
        try:
            from taixiu_features import get_rank_display, get_next_rank_info, get_rank_progress
            progress = get_rank_progress(bal)
            lines = [
                "🏅 **CẤP BẬC**\n━━━━━━━━━━━━━━━━━━",
                f"",
                f"🔹 **{get_rank_display(bal)}**",
            ]
            if progress:
                lines.append(f"   {progress}")
            next_r = get_next_rank_info(bal)
            if next_r:
                e, ti, need = next_r
                lines.append(f"   Cần thêm **{need:,}đ** để lên {e} {ti}")
            else:
                lines.append(f"   🏆 **ĐÃ ĐẠT CẤP CAO NHẤT!** 🏆")
            lines.append(f"\n📌 Cấp bậc dựa trên **số dư**")
            await query.edit_message_text("\n".join(lines), parse_mode="Markdown", reply_markup=kb_back())
        except ImportError:
            await query.edit_message_text("⚠️ Rank system chưa load.", reply_markup=kb_back())

    # ── Level ──
    elif data == "show_level":
        db = get_user(user_id)
        level = db.get("level", 1)
        exp = db.get("exp", 0)
        try:
            from taixiu_features import get_exp_needed, get_next_reward_info, get_level_display
            needed = get_exp_needed(level)
            next_rlv, next_ramt = get_next_reward_info(level)
            lines = [
                f"⭐ **LEVEL SYSTEM**",
                f"━━━━━━━━━━━━━━━━━━",
                f"",
                f"📊 {get_level_display(level, exp)}",
                f"",
                f"📈 EXP cần để lên level: **{needed}**",
                f"🎯 Mỗi ván: **+1 EXP**",
            ]
            if next_rlv:
                lines.append(f"")
                lines.append(f"🎁 Reward tiếp: Level **{next_rlv}** → **{next_ramt:,}đ**")
            else:
                lines.append(f"")
                lines.append(f"🏆 **MAX LEVEL!** 🏆")
        except ImportError:
            lines = [f"⭐ **LEVEL**\n━━━━━━━━━━━━━━━━━━\nLevel **{level}** | EXP **{exp}**\n\n⚠️ Feature chưa load"]
        await query.edit_message_text("\n".join(lines), parse_mode="Markdown", reply_markup=kb_back())

    # ── Help ──
    elif data == "help":
        await query.edit_message_text(
            "❓ **TRỢ GIÚP**\n━━━━━━━━━━━━━━━━━━\n"
            "🎰 **CÁC TRÒ CHƠI**\n"
            "  • /tai - Tài Xỉu\n"
            "  • /xiu - Tài Xỉu\n"
            "  • /bau - Bầu Cua\n"
            "  • /xoc - Xóc Đĩa\n"
            "  • /bj - Blackjack\n"
            "  • /ru - Roulette\n"
            "  • /slot - Slot Machine\n\n"
            "📊 **TIỆN ÍCH**\n"
            "  • /rank - Xem cấp bậc\n"
            "  • /level - Xem Level & EXP\n"
            "  • /giftcode - Nhập code\n"
            "  • /reset - Reset tài khoản\n\n"
            "💡 Mỗi ván chơi được **+1 EXP**\n"
            "💊 Thua liên tiếp được **Payback**\n"
            "🏆 Cấp bậc tăng theo **số dư**",
            parse_mode="Markdown", reply_markup=kb_back()
        )
    # ── History ──
    elif data == "show_history":
        h = get_history(user_id, 10)
        if not h:
            await query.edit_message_text("📊 **LỊCH SỬ**\n━━━━━━━━━━━━━━━━━━\nChưa có ván nào.", parse_mode="Markdown", reply_markup=kb_back())
            return
        lines = ["📊 **LỊCH SỬ 10 VÁN GẦN NHẤT**\n━━━━━━━━━━━━━━━━━━"]
        for r in h:
            lines.append(_fmt_hist(r))
        await query.edit_message_text("\n".join(lines), parse_mode="Markdown", reply_markup=kb_back())

    # ── Leaderboard ──
    elif data == "leaderboard":
        top = get_top_users(10)
        if not top:
            await query.edit_message_text("🏆 **BẢNG XẾP HẠNG**\n━━━━━━━━━━━━━━━━━━\nChưa có người chơi.", parse_mode="Markdown", reply_markup=kb_back())
            return
        lines = ["🏆 **BẢNG XẾP HẠNG (TOP 10)**\n━━━━━━━━━━━━━━━━━━"]
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for i, u in enumerate(top):
            name = u.get("username") or f"User {u['user_id']}"
            lines.append(f"{medals[i]} **{name}** — {u['balance']:,}đ (W{u['total_wins']}/L{u['total_losses']})")
        await query.edit_message_text("\n".join(lines), parse_mode="Markdown", reply_markup=kb_back())

    # ── Admin panel ──
    elif data == "adm_panel":
        await query.edit_message_text("🔑 **ADMIN PANEL** — Chọn hành động:", parse_mode="Markdown", reply_markup=kb_admin())

    elif data == "adm_stats":
        stats = admin_get_stats()
        await query.edit_message_text(
            f"📊 **THỐNG KÊ TOÀN BỘ**\n━━━━━━━━━━━━━━━━━━\n"
            f"👥 Tổng User: **{stats['total_users']}**\n"
            f"🎲 Tổng Ván: **{stats['total_bets']}**\n"
            f"💰 Tổng Số Dư: **{stats['total_balance']:,}đ**",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Quay lại", callback_data="adm_panel")]])
        )

    elif data == "adm_users":
        users = get_all_users()
        lines = ["👥 **DANH SÁCH USER**\n━━━━━━━━━━━━━━━━━━"]
        if users:
            for u in users:
                name = u.get("username") or f"ID:{u['user_id']}"
                lines.append(f"• `{u['user_id']}` {name} — {u['balance']:,}đ ({u['total_bets']} ván)")
            if len(lines) > 50:
                lines = lines[:50] + ["", f"... và {len(users) - 50} user khác"]
        else:
            lines.append("Chưa có user nào.")
        await query.edit_message_text("\n".join(lines), parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Quay lại", callback_data="adm_panel")]]))

    elif data == "adm_setbal":
        s = _get_session(user_id)
        s["adm_setbal"] = True
        await query.edit_message_text("💰 Gõ: `user_id amount`", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Hủy", callback_data="adm_panel")]]))

    elif data == "adm_reset":
        s = _get_session(user_id)
        s["adm_reset"] = True
        await query.edit_message_text("🔄 Gõ: `user_id`", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Hủy", callback_data="adm_panel")]]))

    elif data == "adm_del":
        s = _get_session(user_id)
        s["adm_del"] = True
        await query.edit_message_text("🗑️ Gõ: `user_id`", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Hủy", callback_data="adm_panel")]]))

    elif data == "adm_search":
        s = _get_session(user_id)
        s["adm_search"] = True
        await query.edit_message_text("🔍 Gõ **user\\_id** hoặc **username** để tra cứu:\n\nGõ /cancel để hủy.", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Hủy", callback_data="adm_panel")]]))

    elif data == "adm_setlevel":
        s = _get_session(user_id)
        s["adm_setlevel"] = True
        await query.edit_message_text(
            "⭐ **SET LEVEL USER**\n\n"
            "Gõ: `user_id level [exp]`\n"
            "VD: `123456 50 0` hoặc `123456 100 5`\n\n"
            "Level: 1-1000\n"
            "Gõ /cancel để hủy.",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Hủy", callback_data="adm_panel")]])
        )

    elif data == "adm_odds":
        cfg = get_game_config()
        lines = [
            "⚙️ **TỶ LỆ TRÒ CHƠI**\n━━━━━━━━━━━━━━━━━━\n",
            f"🎲 Tài Xỉu: **x{cfg['taixiu_mult']:.0f}**",
            f"🪙 Xóc Đĩa: **x{cfg['xocdia_mult']:.0f}**",
            f"🎡 Roulette Đỏ/Đen/Lẻ/Chẵn: **x{cfg['roulette_color_mult']:.0f}**",
            f"🎡 Roulette Số cụ thể: **x{cfg['roulette_number_mult']:.0f}**",
            f"🎰 Slot JACKPOT: **x{cfg['slot_jackpot_mult']:.0f}**",
            f"🎰 Slot TRÚNG 2: **x{cfg['slot_pair_mult']:.0f}**",
            f"🃏 Blackjack thường: **x{cfg['bj_normal_mult']:.0f}**",
            f"🃏 BLACKJACK: **x{cfg['bj_blackjack_mult']:.0f}**",
            "",
            "Gõ: `key value`\nVD: `taixiu_mult 3`\n"
            "Gõ `reset` để về mặc định\n"
            "Gõ /cancel để hủy.",
        ]
        await query.edit_message_text(
            "\n".join(lines), parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Hủy", callback_data="adm_panel")]])
        )
        s = _get_session(user_id)
        s["adm_odds"] = True

    # ── Giftcode management ──
    elif data == "adm_giftcode":
        gc_list = get_giftcode_list()
        if gc_list:
            lines = ["🎟️ **QUẢN LÝ GIFTCODE**\n━━━━━━━━━━━━━━━━━━\n"]
            for gc in gc_list[:10]:
                status = "✅" if gc["used_count"] < gc["max_uses"] else "❌"
                lines.append(f"{status} `{gc['code']}` — {gc['amount']:,}đ ({gc['used_count']}/{gc['max_uses']} lượt)")
            lines.append(f"\nGõ: **/giftcode tạo <CODE> <số tiền> [số lượt]**")
            lines.append(f"Gõ: **/giftcode xóa <CODE>**")
        else:
            lines = ["🎟️ **QUẢN LÝ GIFTCODE**\n━━━━━━━━━━━━━━━━━━\nChưa có giftcode nào."]
            lines.append(f"\nGõ: **/giftcode tạo <CODE> <số tiền> [số lượt]**")
        await query.edit_message_text(
            "\n".join(lines), parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Quay lại", callback_data="adm_panel")]])
        )

    # ── Broadcast ──
    elif data == "adm_broadcast":
        s = _get_session(user_id)
        s["adm_broadcast"] = True
        await query.edit_message_text("📢 Gõ nội dung broadcast:\n\nGõ /cancel để hủy.", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Hủy", callback_data="adm_panel")]]))

    # ── Gift all ──
    elif data == "adm_gift_all":
        s = _get_session(user_id)
        s["adm_gift_all"] = True
        await query.edit_message_text("🎁 Gõ số tiền muốn tặng mỗi user:\n\nGõ /cancel để hủy.", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Hủy", callback_data="adm_panel")]]))

    # ── Quick-bet: amount selected → show game option keyboard ──
    elif "_amt_" in data:
        parts = data.split("_amt_")
        game = parts[0].replace("qb_", "")
        amount = int(parts[1])
        s = _get_session(user_id)
        s["awaiting_game"] = game
        kbs = {
            "taixiu": _kb_qb_taixiu,
            "baucua": _kb_qb_baucua,
            "xocdia": _kb_qb_xocdia,
            "bj": _kb_qb_blackjack,
            "blackjack": _kb_qb_blackjack,
            "roulette": _kb_qb_roulette,
            "slot": _kb_qb_slot,
        }
        kb_fn = kbs.get(game)
        if kb_fn:
            await query.edit_message_text(
                f"🎲 **{game.upper()}** — Cược **{amount:,}đ**\nChọn bên bạn muốn cược:",
                parse_mode="Markdown", reply_markup=kb_fn(amount))
        else:
            await query.answer("Không hỗ trợ")
        return

    # ── Quick-bet: Tài Xỉu ──
    elif data.startswith("qb_taixiu_"):
        parts = data.split("_")
        side = parts[2]
        amount = int(parts[3])
        await _qb_play_taixiu(query, context, side, amount)

    # ── Quick-bet: Bầu Cua ──
    elif data.startswith("qb_baucua_"):
        parts = data.split("_")
        bet_name = parts[2]
        amount = int(parts[3])
        await _qb_play_baucua(query, context, bet_name, amount)

    # ── Quick-bet: Xóc Đĩa ──
    elif data.startswith("qb_xocdia_"):
        parts = data.split("_")
        pick = int(parts[2])
        amount = int(parts[3])
        await _qb_play_xocdia(query, context, pick, amount)

    # ── Quick-bet: Roulette ──
    elif data.startswith("qb_roulette_"):
        parts = data.split("_")
        bt = parts[2]
        amount = int(parts[3])
        await _qb_play_roulette(query, context, bt, amount)

    # ── Quick-bet: Blackjack ──
    elif data.startswith("qb_bj_"):
        amount = int(data.split("_")[2])
        await _qb_play_bj(query, context, amount)

    # ── Blackjack actions ──
    elif data.startswith("bj_hit_"):
        amount = int(data.split("_")[2])
        await bj_hit_callback(query, context, user_id, amount)
    elif data.startswith("bj_stand_"):
        amount = int(data.split("_")[2])
        await bj_stand_callback(query, context, user_id, amount)
    elif data.startswith("bj_double_"):
        amount = int(data.split("_")[2])
        await bj_double_callback(query, context, user_id, amount)

    # ── Quick-bet: Slot ──
    elif data.startswith("qb_slot_"):
        amount = int(data.split("_")[2])
        await _qb_play_slot(query, context, amount)

    else:
        await query.answer("Chức năng chưa hỗ trợ")


# ═══════════════════════════════════════════════════════════
# ADMIN
# ═══════════════════════════════════════════════════════════
async def admin_cmd(update, context):
    user = update.effective_user
    s = _get_session(user.id)
    if s.get("is_admin"):
        await update.message.reply_text("🔑 **ADMIN PANEL** — Chọn hành động:", parse_mode="Markdown", reply_markup=kb_admin())
    elif ADMIN_ID and user.id == ADMIN_ID:
        s["is_admin"] = True
        await update.message.reply_text("🔑 **ADMIN PANEL** — Chọn hành động:", parse_mode="Markdown", reply_markup=kb_admin())
    else:
        s["awaiting_pass"] = True
        await update.message.reply_text("🔒 Nhập mật khẩu admin:")

async def handle_message(update, context):
    user = update.effective_user
    s = _get_session(user.id)
    text = update.message.text
    if s.get("awaiting_pass"):
        s.pop("awaiting_pass")
        if text == ADMIN_PASSWORD:
            s["is_admin"] = True
            await update.message.reply_text("✅ Đăng nhập thành công!\n\n🔑 **ADMIN PANEL** — Chọn hành động:", parse_mode="Markdown", reply_markup=kb_admin())
        else:
            await update.message.reply_text("❌ Sai mật khẩu!")
        return
    if not s.get("is_admin"):
        return
    if text == "/cancel":
        for k in ["adm_setbal","adm_reset","adm_del","adm_broadcast","adm_gift_all","adm_search","adm_giftcode","adm_setlevel","adm_odds"]:
            s.pop(k, None)
        await update.message.reply_text("❌ Đã hủy.")
        return

    if s.get("adm_setbal"):
        s.pop("adm_setbal")
        try:
            uid, amt = [int(x) for x in text.strip().split()]
            admin_set_balance(uid, amt)
            await update.message.reply_text(f"✅ Set user {uid} → {amt:,}đ")
        except: await update.message.reply_text("❌ Sai format!")
        return
    if s.get("adm_reset"):
        s.pop("adm_reset")
        try:
            uid = int(text.strip())
            admin_reset_user(uid)
            await update.message.reply_text(f"✅ Reset user {uid}!")
        except: await update.message.reply_text("❌ Sai format!")
        return
    if s.get("adm_del"):
        s.pop("adm_del")
        try:
            uid = int(text.strip())
            admin_delete_user(uid)
            await update.message.reply_text(f"✅ Xóa user {uid}!")
        except: await update.message.reply_text("❌ Sai format!")
        return

    # ── Xử lý broadcast ──
    if s.get("adm_broadcast"):
        s.pop("adm_broadcast")
        try:
            conn = get_db()
            users = conn.execute("SELECT user_id FROM users").fetchall()
            ok, fail = 0, 0
            for u in users:
                try:
                    await context.bot.send_message(chat_id=u["user_id"], text=f"📢 **THÔNG BÁO TỪ ADMIN**\n\n{text}", parse_mode="Markdown")
                    ok += 1
                except:
                    fail += 1
            await update.message.reply_text(f"✅ Gửi OK: {ok} | ❌ Thất bại: {fail}")
        except Exception as e:
            await update.message.reply_text(f"❌ Lỗi: {e}")
        return

    # ── Xử lý tặng tiền hàng loạt ──
    if s.get("adm_gift_all"):
        s.pop("adm_gift_all")
        try:
            amount = int(text.strip())
            conn = get_db()
            users = conn.execute("SELECT user_id FROM users").fetchall()
            for u in users:
                admin_set_balance(u["user_id"], get_user(u["user_id"])["balance"] + amount)
            await update.message.reply_text(f"✅ Đã tặng {amount:,}đ cho {len(users)} user!")
        except Exception as e:
            await update.message.reply_text(f"❌ Lỗi: {e}")
        return

    # ── Xử lý tra cứu user ──
    if s.get("adm_search"):
        s.pop("adm_search")
        try:
            conn = get_db()
            # Thử tìm theo user_id trước
            try:
                uid = int(text.strip())
                u = conn.execute("SELECT * FROM users WHERE user_id = ?", (uid,)).fetchone()
            except ValueError:
                u = None
            # Nếu không có, tìm theo username
            if not u:
                u = conn.execute("SELECT * FROM users WHERE username LIKE ?", (f"%{text.strip()}%",)).fetchone()
            if u:
                u = dict(u)
                uid = u["user_id"]

                # ── Thông tin cơ bản ──
                username = u.get("username") or "N/A"
                balance = u["balance"]
                total_bets = u["total_bets"]
                total_wins = u["total_wins"]
                total_losses = u["total_losses"]
                level = u.get("level", 1)
                exp = u.get("exp", 0)
                created = u.get("created_at", "N/A")[:10] if u.get("created_at") else "N/A"

                # ── Win rate ──
                wr = f"{total_wins/(total_wins+total_losses)*100:.1f}%" if (total_wins+total_losses) > 0 else "N/A"

                # ── Tính P&L từ history ──
                h_all = get_history(uid, 9999)
                total_wagered = sum(r["bet_amount"] for r in h_all)
                total_won = sum(r["win"] for r in h_all)
                profit = total_won - total_wagered
                profit_str = f"+{profit:,}đ" if profit >= 0 else f"{profit:,}đ"

                # ── Rank & Level ──
                try:
                    from taixiu_features import get_rank_display, get_next_rank_info, get_level_display, get_exp_needed, get_next_reward_info
                    rank_str = get_rank_display(balance)
                    next_rank = get_next_rank_info(balance)
                    if next_rank:
                        rank_next = f"   {next_rank[0]} {next_rank[1]} (cần {next_rank[2]:,}đ)"
                    else:
                        rank_next = "   🏆 **TỐI ĐA**"
                    level_str = get_level_display(level, exp)
                    next_rlv, next_ramt = get_next_reward_info(level)
                    reward_str = f"🎁 Reward tiếp: Level **{next_rlv}** → **{next_ramt:,}đ**" if next_rlv else "🏆 **MAX LEVEL**"
                except ImportError:
                    rank_str = "N/A"
                    rank_next = ""
                    level_str = f"Lv.{level} | {exp} EXP"
                    reward_str = ""
                except Exception:
                    rank_str = "N/A"
                    rank_next = ""
                    level_str = f"Lv.{level} | {exp} EXP"
                    reward_str = ""

                # ── History gần nhất (server-side, render 10 ván) ──
                recent = get_history(uid, 10)
                hist_lines = []
                if recent:
                    for r in recent:
                        wl_icon = "✅" if r["win"] > 0 else "❌"
                        pnl = r["win"] - r["bet_amount"]
                        if pnl > 0:
                            pnl_str = f"+{pnl:,}"
                        elif pnl == 0:
                            pnl_str = "0"
                        else:
                            pnl_str = f"{pnl:,}"  # already negative
                        hist_lines.append(f"{wl_icon} {r['bet_type'].replace('_', '·')} {r['bet_amount']:,}đ → {r['win']:,}đ ({pnl_str}đ)")
                else:
                    hist_lines.append("   Chưa có ván nào")
                hist_str = "\n".join(hist_lines)

                # ── Build message ──
                msg = (
                    f"🔍 **THÔNG TIN USER**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"👤 **{username}**\n"
                    f"🆔 `{uid}`\n"
                    f"📅 Tham gia: {created}\n"
                    f"\n"
                    f"💰 **Số dư**: {balance:,}đ\n"
                    f"🏅 **Cấp bậc**: {rank_str}\n"
                    f"   {rank_next}\n"
                    f"⭐ **Level**: {level_str}\n"
                    f"   {reward_str}\n"
                    f"\n"
                    f"📊 **THỐNG KÊ**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🎲 Tổng ván: **{total_bets}**\n"
                    f"✅ Thắng: **{total_wins}**\n"
                    f"❌ Thua: **{total_losses}**\n"
                    f"📈 Win rate: **{wr}**\n"
                    f"💵 Tổng cược: **{total_wagered:,}đ**\n"
                    f"💰 Tổng thắng: **{total_won:,}đ**\n"
                    f"📉 P&L: **{profit_str}**\n"
                    f"\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📋 **10 VÁN GẦN NHẤT**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"{hist_str}"
                )

                await update.message.reply_text(msg, parse_mode="Markdown")
            else:
                await update.message.reply_text("❌ Không tìm thấy user!")
        except Exception as e:
            await update.message.reply_text(f"❌ Lỗi: {e}")
        return

    # ── Set Level User ──
    if s.get("adm_setlevel"):
        s.pop("adm_setlevel")
        try:
            parts = text.strip().split()
            uid = int(parts[0])
            level = int(parts[1])
            exp = int(parts[2]) if len(parts) > 2 else 0
            if level < 1 or level > 1000:
                await update.message.reply_text("❌ Level phải từ 1-1000!")
                return
            admin_set_level(uid, level, exp)
            await update.message.reply_text(f"✅ Đã set user {uid} → Level {level}, EXP {exp}")
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Sai format! Dùng: `user_id level [exp]`", parse_mode="Markdown")
        return

    # ── Game Odds ──
    if s.get("adm_odds"):
        s.pop("adm_odds")
        text_lower = text.strip().lower()
        if text_lower == "reset":
            reset_game_config()
            await update.message.reply_text("✅ Đã reset tất cả tỷ lệ về mặc định!")
            return
        try:
            key, val = text.strip().split()
            valid_keys = [
                "taixiu_mult", "xocdia_mult",
                "roulette_color_mult", "roulette_number_mult",
                "slot_jackpot_mult", "slot_pair_mult",
                "bj_normal_mult", "bj_blackjack_mult"
            ]
            if key not in valid_keys:
                await update.message.reply_text(
                    f"❌ Key không hợp lệ!\n\nKeys: {', '.join(valid_keys)}",
                    parse_mode="Markdown"
                )
                return
            value = float(val)
            if value < 0 or value > 100:
                await update.message.reply_text("❌ Giá trị phải từ 0-100!")
                return
            set_game_config(key, value)
            await update.message.reply_text(f"✅ Đã set `{key}` = **{value}**", parse_mode="Markdown")
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Sai format! Dùng: `key value`\\nVD: `taixiu_mult 3`", parse_mode="Markdown")
        return


# ═══════════════════════════════════════════════════════════
# PARSE AMOUNT
# ═══════════════════════════════════════════════════════════
def _parse_amount(text, balance):
    text = text.strip().lower()
    if text == "all":
        return balance
    if text.endswith("k"):
        try:
            val = int(float(text[:-1]) * 1000)
            return min(val, balance)
        except:
            return -1
    try:
        val = int(text)
        if val < 100:
            return -1
        return min(val, balance)
    except:
        return -1

# ═══════════════════════════════════════════════════════════
# SLASH COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════

async def _slash_tai(update, context, args):
    user = update.effective_user
    db = get_user(user.id, user.username or user.first_name)
    if not args:
        await update.message.reply_text("VD: `/tai 10k`", parse_mode="Markdown")
        return
    amount = _parse_amount(args[0], db["balance"])
    if amount <= 0:
        await update.message.reply_text("❌ Số tiền không hợp lệ!")
        return
    await _play_taixiu(update, context, "tai", amount)


async def _slash_xiu(update, context, args):
    user = update.effective_user
    db = get_user(user.id, user.username or user.first_name)
    if not args:
        await update.message.reply_text("VD: `/xiu 10k`", parse_mode="Markdown")
        return
    amount = _parse_amount(args[0], db["balance"])
    if amount <= 0:
        await update.message.reply_text("❌ Số tiền không hợp lệ!")
        return
    await _play_taixiu(update, context, "xiu", amount)


async def _slash_bau(update, context, args):
    user = update.effective_user
    db = get_user(user.id, user.username or user.first_name)
    if len(args) < 2:
        await update.message.reply_text("VD: `/bau cua 10k`", parse_mode="Markdown")
        return
    amount = _parse_amount(args[1], db["balance"])
    if amount <= 0:
        await update.message.reply_text("❌ Số tiền không hợp lệ!")
        return
    await _play_baucua(update, context, args[0], amount)


async def _slash_xoc(update, context, args):
    user = update.effective_user
    db = get_user(user.id, user.username or user.first_name)
    if len(args) < 2:
        await update.message.reply_text("VD: `/xoc 2 10k`", parse_mode="Markdown")
        return
    try:
        pick = int(args[0])
    except:
        await update.message.reply_text("❌ Chọn số 0-4!")
        return
    amount = _parse_amount(args[1], db["balance"])
    if amount <= 0:
        await update.message.reply_text("❌ Số tiền không hợp lệ!")
        return
    await _play_xocdia(update, context, pick, amount)


async def _slash_bj(update, context, args):
    user = update.effective_user
    db = get_user(user.id, user.username or user.first_name)
    if not args:
        await update.message.reply_text("VD: `/bj 10k`", parse_mode="Markdown")
        return
    amount = _parse_amount(args[0], db["balance"])
    if amount <= 0:
        await update.message.reply_text("❌ Số tiền không hợp lệ!")
        return
    await _play_blackjack(update, context, amount)


async def _slash_ru(update, context, args):
    user = update.effective_user
    db = get_user(user.id, user.username or user.first_name)
    if len(args) < 2:
        await update.message.reply_text("VD: `/ru red 10k`", parse_mode="Markdown")
        return
    amount = _parse_amount(args[1], db["balance"])
    if amount <= 0:
        await update.message.reply_text("❌ Số tiền không hợp lệ!")
        return
    await _play_roulette(update, context, args[0], amount)


async def _slash_slot(update, context, args):
    user = update.effective_user
    db = get_user(user.id, user.username or user.first_name)
    if not args:
        await update.message.reply_text("VD: `/slot 10k`", parse_mode="Markdown")
        return
    amount = _parse_amount(args[0], db["balance"])
    if amount <= 0:
        await update.message.reply_text("❌ Số tiền không hợp lệ!")
        return
    await _play_slot(update, context, amount)


async def _slash_rank(update, context):
    user = update.effective_user
    db = get_user(user.id, user.username or user.first_name)
    bal = db["balance"]
    try:
        from taixiu_features import get_rank_display, get_next_rank_info, get_rank_progress
        progress = get_rank_progress(bal)
        next_r = get_next_rank_info(bal)
        lines = [
            "🏅 **CẤP BẬC**\n━━━━━━━━━━━━━━━━━━",
            "",
            f"🔹 **{get_rank_display(bal)}**",
        ]
        if progress:
            lines.append(f"   {progress}")
        if next_r:
            e, ti, need = next_r
            lines.append(f"   Cần thêm **{need:,}đ** để lên {e} {ti}")
        else:
            lines.append(f"   🏆 **ĐÃ ĐẠT CẤP CAO NHẤT!** 🏆")
        lines.append("")
        lines.append("📌 Cấp bậc dựa trên **số dư**")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except ImportError:
        await update.message.reply_text("⚠️ Rank system chưa load.")


async def _slash_level(update, context):
    user = update.effective_user
    db = get_user(user.id, user.username or user.first_name)
    level = db.get("level", 1)
    exp = db.get("exp", 0)
    try:
        from taixiu_features import get_exp_needed, get_next_reward_info, get_level_display
        needed = get_exp_needed(level)
        next_rlv, next_ramt = get_next_reward_info(level)
        lines = [
            f"⭐ **LEVEL SYSTEM**",
            f"━━━━━━━━━━━━━━━━━━",
            f"",
            f"📊 {get_level_display(level, exp)}",
            f"",
            f"📈 EXP cần để lên level: **{needed}**",
            f"🎯 Mỗi ván: **+1 EXP**",
        ]
        if next_rlv:
            lines.append(f"")
            lines.append(f"🎁 Reward tiếp: Level **{next_rlv}** → **{next_ramt:,}đ**")
        else:
            lines.append(f"")
            lines.append(f"🏆 **MAX LEVEL!** 🏆")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
    except ImportError:
        await update.message.reply_text(f"⭐ Level **{level}** | EXP **{exp}**\n\n⚠️ Feature chưa load", parse_mode="Markdown")


async def _slash_history(update, context):
    user = update.effective_user
    db = get_user(user.id, user.username or user.first_name)
    h = get_history(user.id, 10)
    if not h:
        await update.message.reply_text("📊 **Lịch sử**: Chưa có ván nào.", parse_mode="Markdown")
        return
    lines = ["📊 **10 VÁN GẦN NHẤT**\n━━━━━━━━━━━━━━━━━━"]
    for r in h:
        lines.append(_fmt_hist(r))
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def _slash_leaderboard(update, context):
    top = get_top_users(10)
    if not top:
        await update.message.reply_text("🏆 Chưa có người chơi.", parse_mode="Markdown")
        return
    lines = ["🏆 **BẢNG XẾP HẠNG (TOP 10)**\n━━━━━━━━━━━━━━━━━━"]
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    for i, u in enumerate(top):
        name = u.get("username") or f"User {u['user_id']}"
        lines.append(f"{medals[i]} **{name}** — {u['balance']:,}đ (W{u['total_wins']}/L{u['total_losses']})")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def _slash_help(update, context):
    await update.message.reply_text(
        "❓ **TRỢ GIÚP**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🎰 **CÁC TRÒ CHƠI**\n"
        "  • /tai - Tài Xỉu\n"
        "  • /xiu - Tài Xỉu\n"
        "  • /bau - Bầu Cua\n"
        "  • /xoc - Xóc Đĩa\n"
        "  • /bj - Blackjack\n"
        "  • /ru - Roulette\n"
        "  • /slot - Slot Machine\n\n"
        "📊 **TIỆN ÍCH**\n"
        "  • /rank - Xem cấp bậc\n"
        "  • /level - Xem Level & EXP\n"
        "  • /giftcode - Nhập code\n"
        "  • /reset - Reset tài khoản\n\n"
        "💡 Mỗi ván chơi được **+1 EXP**\n"
        "💊 Thua liên tiếp được **Payback**\n"
        "🏆 Cấp bậc tăng theo **số dư**",
        parse_mode="Markdown"
    )


async def _slash_giftcode(update, context):
    user = update.effective_user
    is_admin = _get_session(user.id).get("is_admin")
    if not context.args:
        await update.message.reply_text(
            "🎟️ **GIFTCODE**\n━━━━━━━━━━━━━━━━━━\n"
            "Dùng: `/giftcode <CODE>` để nhận thưởng.\n\n"
            + ("👑 **Admin:** `/giftcode tạo <CODE> <amount> [max_uses]`\n"
               "👑 **Admin:** `/giftcode xóa <CODE>`" if is_admin else ""),
            parse_mode="Markdown"
        )
        return

    if is_admin and context.args[0] == "tạo" and len(context.args) >= 3:
        code = context.args[1].upper()
        try:
            amount = int(context.args[2])
            max_uses = int(context.args[3]) if len(context.args) > 3 else 1
            create_giftcode(code, amount, max_uses, user.id)
            await update.message.reply_text(f"🎟️ Đã tạo giftcode **{code}** — {amount:,}đ ({max_uses} lượt)", parse_mode="Markdown")
        except ValueError:
            await update.message.reply_text("❌ Sai format! Dùng: `/giftcode tạo CODE amount [max_uses]`", parse_mode="Markdown")
        return

    if is_admin and context.args[0] == "xóa" and len(context.args) >= 2:
        code = context.args[1].upper()
        delete_giftcode(code)
        await update.message.reply_text(f"🗑️ Đã xóa giftcode **{code}**", parse_mode="Markdown")
        return

    # Người chơi nhập code
    code = context.args[0].upper()
    db = get_user(user.id, user.username or user.first_name)
    result = redeem_giftcode(code, user.id)
    if result["success"]:
        admin_set_balance(user.id, db["balance"] + result["amount"])
        await update.message.reply_text(f"🎟️ **NHẬN GIFTCODE THÀNH CÔNG!**\n━━━━━━━━━━━━━━━━━━\nBạn nhận được **{result['amount']:,}đ** 🎉\n💵 Số dư mới: **{db['balance'] + result['amount']:,}đ**", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ {result['message']}")


async def reset_cmd(update, context):
    user = update.effective_user
    uid = user.id
    await update.message.reply_text(
        f"🔄 **RESET TÀI KHOẢN**\n━━━━━━━━━━━━━━━━━━\n"
        f"Bạn có chắc muốn reset về **10,000đ**?\n"
        f"Tất cả dữ liệu cũ sẽ bị xóa.\n\n"
        f"Bấm `/reset xác nhận` để tiếp tục.",
        parse_mode="Markdown"
    )


async def reset_confirm_cmd(update, context):
    user = update.effective_user
    admin_reset_user(user.id)
    await update.message.reply_text("✅ Đã reset tài khoản về **10,000đ**!", parse_mode="Markdown")


async def start_cmd(update, context):
    """Named function for /start — referenced by taixiu_features."""
    await update.message.reply_text(
        _menu_text(update.effective_user.id, update.effective_user.first_name),
        parse_mode="Markdown", reply_markup=kb_main_menu()
    )


# ═══════════════════════════════════════════════════════════
# COMMAND ROUTER
# ═══════════════════════════════════════════════════════════

async def cmd_router(update, context):
    text = update.message.text.strip().lower()
    # Game commands
    if text.startswith("/tai "):
        await _slash_tai(update, context, text[5:].strip().split())
    elif text.startswith("/xiu "):
        await _slash_xiu(update, context, text[5:].strip().split())
    elif text.startswith("/bau "):
        await _slash_bau(update, context, text[5:].strip().split())
    elif text.startswith("/xoc "):
        await _slash_xoc(update, context, text[5:].strip().split())
    elif text.startswith("/bj "):
        await _slash_bj(update, context, text[4:].strip().split())
    elif text.startswith("/ru "):
        await _slash_ru(update, context, text[4:].strip().split())
    elif text.startswith("/slot "):
        await _slash_slot(update, context, text[6:].strip().split())
    elif text.startswith("/giftcode "):
        await _slash_giftcode(update, context)
    elif text.startswith("/reset xác nhận") or text == "/reset xác nhận":
        await reset_confirm_cmd(update, context)
    else:
        # Unknown command
        pass


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    # Callback handler
    app.add_handler(CallbackQueryHandler(callback_router, pattern=".*"))

    # Admin message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_message))

    # Slash command handlers
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", _slash_help))
    app.add_handler(CommandHandler("tai", lambda u, c: _slash_tai(u, c, c.args)))
    app.add_handler(CommandHandler("xiu", lambda u, c: _slash_xiu(u, c, c.args)))
    app.add_handler(CommandHandler("bau", lambda u, c: _slash_bau(u, c, c.args)))
    app.add_handler(CommandHandler("xoc", lambda u, c: _slash_xoc(u, c, c.args)))
    app.add_handler(CommandHandler("bj", lambda u, c: _slash_bj(u, c, c.args)))
    app.add_handler(CommandHandler("ru", lambda u, c: _slash_ru(u, c, c.args)))
    app.add_handler(CommandHandler("slot", lambda u, c: _slash_slot(u, c, c.args)))
    app.add_handler(CommandHandler("rank", _slash_rank))
    app.add_handler(CommandHandler("level", _slash_level))
    app.add_handler(CommandHandler("history", _slash_history))
    app.add_handler(CommandHandler("leaderboard", _slash_leaderboard))
    app.add_handler(CommandHandler("giftcode", _slash_giftcode))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("cancel", lambda u, c: u.message.reply_text("❌ Đã hủy.")))

    # Generic message router (for non-command messages from non-admin users)
    # Note: admin messages are already handled above via handle_message

    # Try to load taixiu_features
    try:
        import taixiu_features
        print("✅ taixiu_features loaded — Rank, Level & Payback system active!")
        print("   🏅 /rank — Xem cấp bậc")
        print("   ⭐ /level — Xem level + EXP")
        print("   💊 Payback tự động khi thua liên tiếp")
    except Exception as e:
        print(f"⚠️ taixiu_features not loaded: {e}")

    print(f"🤖 Bot đang chạy... (PID: {os.getpid()})")
    app.run_polling()


if __name__ == "__main__":
    main()
