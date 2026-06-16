import os

token = open(os.path.join(os.path.dirname(__file__), "token.txt")).read().strip()
TOKEN_LINE = f'TOKEN="{token}"'

# Read current file
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "taixiu_bot.py"), "r") as f:
    lines = f.readlines()

# Find and replace TOKEN line
fixed = False
for i, line in enumerate(lines):
    if line.startswith("TOKEN"):
        lines[i] = TOKEN_LINE + "\n"
        fixed = True
        print(f"Replaced TOKEN at line {i+1}: {lines[i].strip()}")
        break

if not fixed:
    print("WARNING: No TOKEN line found!")
else:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "taixiu_bot.py"), "w") as f:
        f.writelines(lines)
    print("Done!")
