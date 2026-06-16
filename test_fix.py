#!/usr/bin/env python3
"""Test that the dual-import fix works when taixiu_bot.py runs as __main__."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# Simulate: python3 taixiu_bot.py (where taixiu_bot IS __main__)
# We do this by importing taixiu_bot, then patching the module's name
import taixiu_bot
# Override __main__ to be taixiu_bot (simulates running it directly)
sys.modules['__main__'] = taixiu_bot

# Now import taixiu_features — it should find taixiu_bot via either key
import taixiu_features

# Check: place_bet in taixiu_bot module should be patched  
print(f"taixiu_bot.place_bet module: {taixiu_bot.place_bet.__module__}")

# Check: __main__ (which IS taixiu_bot) should also have patched place_bet
main = sys.modules['__main__']
print(f"__main__.place_bet module: {main.place_bet.__module__}")
print(f"Same object: {taixiu_bot.place_bet is main.place_bet}")

# Test EXP
from taixiu_db import get_db, get_user, init_db
init_db()
conn = get_db()

test_uid = 999999003
conn.execute("DELETE FROM history WHERE user_id = ?", (test_uid,))
conn.execute("DELETE FROM users WHERE user_id = ?", (test_uid,))
conn.execute("INSERT INTO users (user_id, username, balance, level, exp, total_bets, total_wins, total_losses) VALUES (?, ?, 10000, 1, 0, 0, 0, 0)", (test_uid, "test3"))
conn.commit()

b = get_user(test_uid)
for i in range(3):
    taixiu_bot.place_bet(test_uid, "taixiu_tai", 1000, {"dice": [1,2,3], "total": 6}, "xiu", 0)
a = get_user(test_uid)
print(f"BEFORE: Lv={b['level']} Exp={b['exp']}")
print(f"AFTER:  Lv={a['level']} Exp={a['exp']}")
print(f"EXP gain: {a['exp'] - b['exp']} (expected 3)")

conn.execute("DELETE FROM history WHERE user_id = ?", (test_uid,))
conn.execute("DELETE FROM users WHERE user_id = ?", (test_uid,))
conn.commit()

if a['exp'] - b['exp'] == 3:
    print("✅ LEVEL SYSTEM FIXED — patch works on __main__!")
else:
    print("❌ STILL BROKEN")
