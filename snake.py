import pygame
import random
import sys
from pygame.math import Vector2

pygame.init()
CELL_SIZE = 20
CELL_NUMBER = 25
SCREEN = pygame.display.set_mode((CELL_SIZE * CELL_NUMBER, CELL_SIZE * CELL_NUMBER))
CLOCK = pygame.time.Clock()
FONT = pygame.font.SysFont('arial', 36)

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
            pygame.draw.rect(SCREEN, (183, 111, 122), block_rect)

    def reset(self):
        self.__init__()

class FRUIT:
    def __init__(self):
        self.randomize()

    def randomize(self):
        self.pos = Vector2(random.randint(0, CELL_NUMBER - 1), random.randint(0, CELL_NUMBER - 1))

    def draw(self):
        fruit_rect = pygame.Rect(int(self.pos.x * CELL_SIZE), int(self.pos.y * CELL_SIZE), CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(SCREEN, (126, 166, 114), fruit_rect)

class MAIN:
    def __init__(self):
        self.snake = SNAKE()
        self.fruit = FRUIT()

    def update(self):
        self.snake.move()
        self.check_collision()
        self.check_fail()

    def draw_elements(self):
        self.draw_grass()
        self.fruit.draw()
        self.snake.draw()
        self.draw_score()

    def check_collision(self):
        if self.fruit.pos == self.snake.body[0]:
            self.fruit.randomize()
            self.snake.add_block()
            # make sure the new fruit doesn't spawn on the snake
            for block in self.snake.body:
                if block == self.fruit.pos:
                    self.fruit.randomize()

    def check_fail(self):
        # hit wall
        if not 0 <= self.snake.body[0].x < CELL_NUMBER or not 0 <= self.snake.body[0].y < CELL_NUMBER:
            self.game_over()
        # hit self
        for block in self.snake.body[1:]:
            if block == self.snake.body[0]:
                self.game_over()

    def game_over(self):
        self.snake.reset()

    def draw_grass(self):
        grass_color = (167, 209, 61)
        for row in range(CELL_NUMBER):
            if row % 2 == 0:
                for col in range(CELL_NUMBER):
                    if col % 2 == 0:
                        grass_rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                        pygame.draw.rect(SCREEN, grass_color, grass_rect)
            else:
                for col in range(CELL_NUMBER):
                    if col % 2 != 0:
                        grass_rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                        pygame.draw.rect(SCREEN, grass_color, grass_rect)

    def draw_score(self):
        score_text = str(len(self.snake.body) - 3)
        score_surface = FONT.render(score_text, True, (56, 74, 12))
        score_x = int(CELL_SIZE * CELL_NUMBER - 60)
        score_y = int(CELL_SIZE * CELL_NUMBER - 40)
        score_rect = score_surface.get_rect(center=(score_x, score_y))
        apple_rect = pygame.Rect(score_rect.left - 40, score_rect.top, CELL_SIZE, CELL_SIZE)
        SCREEN.blit(score_surface, score_rect)
        pygame.draw.rect(SCREEN, (126, 166, 114), apple_rect)

SCREEN_UPDATE = pygame.USEREVENT
pygame.time.set_timer(SCREEN_UPDATE, 150)

main = MAIN()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == SCREEN_UPDATE:
            main.update()
        if event.type == pygame.KEYDOWN:
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
    pygame.display.update()
    CLOCK.tick(60)

