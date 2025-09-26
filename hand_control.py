# File: hand_control.py
# XÓA TẤT CẢ MÃ CŨ VÀ DÁN MÃ MỚI NÀY VÀO

import cv2
import mediapipe as mp
import math
import pygame # Cần pygame để tạo debug surface và lấy thời gian

# Initialize MediaPipe Hands - Khởi tạo một lần và dùng chung
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
)

class HandTracker:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open webcam.")
            exit()
        self.frame = None
        self.results = None # Lưu kết quả của mediapipe ở đây
        self.wrist_x, self.wrist_y = None, None
        self.center_x, self.center_y = None, None
        self.frame_width, self.frame_height = None, None
        self.condition_status = "Not Checked"

    def update(self):
        ret, frame = self.cap.read()
        if not ret:
            print("Error: Could not read frame.")
            return False
        self.frame = cv2.flip(frame, 1)
        self.frame_height, self.frame_width, _ = self.frame.shape
        frame_rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
        
        # Xử lý và lưu kết quả vào self.results
        self.results = hands.process(frame_rgb)

        # Reset trạng thái
        self.wrist_x, self.wrist_y, self.center_x, self.center_y = None, None, None, None
        self.condition_status = "Not Checked"

        if self.results.multi_hand_landmarks:
            for hand_landmarks in self.results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    self.frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=4),
                    mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
                )

                wrist = hand_landmarks.landmark[0]
                self.wrist_x = int(wrist.x * self.frame_width)
                self.wrist_y = int(wrist.y * self.frame_height)

                x_coords = [lm.x * self.frame_width for lm in hand_landmarks.landmark]
                y_coords = [lm.y * self.frame_height for lm in hand_landmarks.landmark]
                min_x, max_x = int(min(x_coords)) - 20, int(max(x_coords)) + 20
                min_y, max_y = int(min(y_coords)) - 20, int(max(y_coords)) + 20

                cv2.rectangle(self.frame, (min_x, min_y), (max_x, max_y), (255, 255, 0), 2)
                self.center_x = (min_x + max_x) // 2
                self.center_y = (min_y + max_y) // 2
                cv2.circle(self.frame, (self.center_x, self.center_y), 5, (0, 255, 255), -1)

                self.condition_status = "Checked"
        return True

    def draw_debug_info(self, gesture, movement):
        debug_surface = pygame.Surface((280, 150), pygame.SRCALPHA)
        font = pygame.font.Font("Roboto-Regular.ttf", 18)
        
        pygame.draw.rect(debug_surface, (15, 15, 35, 200), (0, 0, 280, 150), border_radius=8)
        pygame.draw.rect(debug_surface, (50, 200, 255), (0, 0, 280, 150), 2, border_radius=8)

        info = [
            f"Gesture: {gesture}",
            f"Movement: {movement}",
            f"Center: ({self.center_x}, {self.center_y})" if self.center_x else "Center: N/A",
            f"Status: {self.condition_status}"
        ]

        for i, text in enumerate(info):
            text_surf = font.render(text, True, (220, 220, 255))
            debug_surface.blit(text_surf, (15, 15 + i * 30))
        return debug_surface

    def show_frame(self):
        cv2.imshow("Hand Tracking", self.frame)

    def release(self):
        if self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()

class MoveDetector:
    def __init__(self):
        self.BOX_SIZE = 200
        self.MOVE_THRESHOLD = 15
        self.last_center_x = None
        self.cumulative_delta_x = 0
        self.movement = ""
        self.box_left, self.box_right, self.box_top, self.box_bottom = None, None, None, None

    def detect(self, tracker):
        if self.box_left is None and tracker.frame_width is not None:
            self.box_left = (tracker.frame_width // 2) - (self.BOX_SIZE // 2)
            self.box_right = (tracker.frame_width // 2) + (self.BOX_SIZE // 2)
            self.box_top = (tracker.frame_height // 2) - (self.BOX_SIZE // 2)
            self.box_bottom = (tracker.frame_height // 2) + (self.BOX_SIZE // 2)
        
        if self.box_left is None: return ""

        cv2.rectangle(tracker.frame, (self.box_left, self.box_top), (self.box_right, self.box_bottom), (0, 255, 255), 2)
        
        self.movement = ""
        if tracker.center_x is None or tracker.center_y is None:
            self.last_center_x, self.cumulative_delta_x = None, 0
            return self.movement

        hand_in_box = self.box_left <= tracker.center_x <= self.box_right and self.box_top <= tracker.center_y <= self.box_bottom

        if hand_in_box:
            if self.last_center_x is not None:
                delta_x = tracker.center_x - self.last_center_x
                self.cumulative_delta_x += delta_x
                if self.cumulative_delta_x > self.MOVE_THRESHOLD:
                    self.movement, self.cumulative_delta_x = "Move Right", 0
                elif self.cumulative_delta_x < -self.MOVE_THRESHOLD:
                    self.movement, self.cumulative_delta_x = "Move Left", 0
                else:
                    self.movement = "In Box"
            else:
                self.movement = "In Box"
        else:
            self.movement, self.cumulative_delta_x = "Outside Box", 0

        self.last_center_x = tracker.center_x
        return self.movement

# =================================================================================
# LỚP PHÁT HIỆN "BÚNG TAY" MỚI - ĐỂ XOAY KHỐI
# =================================================================================
class FingerTapDetector:
    def __init__(self, ready_threshold=0.15, cooldown=0.5):
        self.gesture = "None"
        self.ready_threshold = ready_threshold  # Ngón tay phải duỗi trong 0.15s để sẵn sàng
        self.cooldown = cooldown  # Nghỉ 0.5s sau mỗi lần xoay
        
        self.is_ready = False
        self.time_finger_up = 0
        self.last_tap_time = 0

    def detect(self, tracker):
        current_time = pygame.time.get_ticks() / 1000.0
        self.gesture = "None"

        if current_time - self.last_tap_time < self.cooldown:
            return self.gesture

        if not tracker.results or not tracker.results.multi_hand_landmarks:
            self.is_ready = False
            self.time_finger_up = 0
            return self.gesture

        hand_landmarks = tracker.results.multi_hand_landmarks[0]
        index_tip = hand_landmarks.landmark[8]
        index_pip = hand_landmarks.landmark[6]
        
        is_finger_up = index_tip.y < index_pip.y

        if is_finger_up:
            if self.time_finger_up == 0:
                self.time_finger_up = current_time
            
            if not self.is_ready and (current_time - self.time_finger_up > self.ready_threshold):
                self.is_ready = True
        else:
            if self.is_ready:
                self.gesture = "Tap (Rotate)"
                self.last_tap_time = current_time
            
            self.is_ready = False
            self.time_finger_up = 0
            
        return self.gesture

class DropDetector:
    def __init__(self, move_threshold=20):
        self.gesture = "None"
        self.last_center_y = None
        self.cumulative_delta_y = 0
        self.MOVE_THRESHOLD = move_threshold # Độ nhạy của chuyển động

    def detect(self, tracker):
        self.gesture = "None"

        # Nếu không có tay, reset và thoát
        if tracker.center_y is None:
            self.last_center_y = None
            self.cumulative_delta_y = 0
            return self.gesture

        if self.last_center_y is not None:
            # Tính toán sự thay đổi vị trí theo chiều dọc
            delta_y = tracker.center_y - self.last_center_y

            # Chỉ tích lũy khi tay đi xuống (delta_y > 0)
            if delta_y > 0:
                self.cumulative_delta_y += delta_y
            else:
                # Nếu tay đi lên, reset bộ đếm
                self.cumulative_delta_y = 0
            
            # Nếu di chuyển xuống đủ nhiều, kích hoạt cử chỉ
            if self.cumulative_delta_y > self.MOVE_THRESHOLD:
                self.gesture = "Drop Down"
                # Reset ngay lập tức để cử chỉ chỉ kích hoạt 1 lần cho mỗi cú trượt tay
                self.cumulative_delta_y = 0

        # Cập nhật vị trí cuối cùng của tay
        self.last_center_y = tracker.center_y
        return self.gesture

class WaveDetector:
    def __init__(self):
        self.WAVE_THRESHOLD, self.WAVE_COUNT_needed = 80, 3
        self.wave_directions, self.last_wrist_x = [], None
        self.gesture = "None"

    def detect(self, tracker):
        self.gesture = "None"
        if tracker.wrist_x is None:
            self.last_wrist_x, self.wave_directions = None, []
            return self.gesture

        if self.last_wrist_x is not None:
            delta_x = tracker.wrist_x - self.last_wrist_x
            
            if delta_x > self.WAVE_THRESHOLD:
                if not self.wave_directions or self.wave_directions[-1] != 'R': self.wave_directions.append('R')
            elif delta_x < -self.WAVE_THRESHOLD:
                if not self.wave_directions or self.wave_directions[-1] != 'L': self.wave_directions.append('L')

            if len(self.wave_directions) > self.WAVE_COUNT_needed * 2: self.wave_directions.pop(0)
            if len(self.wave_directions) >= self.WAVE_COUNT_needed:
                self.gesture, self.wave_directions = "Wave (Play Again)", []

        self.last_wrist_x = tracker.wrist_x
        return self.gesture

# Bỏ đi lớp PointUpDetector vì ta không dùng nữa