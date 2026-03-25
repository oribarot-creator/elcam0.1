import random
import re
import sqlite3
import sys

import pygame


BOARD_WIDTH = 10
BOARD_HEIGHT = 20
CELL_SIZE = 30
SIDEBAR_WIDTH = 220
WINDOW_WIDTH = BOARD_WIDTH * CELL_SIZE + SIDEBAR_WIDTH
WINDOW_HEIGHT = BOARD_HEIGHT * CELL_SIZE
FPS = 60

BG_COLOR = (18, 23, 31)
GRID_COLOR = (40, 46, 58)
PANEL_COLOR = (27, 33, 45)
TEXT_COLOR = (231, 236, 245)
MUTED_TEXT_COLOR = (157, 167, 184)
GHOST_COLOR = (110, 120, 140)

PIECE_COLORS = {
	"I": (70, 220, 235),
	"O": (240, 210, 75),
	"T": (190, 95, 220),
	"S": (95, 210, 120),
	"Z": (230, 95, 95),
	"J": (80, 125, 220),
	"L": (230, 155, 70),
}

# Rotations are defined as (x, y) offsets from a piece origin.
SHAPES = {
	"I": [
		[(0, 1), (1, 1), (2, 1), (3, 1)],
		[(2, 0), (2, 1), (2, 2), (2, 3)],
		[(0, 2), (1, 2), (2, 2), (3, 2)],
		[(1, 0), (1, 1), (1, 2), (1, 3)],
	],
	"O": [
		[(1, 0), (2, 0), (1, 1), (2, 1)],
		[(1, 0), (2, 0), (1, 1), (2, 1)],
		[(1, 0), (2, 0), (1, 1), (2, 1)],
		[(1, 0), (2, 0), (1, 1), (2, 1)],
	],
	"T": [
		[(1, 0), (0, 1), (1, 1), (2, 1)],
		[(1, 0), (1, 1), (2, 1), (1, 2)],
		[(0, 1), (1, 1), (2, 1), (1, 2)],
		[(1, 0), (0, 1), (1, 1), (1, 2)],
	],
	"S": [
		[(1, 0), (2, 0), (0, 1), (1, 1)],
		[(1, 0), (1, 1), (2, 1), (2, 2)],
		[(1, 1), (2, 1), (0, 2), (1, 2)],
		[(0, 0), (0, 1), (1, 1), (1, 2)],
	],
	"Z": [
		[(0, 0), (1, 0), (1, 1), (2, 1)],
		[(2, 0), (1, 1), (2, 1), (1, 2)],
		[(0, 1), (1, 1), (1, 2), (2, 2)],
		[(1, 0), (0, 1), (1, 1), (0, 2)],
	],
	"J": [
		[(0, 0), (0, 1), (1, 1), (2, 1)],
		[(1, 0), (2, 0), (1, 1), (1, 2)],
		[(0, 1), (1, 1), (2, 1), (2, 2)],
		[(1, 0), (1, 1), (0, 2), (1, 2)],
	],
	"L": [
		[(2, 0), (0, 1), (1, 1), (2, 1)],
		[(1, 0), (1, 1), (1, 2), (2, 2)],
		[(0, 1), (1, 1), (2, 1), (0, 2)],
		[(0, 0), (1, 0), (1, 1), (1, 2)],
	],
}

SCORE_TABLE = {1: 100, 2: 300, 3: 500, 4: 800}

DB_FILE = "tetris_scores.db"
CURRENT_PLAYER = ""


def init_db():
	"""Create the DB and table if they don't exist yet."""
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
		con.execute(
			"INSERT INTO scores(name, score) VALUES (?,?)",
			(name, score),
		)
		con.commit()


def fetch_top_scores(limit=5):
	with sqlite3.connect(DB_FILE) as con:
		rows = con.execute(
			"SELECT name, score FROM scores ORDER BY score DESC LIMIT ?", (limit,)
		).fetchall()
	return rows


def ask_name_once(screen, title_font, ui_font):
	"""Ask for the player name once when the game starts."""
	global CURRENT_PLAYER
	name = ""
	while True:
		screen.fill(BG_COLOR)
		title = title_font.render("ENTER YOUR NAME", True, TEXT_COLOR)
		tr = title.get_rect(center=(WINDOW_WIDTH // 2, 120))
		screen.blit(title, tr)

		prompt = ui_font.render("Name (max 10 letters):", True, TEXT_COLOR)
		pr = prompt.get_rect(center=(WINDOW_WIDTH // 2, 200))
		screen.blit(prompt, pr)

		box = pygame.Rect(0, 0, 300, 50)
		box.center = (WINDOW_WIDTH // 2, 270)
		pygame.draw.rect(screen, PANEL_COLOR, box, border_radius=10)
		txt_surface = ui_font.render(name, True, TEXT_COLOR)
		screen.blit(txt_surface, txt_surface.get_rect(center=box.center))

		hint = ui_font.render("Press ENTER when done", True, TEXT_COLOR)
		hr = hint.get_rect(center=(WINDOW_WIDTH // 2, 350))
		screen.blit(hint, hr)

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


def game_over_screen(screen, final_score, title_font, ui_font):
	"""Persist score and show top 5 leaderboard until R is pressed."""
	insert_score(CURRENT_PLAYER, final_score)
	top5 = fetch_top_scores()

	while True:
		screen.fill(BG_COLOR)

		title = title_font.render("GAME OVER", True, (200, 0, 0))
		tr = title.get_rect(center=(WINDOW_WIDTH // 2, 80))
		screen.blit(title, tr)

		score_surf = ui_font.render(f"Score: {final_score}", True, TEXT_COLOR)
		sr = score_surf.get_rect(center=(WINDOW_WIDTH // 2, 140))
		screen.blit(score_surf, sr)

		table_title = ui_font.render("TOP 5:", True, TEXT_COLOR)
		ttr = table_title.get_rect(center=(WINDOW_WIDTH // 2, 200))
		screen.blit(table_title, ttr)

		for idx, (player_name, score) in enumerate(top5):
			line = ui_font.render(f"{idx + 1}. {player_name} - {score}", True, TEXT_COLOR)
			lr = line.get_rect(center=(WINDOW_WIDTH // 2, 250 + idx * 40))
			screen.blit(line, lr)

		retry = ui_font.render("Press R for menu", True, (200, 0, 0))
		rr = retry.get_rect(center=(WINDOW_WIDTH // 2, 500))
		screen.blit(retry, rr)

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


class TetrisGame:
	def __init__(self):
		pygame.init()
		self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
		pygame.display.set_caption("Tetris")
		self.clock = pygame.time.Clock()
		self.title_font = pygame.font.SysFont("consolas", 32, bold=True)
		self.ui_font = pygame.font.SysFont("consolas", 24)
		self.small_font = pygame.font.SysFont("consolas", 18)
		pygame.key.set_repeat(160, 50)
		self.reset_game()

	def reset_game(self):
		self.board = [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
		self.score = 0
		self.lines = 0
		self.level = 1
		self.paused = False
		self.game_over = False
		self.fall_timer = 0
		self.bag = []
		self.current_piece = self.random_piece()
		self.next_piece = self.random_piece()

	def random_piece(self):
		if not self.bag:
			self.bag = list(SHAPES.keys())
			random.shuffle(self.bag)
		piece_name = self.bag.pop()
		return {
			"name": piece_name,
			"rotation": 0,
			"x": 3,
			"y": -1,
			"color": PIECE_COLORS[piece_name],
		}

	def fall_interval_ms(self):
		return max(80, 600 - (self.level - 1) * 45)

	def piece_cells(self, piece):
		cells = []
		for offset_x, offset_y in SHAPES[piece["name"]][piece["rotation"]]:
			cells.append((piece["x"] + offset_x, piece["y"] + offset_y))
		return cells

	def valid_position(self, piece):
		for cell_x, cell_y in self.piece_cells(piece):
			if cell_x < 0 or cell_x >= BOARD_WIDTH or cell_y >= BOARD_HEIGHT:
				return False
			if cell_y >= 0 and self.board[cell_y][cell_x] is not None:
				return False
		return True

	def try_move(self, delta_x, delta_y):
		moved = dict(self.current_piece)
		moved["x"] += delta_x
		moved["y"] += delta_y
		if self.valid_position(moved):
			self.current_piece = moved
			return True
		return False

	def try_rotate(self):
		rotated = dict(self.current_piece)
		rotated["rotation"] = (rotated["rotation"] + 1) % 4
		for kick in (0, -1, 1, -2, 2):
			kicked = dict(rotated)
			kicked["x"] += kick
			if self.valid_position(kicked):
				self.current_piece = kicked
				return True
		return False

	def hard_drop(self):
		dropped_cells = 0
		while self.try_move(0, 1):
			dropped_cells += 1
		self.score += dropped_cells * 2
		self.lock_piece()

	def lock_piece(self):
		for cell_x, cell_y in self.piece_cells(self.current_piece):
			if cell_y < 0:
				self.game_over = True
				return
			self.board[cell_y][cell_x] = self.current_piece["color"]
		cleared = self.clear_lines()
		if cleared:
			self.lines += cleared
			self.score += SCORE_TABLE[cleared] * self.level
			self.level = 1 + self.lines // 10
		self.current_piece = self.next_piece
		self.next_piece = self.random_piece()
		if not self.valid_position(self.current_piece):
			self.game_over = True

	def clear_lines(self):
		remaining_rows = [row for row in self.board if any(cell is None for cell in row)]
		cleared = BOARD_HEIGHT - len(remaining_rows)
		if cleared > 0:
			for _ in range(cleared):
				remaining_rows.insert(0, [None for _ in range(BOARD_WIDTH)])
			self.board = remaining_rows
		return cleared

	def ghost_piece(self):
		ghost = dict(self.current_piece)
		while True:
			candidate = dict(ghost)
			candidate["y"] += 1
			if not self.valid_position(candidate):
				break
			ghost = candidate
		return ghost

	def handle_keydown(self, key):
		if key == pygame.K_ESCAPE:
			pygame.quit()
			sys.exit()
		if key == pygame.K_p:
			if not self.game_over:
				self.paused = not self.paused
			return
		if self.paused or self.game_over:
			return

		if key in (pygame.K_LEFT, pygame.K_a):
			self.try_move(-1, 0)
		elif key in (pygame.K_RIGHT, pygame.K_d):
			self.try_move(1, 0)
		elif key in (pygame.K_DOWN, pygame.K_s):
			if self.try_move(0, 1):
				self.score += 1
		elif key in (pygame.K_UP, pygame.K_w, pygame.K_x):
			self.try_rotate()
		elif key == pygame.K_SPACE:
			self.hard_drop()

	def update(self, elapsed_ms):
		if self.paused or self.game_over:
			return
		self.fall_timer += elapsed_ms
		if self.fall_timer >= self.fall_interval_ms():
			self.fall_timer = 0
			if not self.try_move(0, 1):
				self.lock_piece()

	def draw_cell(self, x, y, color, inset=1):
		rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
		rect = rect.inflate(-inset * 2, -inset * 2)
		pygame.draw.rect(self.screen, color, rect, border_radius=4)

	def draw_board(self):
		board_surface = pygame.Rect(0, 0, BOARD_WIDTH * CELL_SIZE, WINDOW_HEIGHT)
		pygame.draw.rect(self.screen, BG_COLOR, board_surface)

		for y in range(BOARD_HEIGHT):
			for x in range(BOARD_WIDTH):
				grid_rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
				pygame.draw.rect(self.screen, GRID_COLOR, grid_rect, width=1)
				if self.board[y][x] is not None:
					self.draw_cell(x, y, self.board[y][x])

		ghost = self.ghost_piece()
		for cell_x, cell_y in self.piece_cells(ghost):
			if cell_y >= 0:
				self.draw_cell(cell_x, cell_y, GHOST_COLOR, inset=6)

		for cell_x, cell_y in self.piece_cells(self.current_piece):
			if cell_y >= 0:
				self.draw_cell(cell_x, cell_y, self.current_piece["color"])

	def draw_next_piece(self):
		preview_origin_x = BOARD_WIDTH * CELL_SIZE + 45
		preview_origin_y = 100
		for offset_x, offset_y in SHAPES[self.next_piece["name"]][0]:
			x = preview_origin_x + offset_x * 24
			y = preview_origin_y + offset_y * 24
			rect = pygame.Rect(x, y, 22, 22)
			pygame.draw.rect(self.screen, self.next_piece["color"], rect, border_radius=3)

	def draw_sidebar(self):
		panel_rect = pygame.Rect(BOARD_WIDTH * CELL_SIZE, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT)
		pygame.draw.rect(self.screen, PANEL_COLOR, panel_rect)

		title = self.title_font.render("TETRIS", True, TEXT_COLOR)
		self.screen.blit(title, (BOARD_WIDTH * CELL_SIZE + 25, 20))

		next_label = self.ui_font.render("Next", True, TEXT_COLOR)
		self.screen.blit(next_label, (BOARD_WIDTH * CELL_SIZE + 25, 70))
		self.draw_next_piece()

		score_label = self.ui_font.render(f"Score: {self.score}", True, TEXT_COLOR)
		lines_label = self.ui_font.render(f"Lines: {self.lines}", True, TEXT_COLOR)
		level_label = self.ui_font.render(f"Level: {self.level}", True, TEXT_COLOR)
		self.screen.blit(score_label, (BOARD_WIDTH * CELL_SIZE + 25, 250))
		self.screen.blit(lines_label, (BOARD_WIDTH * CELL_SIZE + 25, 290))
		self.screen.blit(level_label, (BOARD_WIDTH * CELL_SIZE + 25, 330))

		controls = [
			"Move: Arrows or A/D",
			"Rotate: Up or W",
			"Soft drop: Down or S",
			"Hard drop: Space",
			"Pause: P",
			"Menu (game over): R",
			"Quit: Esc",
		]
		start_y = 410
		for index, text in enumerate(controls):
			control_line = self.small_font.render(text, True, MUTED_TEXT_COLOR)
			self.screen.blit(control_line, (BOARD_WIDTH * CELL_SIZE + 18, start_y + index * 24))

		if self.paused and not self.game_over:
			pause_text = self.ui_font.render("Paused", True, TEXT_COLOR)
			self.screen.blit(pause_text, (BOARD_WIDTH * CELL_SIZE + 70, 370))

	def draw_game_over_overlay(self):
		overlay = pygame.Surface((BOARD_WIDTH * CELL_SIZE, WINDOW_HEIGHT), pygame.SRCALPHA)
		overlay.fill((0, 0, 0, 145))
		self.screen.blit(overlay, (0, 0))
		title = self.title_font.render("Game Over", True, TEXT_COLOR)
		restart = self.small_font.render("Press R for menu", True, TEXT_COLOR)
		self.screen.blit(title, (45, 250))
		self.screen.blit(restart, (65, 295))

	def draw(self):
		self.draw_board()
		self.draw_sidebar()
		if self.game_over:
			self.draw_game_over_overlay()
		pygame.display.flip()

	def run(self):
		ask_name_once(self.screen, self.title_font, self.ui_font)
		while True:
			elapsed_ms = self.clock.tick(FPS)
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()
				if event.type == pygame.KEYDOWN:
					if self.game_over and event.key == pygame.K_r:
						game_over_screen(self.screen, self.score, self.title_font, self.ui_font)
						self.reset_game()
					else:
						self.handle_keydown(event.key)

			self.update(elapsed_ms)
			self.draw()


def main():
	game = TetrisGame()
	game.run()


if __name__ == "__main__":
	main()
