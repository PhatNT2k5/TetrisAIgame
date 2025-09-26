# main_game.py
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import pygame
import random
import math
from hand_control import * # Import tất cả các lớp từ file hand_control

pygame.init()

# --- CẤU HÌNH VÀ HẰNG SỐ ---
WIDTH, HEIGHT = 1280, 720
ROWS, COLS = 20, 10
BLOCK = 30
BOARD_WIDTH = COLS * BLOCK
BOARD_HEIGHT = ROWS * BLOCK
FONT_SIZE = 24

win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon Tetris")
clock = pygame.time.Clock()

try:
    font = pygame.font.Font("Roboto-Regular.ttf", FONT_SIZE)
    logo_img = pygame.image.load("logo.png").convert_alpha()
    logo_img = pygame.transform.scale(logo_img, (180, 180))
except pygame.error as e:
    print(f"Lỗi tải file: {e}. Hãy chắc chắn file 'Roboto-Regular.ttf' và 'logo.png' có trong thư mục.")
    exit()

# --- BẢNG MÀU NEON ---
COLORS = { 'background': (10, 10, 25), 'grid': (20, 30, 70), 'panel_bg': (15, 15, 35, 200), 'panel_border': (50, 200, 255), 'text': (220, 220, 255), 'glow_text': (100, 255, 255), 'game_over': (255, 50, 50), 'ghost': (255, 255, 255, 50) }
SHAPES = { 'I': [[1, 1, 1, 1]], 'O': [[1, 1], [1, 1]], 'T': [[0, 1, 0], [1, 1, 1]], 'S': [[0, 1, 1], [1, 1, 0]], 'Z': [[1, 1, 0], [0, 1, 1]], 'J': [[1, 0, 0], [1, 1, 1]], 'L': [[0, 0, 1], [1, 1, 1]] }
SHAPE_COLORS = { 'I': (0, 220, 255), 'O': (255, 220, 0), 'T': (200, 50, 255), 'S': (50, 255, 100), 'Z': (255, 50, 50), 'J': (50, 100, 255), 'L': (255, 150, 0) }
TRASH_TALK_LINES = ["Gà quá vậy bạn ơi", "Đặt khối vậy là thua chắc rồi", "Chơi riết mà vẫn vậy hả?", "Tui không cố đâu, tại bạn yếu", "Sắp x2 điểm rồi đó, chịu không?", "Có cần tui nhường không bạn?"]

# --- CÁC HÀM TIỆN ÍCH VÀ VẼ ---
def rotate(shape): return [list(row)[::-1] for row in zip(*shape)]
def check_collision(board, shape, offset):
    ox, oy = offset
    for y, row in enumerate(shape):
        for x, val in enumerate(row):
            if val and (x + ox < 0 or x + ox >= COLS or y + oy >= ROWS or (y + oy >= 0 and board[y + oy][x + ox])): return True
    return False
def clear_rows(board):
    new_board = [row for row in board if not all(row)]
    return [[0]*COLS for _ in range(ROWS - len(new_board))] + new_board, ROWS - len(new_board)
def draw_detailed_block(surface, color, rect, is_ghost=False):
    if is_ghost:
        pygame.draw.rect(surface, COLORS['ghost'], rect, 2, border_radius=3)
        return
    highlight = tuple(min(c + 80, 255) for c in color)
    pygame.draw.rect(surface, color, rect.inflate(-6, -6), border_radius=4)
    pygame.draw.rect(surface, highlight, rect, 1, border_radius=5)
def draw_panel(surface, rect, title, title_font):
    panel_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel_surface, COLORS['panel_bg'], (0, 0, *rect.size), border_radius=8)
    pygame.draw.rect(panel_surface, COLORS['panel_border'], (0, 0, *rect.size), 2, border_radius=8)
    if title:
        title_surf = title_font.render(title, True, COLORS['text'])
        panel_surface.blit(title_surf, (rect.width / 2 - title_surf.get_width() / 2, 15))
    surface.blit(panel_surface, rect.topleft)
def draw_animated_grid_bg(surface, offset):
    for i in range(0, HEIGHT, 40): pygame.draw.line(surface, COLORS['grid'], (0, (i + offset) % HEIGHT), (WIDTH, (i + offset) % HEIGHT))
    for i in range(0, WIDTH, 40): pygame.draw.line(surface, COLORS['grid'], ((i + offset) % WIDTH, 0), ((i + offset) % WIDTH, HEIGHT))

class Particle:
    def __init__(self, x, y, color):
        self.x, self.y, self.color = x, y, color
        self.vx, self.vy = random.uniform(-4, 4), random.uniform(-6, 2)
        self.alpha, self.size = 255, random.randint(3, 7)
        self.lifetime = random.uniform(0.4, 0.8)
    def update(self, dt):
        self.x, self.y, self.vy, self.alpha, self.lifetime = self.x + self.vx, self.y + self.vy, self.vy + 0.2, self.alpha - (255 / self.lifetime) * dt, self.lifetime - dt
        return self.lifetime > 0
    def draw(self, surface):
        if self.alpha > 0:
            temp_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.rect(temp_surface, (*self.color, int(self.alpha)), (0, 0, self.size, self.size))
            surface.blit(temp_surface, (int(self.x), int(self.y)))

class Tetris:
    # (Same as the previous complete version)
    # ... [Implementation of Tetris class including spawn_piece, move, rotate_piece, lock_piece, update, and draw]
    def __init__(self, offset_x=0):
        self.offset_x = offset_x
        self.board = [[0]*COLS for _ in range(ROWS)]
        self.score = 0
        self.game_over = False
        self.particles = []
        self.line_clear_animation = [] 
        self.spawn_piece()
        
    def spawn_piece(self):
        self.piece_key = getattr(self, 'next_piece_key', random.choice(list(SHAPES.keys())))
        self.next_piece_key = random.choice(list(SHAPES.keys()))
        self.shape = SHAPES[self.piece_key]
        self.color = SHAPE_COLORS[self.piece_key]
        self.x, self.y = COLS // 2 - len(self.shape[0]) // 2, 0
        if check_collision(self.board, self.shape, (self.x, self.y)): self.game_over = True

    def move(self, dx, dy):
        if not self.game_over and not check_collision(self.board, self.shape, (self.x + dx, self.y + dy)):
            self.x, self.y = self.x + dx, self.y + dy
            return True
        return False

    def rotate_piece(self):
        if self.game_over: return
        rotated = rotate(self.shape)
        if not check_collision(self.board, rotated, (self.x, self.y)): self.shape = rotated

    def lock_piece(self):
        for y, row in enumerate(self.shape):
            for x, val in enumerate(row):
                if val:
                    block_x, block_y = self.offset_x + (self.x + x) * BLOCK + BLOCK // 2, (self.y + y) * BLOCK + BLOCK // 2
                    for _ in range(3): self.particles.append(Particle(block_x, block_y, self.color))
        
        for y, row in enumerate(self.shape):
            for x, val in enumerate(row):
                if val: self.board[y + self.y][x + self.x] = self.piece_key
        
        rows_to_clear = [i for i, row in enumerate(self.board) if all(row)]
        if rows_to_clear:
            self.board, cleared = clear_rows(self.board)
            self.score += cleared * 100 * cleared
            for r in rows_to_clear:
                self.line_clear_animation.append({'y': r, 'timer': 0.2})
                for x in range(COLS):
                    for _ in range(5): self.particles.append(Particle(self.offset_x + x*BLOCK + BLOCK//2, r*BLOCK + BLOCK//2, (255,255,255)))

        if not self.game_over: self.spawn_piece()

    def update(self):
        if not self.game_over and not self.move(0, 1): self.lock_piece()
    
    def draw(self, surface, dt):
        board_rect = pygame.Rect(self.offset_x, 0, BOARD_WIDTH, BOARD_HEIGHT)
        next_piece_rect = pygame.Rect(self.offset_x + BOARD_WIDTH + 20, 50, 160, 160)
        score_rect = pygame.Rect(self.offset_x + BOARD_WIDTH + 20, 230, 160, 80)
        
        draw_panel(surface, board_rect, "", font)
        draw_panel(surface, next_piece_rect, "NEXT", font)
        draw_panel(surface, score_rect, "SCORE", font)
        
        for y in range(ROWS): pygame.draw.line(surface, COLORS['grid'], (self.offset_x, y * BLOCK), (self.offset_x + BOARD_WIDTH, y * BLOCK))
        for x in range(COLS): pygame.draw.line(surface, COLORS['grid'], (self.offset_x + x * BLOCK, 0), (self.offset_x + x * BLOCK, BOARD_HEIGHT))

        for y, row in enumerate(self.board):
            for x, cell in enumerate(row):
                if cell: draw_detailed_block(surface, SHAPE_COLORS[cell] if not self.game_over else (80, 80, 80), pygame.Rect(self.offset_x + x * BLOCK, y * BLOCK, BLOCK, BLOCK))

        if not self.game_over:
            ghost_y = self.y
            while not check_collision(self.board, self.shape, (self.x, ghost_y + 1)): ghost_y += 1
            for y, row in enumerate(self.shape):
                for x, val in enumerate(row):
                    if val: draw_detailed_block(surface, self.color, pygame.Rect(self.offset_x + (self.x + x) * BLOCK, (ghost_y + y) * BLOCK, BLOCK, BLOCK), is_ghost=True)
            for y, row in enumerate(self.shape):
                for x, val in enumerate(row):
                    if val: draw_detailed_block(surface, self.color, pygame.Rect(self.offset_x + (self.x + x) * BLOCK, (self.y + y) * BLOCK, BLOCK, BLOCK))
        
        for anim in self.line_clear_animation[:]:
            anim['timer'] -= dt
            if anim['timer'] <= 0: self.line_clear_animation.remove(anim)
            else:
                flash = pygame.Surface((BOARD_WIDTH, BLOCK)); flash.set_alpha(anim['timer'] / 0.2 * 200); flash.fill((255, 255, 255))
                surface.blit(flash, (self.offset_x, anim['y'] * BLOCK))
        
        for p in self.particles[:]:
            p.draw(surface)
            if not p.update(dt): self.particles.remove(p)

        next_shape = SHAPES[self.next_piece_key]; next_color = SHAPE_COLORS[self.next_piece_key]
        scaled_block = BLOCK * 0.7
        start_x, start_y = next_piece_rect.centerx - (len(next_shape[0]) * scaled_block) / 2, next_piece_rect.centery - (len(next_shape) * scaled_block) / 2 + 10
        for y, row in enumerate(next_shape):
            for x, val in enumerate(row):
                if val: draw_detailed_block(surface, next_color, pygame.Rect(start_x + x * scaled_block, start_y + y * scaled_block, scaled_block, scaled_block))

        score_font = pygame.font.Font("Roboto-Regular.ttf", 32)
        score_surf = score_font.render(f"{self.score}", True, COLORS['text'])
        surface.blit(score_surf, (score_rect.centerx - score_surf.get_width()/2, score_rect.centery))

        if self.game_over:
            over_font = pygame.font.Font("Roboto-Regular.ttf", 50)
            retry_font = pygame.font.Font("Roboto-Regular.ttf", 24)
            over_text = over_font.render("GAME OVER", True, COLORS['game_over'])
            retry_text = retry_font.render("Press R to retry - Q to menu", True, COLORS['text'])
            surface.blit(over_text, over_text.get_rect(center=(self.offset_x + BOARD_WIDTH/2, BOARD_HEIGHT/2 - 30)))
            surface.blit(retry_text, retry_text.get_rect(center=(self.offset_x + BOARD_WIDTH/2, BOARD_HEIGHT/2 + 30)))

class TetrisAI(Tetris):
    def __init__(self, offset_x=0):
        super().__init__(offset_x)
        self.ai_mode = "idle"
        self.ai_target_rot, self.ai_target_x = 0, 0

    def update_ai(self, can_drop=True):
        if self.game_over: return
        if self.ai_mode == "idle":
            self.ai_target_rot, self.ai_target_x = self.find_best_move()
            self.ai_mode = "rotating"
        elif self.ai_mode == "rotating":
            if self.ai_target_rot > 0: self.rotate_piece(); self.ai_target_rot -= 1
            else: self.ai_mode = "moving"
        elif self.ai_mode == "moving":
            if self.x < self.ai_target_x: self.move(1, 0)
            elif self.x > self.ai_target_x: self.move(-1, 0)
            else: self.ai_mode = "dropping"
        elif self.ai_mode == "dropping":
            if can_drop:
                if not self.move(0, 1):
                    self.lock_piece()
                    self.ai_mode = "idle"

    def find_best_move(self):
        best_score, best_rotation, best_x = -float('inf'), 0, 0
        for r in range(4):
            test_shape = self.shape
            for _ in range(r): test_shape = rotate(test_shape)
            for x in range(COLS - len(test_shape[0]) + 1):
                y = 0
                while not check_collision(self.board, test_shape, (x, y + 1)): y += 1
                
                temp_board = [row[:] for row in self.board]
                for ty, row in enumerate(test_shape):
                    for tx, val in enumerate(row):
                        if val: temp_board[ty + y][tx + x] = 'X'
                
                score = self.evaluate_board(temp_board)
                if score > best_score:
                    best_score, best_rotation, best_x = score, r, x
        return best_rotation, best_x

    def evaluate_board(self, board):
        heights = [next((r for r in range(ROWS) if board[r][c]), ROWS) for c in range(COLS)]
        agg_height = sum(ROWS - h for h in heights)
        completed_lines = sum(1 for row in board if all(row))
        holes = sum(1 for c in range(COLS) for r in range(heights[c], ROWS) if not board[r][c])
        bumpiness = sum(abs(heights[i] - heights[i+1]) for i in range(COLS-1))
        return completed_lines * 0.76 - agg_height * 0.51 - holes * 0.35 - bumpiness * 0.18

# --- CÁC CHẾ ĐỘ CHƠI VÀ MENU ---
def draw_menu(surface, selected, grid_offset):
    draw_animated_grid_bg(surface, grid_offset)
    title_font, pulse = pygame.font.Font("Roboto-Regular.ttf", 90), (math.sin(pygame.time.get_ticks() * 0.002) + 1) / 2
    glow_color = (100, COLORS['glow_text'][1] * (0.8 + pulse * 0.2), COLORS['glow_text'][2] * (0.8 + pulse * 0.2))
    
    title_surf = title_font.render("TETRIS", True, COLORS['text'])
    glow_surf = title_font.render("TETRIS", True, glow_color)
    for i in range(4, 0, -1):
        temp_glow = glow_surf.copy(); temp_glow.set_alpha(50 // i)
        surface.blit(temp_glow, (WIDTH/2 - temp_glow.get_width()/2, HEIGHT/4 - temp_glow.get_height()/2 + i*2))
    surface.blit(title_surf, (WIDTH/2 - title_surf.get_width()/2, HEIGHT/4 - title_surf.get_height()/2))
    surface.blit(logo_img, (WIDTH/2 - logo_img.get_width()/2, 20))

    options = ["1. Solo with Hand Control", "2. Solo vs AI (Keyboard)"]
    for i, text in enumerate(options):
        op_font = pygame.font.Font("Roboto-Regular.ttf", int(FONT_SIZE * (1.5 if selected == i else 1.2)))
        color = COLORS['glow_text'] if selected == i else COLORS['text']
        prefix, suffix = ("> " if selected == i else ""), (" <" if selected == i else "")
        option_surf = op_font.render(prefix + text + suffix, True, color)
        surface.blit(option_surf, option_surf.get_rect(center=(WIDTH/2, HEIGHT/2 + 50 + i * 70)))

def menu_loop():
    selected, grid_offset = 0, 0
    while True:
        grid_offset = (grid_offset - 0.2) % 40
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_DOWN, pygame.K_s): selected = (selected + 1) % 2
                elif event.key in (pygame.K_UP, pygame.K_w): selected = (selected - 1 + 2) % 2
                elif event.key == pygame.K_RETURN: return 'solo' if selected == 0 else 'ai'
        win.fill(COLORS['background']); draw_menu(win, selected, grid_offset); pygame.display.flip(); clock.tick(60)

# File: test.py
# TÌM HÀM solo_mode() CŨ VÀ THAY THẾ TOÀN BỘ BẰNG HÀM NÀY

def solo_mode():
    tracker = HandTracker()
    try:
        # === KHỞI TẠO CÁC BỘ PHÁT HIỆN ===
        move_detector = MoveDetector()
        wave_detector = WaveDetector()
        tap_detector = FingerTapDetector()
        # THÊM bộ phát hiện thả khối mới
        drop_detector = DropDetector()
        # BỎ ĐI fist_detector
        
        game_is_running = True
        while game_is_running:
            game = Tetris(offset_x=(WIDTH - BOARD_WIDTH) / 2 - 100)
            fall_speed, fall_time, move_delay, move_timer = 0.5, 0, 0.12, 0
            
            in_game = True
            while in_game:
                dt = clock.tick(60) / 1000
                fall_time, move_timer = fall_time + dt, move_timer + dt

                # Reset các hành động ở mỗi vòng lặp
                gesture, movement, drop_action = "None", "None", "None"

                if tracker.update():
                    # === LẤY CÁC HÀNH ĐỘNG TỪ BỘ PHÁT HIỆN ===
                    # 1. Lấy chuyển động ngang
                    movement = move_detector.detect(tracker)
                    # 2. Lấy hành động thả khối (đi xuống)
                    drop_action = drop_detector.detect(tracker)
                    # 3. Lấy các cử chỉ đặc biệt (vẫy tay, xoay)
                    gestures = [
                        wave_detector.detect(tracker),
                        tap_detector.detect(tracker)
                    ]
                    gesture = next((g for g in gestures if g != "None"), "None")

                for event in pygame.event.get():
                    if event.type == pygame.QUIT: in_game, game_is_running = False, False
                    if game.game_over and event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_q: in_game, game_is_running = False, False
                        elif event.key == pygame.K_r: in_game = False

                if not game.game_over:
                    # Xử lý di chuyển ngang
                    if movement == "Move Left" and move_timer > move_delay:
                        game.move(-1, 0); move_timer = 0
                    elif movement == "Move Right" and move_timer > move_delay:
                        game.move(1, 0); move_timer = 0
                    
                    # Xử lý xoay khối
                    if gesture == "Tap (Rotate)":
                        game.rotate_piece()

                    # === XỬ LÝ THẢ KHỐI BẰNG HÀNH ĐỘNG MỚI ===
                    if drop_action == "Drop Down":
                        game.update() # Gọi update() để khối rơi xuống 1 nấc
                    
                    # Tự động rơi xuống theo thời gian
                    if fall_time > fall_speed: 
                        game.update()
                        fall_time = 0

                # Chơi lại bằng cử chỉ vẫy tay
                if gesture == "Wave (Play Again)" and game.game_over:
                    in_game = False

                # Vẽ mọi thứ lên màn hình
                win.fill(COLORS['background'])
                draw_animated_grid_bg(win, pygame.time.get_ticks() * 0.01)
                game.draw(win, dt)
                win.blit(tracker.draw_debug_info(gesture, movement), (20, HEIGHT - 170))
                tracker.show_frame()
                pygame.display.flip()
    finally:
        tracker.release()
def vs_ai_mode():
    game_is_running = True
    while game_is_running:
        board_area_width = (BOARD_WIDTH + 180) * 2
        start_x = (WIDTH - board_area_width) // 2 + 50
        player_x = start_x
        ai_x = start_x + BOARD_WIDTH + 180 + 50
        
        player_game, ai_game = Tetris(offset_x=player_x), TetrisAI(offset_x=ai_x)
        fall_speed, player_fall_time, move_delay, move_timer = 0.4, 0, 0.1, 0
        ai_drop_speed, ai_drop_timer = 0.05, 0 # AI moves very fast
        
        last_trash_talk_time, trash_talk_interval, current_trash_msg, msg_alpha = 0, 5, "", 0
        
        in_game = True
        while in_game:
            dt = clock.tick(60) / 1000
            player_fall_time, move_timer, ai_drop_timer = player_fall_time + dt, move_timer + dt, ai_drop_timer + dt
            
            # AI Logic
            ai_game.update_ai(can_drop=(ai_drop_timer > ai_drop_speed))
            
            # Player Logic
            for event in pygame.event.get():
                if event.type == pygame.QUIT: in_game, game_is_running = False, False
                if player_game.game_over and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q: in_game, game_is_running = False, False
                    elif event.key == pygame.K_r: in_game = False
                if not player_game.game_over and event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_UP, pygame.K_w): player_game.rotate_piece()
            
            keys = pygame.key.get_pressed()
            if not player_game.game_over:
                if keys[pygame.K_LEFT] and move_timer > move_delay: player_game.move(-1, 0); move_timer = 0
                if keys[pygame.K_RIGHT] and move_timer > move_delay: player_game.move(1, 0); move_timer = 0
                if keys[pygame.K_DOWN]: player_game.update()
            if player_fall_time > fall_speed: player_game.update(); player_fall_time = 0
            
            # Trash Talk Logic
            last_trash_talk_time += dt
            if ai_game.score > player_game.score + 200 and last_trash_talk_time > trash_talk_interval:
                current_trash_msg, last_trash_talk_time, msg_alpha = random.choice(TRASH_TALK_LINES), 0, 255
            if msg_alpha > 0: msg_alpha -= 100 * dt

            # Drawing
            win.fill(COLORS['background']); draw_animated_grid_bg(win, pygame.time.get_ticks() * 0.01)
            player_game.draw(win, dt); ai_game.draw(win, dt)
            
            # Labels
            label_font = pygame.font.Font("Roboto-Regular.ttf", 40)
            player_label = label_font.render("YOU", True, (50, 200, 255))
            ai_label = label_font.render("AI", True, (255, 100, 100))
            win.blit(player_label, player_label.get_rect(midbottom=(player_x + BOARD_WIDTH/2, -5)))
            win.blit(ai_label, ai_label.get_rect(midbottom=(ai_x + BOARD_WIDTH/2, -5)))

            # Trash talk bubble
            if msg_alpha > 0:
                bubble_font = pygame.font.Font("Roboto-Regular.ttf", 22)
                text = bubble_font.render(current_trash_msg, True, COLORS['game_over'])
                text_rect = text.get_rect(center=(WIDTH/2, HEIGHT - 50))
                bubble_rect = text_rect.inflate(20, 10) # Tăng kích thước thêm 20px chiều rộng, 10px chiều cao
                bubble_surf = pygame.Surface(bubble_rect.size, pygame.SRCALPHA)
                bubble_surf.set_alpha(msg_alpha)
                pygame.draw.rect(bubble_surf, COLORS['panel_bg'], (0, 0, *bubble_rect.size), border_radius=10)
                pygame.draw.rect(bubble_surf, COLORS['game_over'], (0, 0, *bubble_rect.size), 2, border_radius=10)
                bubble_surf.blit(text, text.get_rect(center=(bubble_rect.width/2, bubble_rect.height/2)))
                win.blit(bubble_surf, bubble_rect)
            
            pygame.display.flip()

if __name__ == "__main__":
    while True:
        mode = menu_loop()
        if mode == 'solo': solo_mode()
        elif mode == 'ai': vs_ai_mode()