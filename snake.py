
import pygame
import random
import sys
from pygame.math import Vector2

pygame.init()
CELL_SIZE = 20
CELL_NUMBER = 25
SCREEN = pygame.display.set_mode((CELL_SIZE * CELL_NUMBER, CELL_SIZE * CELL_NUMBER))
CLOCK = pygame.time.Clock()
FONT_BIG = pygame.font.SysFont('arial', 44)
FONT_MED = pygame.font.SysFont('arial', 28)

# ----------------------------- GAME CLASSES -----------------------------
class SNAKE:
    def __init__(self):
        self.body = [Vector2(5, 10), Vector2(4, 10), Vector2(3, 10)]
        self.direction = Vector2(1, 0)
        self.grow = False

    def move(self):
        if self.grow:
            body_copy = self.body[:]
            body_copy.insert(0, body_copy[0] + self.direction)
            self.body = body_copy
            self.grow = False
        else:
            body_copy = self.body[:-1]
            body_copy.insert(0, body_copy[0] + self.direction)
            self.body = body_copy

    def add_block(self):
        self.grow = True

    def draw(self):
        for block in self.body:
            x_pos = int(block.x * CELL_SIZE)
            y_pos = int(block.y * CELL_SIZE)
            block_rect = pygame.Rect(x_pos, y_pos, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(SCREEN, (0, 120, 0), block_rect)

    def reset(self):
        self.__init__()

class FRUIT:
    def __init__(self):
        self.randomize()

    def randomize(self):
        self.pos = Vector2(random.randint(0, CELL_NUMBER - 1),
                          random.randint(0, CELL_NUMBER - 1))

    def draw(self):
        fruit_rect = pygame.Rect(int(self.pos.x * CELL_SIZE),
                                 int(self.pos.y * CELL_SIZE),
                                 CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(SCREEN, (200, 0, 0), fruit_rect)

class POISON_FRUIT:
    def __init__(self):
        self.pos = Vector2(-1, -1)  # off-screen
        self.active = False

    def randomize(self, snake_body):
        while True:
            pos = Vector2(random.randint(0, CELL_NUMBER - 1),
                         random.randint(0, CELL_NUMBER - 1))
            if pos not in snake_body:
                self.pos = pos
                self.active = True
                return

    def draw(self):
        if self.active:
            rect = pygame.Rect(int(self.pos.x * CELL_SIZE),
                              int(self.pos.y * CELL_SIZE),
                              CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(SCREEN, (58, 3, 66), rect)

class MAIN:
    def __init__(self, apple_count, hard_mode):
        self.apple_count = apple_count
        self.hard_mode = hard_mode
        self.snake = SNAKE()
        self.fruits = [FRUIT() for _ in range(self.apple_count)]
        self.poison = POISON_FRUIT()
        self.game_over_flag = False

    def update(self):
        if self.game_over_flag:
            return
        self.snake.move()
        self.check_collision()
        self.check_fail()

    def draw_elements(self):
        self.draw_grass()
        for f in self.fruits:
            f.draw()
        if self.hard_mode:
            self.poison.draw()
        self.snake.draw()
        self.draw_score()

    def check_collision(self):
        head = self.snake.body[0]
        # normal apples
        for f in self.fruits:
            if f.pos == head:
                self.snake.add_block()
                f.randomize()
                while f.pos in self.snake.body:
                    f.randomize()
                # hard mode: chance to spawn poison
                if self.hard_mode and random.random() < 0.30:
                    self.poison.randomize(self.snake.body)
        # poison apple
        if self.hard_mode and self.poison.active and self.poison.pos == head:
            self.game_over_flag = True

    def check_fail(self):
        head = self.snake.body[0]
        # wall
        if not 0 <= head.x < CELL_NUMBER or not 0 <= head.y < CELL_NUMBER:
            self.game_over()
        # self bite
        for block in self.snake.body[1:]:
            if block == head:
                self.game_over()

    def game_over(self):
        self.game_over_flag = True

    def draw_grass(self):
        grass_color = (167, 209, 61)
        for row in range(CELL_NUMBER):
            if row % 2 == 0:
                for col in range(CELL_NUMBER):
                    if col % 2 == 0:
                        grass_rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE,
                                                CELL_SIZE, CELL_SIZE)
                        pygame.draw.rect(SCREEN, grass_color, grass_rect)
            else:
                for col in range(CELL_NUMBER):
                    if col % 2 != 0:
                        grass_rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE,
                                                CELL_SIZE, CELL_SIZE)
                        pygame.draw.rect(SCREEN, grass_color, grass_rect)

    def draw_score(self):
        score_text = str(len(self.snake.body) - 3)
        score_surface = FONT_MED.render(score_text, True, (56, 74, 12))
        score_x = int(CELL_SIZE * CELL_NUMBER - 60)
        score_y = int(CELL_SIZE * CELL_NUMBER - 40)
        score_rect = score_surface.get_rect(center=(score_x, score_y))
        SCREEN.blit(score_surface, score_rect)

# ----------------------------- MENU -----------------------------
class Menu:
    def __init__(self):
        self.apple_options = [1, 3, 5, 7]
        self.apple_idx = 1  # default 3 apples
        self.mode_options = ['NORMAL', 'HARD']
        self.mode_idx = 0
        self.selector = 0  # 0 = apples, 1 = mode
        self.start = False

    def run(self):
        while not self.start:
            self.handle_events()
            self.draw()
            CLOCK.tick(130)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    if self.selector == 0:
                        self.apple_idx = (self.apple_idx - 1) % len(self.apple_options)
                    else:
                        self.mode_idx = (self.mode_idx - 1) % len(self.mode_options)
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    if self.selector == 0:
                        self.apple_idx = (self.apple_idx + 1) % len(self.apple_options)
                    else:
                        self.mode_idx = (self.mode_idx + 1) % len(self.mode_options)
                if event.key == pygame.K_DOWN:
                    self.selector = 1
                if event.key == pygame.K_UP:
                    self.selector = 0
                if event.key == pygame.K_SPACE:
                    self.start = True

    def draw(self):
        SCREEN.fill((175, 215, 70))
        title = FONT_BIG.render("SNAKE GAME", True, (56, 74, 12))
        title_rect = title.get_rect(center=(SCREEN.get_width() // 2, 80))
        SCREEN.blit(title, title_rect)

        # Apples selector
        apples_label = FONT_MED.render("Apples:", True, (56, 74, 12))
        SCREEN.blit(apples_label, (120, 180))
        gap = 60
        for idx, num in enumerate(self.apple_options):
            color = (56, 74, 12) if idx != self.apple_idx else (255, 255, 255)
            if self.selector == 0 and idx == self.apple_idx:
                color = (255, 215, 0)
            txt = FONT_MED.render(str(num), True, color)
            SCREEN.blit(txt, (120 + idx * gap, 220))

        # Mode selector
        mode_label = FONT_MED.render("Mode:", True, (56, 74, 12))
        SCREEN.blit(mode_label, (120, 280))
        for idx, mode in enumerate(self.mode_options):
            color = (56, 74, 12) if idx != self.mode_idx else (255, 255, 255)
            if self.selector == 1 and idx == self.mode_idx:
                color = (255, 215, 0)
            txt = FONT_MED.render(mode, True, color)
            SCREEN.blit(txt, (120 + idx * 140, 320))

        # Start hint
        hint = FONT_MED.render("Press SPACE to start", True, (56, 74, 12))
        hint_rect = hint.get_rect(center=(SCREEN.get_width() // 2, 400))
        SCREEN.blit(hint, hint_rect)

        pygame.display.update()

# ----------------------------- MAIN FLOW -----------------------------
def main_game(apple_count, hard_mode):
    main = MAIN(apple_count, hard_mode)
    SCREEN_UPDATE = pygame.USEREVENT
    pygame.time.set_timer(SCREEN_UPDATE, 150)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == SCREEN_UPDATE:
                main.update()
            if event.type == pygame.KEYDOWN:
                if main.game_over_flag and event.key == pygame.K_r:
                    return  # back to menu
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                # direction controls
                if event.key == pygame.K_UP and main.snake.direction.y != 1:
                    main.snake.direction = Vector2(0, -1)
                if event.key == pygame.K_DOWN and main.snake.direction.y != -1:
                    main.snake.direction = Vector2(0, 1)
                if event.key == pygame.K_LEFT and main.snake.direction.x != 1:
                    main.snake.direction = Vector2(-1, 0)
                if event.key == pygame.K_RIGHT and main.snake.direction.x != -1:
                    main.snake.direction = Vector2(1, 0)

        SCREEN.fill((175, 215, 70))
        main.draw_elements()
        if main.game_over_flag:
            msg = FONT_BIG.render("GAME OVER", True, (200, 0, 0))
            msg_rect = msg.get_rect(center=(SCREEN.get_width() // 2,
                                            SCREEN.get_height() // 2 - 30))
            SCREEN.blit(msg, msg_rect)
            retry = FONT_MED.render("Press R for menu", True, (200, 0, 0))
            retry_rect = retry.get_rect(center=(SCREEN.get_width() // 2,
                                               SCREEN.get_height() // 2 + 20))
            SCREEN.blit(retry, retry_rect)
        pygame.display.update()
        CLOCK.tick(100)

# ----------------------------- LOOP -----------------------------
while True:
    menu = Menu()
    menu.run()
    apples = menu.apple_options[menu.apple_idx]
    hard = menu.mode_options[menu.mode_idx] == 'HARD'
    main_game(apples, hard)