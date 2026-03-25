import re
import sqlite3
import sys

import pygame


WINDOW_WIDTH = 700
WINDOW_HEIGHT = 760
FPS = 60

PLAY_TOP = 80
PLAY_BOTTOM = WINDOW_HEIGHT - 70

BG_TOP = (15, 20, 34)
BG_BOTTOM = (26, 36, 58)
TEXT_COLOR = (236, 242, 255)
MUTED_TEXT = (166, 179, 208)
BASE_COLOR = (91, 164, 255)
ACTIVE_COLOR = (255, 204, 110)
PERFECT_COLOR = (138, 243, 174)

BLOCK_HEIGHT = 26
START_BLOCK_WIDTH = 260
MIN_BLOCK_WIDTH = 36
START_SPEED = 4.2
SPEED_GROWTH = 0.15
PERFECT_TOLERANCE = 5
CAMERA_TOP_MARGIN = PLAY_TOP + 60
CAMERA_SMOOTHING = 0.18
PERFECT_FX_MS = 420

DB_FILE = "tower_scores.db"
CURRENT_PLAYER = ""


def init_db():
    with sqlite3.connect(DB_FILE) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS scores(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                score INTEGER NOT NULL,
                created DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        con.commit()


def insert_score(name, score):
    with sqlite3.connect(DB_FILE) as con:
        con.execute("INSERT INTO scores(name, score) VALUES (?,?)", (name, score))
        con.commit()


def fetch_top_scores(limit=5):
    with sqlite3.connect(DB_FILE) as con:
        rows = con.execute(
            "SELECT name, score FROM scores ORDER BY score DESC LIMIT ?", (limit,)
        ).fetchall()
    return rows


def ask_name_once(screen, title_font, ui_font):
    global CURRENT_PLAYER
    name = ""

    while True:
        screen.fill(BG_TOP)
        title = title_font.render("ENTER YOUR NAME", True, TEXT_COLOR)
        screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 130)))

        prompt = ui_font.render("Name (max 10 letters):", True, TEXT_COLOR)
        screen.blit(prompt, prompt.get_rect(center=(WINDOW_WIDTH // 2, 220)))

        box = pygame.Rect(0, 0, 320, 52)
        box.center = (WINDOW_WIDTH // 2, 292)
        pygame.draw.rect(screen, (38, 50, 82), box, border_radius=10)

        text = ui_font.render(name, True, TEXT_COLOR)
        screen.blit(text, text.get_rect(center=box.center))

        hint = ui_font.render("Press ENTER when done", True, MUTED_TEXT)
        screen.blit(hint, hint.get_rect(center=(WINDOW_WIDTH // 2, 370)))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif event.key == pygame.K_RETURN:
                    clean = re.sub(r"[^A-Za-z0-9]", "", name)[:10]
                    CURRENT_PLAYER = clean or "Player"
                    return
                elif len(name) < 10 and event.unicode.isalnum():
                    name += event.unicode


def game_over_screen(screen, final_score, title_font, ui_font, small_font):
    insert_score(CURRENT_PLAYER, final_score)
    top5 = fetch_top_scores()

    while True:
        screen.fill(BG_TOP)

        title = title_font.render("GAME OVER", True, TEXT_COLOR)
        screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 90)))

        score = ui_font.render(f"Score: {final_score}", True, TEXT_COLOR)
        screen.blit(score, score.get_rect(center=(WINDOW_WIDTH // 2, 150)))

        top = ui_font.render("TOP 5", True, TEXT_COLOR)
        screen.blit(top, top.get_rect(center=(WINDOW_WIDTH // 2, 210)))

        for idx, (player_name, points) in enumerate(top5):
            line = ui_font.render(f"{idx + 1}. {player_name} - {points}", True, TEXT_COLOR)
            screen.blit(line, line.get_rect(center=(WINDOW_WIDTH // 2, 260 + idx * 46)))

        hint = small_font.render("Press R to play again  |  Esc to quit", True, MUTED_TEXT)
        screen.blit(hint, hint.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 70)))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r:
                    return


init_db()


class TowerGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Tower")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 26)
        self.small_font = pygame.font.SysFont("consolas", 18)
        self.big_font = pygame.font.SysFont("consolas", 48, bold=True)
        self.reset_game()

    def reset_game(self):
        base_y = PLAY_BOTTOM - BLOCK_HEIGHT
        base_x = (WINDOW_WIDTH - START_BLOCK_WIDTH) // 2

        self.stack = [pygame.Rect(base_x, base_y, START_BLOCK_WIDTH, BLOCK_HEIGHT)]
        self.score = 0
        self.best_combo = 0
        self.combo = 0
        self.game_over = False
        self.camera_y = 0.0
        self.perfect_effects = []

        self.active_width = START_BLOCK_WIDTH
        self.active_block = pygame.Rect(0, base_y - BLOCK_HEIGHT, self.active_width, BLOCK_HEIGHT)
        self.active_block.centerx = WINDOW_WIDTH // 2
        self.active_direction = 1
        self.active_speed = START_SPEED
        self.active_color = ACTIVE_COLOR

    def next_active_block(self):
        target_y = self.stack[-1].y - BLOCK_HEIGHT
        self.active_block = pygame.Rect(0, target_y, self.active_width, BLOCK_HEIGHT)
        self.active_block.centerx = WINDOW_WIDTH // 2
        self.active_direction *= -1
        self.active_speed = min(11.0, START_SPEED + self.score * SPEED_GROWTH)
        self.active_color = ACTIVE_COLOR

    def trigger_perfect_effect(self, block):
        self.perfect_effects.append(
            {
                "x": block.centerx,
                "y": block.centery,
                "age": 0,
                "duration": PERFECT_FX_MS,
            }
        )

    def update_camera(self):
        tracked_top = min(self.active_block.y, self.stack[-1].y)
        target_camera = max(0.0, CAMERA_TOP_MARGIN - tracked_top)
        self.camera_y += (target_camera - self.camera_y) * CAMERA_SMOOTHING

    def world_to_screen_rect(self, rect):
        return pygame.Rect(rect.x, int(rect.y + self.camera_y), rect.width, rect.height)

    def move_active_block(self):
        self.active_block.x += int(self.active_speed) * self.active_direction

        if self.active_block.left <= 0:
            self.active_block.left = 0
            self.active_direction = 1
        elif self.active_block.right >= WINDOW_WIDTH:
            self.active_block.right = WINDOW_WIDTH
            self.active_direction = -1

    def place_block(self):
        previous = self.stack[-1]
        overlap_left = max(self.active_block.left, previous.left)
        overlap_right = min(self.active_block.right, previous.right)
        overlap_width = overlap_right - overlap_left

        if overlap_width <= 0:
            self.game_over = True
            return

        perfect = abs(self.active_block.centerx - previous.centerx) <= PERFECT_TOLERANCE
        if perfect:
            overlap_left = previous.left
            overlap_width = previous.width
            self.combo += 1
            self.best_combo = max(self.best_combo, self.combo)
            self.active_color = PERFECT_COLOR
            self.score += 2
        else:
            self.combo = 0
            self.score += 1

        self.active_width = overlap_width

        if self.active_width < MIN_BLOCK_WIDTH:
            self.game_over = True
            return

        placed = pygame.Rect(overlap_left, self.active_block.y, self.active_width, BLOCK_HEIGHT)
        self.stack.append(placed)
        if perfect:
            self.trigger_perfect_effect(placed)

        self.next_active_block()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r:
                    self.reset_game()
                if event.key == pygame.K_SPACE and not self.game_over:
                    self.place_block()

    def update(self, elapsed_ms):
        if self.game_over:
            return
        self.move_active_block()
        self.update_camera()

        alive_effects = []
        for effect in self.perfect_effects:
            effect["age"] += elapsed_ms
            if effect["age"] < effect["duration"]:
                alive_effects.append(effect)
        self.perfect_effects = alive_effects

    def draw_background(self):
        for y in range(WINDOW_HEIGHT):
            t = y / WINDOW_HEIGHT
            r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
            g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
            b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WINDOW_WIDTH, y))

        pygame.draw.rect(self.screen, (15, 19, 31), (0, 0, WINDOW_WIDTH, PLAY_TOP - 18))

    def draw_stack(self):
        depth = len(self.stack)
        for i, block in enumerate(self.stack):
            draw_block = self.world_to_screen_rect(block)
            if draw_block.bottom < PLAY_TOP or draw_block.top > WINDOW_HEIGHT:
                continue
            shade = int(70 + (150 * (i + 1) / max(1, depth)))
            color = (min(255, shade), min(255, shade + 35), 255)
            pygame.draw.rect(self.screen, color, draw_block, border_radius=5)
            pygame.draw.rect(self.screen, (24, 32, 56), draw_block, 1, border_radius=5)

        if not self.game_over:
            draw_active = self.world_to_screen_rect(self.active_block)
            pygame.draw.rect(self.screen, self.active_color, draw_active, border_radius=5)
            pygame.draw.rect(self.screen, (24, 32, 56), draw_active, 1, border_radius=5)

        for effect in self.perfect_effects:
            progress = effect["age"] / effect["duration"]
            radius = int(8 + progress * 45)
            alpha = max(0, int(220 * (1.0 - progress)))
            line_width = max(1, int(4 * (1.0 - progress)))
            fx_surface = pygame.Surface((radius * 2 + 6, radius * 2 + 6), pygame.SRCALPHA)
            pygame.draw.circle(
                fx_surface,
                (PERFECT_COLOR[0], PERFECT_COLOR[1], PERFECT_COLOR[2], alpha),
                (radius + 3, radius + 3),
                radius,
                line_width,
            )
            draw_x = effect["x"] - radius - 3
            draw_y = int(effect["y"] + self.camera_y) - radius - 3
            self.screen.blit(fx_surface, (draw_x, draw_y))

    def draw_hud(self):
        title = self.font.render("Tower", True, TEXT_COLOR)
        score = self.font.render(f"Score: {self.score}", True, TEXT_COLOR)
        combo = self.small_font.render(f"Best combo: {self.best_combo}", True, MUTED_TEXT)
        chain = self.small_font.render(f"Current combo: {self.combo}", True, MUTED_TEXT)
        hint = self.small_font.render("Space: Drop block   R: Restart   Esc: Quit", True, MUTED_TEXT)

        self.screen.blit(title, (18, 18))
        self.screen.blit(score, (WINDOW_WIDTH - 180, 18))
        self.screen.blit(combo, (18, 50))
        self.screen.blit(chain, (220, 50))
        self.screen.blit(hint, (18, WINDOW_HEIGHT - 34))

    def draw_game_over(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        title = self.big_font.render("Game Over", True, TEXT_COLOR)
        detail = self.font.render(f"Final score: {self.score}", True, TEXT_COLOR)
        hint = self.small_font.render("Press R for leaderboard", True, MUTED_TEXT)

        self.screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 45)))
        self.screen.blit(detail, detail.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 10)))
        self.screen.blit(hint, hint.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 52)))

    def draw(self):
        self.draw_background()
        self.draw_stack()
        self.draw_hud()
        if self.game_over:
            self.draw_game_over()
        pygame.display.flip()

    def run(self):
        ask_name_once(self.screen, self.big_font, self.font)
        while True:
            elapsed_ms = self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.key == pygame.K_r:
                        if self.game_over:
                            game_over_screen(
                                self.screen,
                                self.score,
                                self.big_font,
                                self.font,
                                self.small_font,
                            )
                        self.reset_game()
                    if event.key == pygame.K_SPACE and not self.game_over:
                        self.place_block()

            self.update(elapsed_ms)
            self.draw()


def main():
    game = TowerGame()
    game.run()


if __name__ == "__main__":
    main()
