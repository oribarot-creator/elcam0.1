import random
import sys

import pygame


WINDOW_WIDTH = 960
WINDOW_HEIGHT = 700
FPS = 60
MAX_LEVEL = 20

PLAYER_WIDTH = 64
PLAYER_HEIGHT = 20
PLAYER_SPEED = 7
PLAYER_COOLDOWN_MS = 220

PLAYER_BULLET_WIDTH = 5
PLAYER_BULLET_HEIGHT = 14
PLAYER_BULLET_SPEED = 10

ENEMY_WIDTH = 42
ENEMY_HEIGHT = 26
ENEMY_SPACING_X = 18
ENEMY_SPACING_Y = 16
ENEMY_START_Y = 90

ENEMY_BULLET_WIDTH = 5
ENEMY_BULLET_HEIGHT = 14
ENEMY_BULLET_SPEED_BASE = 4
ENEMY_BULLET_COOLDOWN_MS_BASE = 900

START_LIVES = 3
LEVEL_TRANSITION_MS = 1300

BG_COLOR = (10, 13, 24)
PANEL_COLOR = (21, 29, 47)
PANEL_BORDER_COLOR = (63, 78, 111)
PLAYER_COLOR = (130, 245, 175)
PLAYER_BULLET_COLOR = (255, 244, 188)
ENEMY_BULLET_COLOR = (255, 140, 140)
TEXT_COLOR = (231, 236, 247)
MUTED_TEXT_COLOR = (154, 166, 190)

BUNKER_COUNT = 4
BUNKER_BLOCK_SIZE = 10
BUNKER_TOP = WINDOW_HEIGHT - 190
BUNKER_HP_MAX = 3
BUNKER_COLORS = {
    3: (138, 232, 171),
    2: (97, 193, 130),
    1: (72, 132, 96),
}

ENEMY_COLORS = [
    (255, 105, 130),
    (255, 165, 90),
    (255, 220, 110),
    (120, 210, 255),
    (190, 145, 255),
    (115, 235, 175),
]

ALIEN_SPRITES = {
    0: [
        [
            "0011001100",
            "0111111110",
            "1110110111",
            "1111111111",
            "1011111101",
            "0011001100",
            "0110011001",
        ],
        [
            "0011001100",
            "0111111110",
            "1110110111",
            "1111111111",
            "0011111100",
            "0110011001",
            "1000000001",
        ],
    ],
    1: [
        [
            "0001111000",
            "0011111100",
            "0110110110",
            "1111111111",
            "1101111011",
            "0011001100",
            "0110011001",
        ],
        [
            "0001111000",
            "0011111100",
            "0110110110",
            "1111111111",
            "0011111100",
            "0110011001",
            "1000000001",
        ],
    ],
    2: [
        [
            "0011111100",
            "0111111110",
            "1111011111",
            "1111111111",
            "0110110110",
            "0011001100",
            "0100000010",
        ],
        [
            "0011111100",
            "0111111110",
            "1111011111",
            "1111111111",
            "0011111100",
            "0101101010",
            "1000000001",
        ],
    ],
}


class SpaceInvadersGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Space Invaders - 20 Levels")
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("consolas", 24)
        self.small_font = pygame.font.SysFont("consolas", 18)
        self.big_font = pygame.font.SysFont("consolas", 42, bold=True)

        self.player = pygame.Rect(
            (WINDOW_WIDTH - PLAYER_WIDTH) // 2,
            WINDOW_HEIGHT - 70,
            PLAYER_WIDTH,
            PLAYER_HEIGHT,
        )

        self.level = 1
        self.score = 0
        self.lives = START_LIVES

        self.player_bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.bunker_blocks = []

        self.enemy_direction = 1
        self.enemy_speed = 1.0
        self.enemy_drop = 16
        self.enemy_shot_cooldown_ms = ENEMY_BULLET_COOLDOWN_MS_BASE
        self.enemy_shot_timer = 0

        self.last_player_shot_ms = 0
        self.level_clear_timer = 0

        self.game_started = False
        self.game_over = False
        self.victory = False

        self.stars = [
            {
                "x": random.randint(0, WINDOW_WIDTH - 1),
                "y": random.randint(56, WINDOW_HEIGHT - 1),
                "r": random.choice([1, 1, 1, 2]),
                "c": random.choice([(90, 105, 150), (120, 140, 185), (170, 190, 230)]),
            }
            for _ in range(90)
        ]

        self.setup_level(self.level)

    def create_bunkers(self):
        self.bunker_blocks = []
        bunker_shape = [
            "1111111111",
            "1111111111",
            "1111111111",
            "1110111011",
            "1100010001",
            "1000000000",
        ]

        shape_cols = len(bunker_shape[0])
        bunker_width = shape_cols * BUNKER_BLOCK_SIZE
        gap = (WINDOW_WIDTH - (BUNKER_COUNT * bunker_width)) // (BUNKER_COUNT + 1)

        for bunker_idx in range(BUNKER_COUNT):
            start_x = gap + bunker_idx * (bunker_width + gap)
            for row, row_mask in enumerate(bunker_shape):
                for col, cell in enumerate(row_mask):
                    if cell == "1":
                        rect = pygame.Rect(
                            start_x + col * BUNKER_BLOCK_SIZE,
                            BUNKER_TOP + row * BUNKER_BLOCK_SIZE,
                            BUNKER_BLOCK_SIZE,
                            BUNKER_BLOCK_SIZE,
                        )
                        self.bunker_blocks.append({"rect": rect, "hp": BUNKER_HP_MAX})

    def setup_level(self, level):
        self.enemies = []
        self.player_bullets = []
        self.enemy_bullets = []
        self.create_bunkers()

        rows = min(3 + (level - 1) // 2, 6)
        cols = min(7 + (level - 1) // 3, 12)

        total_width = cols * ENEMY_WIDTH + (cols - 1) * ENEMY_SPACING_X
        start_x = (WINDOW_WIDTH - total_width) // 2

        for row in range(rows):
            for col in range(cols):
                x = start_x + col * (ENEMY_WIDTH + ENEMY_SPACING_X)
                y = ENEMY_START_Y + row * (ENEMY_HEIGHT + ENEMY_SPACING_Y)
                color = ENEMY_COLORS[row % len(ENEMY_COLORS)]
                enemy = {
                    "rect": pygame.Rect(x, y, ENEMY_WIDTH, ENEMY_HEIGHT),
                    "color": color,
                    "points": (rows - row) * 10,
                    "sprite_type": row % len(ALIEN_SPRITES),
                }
                self.enemies.append(enemy)

        self.enemy_direction = 1
        self.enemy_speed = min(1.0 + (level - 1) * 0.22, 5.0)
        self.enemy_drop = min(16 + (level - 1), 30)
        self.enemy_shot_cooldown_ms = max(
            220,
            ENEMY_BULLET_COOLDOWN_MS_BASE - (level - 1) * 30,
        )
        self.enemy_shot_timer = 0

        self.player.centerx = WINDOW_WIDTH // 2

    def shoot_player_bullet(self):
        now = pygame.time.get_ticks()
        if now - self.last_player_shot_ms < PLAYER_COOLDOWN_MS:
            return

        bullet = pygame.Rect(
            self.player.centerx - PLAYER_BULLET_WIDTH // 2,
            self.player.top - PLAYER_BULLET_HEIGHT,
            PLAYER_BULLET_WIDTH,
            PLAYER_BULLET_HEIGHT,
        )
        self.player_bullets.append(bullet)
        self.last_player_shot_ms = now

    def shoot_enemy_bullet(self):
        if not self.enemies:
            return

        # Pick among lower enemies per column to make shots feel fairer.
        columns = {}
        for enemy in self.enemies:
            col_key = enemy["rect"].centerx // 12
            existing = columns.get(col_key)
            if existing is None or enemy["rect"].bottom > existing["rect"].bottom:
                columns[col_key] = enemy

        shooters = list(columns.values())
        shooter = random.choice(shooters)
        bullet = pygame.Rect(
            shooter["rect"].centerx - ENEMY_BULLET_WIDTH // 2,
            shooter["rect"].bottom + 4,
            ENEMY_BULLET_WIDTH,
            ENEMY_BULLET_HEIGHT,
        )
        self.enemy_bullets.append(bullet)

    def reset_player_position(self):
        self.player.centerx = WINDOW_WIDTH // 2
        self.player_bullets.clear()
        self.enemy_bullets.clear()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_SPACE:
                    if self.game_over or self.victory:
                        self.restart_game()
                    elif not self.game_started:
                        self.game_started = True
                    else:
                        self.shoot_player_bullet()
                if event.key == pygame.K_r:
                    self.restart_game()

    def restart_game(self):
        self.level = 1
        self.score = 0
        self.lives = START_LIVES
        self.game_started = True
        self.game_over = False
        self.victory = False
        self.level_clear_timer = 0
        self.setup_level(self.level)

    def update_player(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.x += PLAYER_SPEED

        self.player.x = max(0, min(self.player.x, WINDOW_WIDTH - PLAYER_WIDTH))

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.shoot_player_bullet()

    def update_bullets(self):
        for bullet in self.player_bullets:
            bullet.y -= PLAYER_BULLET_SPEED
        self.player_bullets = [b for b in self.player_bullets if b.bottom > 0]

        enemy_bullet_speed = min(
            ENEMY_BULLET_SPEED_BASE + (self.level - 1) * 0.18,
            8.0,
        )
        for bullet in self.enemy_bullets:
            bullet.y += enemy_bullet_speed
        self.enemy_bullets = [b for b in self.enemy_bullets if b.top < WINDOW_HEIGHT]

    def update_enemies(self, elapsed_ms):
        if not self.enemies:
            return

        shift_x = self.enemy_direction * self.enemy_speed
        hit_edge = False

        for enemy in self.enemies:
            enemy["rect"].x += shift_x
            if enemy["rect"].left <= 10 or enemy["rect"].right >= WINDOW_WIDTH - 10:
                hit_edge = True

        if hit_edge:
            self.enemy_direction *= -1
            for enemy in self.enemies:
                enemy["rect"].y += self.enemy_drop

        for enemy in self.enemies:
            if enemy["rect"].bottom >= self.player.top:
                self.game_over = True
                return

        if self.bunker_blocks:
            remaining_blocks = []
            for block in self.bunker_blocks:
                collided = False
                for enemy in self.enemies:
                    if enemy["rect"].colliderect(block["rect"]):
                        collided = True
                        break
                if not collided:
                    remaining_blocks.append(block)
            self.bunker_blocks = remaining_blocks

        self.enemy_shot_timer += elapsed_ms
        if self.enemy_shot_timer >= self.enemy_shot_cooldown_ms:
            self.enemy_shot_timer = 0
            self.shoot_enemy_bullet()

    def handle_collisions(self):
        removed_bullets = []
        removed_enemies = []

        for bullet in self.player_bullets:
            for enemy in self.enemies:
                if bullet.colliderect(enemy["rect"]):
                    removed_bullets.append(bullet)
                    removed_enemies.append(enemy)
                    self.score += enemy["points"]
                    break

        if removed_bullets:
            self.player_bullets = [b for b in self.player_bullets if b not in removed_bullets]
        if removed_enemies:
            self.enemies = [e for e in self.enemies if e not in removed_enemies]

        # Player bullets damage bunkers before reaching enemies behind them.
        if self.player_bullets and self.bunker_blocks:
            still_flying = []
            for bullet in self.player_bullets:
                hit_bunker = False
                for block in self.bunker_blocks:
                    if bullet.colliderect(block["rect"]):
                        block["hp"] -= 1
                        hit_bunker = True
                        break
                if not hit_bunker:
                    still_flying.append(bullet)
            self.player_bullets = still_flying
            self.bunker_blocks = [b for b in self.bunker_blocks if b["hp"] > 0]

        # Enemy bullets also chip away bunker blocks over multiple hits.
        if self.enemy_bullets and self.bunker_blocks:
            still_falling = []
            for bullet in self.enemy_bullets:
                hit_bunker = False
                for block in self.bunker_blocks:
                    if bullet.colliderect(block["rect"]):
                        block["hp"] -= 1
                        hit_bunker = True
                        break
                if not hit_bunker:
                    still_falling.append(bullet)
            self.enemy_bullets = still_falling
            self.bunker_blocks = [b for b in self.bunker_blocks if b["hp"] > 0]

        hit_player = False
        for bullet in self.enemy_bullets:
            if bullet.colliderect(self.player):
                hit_player = True
                break

        if hit_player:
            self.lives -= 1
            if self.lives <= 0:
                self.game_over = True
            else:
                self.reset_player_position()
            return

        if not self.enemies and not self.victory and not self.game_over:
            if self.level >= MAX_LEVEL:
                self.victory = True
                return
            self.level_clear_timer = LEVEL_TRANSITION_MS

    def update_level_transition(self, elapsed_ms):
        if self.level_clear_timer <= 0:
            return

        self.level_clear_timer -= elapsed_ms
        if self.level_clear_timer <= 0:
            self.level += 1
            self.setup_level(self.level)

    def update(self, elapsed_ms):
        # Keep movement responsive even before pressing start.
        self.update_player()

        if not self.game_started or self.game_over or self.victory:
            return

        self.update_level_transition(elapsed_ms)
        if self.level_clear_timer > 0:
            return

        self.update_bullets()
        self.update_enemies(elapsed_ms)
        self.handle_collisions()

    def draw_background(self):
        top = (8, 11, 22)
        bottom = (18, 24, 46)
        for y in range(WINDOW_HEIGHT):
            blend = y / WINDOW_HEIGHT
            r = int(top[0] + (bottom[0] - top[0]) * blend)
            g = int(top[1] + (bottom[1] - top[1]) * blend)
            b = int(top[2] + (bottom[2] - top[2]) * blend)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WINDOW_WIDTH, y))

        for star in self.stars:
            pygame.draw.circle(self.screen, star["c"], (star["x"], star["y"]), star["r"])

    def draw_hud(self):
        hud_rect = pygame.Rect(0, 0, WINDOW_WIDTH, 56)
        pygame.draw.rect(self.screen, PANEL_COLOR, hud_rect)
        pygame.draw.line(self.screen, PANEL_BORDER_COLOR, (0, 55), (WINDOW_WIDTH, 55), 2)

        score_text = self.font.render(f"Score: {self.score}", True, TEXT_COLOR)
        lives_text = self.font.render(f"Lives: {self.lives}", True, TEXT_COLOR)
        level_text = self.font.render(f"Level: {self.level}/{MAX_LEVEL}", True, TEXT_COLOR)

        self.screen.blit(score_text, (18, 15))
        self.screen.blit(level_text, (WINDOW_WIDTH // 2 - 84, 15))
        self.screen.blit(lives_text, (WINDOW_WIDTH - 150, 15))

    def draw_entities(self):
        # Player ship body + canopy + wing accents.
        pygame.draw.rect(self.screen, PLAYER_COLOR, self.player, border_radius=6)
        canopy = pygame.Rect(self.player.x + 18, self.player.y - 8, self.player.width - 36, 8)
        pygame.draw.rect(self.screen, (183, 255, 213), canopy, border_radius=4)
        pygame.draw.rect(self.screen, (71, 140, 100), self.player, 2, border_radius=6)

        if self.bunker_blocks:
            for block in self.bunker_blocks:
                color = BUNKER_COLORS.get(block["hp"], BUNKER_COLORS[1])
                pygame.draw.rect(self.screen, color, block["rect"])
                pygame.draw.rect(self.screen, BG_COLOR, block["rect"], 1)

        for bullet in self.player_bullets:
            pygame.draw.rect(self.screen, PLAYER_BULLET_COLOR, bullet, border_radius=3)
        for bullet in self.enemy_bullets:
            pygame.draw.rect(self.screen, ENEMY_BULLET_COLOR, bullet, border_radius=3)

        for enemy in self.enemies:
            self.draw_alien(enemy)

    def draw_alien(self, enemy):
        body = enemy["rect"]
        sprite_type = enemy.get("sprite_type", 0)
        frame_index = (pygame.time.get_ticks() // 260) % 2
        sprite = ALIEN_SPRITES[sprite_type][frame_index]

        rows = len(sprite)
        cols = len(sprite[0])
        pixel_size = max(2, min(body.width // cols, body.height // rows))

        sprite_width = cols * pixel_size
        sprite_height = rows * pixel_size
        start_x = body.x + (body.width - sprite_width) // 2
        start_y = body.y + (body.height - sprite_height) // 2

        shade = tuple(max(0, c - 55) for c in enemy["color"])
        for row_idx, row_bits in enumerate(sprite):
            for col_idx, bit in enumerate(row_bits):
                if bit != "1":
                    continue
                px = start_x + col_idx * pixel_size
                py = start_y + row_idx * pixel_size
                pixel_rect = pygame.Rect(px, py, pixel_size, pixel_size)
                pygame.draw.rect(self.screen, enemy["color"], pixel_rect)

                # Add subtle lower-right shading for depth without losing retro style.
                if pixel_size >= 3:
                    shade_rect = pygame.Rect(
                        px + pixel_size - 2,
                        py + pixel_size - 2,
                        2,
                        2,
                    )
                    pygame.draw.rect(self.screen, shade, shade_rect)

    def draw_center_message(self, title, subtitle):
        title_surface = self.big_font.render(title, True, TEXT_COLOR)
        subtitle_surface = self.font.render(subtitle, True, MUTED_TEXT_COLOR)
        self.screen.blit(
            title_surface,
            title_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20)),
        )
        self.screen.blit(
            subtitle_surface,
            subtitle_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 34)),
        )

    def draw(self):
        self.draw_background()
        self.draw_hud()
        self.draw_entities()

        if not self.game_started:
            self.draw_center_message(
                "SPACE INVADERS",
                "Press SPACE to start | Arrows to move | SPACE/UP to shoot",
            )

        if self.level_clear_timer > 0:
            self.draw_center_message(
                f"Level {self.level} Clear!",
                f"Preparing Level {self.level + 1}",
            )

        if self.game_over:
            self.draw_center_message(
                "Game Over",
                "Press SPACE or R to restart | ESC to quit",
            )

        if self.victory:
            self.draw_center_message(
                "Victory!",
                "You completed all 20 levels. Press SPACE or R to play again",
            )

        footer = self.small_font.render(
            "Controls: Left/Right move, Space/Up shoot, R restart, ESC quit",
            True,
            MUTED_TEXT_COLOR,
        )
        self.screen.blit(footer, (18, WINDOW_HEIGHT - 28))

        pygame.display.flip()

    def run(self):
        while True:
            elapsed_ms = self.clock.tick(FPS)
            self.handle_events()
            self.update(elapsed_ms)
            self.draw()


def main():
    game = SpaceInvadersGame()
    game.run()


if __name__ == "__main__":
    main()
