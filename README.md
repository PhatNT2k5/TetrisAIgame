#  Neon Tetris – Hand Controlled & AI Mode  


##  Giới thiệu  
Dự án này là một phiên bản **Tetris hiện đại** với hiệu ứng neon, có hai chế độ chơi đặc biệt:  

-  **Hand Control Mode** – Điều khiển khối Tetris bằng cử chỉ tay qua webcam (sử dụng **MediaPipe**).  
-  **VS AI Mode** – Đấu Tetris trực tiếp với AI được lập trình sẵn.  

Ngoài ra, game có hiệu ứng particle, giao diện neon, và thêm cả **“trash talk”** vui nhộn khi chơi với AI.  

---

## Tính năng  
- 🎥 Nhận diện bàn tay qua **MediaPipe + OpenCV**.  
- ⬅️➡️ **Move Left / Move Right** bằng cử chỉ tay trong khung.  
- 🔄 **Rotate** bằng động tác **búng ngón tay**.  
- ⬇️ **Drop nhanh** bằng động tác **kéo tay xuống**.  
-  **Wave tay** để **chơi lại**.  
-  AI thông minh có thể tự tính toán nước đi tốt nhất (lookahead).  

---

##  Cấu trúc dự án  
```
FlappyWukong/
│── main.py             # Game chính (menu, solo mode, vs AI)
│── test.py             # Phiên bản cải tiến với hand control
│── hand_control.py     # Module nhận diện tay & cử chỉ
│── requirements.txt    # Thư viện cần cài
│── logo.png            # Logo game
│── Assets/             # Hình ảnh, background
│── sounds/             # Âm thanh game
│── font/               # Font chữ (Roboto, Patriot, ...)
```

---

##  Cài đặt  
### 1. Clone repo  
```bash
git clone https://github.com/PhatNT2k5/TetrisAIgame
cd FlappyWukong
```

### 2. Tạo môi trường ảo (khuyến nghị)  
```bash
python -m venv venv
source venv/bin/activate   # (Linux/Mac)
venv\Scripts\activate      # (Windows)
```

### 3. Cài đặt thư viện  
```bash
pip install -r requirements.txt
```

---

##  Chạy game  
### Chế độ menu:
```bash
python main.py
```
- Chọn **Solo Mode** (Hand Control).  
- Chọn **VS AI Mode** (đấu với AI).  

### Nếu muốn thử bản Neon nâng cấp:
```bash
python test.py
```

---

## Điều khiển (Hand Mode)  
- Đặt tay trong khung nhận diện.  
- Di chuyển sang trái/phải bằng cách đưa tay sang ngang.  
- Búng ngón tay để xoay khối.  
- Kéo tay xuống để thả nhanh.  
- Vẫy tay để restart.  

---

##  Dependencies chính  
- `pygame` – Game engine  
- `opencv-python` – Webcam  
- `mediapipe` – Nhận diện tay  
- `numpy` – Tính toán ma trận  
- `matplotlib`, `scipy` – Hỗ trợ AI  

(Chi tiết trong `requirements.txt`)  

---

##  License  
MIT License – thoải mái sử dụng & chỉnh sửa.  
