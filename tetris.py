#
# 교육 환경 설정 및 간단한 파이썬 연습 코드
# 기능 : 개선된 테트리스 #3 — 배경음악  (브랜치: feature/bgm → develop)
#
# 작성일 : 2026-07-06
# 작성자 : 백정열, SKALA
#
# 변경일 : 2026-07-06
# 변경 내용 : 추가 기능 확대 - 게임 진행 중 테트리스 배경음악 재생, 
#사전 준비: bgm.mp3 파일을 tetris.py와 같은 폴더에 준비하거나
#           아래 generate_bgm() 함수로 간단한 비프음을 생성할 수 있습니다.
#
# [BGM 파일 없을 때 대안]
#   pip install numpy
#   python -c "import tetris_v4_bgm"  # 실행 시 자동으로 bgm.wav 생성
#
# All Rights Reserved by SK AX, SKALA
#

import pygame
import random
import os
import struct
import wave

# ─────────────────────────────────────────────
# BGM 파일 생성 (bgm.mp3가 없을 때 간단한 wav 생성)
# ─────────────────────────────────────────────
def generate_bgm(filename="bgm.wav"):
    """numpy 없이 순수 파이썬으로 간단한 테트리스풍 멜로디 wav 생성"""
    sample_rate = 44100
    # 테트리스 테마 일부 (주파수, 박자)
    notes = [
        (659, 0.5), (494, 0.25), (523, 0.25), (587, 0.5),
        (523, 0.25), (494, 0.25), (440, 0.5), (440, 0.25),
        (523, 0.25), (659, 0.5), (587, 0.25), (523, 0.25),
        (494, 0.75), (523, 0.25), (587, 0.5), (659, 0.5),
        (523, 0.5), (440, 0.5), (440, 0.5), (0, 0.25),
    ]
    frames = []
    for freq, duration in notes * 4:  # 4번 반복
        n_samples = int(sample_rate * duration)
        for i in range(n_samples):
            if freq == 0:
                val = 0
            else:
                import math
                val = int(32767 * 0.3 * math.sin(2 * math.pi * freq * i / sample_rate))
            frames.append(struct.pack('<h', val))

    with wave.open(filename, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))
    return filename


# ─────────────────────────────────────────────
# 상수
# ─────────────────────────────────────────────
BOARD_WIDTH   = 300
BOARD_HEIGHT  = 600
SIDE_WIDTH    = 150
SCREEN_WIDTH  = BOARD_WIDTH + SIDE_WIDTH
SCREEN_HEIGHT = BOARD_HEIGHT
BLOCK_SIZE = 30
COLS = 10
ROWS = 20

BLACK      = (0, 0, 0)
WHITE      = (255, 255, 255)
GRAY       = (50, 50, 50)
LIGHT_GRAY = (180, 180, 180)
YELLOW     = (255, 215, 0)
GREEN      = (0, 220, 100)

COLORS = [
    (0, 240, 240), (0, 0, 240), (240, 160, 0), (240, 240, 0),
    (0, 240, 0), (160, 0, 240), (240, 0, 0),
]
SHAPES = [
    [[1,1,1,1]],
    [[1,0,0],[1,1,1]],
    [[0,0,1],[1,1,1]],
    [[1,1],[1,1]],
    [[0,1,1],[1,1,0]],
    [[0,1,0],[1,1,1]],
    [[1,1,0],[0,1,1]],
]
LINE_SCORES = {1: 100, 2: 300, 3: 500, 4: 800}


class Tetromino:
    def __init__(self):
        idx = random.randint(0, len(SHAPES) - 1)
        self.shape = [row[:] for row in SHAPES[idx]]
        self.color = COLORS[idx]
        self.x = COLS // 2 - len(self.shape[0]) // 2
        self.y = 0


class Board:
    def __init__(self):
        self.grid = [[None] * COLS for _ in range(ROWS)]

    def is_valid(self, piece, dx=0, dy=0, shape=None):
        s = shape if shape else piece.shape
        for r, row in enumerate(s):
            for c, cell in enumerate(row):
                if cell:
                    nx, ny = piece.x + c + dx, piece.y + r + dy
                    if nx < 0 or nx >= COLS or ny >= ROWS:
                        return False
                    if ny >= 0 and self.grid[ny][nx]:
                        return False
        return True

    def lock(self, piece):
        for r, row in enumerate(piece.shape):
            for c, cell in enumerate(row):
                if cell:
                    self.grid[piece.y + r][piece.x + c] = piece.color

    def clear_lines(self):
        full = [r for r in range(ROWS) if all(self.grid[r])]
        for r in full:
            del self.grid[r]
            self.grid.insert(0, [None] * COLS)
        return len(full)

    def draw(self, surface):
        for r in range(ROWS):
            for c in range(COLS):
                color = self.grid[r][c]
                rect = pygame.Rect(c * BLOCK_SIZE, r * BLOCK_SIZE, BLOCK_SIZE - 1, BLOCK_SIZE - 1)
                if color:
                    pygame.draw.rect(surface, color, rect)
                else:
                    pygame.draw.rect(surface, GRAY, rect, 1)


def draw_piece(surface, piece):
    for r, row in enumerate(piece.shape):
        for c, cell in enumerate(row):
            if cell:
                rect = pygame.Rect(
                    (piece.x + c) * BLOCK_SIZE, (piece.y + r) * BLOCK_SIZE,
                    BLOCK_SIZE - 1, BLOCK_SIZE - 1
                )
                pygame.draw.rect(surface, piece.color, rect)


def draw_next_piece(surface, next_piece, font):
    px, py = BOARD_WIDTH + 10, 10
    surface.blit(font.render("NEXT", True, WHITE), (px + 20, py))
    size = BLOCK_SIZE * 4
    pygame.draw.rect(surface, GRAY, (px, py + 30, size + 10, size + 10), 1)
    sw = len(next_piece.shape[0]) * BLOCK_SIZE
    sh = len(next_piece.shape)    * BLOCK_SIZE
    ox = px + (size - sw) // 2 + 5
    oy = py + 30 + (size - sh) // 2 + 5
    for r, row in enumerate(next_piece.shape):
        for c, cell in enumerate(row):
            if cell:
                pygame.draw.rect(surface, next_piece.color,
                    (ox + c * BLOCK_SIZE, oy + r * BLOCK_SIZE, BLOCK_SIZE - 1, BLOCK_SIZE - 1))


def draw_score(surface, score, lines, font, small_font):
    px, y = BOARD_WIDTH + 10, 200
    pygame.draw.line(surface, LIGHT_GRAY, (px, y), (px + 130, y), 1)
    y += 15
    surface.blit(font.render("SCORE", True, YELLOW), (px + 10, y));  y += 30
    surface.blit(small_font.render(str(score), True, WHITE), (px + 10, y)); y += 40
    surface.blit(font.render("LINES", True, LIGHT_GRAY), (px + 10, y)); y += 30
    surface.blit(small_font.render(str(lines), True, WHITE), (px + 10, y))


# ─────────────────────────────────────────────
# [추가] BGM 로드 및 재생
# ─────────────────────────────────────────────
def load_bgm():
    """bgm.mp3 또는 bgm.wav를 로드. 없으면 자동 생성."""
    for filename in ("bgm.mp3", "bgm.wav"):
        if os.path.exists(filename):
            return filename
    # 파일이 없으면 간단한 wav 생성
    print("[BGM] bgm 파일이 없어 bgm.wav를 자동 생성합니다.")
    return generate_bgm("bgm.wav")


def main():
    pygame.init()
    pygame.mixer.init()   # [추가] 사운드 믹서 초기화

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("테트리스 (BGM)")
    clock = pygame.time.Clock()
    font       = pygame.font.SysFont("Arial", 20, bold=True)
    small_font = pygame.font.SysFont("Arial", 28, bold=True)

    # [추가] BGM 로드 및 반복 재생
    bgm_file = load_bgm()
    pygame.mixer.music.load(bgm_file)
    pygame.mixer.music.set_volume(0.5)   # 볼륨 50%
    pygame.mixer.music.play(-1)           # -1: 무한 반복

    board      = Board()
    piece      = Tetromino()
    next_piece = Tetromino()
    fall_time  = 0
    fall_speed = 500
    score      = 0
    total_lines = 0
    bgm_playing = True   # [추가] BGM 상태

    running   = True
    game_over = False

    while running:
        dt = clock.tick(60)
        screen.fill(BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if not game_over and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    if board.is_valid(piece, dx=-1): piece.x -= 1
                elif event.key == pygame.K_RIGHT:
                    if board.is_valid(piece, dx=1): piece.x += 1
                elif event.key == pygame.K_DOWN:
                    if board.is_valid(piece, dy=1): piece.y += 1
                elif event.key == pygame.K_UP:
                    rotated = [
                        [piece.shape[r][c] for r in range(len(piece.shape) - 1, -1, -1)]
                        for c in range(len(piece.shape[0]))
                    ]
                    if board.is_valid(piece, shape=rotated):
                        piece.shape = rotated
                elif event.key == pygame.K_SPACE:
                    while board.is_valid(piece, dy=1):
                        piece.y += 1
                # [추가] M 키로 BGM 음소거 토글
                elif event.key == pygame.K_m:
                    if bgm_playing:
                        pygame.mixer.music.pause()
                        bgm_playing = False
                    else:
                        pygame.mixer.music.unpause()
                        bgm_playing = True

        if not game_over:
            fall_time += dt
            if fall_time >= fall_speed:
                fall_time = 0
                if board.is_valid(piece, dy=1):
                    piece.y += 1
                else:
                    board.lock(piece)
                    cleared = board.clear_lines()
                    if cleared > 0:
                        score += LINE_SCORES.get(cleared, 0)
                        total_lines += cleared
                    piece = next_piece
                    next_piece = Tetromino()
                    if not board.is_valid(piece):
                        game_over = True
                        pygame.mixer.music.stop()  # [추가] 게임 오버 시 BGM 정지

        board.draw(screen)
        if not game_over:
            draw_piece(screen, piece)

        pygame.draw.line(screen, LIGHT_GRAY, (BOARD_WIDTH, 0), (BOARD_WIDTH, SCREEN_HEIGHT), 1)
        draw_next_piece(screen, next_piece, font)
        draw_score(screen, score, total_lines, font, small_font)

        # [추가] BGM 상태 표시
        bgm_text = "BGM: ON  [M]" if bgm_playing else "BGM: OFF [M]"
        bgm_color = GREEN if bgm_playing else LIGHT_GRAY
        surface_bgm = font.render(bgm_text, True, bgm_color)
        screen.blit(surface_bgm, (BOARD_WIDTH + 5, SCREEN_HEIGHT - 30))

        if game_over:
            overlay = pygame.Surface((BOARD_WIDTH, 80), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, SCREEN_HEIGHT // 2 - 40))
            msg  = font.render("GAME OVER", True, WHITE)
            msg2 = small_font.render(f"Score: {score}", True, YELLOW)
            screen.blit(msg,  (BOARD_WIDTH // 2 - msg.get_width()  // 2, SCREEN_HEIGHT // 2 - 30))
            screen.blit(msg2, (BOARD_WIDTH // 2 - msg2.get_width() // 2, SCREEN_HEIGHT // 2 + 5))

        pygame.display.flip()

    pygame.mixer.music.stop()
    pygame.quit()


if __name__ == "__main__":
    main()
