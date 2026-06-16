# 🎲 Casino Bot Telegram

Bot Telegram chơi game casino với 6 game, hệ thống level, ranking và animation hoành tráng.

---

## 📋 Danh sách game

| Game | Lệnh | Mô tả | Tỷ lệ thắng |
|------|-------|-------|-------------|
| 🎲 Tài Xỉu | `/tai 10k` / `/xiu 10k` | Đoán tổng 3 xúc xắc: Tài (11-17) hoặc Xỉu (4-10) | x2 |
| 🦀 Bầu Cua | `/bau cua 10k` | Đoán mặt: Bầu, Cua, Tôm, Cá, Gà, Nai | x3 (trúng 1), x2 (trúng 2) |
| 🪙 Xóc Đĩa | `/xoc 2 10k` | Đoán số đồng xu ngửa (0-4) | x2 |
| 🃏 Blackjack | `/bj 10k` | Đánh bại dealer, gần 21 nhất | x2 (thắng), x2.5 (Blackjack) |
| 🎡 Roulette | `/ru red 10k` / `/ru 7 10k` | Cược Đỏ/Đen/Lẻ/Chẵn (x2) hoặc số cụ thể (x35) | x2 / x35 |
| 🎰 Slot | `/slot 10k` | Quay 3 reel, 3 giống nhau = JACKPOT | x10 (3 giống), x2 (2 giống) |

---

## 🎮 Cách chơi

### Nhanh (Quick Bet)
Nhấn nút game trên menu → chọn mức cược → chơi ngay.

### Lệnh trực tiếp
```
/tai 10k      → cược Tài 10,000đ
/xiu 50k      → cược Xỉu 50,000đ
/bau cua 10k  → cược Bầu Cua 10,000đ
/xoc 2 10k    → cược Xóc Đĩa, đoán 2 ngửa, 10,000đ
/bj 10k       → chơi Blackjack 10,000đ
/ru red 10k   → cược Roulette Đỏ 10,000đ
/ru 7 10k     → cược Roulette số 7, 10,000đ
/slot 10k     → chơi Slot 10,000đ
```

### Đơn vị tiền
- `10k` = 10,000đ
- `50k` = 50,000đ
- `100k` = 100,000đ
- Hoặc nhập số: `10000`

---

## 🃏 Blackjack - Luật chơi chi tiết

Blackjack là game tương tác, người chơi tự quyết định:

- **HIT** 🤚 — Lấy thêm bài
- **STAND** ✋ — Giữ bài, so điểm với Dealer
- **DOUBLE** 💰 — Gấp đôi cược, lấy đúng 1 lá, không chọn nữa

**Quy tắc:**
- Càng gần 21 càng tốt, không được quá 21
- **BLACKJACK** (21 từ 2 lá đầu) → Thắng x2.5
- **Thắng thường** → Thắng x2
- **Hòa** → Hoàn tiền
- **Dealer** PHẢI hit khi < 17, stand khi ≥ 17
- Auto stand khi đạt 21

---

## 🏆 Hệ thống Level & Ranking

### Level
- Mỗi ván chơi: +1 EXP
- Level tối đa: 1000
- Reward mỗi 10 level (tăng dần)

### Ranking
- Xem `/rank` để thấy thứ hạng
- Xem `/level` để thấy level & EXP hiện tại
- Xem `/leaderboard` để thấy Top 10 người chơi

### Bảng xếp hạng
| Thứ hạng | Tiêu đề |
|-----------|---------|
| #1 | 👑 Vô Địch |
| #2-3 | 🥇 Top 3 |
| #4-10 | 🥈 Top 10 |
| #11-20 | 🥉 Top 20 |

---

## 💰 Payback System

Hệ thống hoàn tiền tự động khi thua liên tiếp:
- Thua liên tiếp → nhận payback (tiền hoàn)
- Milestone越大, payback越大

---

## 🔑 Lệnh admin

```
/admin          → Mở Admin Panel
/giftcode ABCD  → Redeem giftcode
/reset xác nhận → Reset tài khoản
/history        → Xem lịch sử chơi
```

---

## 📊 Thống kê

```
/start     → Xem menu chính (stats + lịch sử nhanh)
/history   → Xem lịch sử chơi đầy đủ
/leaderboard → Top 10 người chơi
```

---

## 🛠️ Cài đặt chi tiết

### Bước 1: Yêu cầu hệ thống
- Python 3.10 hoặc mới hơn
- pip (quản lý package)
- Terminal / Command Prompt

### Bước 2: Tạo Bot trên Telegram
1. Mở Telegram, tìm **@BotFather**
2. Nhấn `/newbot`
3. Đặt tên cho bot (ví dụ: `Casino Bot`)
4. Đặt username (phải kết thúc bằng `bot`, ví dụ: `my_casino_xxx_bot`)
5. BotFather sẽ trả về **token** dạng:
   ```
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```
6. **LƯU TOKEN NÀY** — dùng ở Bước 4

### Bước 3: Clone hoặc tải source
```bash
cd ~
git clone <repo-url> taixiu-bot
# Hoặc copy thư mục taixiu-bot vào ~/taixiu-bot
```

### Bước 4: Cấu hình Token

**Sửa trực tiếp trong code**
Mở `taixiu_bot.py`, tìm dòng:
```python
return "YOUR_TELEGRAM_TOKEN_BOT"
```
Thay bằng:
```python
return "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
```

### Bước 5: Cài dependencies
```bash
cd ~/taixiu-bot
pip install python-telegram-bot
```

Nếu dùng Python 3.10+ và gặp lỗi, thử:
```bash
pip3 install python-telegram-bot --upgrade
```

### Bước 6: Chạy bot
```bash
cd ~/taixiu-bot
python3 taixiu_bot.py
```

Thấy dòng `Bot is running...` hoặc `Started` = thành công.

### Bước 7: Test
1. Mở Telegram, tìm bot刚才 tạo (username ở Bước 2)
2. Nhấn `/start`
3. Thấy menu = bot chạy OK

---

## 🛑 Dừng bot

### Dừng bằng Terminal
Nhấn `Ctrl + C` trong terminal đang chạy bot.

### Dừng bằng lệnh
```bash
# Tìm PID của bot
ps aux | grep taixiu_bot

# Kill theo PID
kill <PID>

# Hoặc kill tất cả
pkill -f taixiu_bot.py
```

### Kill từ xa (nếu bot chạy background)
```bash
pkill -f "python3 taixiu_bot.py"
```

---

## 🔧 Troubleshooting

### Lỗi `ModuleNotFoundError: No module named 'telegram'`
```bash
pip install python-telegram-bot
```

### Lỗi `Token is invalid` / `401 Unauthorized`
- Kiểm tra token trong `token.txt` đúng chưa
- Token không có khoảng trắng thừa
- Bot chưa bị BotFather kill

### Lỗi `chat_not_found`
- Bot chưa được start bởi user
- Nhấn `/start` với bot trước

### Bot không nhận lệnh
- Kiểm tra bot có đang chạy không: `ps aux | grep taixiu`
- Restart bot: `pkill -f taixiu_bot.py && cd ~/taixiu-bot && python3 taixiu_bot.py`

### Lỗi `database is locked`
```bash
# Kill bot rồi chạy lại
pkill -f taixiu_bot.py
cd ~/taixiu-bot
python3 taixiu_bot.py
```

---

## 📁 Cấu trúc file

```
taixiu-bot/
├── taixiu_bot.py      # File chính (~2100 dòng)
├── taixiu_db.py       # Database SQLite
├── taixiu_features.py # Ranking, Level, Payback
├── new_anims.py       # Animation 6 game
├── token.txt          # Bot token (không commit)
└── README.md          # Tài liệu này
```

---

## 🎯 Tính năng chính

- ✅ 6 game casino với animation rolling
- ✅ Quick Bet (chọn nhanh mức cược)
- ✅ Blackjack tương tác (HIT/STAND/DOUBLE)
- ✅ Hệ thống Level/EXP (max 1000)
- ✅ Ranking & Leaderboard
- ✅ Payback hoàn tiền khi thua
- ✅ Lịch sử chơi chi tiết
- ✅ Admin Panel (quản lý user, broadcast, giftcode)
- ✅ Markdown format đẹp mắt

---

## ⚠️ Lưu ý

- Balance mặc định: 10,000đ khi tạo tài khoản mới
- Không chia sẻ token bot với người khác
