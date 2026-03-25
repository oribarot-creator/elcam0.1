import random
import sys

import pygame


WINDOW_WIDTH = 900
WINDOW_HEIGHT = 650
FPS = 60

PADDLE_WIDTH = 120
PADDLE_HEIGHT = 16
PADDLE_SPEED = 8

BALL_RADIUS = 10
BALL_SPEED = 5
MAX_BOUNCE_X = 6

BRICK_ROWS = 6
BRICK_COLS = 10
BRICK_GAP = 6
BRICK_TOP = 90
BRICK_SIDE_MARGIN = 40
BRICK_HEIGHT = 28

LIVES_START = 3

BG_COLOR = (18, 24, 36)
PADDLE_COLOR = (220, 228, 245)
BALL_COLOR = (255, 214, 102)
TEXT_COLOR = (232, 238, 252)
MUTED_TEXT = (157, 170, 198)
OVERLAY_COLOR = (0, 0, 0, 145)

BRICK_COLORS = [
    (255, 107, 107),
    (255, 159, 67),
    (255, 230, 109),
    (123, 237, 159),
    (112, 161, 255),
    (203, 132, 255),
]


class BrickBreakerGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Brick Breaker")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 24)
        self.small_font = pygame.font.SysFont("consolas", 18)
        self.big_font = pygame.font.SysFont("consolas", 42, bold=True)
        self.reset_game()

    def reset_game(self):
        self.score = 0
        self.lives = LIVES_START
        self.win = False
        self.game_over = False
        self.bricks = self.create_bricks()
        self.reset_round()

    def reset_round(self):
        self.paddle = pygame.Rect(
            (WINDOW_WIDTH - PADDLE_WIDTH) // 2,
            WINDOW_HEIGHT - 48,
            PADDLE_WIDTH,
            PADDLE_HEIGHT,
        )
        self.ball_x = self.paddle.centerx
        self.ball_y = self.paddle.top - BALL_RADIUS - 2
        self.ball_dx = random.choice([-BALL_SPEED, BALL_SPEED])
        self.ball_dy = -BALL_SPEED
        self.launched = False

    def create_bricks(self):
        bricks = []
        total_gaps = (BRICK_COLS - 1) * BRICK_GAP
        usable_width = WINDOW_WIDTH - (BRICK_SIDE_MARGIN * 2) - total_gaps
        brick_width = usable_width // BRICK_COLS

        for row in range(BRICK_ROWS):
            for col in range(BRICK_COLS):
                x = BRICK_SIDE_MARGIN + col * (brick_width + BRICK_GAP)
                y = BRICK_TOP + row * (BRICK_HEIGHT + BRICK_GAP)
                rect = pygame.Rect(x, y, brick_width, BRICK_HEIGHT)
                color = BRICK_COLORS[row % len(BRICK_COLORS)]
                bricks.append((rect, color))
        return bricks

    def ball_rect(self):
        return pygame.Rect(
            int(self.ball_x - BALL_RADIUS),
            int(self.ball_y - BALL_RADIUS),
            BALL_RADIUS * 2,
            BALL_RADIUS * 2,
        )

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
                if event.key == pygame.K_SPACE:
                    if self.game_over or self.win:
                        self.reset_game()
                    elif not self.launched:
                        self.launched = True

    def move_paddle(self):
        keys = pygame.key.get_pressed()
        move_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        move_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]

        if move_left:
            self.paddle.x -= PADDLE_SPEED
        if move_right:
            self.paddle.x += PADDLE_SPEED

        self.paddle.x = max(0, min(self.paddle.x, WINDOW_WIDTH - self.paddle.width))

    def update_ball(self):
        if self.game_over or self.win:
            return

        if not self.launched:
            self.ball_x = self.paddle.centerx
            self.ball_y = self.paddle.top - BALL_RADIUS - 2
            return

        prev_rect = self.ball_rect()

        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy

        if self.ball_x - BALL_RADIUS <= 0:
            self.ball_x = BALL_RADIUS
            self.ball_dx *= -1
        elif self.ball_x + BALL_RADIUS >= WINDOW_WIDTH:
            self.ball_x = WINDOW_WIDTH - BALL_RADIUS
            self.ball_dx *= -1

        if self.ball_y - BALL_RADIUS <= 0:
            self.ball_y = BALL_RADIUS
            self.ball_dy *= -1

        if self.ball_y - BALL_RADIUS > WINDOW_HEIGHT:
            self.lives -= 1
            if self.lives <= 0:
                self.game_over = True
                self.launched = False
            else:
                self.reset_round()
            return

        current_ball_rect = self.ball_rect()

        if self.ball_dy > 0 and current_ball_rect.colliderect(self.paddle):
            self.ball_y = self.paddle.top - BALL_RADIUS
            self.ball_dy = -abs(self.ball_dy)

            offset = (self.ball_x - self.paddle.centerx) / (self.paddle.width / 2)
            self.ball_dx = max(-MAX_BOUNCE_X, min(MAX_BOUNCE_X, offset * MAX_BOUNCE_X))
            if abs(self.ball_dx) < 1:
                self.ball_dx = -1 if offset < 0 else 1

        for index, (brick_rect, brick_color) in enumerate(self.bricks):
            if not current_ball_rect.colliderect(brick_rect):
                continue

            del self.bricks[index]
            self.score += 10

            if prev_rect.bottom <= brick_rect.top or prev_rect.top >= brick_rect.bottom:
                self.ball_dy *= -1
            else:
                self.ball_dx *= -1

            break

        if not self.bricks:
            self.win = True
            self.launched = False

    def draw_hud(self):
        score_text = self.font.render(f"Score: {self.score}", True, TEXT_COLOR)
        lives_text = self.font.render(f"Lives: {self.lives}", True, TEXT_COLOR)
        controls_text = self.small_font.render(
            "Controls: Left/Right (or A/D), Space launch, R reset, Esc quit",
            True,
            MUTED_TEXT,
        )

        self.screen.blit(score_text, (20, 18))
        self.screen.blit(lives_text, (WINDOW_WIDTH - 170, 18))
        self.screen.blit(controls_text, (20, WINDOW_HEIGHT - 30))

    def draw_bricks(self):
        for brick_rect, brick_color in self.bricks:
            pygame.draw.rect(self.screen, brick_color, brick_rect, border_radius=5)
            pygame.draw.rect(self.screen, (20, 25, 35), brick_rect, width=2, border_radius=5)

    def draw_overlay(self, title, subtitle):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill(OVERLAY_COLOR)
        self.screen.blit(overlay, (0, 0))

        title_surf = self.big_font.render(title, True, TEXT_COLOR)
        subtitle_surf = self.font.render(subtitle, True, TEXT_COLOR)

        self.screen.blit(
            title_surf,
            title_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20)),
        )
        self.screen.blit(
            subtitle_surf,
            subtitle_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 35)),
        )

    def draw(self):
        self.screen.fill(BG_COLOR)

        self.draw_bricks()
        pygame.draw.rect(self.screen, PADDLE_COLOR, self.paddle, border_radius=8)
        pygame.draw.circle(self.screen, BALL_COLOR, (int(self.ball_x), int(self.ball_y)), BALL_RADIUS)

        self.draw_hud()

        if not self.launched and not self.game_over and not self.win:
            launch_hint = self.font.render("Press SPACE to launch", True, TEXT_COLOR)
            self.screen.blit(
                launch_hint,
                launch_hint.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 130)),
            )

        if self.game_over:
            self.draw_overlay("Game Over", "Press SPACE or R to restart")
        elif self.win:
            self.draw_overlay("You Win!", "Press SPACE or R to play again")

        pygame.display.flip()

    def run(self):
        while True:
            self.clock.tick(FPS)
            self.handle_events()
            self.move_paddle()
            self.update_ball()
            self.draw()


def main():
    game = BrickBreakerGame()
    game.run()


if __name__ == "__main__":
    main()
