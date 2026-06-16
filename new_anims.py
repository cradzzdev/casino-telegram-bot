# ═══════════════════════════════════════════════════════════
# ANIMATION ~6s EDITION — COMPACT & SMOOTH
# ═══════════════════════════════════════════════════════════
import random
import asyncio

DICE_EMOJIS = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
BAUCLA_EMOJI_ANIM = ["🍐", "🦀", "🦐", "🐟", "🐔", "🦌"]
BAUCLA_NAMES_ANIM = ["Bầu", "Cua", "Tôm", "Cá", "Gà", "Nai"]
RL_RED_SET = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
SLOT_SYMS_ANIM = ["🍒", "🍋", "🍊", "🍇", "⭐", "💎", "🔔", "7️⃣"]
SLOT_WEIGHTS_ANIM = [25, 20, 18, 15, 10, 6, 4, 2]
CARD_BACK = "🃏"
CARD_HIDDEN = "🂠"


async def _edit_safe(msg, text, parse_mode=None):
    try:
        await msg.edit_text(text, parse_mode=parse_mode)
    except Exception:
        pass


def _sparks():
    return random.choice(["✨", "💫", "⭐", "🌟", "⚡", "💥"])


# ═══════════════════════════════════════════════════════════
# 🎲 TÀI XỈU — ~6s
# ═══════════════════════════════════════════════════════════
async def anim_taixiu(context, chat_id):
    vals = [random.randint(1, 6) for _ in range(3)]
    total = sum(vals)
    de_final = [DICE_EMOJIS[x-1] for x in vals]

    msg = await context.bot.send_message(chat_id=chat_id,
        text="🎲  🎲  🎲\n━━━━━━━━━━━━\n  🚀 Đang tung xúc xắc...")

    # Phase 1: Fast rolls ~1.2s
    for _ in range(6):
        r = [random.randint(1, 6) for _ in range(3)]
        de = [DICE_EMOJIS[x-1] for x in r]
        await _edit_safe(msg, f"{'  '.join(de)}\n━━━━━━━━━━━━\n  ⚡ Tung...")
        await asyncio.sleep(0.2)

    # Phase 2: Slow rolls ~1.2s
    for i in range(3):
        r = [random.randint(1, 6) for _ in range(3)]
        de = [DICE_EMOJIS[x-1] for x in r]
        dots = "●" * (i + 1) + "○" * (2 - i)
        await _edit_safe(msg, f"{'  '.join(de)}\n━━━━━━━━━━━━\n  🎯 {dots}")
        await asyncio.sleep(0.4)

    # Phase 3: Wiggling ~1.2s
    for _ in range(2):
        wig = " ".join("⬆" if random.random() > 0.5 else "⬇" for _ in range(3))
        await _edit_safe(msg, f"{'  '.join(de_final)}\n━━━━━━━━━━━━\n  {wig}")
        await asyncio.sleep(0.3)
        wig2 = " ".join("⬇" if random.random() > 0.5 else "⬆" for _ in range(3))
        await _edit_safe(msg, f"{'  '.join(de_final)}\n━━━━━━━━━━━━\n  {wig2}")
        await asyncio.sleep(0.3)

    # Phase 4: Flash reveal ~1s
    for _ in range(2):
        await _edit_safe(msg, f"✨ ✨ ✨\n━━━━━━━━━━━━\n  💥💥💥")
        await asyncio.sleep(0.15)
        await _edit_safe(msg, f"{'  '.join(de_final)}\n━━━━━━━━━━━━\n  ⭐⭐⭐")
        await asyncio.sleep(0.15)
    await _edit_safe(msg, f"{'  '.join(de_final)}\n━━━━━━━━━━━━\n  ⭐⭐⭐")
    await asyncio.sleep(0.2)

    # Phase 5: Result ~1.5s
    label = "🔥 **TÀI** 🔥" if total >= 10 else "❄️ **XỈU** ❄️"
    bar = "🟥" * min(total, 17) + "⬜" * (17 - min(total, 17))
    await _edit_safe(msg,
        f"╔══════════════╗\n"
        f"║ {de_final[0]}  {de_final[1]}  {de_final[2]} ║\n"
        f"╚══════════════╝\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"  Tổng: **{total}** {bar}\n"
        f"  🏆 → {label}",
        parse_mode="Markdown")
    return vals, msg


# ═══════════════════════════════════════════════════════════
# 🦀 BẦU CUA — ~6s
# ═══════════════════════════════════════════════════════════
async def anim_baucla(context, chat_id):
    vals = [random.randint(1, 6) for _ in range(3)]
    rolled = [(v - 1) % 6 for v in vals]
    e = [BAUCLA_EMOJI_ANIM[x] for x in rolled]

    msg = await context.bot.send_message(chat_id=chat_id,
        text="🔝 🔝 🔝\n━━━━━━━━━━━━\n  🦀 Đang lắc bầu cua...")

    # Phase 1: Fast shaking ~1.5s
    for _ in range(6):
        r = [random.randint(0, 5) for _ in range(3)]
        ed = [BAUCLA_EMOJI_ANIM[x] for x in r]
        await _edit_safe(msg, f"{'  '.join(ed)}\n━━━━━━━━━━━━\n  🌀 Lắc...")
        await asyncio.sleep(0.25)

    # Phase 2: Lid lifting ~1s
    lids = ["🔝", "🔜", "🔓"]
    for lid in lids:
        await _edit_safe(msg, f"{lid} {lid} {lid}\n━━━━━━━━━━━━\n  ⏳ Mở bát...")
        await asyncio.sleep(0.33)

    # Phase 3: Countdown ~1s
    for i in range(2, 0, -1):
        await _edit_safe(msg, f"❓ ❓ ❓\n━━━━━━━━━━━━\n  ⏳ **{i}**...", parse_mode="Markdown")
        await asyncio.sleep(0.5)

    # Phase 4: Reveal one by one ~1s
    for idx in range(3):
        disp = [f"**{BAUCLA_EMOJI_ANIM[rolled[j]]}**" if j <= idx else "❓" for j in range(3)]
        await _edit_safe(msg,
            f"{'  '.join(disp)}\n━━━━━━━━━━━━\n  ⚡ Mở {idx+1}/3...",
            parse_mode="Markdown")
        await asyncio.sleep(0.33)

    # Phase 5: Flash + result ~1.5s
    for _ in range(2):
        await _edit_safe(msg, f"✨ ✨ ✨\n━━━━━━━━━━━━\n  🎉🎉🎉")
        await asyncio.sleep(0.15)
        await _edit_safe(msg, f"{'  '.join(e)}\n━━━━━━━━━━━━\n  ⭐⭐⭐")
        await asyncio.sleep(0.15)
    n = [BAUCLA_NAMES_ANIM[x] for x in rolled]
    await _edit_safe(msg,
        f"╔══════════════╗\n"
        f"║ {e[0]}  {e[1]}  {e[2]} ║\n"
        f"╚══════════════╝\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"  {n[0]} • {n[1]} • {n[2]}",
        parse_mode="Markdown")
    return rolled, msg


# ═══════════════════════════════════════════════════════════
# 🪙 XÓC ĐĨA — ~6s
# ═══════════════════════════════════════════════════════════
async def anim_xocdia(context, chat_id):
    coins = [random.randint(0, 1) for _ in range(4)]
    actual = sum(coins)
    coin_str = " ".join("🔴" if c else "⚫" for c in coins)

    msg = await context.bot.send_message(chat_id=chat_id,
        text="🥏 🥏 🥏 🥏\n━━━━━━━━━━━━\n  🪙 Đang xóc đĩa...")

    # Phase 1: Fast toss ~1.5s
    for _ in range(6):
        r = [random.randint(0, 1) for _ in range(4)]
        s = " ".join("🔴" if c else "⚫" for c in r)
        await _edit_safe(msg, f"{s}\n━━━━━━━━━━━━\n  🌀 Xóc...")
        await asyncio.sleep(0.25)

    # Phase 2: Slow toss ~1s
    for i in range(2):
        r = [random.randint(0, 1) for _ in range(4)]
        s = " ".join("🔴" if c else "⚫" for c in r)
        dots = "●" * (i + 1) + "○" * (1 - i)
        await _edit_safe(msg, f"{s}\n━━━━━━━━━━━━\n  ⏳ {dots}")
        await asyncio.sleep(0.5)

    # Phase 3: Lid suspense ~1s
    for i in range(2, 0, -1):
        await _edit_safe(msg, f"🥏 🥏 🥏 🥏\n━━━━━━━━━━━━\n  🪙 Mở đ�a **{i}**...", parse_mode="Markdown")
        await asyncio.sleep(0.5)

    # Phase 4: Coin reveal ~1s
    for idx in range(4):
        disp = [("🔴" if coins[j] else "⚫") if j <= idx else "❓" for j in range(4)]
        await _edit_safe(msg, f"{' '.join(disp)}\n━━━━━━━━━━━━\n  ⚡ Lật {idx+1}/4...")
        await asyncio.sleep(0.25)

    # Phase 5: Flash + result ~1.5s
    for _ in range(2):
        await _edit_safe(msg, f"✨ ✨ ✨ ✨\n━━━━━━━━━━━━\n  🎉🎉🎉")
        await asyncio.sleep(0.15)
        await _edit_safe(msg, f"{coin_str}\n━━━━━━━━━━━━\n  ⭐⭐⭐")
        await asyncio.sleep(0.15)
    ngua_bar = "🔴" * actual + "⚫" * (4 - actual)
    outcome = "CHẴN" if actual in (0, 2, 4) else "LẺ"
    await _edit_safe(msg,
        f"╔══════════════╗\n"
        f"║ {coin_str} ║\n"
        f"╚══════════════╝\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"  Ngửa: **{actual}** {ngua_bar}\n"
        f"  🏆 **{outcome}** 🏆",
        parse_mode="Markdown")
    return coins, msg


# ═══════════════════════════════════════════════════════════
# 🎡 ROULETTE — ~6s
# ═══════════════════════════════════════════════════════════
async def anim_roulette(context, chat_id):
    number = random.randint(0, 36)
    col = "green" if number == 0 else ("red" if number in RL_RED_SET else "black")
    col_e = "🟢" if col == "green" else ("🔴" if col == "red" else "⚫")
    col_name = "XANH 🟢" if col == "green" else ("ĐỎ 🔴" if col == "red" else "ĐEN ⚫")

    msg = await context.bot.send_message(chat_id=chat_id,
        text="🎡\n━━━━━━━━━━━━\n  🚀 Đang quay roulette...")

    # Phase 1: Fast spin ~1.5s
    wheel = ["◐", "◑", "◒", "◓", "◔", "◕"]
    for i in range(8):
        n = random.randint(0, 36)
        c = "🟢" if n == 0 else ("🔴" if n in RL_RED_SET else "⚫")
        await _edit_safe(msg, f"🎡 {wheel[i % len(wheel)]}\n{c} **{n:02d}**\n━━━━━━━━━━━━\n  ⚡ Vù...", parse_mode="Markdown")
        await asyncio.sleep(0.18)

    # Phase 2: Ball rolling ~1s
    for i in range(3):
        n = random.randint(0, 36)
        c = "🟢" if n == 0 else ("🔴" if n in RL_RED_SET else "⚫")
        await _edit_safe(msg, f"🎱 🎡\n{c} **{n:02d}**\n━━━━━━━━━━━━\n  🔄 Bóng lăn...", parse_mode="Markdown")
        await asyncio.sleep(0.33)

    # Phase 3: Clicking ~1.5s
    for i in range(4):
        n = random.randint(0, 36)
        c = "🟢" if n == 0 else ("🔴" if n in RL_RED_SET else "⚫")
        clicks = "👆" * (4 - i)
        await _edit_safe(msg, f"{c} **{n:02d}**\n━━━━━━━━━━━━\n  {clicks} Cạch...", parse_mode="Markdown")
        await asyncio.sleep(0.38)

    # Phase 4: Suspense ~0.6s
    await _edit_safe(msg, f"{col_e} **? ?**\n━━━━━━━━━━━━\n  ⏳ ...", parse_mode="Markdown")
    await asyncio.sleep(0.3)
    await _edit_safe(msg, f"{col_e} **? ?**\n━━━━━━━━━━━━\n  ⏳ ....", parse_mode="Markdown")
    await asyncio.sleep(0.3)

    # Phase 5: Flash + result ~1.4s
    border = "🔴⚫🟢🔴⚫🟢🔴⚫🟢"
    for _ in range(2):
        await _edit_safe(msg, f"✨ 🎡 ✨\n━━━━━━━━━━━━\n  🎉🎉🎉")
        await asyncio.sleep(0.15)
        await _edit_safe(msg, f"{col_e} **{number:02d}**\n━━━━━━━━━━━━\n  ⭐⭐⭐")
        await asyncio.sleep(0.15)
    await _edit_safe(msg,
        f"╔══════════════╗\n"
        f"║ {col_e} **{number:02d}** ║\n"
        f"╚══════════════╝\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"  🏆 **{col_name}** 🏆\n"
        f"  {border}",
        parse_mode="Markdown")
    return number, msg


# ═══════════════════════════════════════════════════════════
# 🎰 SLOT — ~6s
# ═══════════════════════════════════════════════════════════
async def anim_slot(context, chat_id):
    result = random.choices(SLOT_SYMS_ANIM, weights=SLOT_WEIGHTS_ANIM, k=3)

    msg = await context.bot.send_message(chat_id=chat_id,
        text="╔═════════╗\n║ ❓ ❓ ❓ ║\n╚═════════╝\n━━━━━━━━━━━━\n  🎰 Đang quay...")

    # Phase 1: All spin ~1.2s
    for _ in range(5):
        r = random.choices(SLOT_SYMS_ANIM, weights=SLOT_WEIGHTS_ANIM, k=3)
        await _edit_safe(msg,
            f"╔═════════╗\n║ {r[0]} {r[1]} {r[2]} ║\n╚═════════╝\n━━━━━━━━━━━━\n  🌀 Quay...")
        await asyncio.sleep(0.24)

    # Phase 2: Lock reel 1 ~1s
    for _ in range(3):
        r2 = random.choices(SLOT_SYMS_ANIM, weights=SLOT_WEIGHTS_ANIM, k=1)[0]
        r3 = random.choices(SLOT_SYMS_ANIM, weights=SLOT_WEIGHTS_ANIM, k=1)[0]
        await _edit_safe(msg,
            f"╔═════════╗\n║ 🔒{result[0]} {r2} {r3} ║\n╚═════════╝\n━━━━━━━━━━━━\n  🔒 Dừng 1...")
        await asyncio.sleep(0.33)

    # Phase 3: Lock reel 2 ~1s
    for _ in range(3):
        r3 = random.choices(SLOT_SYMS_ANIM, weights=SLOT_WEIGHTS_ANIM, k=1)[0]
        await _edit_safe(msg,
            f"╔═════════╗\n║ 🔒{result[0]} 🔒{result[1]} {r3} ║\n╚═════════╝\n━━━━━━━━━━━━\n  🔒🔒 Dừng 2...")
        await asyncio.sleep(0.33)

    # Phase 4: Drumroll ~1.2s
    for i in range(3):
        r3 = random.choices(SLOT_SYMS_ANIM, weights=SLOT_WEIGHTS_ANIM, k=1)[0]
        drum = "🥁" * (i + 1)
        await _edit_safe(msg,
            f"╔═════════╗\n║ 🔒{result[0]} 🔒{result[1]} {r3} ║\n╚═════════╝\n━━━━━━━━━━━━\n  {drum} Sắp dừng...")
        await asyncio.sleep(0.4)

    # Phase 5: Flash ~0.8s
    for _ in range(2):
        r3 = random.choices(SLOT_SYMS_ANIM, weights=SLOT_WEIGHTS_ANIM, k=1)[0]
        await _edit_safe(msg,
            f"╔═════════╗\n║ 🔒{result[0]} 🔒{result[1]} {r3} ║\n╚═════════╝\n━━━━━━━━━━━━\n  ⏳ ...")
        await asyncio.sleep(0.2)
        await _edit_safe(msg,
            f"╔═════════╗\n║ 🔒{result[0]} 🔒{result[1]} ❓ ║\n╚═════════╝\n━━━━━━━━━━━━\n  🔥...")
        await asyncio.sleep(0.2)

    # Phase 6: Result ~1s
    is_jackpot = result[0] == result[1] == result[2]
    is_pair = not is_jackpot and (result[0] == result[1] or result[1] == result[2] or result[0] == result[2])

    if is_jackpot:
        for _ in range(3):
            await _edit_safe(msg,
                f"╔═════════╗\n║ 🔒{result[0]} 🔒{result[1]} 🔒{result[2]} ║\n╚═════════╝\n━━━━━━━━━━━━\n  🎉💎🎉💎🎉💎")
            await asyncio.sleep(0.15)
            await _edit_safe(msg,
                f"╔═════════╗\n║ 🔒{result[0]} 🔒{result[1]} 🔒{result[2]} ║\n╚═════════╝\n━━━━━━━━━━━━\n  💎🔥💎🔥💎🔥")
            await asyncio.sleep(0.15)
        border = "🎉💎🎉💎🎉💎🎉💎"
        wt = "🎰 **JACKPOT! x10** 🎰"
    elif is_pair:
        border = "🏆✨🏆✨🏆✨🏆✨"
        wt = "✨ **TRÚNG 2! x2** ✨"
    else:
        border = "💀💀💀💀💀💀💀💀"
        wt = "😢 **KHÔNG TRÚNG** 😢"

    await _edit_safe(msg,
        f"╔══════════════╗\n"
        f"║  {result[0]}  {result[1]}  {result[2]}  ║\n"
        f"╚══════════════╝\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{border}\n"
        f"{wt}\n"
        f"{border}",
        parse_mode="Markdown")
    return result, msg


# ═══════════════════════════════════════════════════════════
# 🃏 BLACKJACK — ~6s
# ═══════════════════════════════════════════════════════════
async def anim_blackjack(context, chat_id, player_hand, dealer_hand, pv, dv):
    msg = await context.bot.send_message(chat_id=chat_id,
        text="🃏 🃏\n━━━━━━━━━━━━\n  🃏 Đang chia bài...")

    # Phase 1: Shuffle ~0.8s
    for i in range(2):
        cv = "🂠 🂠 🂠 🂠" if i == 0 else "🂡 🃁 🃑 🃒"
        await _edit_safe(msg, f"🃏 **BLACKJACK**\n━━━━━━━━━━━━\n  {cv}\n━━━━━━━━━━━━\n  🔀 Xào...", parse_mode="Markdown")
        await asyncio.sleep(0.4)

    # Phase 2: Deal 4 cards face down ~1.2s
    display = ["🃏"] * 4
    for i in range(4):
        display[i] = CARD_HIDDEN
        p_str = " ".join(display[:2])
        d_str = " ".join(display[2:])
        who = "👤" if i < 2 else "🤖"
        await _edit_safe(msg,
            f"🃏 **BLACKJACK**\n━━━━━━━━━━━━\n"
            f"Bạn: {p_str}\nDealer: {d_str}\n━━━━━━━━━━━━\n"
            f"  {who} nhận bài... {_sparks()}", parse_mode="Markdown")
        await asyncio.sleep(0.3)

    # Phase 3: Flip player cards ~1s
    for flip in range(2):
        p = [str(player_hand[j]) if j <= flip else CARD_HIDDEN for j in range(2)]
        d_str = " ".join(display[2:])
        score = f" = **{pv}**" if flip == 1 else ""
        await _edit_safe(msg,
            f"🃏 **BLACKJACK**\n━━━━━━━━━━━━\n"
            f"Bạn: {' '.join(p)}{score}\nDealer: {d_str}\n━━━━━━━━━━━━\n"
            f"  🔄 Lật... {_sparks()}", parse_mode="Markdown")
        await asyncio.sleep(0.5)

    # Phase 4: Flip dealer cards ~1s
    for flip in range(2):
        p_str = f"{player_hand[0]} {player_hand[1]}"
        d = [str(dealer_hand[j]) if j <= flip else CARD_HIDDEN for j in range(2)]
        score = f" = **{dv}**" if flip == 1 else ""
        who = "Dealer lật..." if flip == 0 else "Tính điểm..."
        await _edit_safe(msg,
            f"🃏 **BLACKJACK**\n━━━━━━━━━━━━\n"
            f"Bạn: {p_str} = **{pv}**\nDealer: {' '.join(d)}{score}\n━━━━━━━━━━━━\n"
            f"  🔄 {who} {_sparks()}", parse_mode="Markdown")
        await asyncio.sleep(0.5)

    # Phase 5: Flash + final ~1.5s
    p_str = f"{player_hand[0]} {player_hand[1]}"
    d_str = f"{dealer_hand[0]} {dealer_hand[1]}"
    for _ in range(2):
        await _edit_safe(msg,
            f"🃏 **BLACKJACK**\n━━━━━━━━━━━━\n"
            f"Bạn: {p_str} = **{pv}**\nDealer: {d_str} = **{dv}**\n━━━━━━━━━━━━\n"
            f"  ✨✨✨✨", parse_mode="Markdown")
        await asyncio.sleep(0.2)
    await _edit_safe(msg,
        f"╔══════════════╗\n"
        f"║ 🃏 BLACKJACK ║\n"
        f"╚══════════════╝\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"  👤 {p_str} = **{pv}**\n"
        f"  🤖 {d_str} = **{dv}**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"  🏆 Tính kết quả...",
        parse_mode="Markdown")
    return msg
