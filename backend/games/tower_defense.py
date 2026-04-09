import math
import random
import sys

import pygame


WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 720
FPS = 60

GRID_COLS = 12
GRID_ROWS = 10
CELL_SIZE = 52
PLAY_X = 24
PLAY_Y = 90
PLAY_WIDTH = GRID_COLS * CELL_SIZE
PLAY_HEIGHT = GRID_ROWS * CELL_SIZE
PANEL_X = PLAY_X + PLAY_WIDTH + 16

MAX_WAVES = 15
MAX_TOWER_LEVEL = 15
MAX_PATH_LEVEL = 8

BG_TOP = (16, 22, 34)
BG_BOTTOM = (28, 38, 56)
TEXT_COLOR = (232, 240, 255)
MUTED_TEXT = (151, 168, 197)
PANEL_BG = (29, 39, 61)
GRID_COLOR = (43, 56, 84)
BUILDABLE_A = (52, 74, 108)
BUILDABLE_B = (58, 81, 117)
PATH_COLOR = (122, 96, 70)
PATH_EDGE = (164, 130, 90)
WATER_A = (48, 94, 146)
WATER_B = (56, 106, 164)
WATER_EDGE = (122, 188, 244)
ENEMY_COLOR = (255, 120, 120)
HP_BAR_BG = (36, 28, 34)
HP_BAR_FG = (94, 231, 133)
PROJECTILE_COLOR = (255, 226, 129)
SPLASH_COLOR = (255, 167, 99)

TOWER_TYPES = {
    1: {
        "name": "Rapid",
        "cost": 60,
        "range": 115,
        "damage": 8,
        "cooldown_ms": 280,
        "projectile_speed": 420,
        "splash_radius": 0,
        "color": (120, 216, 255),
    },
    2: {
        "name": "Ship",
        "cost": 110,
        "range": 130,
        "damage": 28,
        "cooldown_ms": 560,
        "projectile_speed": 360,
        "splash_radius": 38,
        "color": (120, 197, 255),
    },
    3: {
        "name": "Plane",
        "cost": 145,
        "range": 92,
        "damage": 22,
        "cooldown_ms": 420,
        "projectile_speed": 620,
        "splash_radius": 15,
        "color": (193, 228, 255),
    },
}

LEVEL_DAMAGE_SCALE = 0.5
LEVEL_RANGE_SCALE = 0.12
LEVEL_COOLDOWN_REDUCTION = 0.09
PATH_A_DAMAGE_SCALE = 0.34
PATH_A_COOLDOWN_SCALE = 0.07
PATH_B_RANGE_SCALE = 0.22
PATH_B_SPLASH_SCALE = 0.36
PLANE_ORBIT_RADIUS = 74
PLANE_ORBIT_SPEED = 2.2

TOWER_SPRITES = {
    1: [
        "00100",
        "01110",
        "11111",
        "01110",
        "01110",
    ],
    2: [
        "11111",
        "11111",
        "01110",
        "11111",
        "00100",
    ],
    3: [
        "10001",
        "01110",
        "11111",
        "01110",
        "10001",
    ],
}

ENEMY_SPRITES = {
    "normal": [
        "01110",
        "11111",
        "10101",
        "11111",
        "01010",
    ],
    "elite": [
        "01110",
        "11111",
        "11111",
        "10101",
        "01010",
    ],
    "tank": [
        "11111",
        "11111",
        "10101",
        "11111",
        "01110",
    ],
    "super_tank": [
        "11111",
        "11011",
        "11111",
        "11011",
        "11111",
    ],
    "soldier": [
        "00100",
        "01110",
        "11111",
        "00100",
        "01010",
    ],
    "ship": [
        "00100",
        "01110",
        "11111",
        "01110",
        "11111",
    ],
    "plane": [
        "10001",
        "01110",
        "11111",
        "01110",
        "10001",
    ],
}


def tile_center(tile_col, tile_row):
    cx = PLAY_X + tile_col * CELL_SIZE + CELL_SIZE // 2
    cy = PLAY_Y + tile_row * CELL_SIZE + CELL_SIZE // 2
    return (float(cx), float(cy))


def world_to_tile(mx, my):
    if mx < PLAY_X or my < PLAY_Y:
        return None
    rel_x = mx - PLAY_X
    rel_y = my - PLAY_Y
    col = rel_x // CELL_SIZE
    row = rel_y // CELL_SIZE
    if 0 <= col < GRID_COLS and 0 <= row < GRID_ROWS:
        return (int(col), int(row))
    return None


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


class TowerDefenseGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Pixel Tower Defense")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 24)
        self.small_font = pygame.font.SysFont("consolas", 17)
        self.big_font = pygame.font.SysFont("consolas", 40, bold=True)

        self.land_path_tiles = [
            (0, 5),
            (1, 5),
            (2, 5),
            (3, 5),
            (3, 4),
            (3, 3),
            (2, 3),
            (1, 3),
            (1, 2),
            (2, 2),
            (3, 2),
            (4, 2),
            (5, 2),
            (6, 2),
            (6, 3),
            (6, 4),
            (5, 4),
            (4, 4),
            (4, 5),
            (4, 6),
            (5, 6),
            (6, 6),
            (7, 6),
            (8, 6),
            (8, 5),
            (8, 4),
            (9, 4),
            (10, 4),
            (10, 3),
            (10, 2),
            (11, 2),
        ]
        self.water_path_tiles = [
            (0, 6),
            (1, 6),
            (2, 6),
            (3, 6),
            (4, 7),
            (5, 7),
            (6, 7),
            (7, 7),
            (8, 7),
            (9, 6),
            (10, 6),
            (11, 6),
        ]
        self.air_path_tiles = []

        # Compatibility aliases for existing systems that expect a default route.
        self.path_tiles = self.land_path_tiles
        self.path_points = [tile_center(c, r) for c, r in self.land_path_tiles]
        self.water_path_points = [tile_center(c, r) for c, r in self.water_path_tiles]
        self.air_path_points = [tile_center(c, r) for c, r in self.air_path_tiles]

        self.path_set = set(self.land_path_tiles)
        self.water_path_set = set(self.water_path_tiles)
        self.route_blocked_set = self.path_set | self.water_path_set
        self.water_tiles = set(self.water_path_tiles)
        self.water_points = [tile_center(c, r) for c, r in self.water_tiles]

        self.reset_game()

    def reset_game(self):
        self.gold = 220
        self.lives = 20
        self.wave = 0
        self.score = 0
        self.kills = 0
        self.game_over = False
        self.victory = False
        self.paused = False
        self.speed_multiplier = 1

        self.selected_tower_type = 1
        self.selected_tower = None
        self.dragging_tower_type = None
        self.drag_mouse = (0, 0)
        self.tower_card_rects = {}
        self.upgrade_button_rects = {}
        self.hover_tile = None
        self.status_text = "Press Space to start wave"
        self.status_ms = 0

        self.towers = []
        self.enemies = []
        self.projectiles = []

        self.wave_active = False
        self.wave_spawn_timer = 0
        self.spawn_queue = []
        self.base_enemy_speed = 0.0
        self.base_enemy_hp = 0
        self.enemy_reward = 0

    def set_status(self, text, ms=1100):
        self.status_text = text
        self.status_ms = ms

    def can_place_tower(self, tile, tower_type=None):
        if tile is None:
            return False

        chosen_type = self.selected_tower_type if tower_type is None else tower_type
        is_ship_tower = chosen_type == 2

        if is_ship_tower:
            if tile not in self.water_tiles:
                return False
        else:
            if tile in self.route_blocked_set:
                return False
            if tile in self.water_tiles:
                return False
        for tower in self.towers:
            if tower["tile"] == tile:
                return False
        return True

    def start_wave(self):
        if self.wave_active or self.game_over or self.victory:
            return
        if self.wave >= MAX_WAVES:
            return

        self.wave += 1
        self.wave_active = True
        self.wave_spawn_timer = 0

        count = 10 + self.wave * 2
        self.base_enemy_speed = 62 + self.wave * 5
        self.base_enemy_hp = 57 + self.wave * 15
        self.enemy_reward = 8 + self.wave

        elite_ratio = min(0.34, max(0.0, (self.wave - 3) * 0.034))
        soldier_ratio = min(0.58, max(0.18, (self.wave - 1) * 0.048))
        tank_ratio = min(0.27, max(0.0, (self.wave - 6) * 0.028))
        super_tank_ratio = min(0.12, max(0.0, (self.wave - 10) * 0.016))

        self.spawn_queue = []
        for i in range(count):
            roll = random.random()

            if roll < super_tank_ratio:
                hp_mult = 6.4 + self.wave * 0.15
                speed_mult = 0.67
                reward_mult = 4.5
                tier = "super_tank"
                color = (167, 72, 222)
                split_count = 2 if self.wave < 12 else 3
                movement_mode = "ground"
                armor = 0.22
            elif roll < super_tank_ratio + tank_ratio:
                hp_mult = 3.0 + self.wave * 0.09
                speed_mult = 0.80
                reward_mult = 2.2
                tier = "tank"
                color = (198, 112, 255)
                split_count = 0
                movement_mode = "ground"
                armor = 0.15
            elif roll < super_tank_ratio + tank_ratio + soldier_ratio:
                hp_mult = 1.4 + self.wave * 0.036
                speed_mult = 1.24
                reward_mult = 1.24
                tier = "soldier"
                color = (255, 210, 127)
                split_count = 0
                movement_mode = "ground"
                armor = 0.09
            elif roll < super_tank_ratio + tank_ratio + soldier_ratio + elite_ratio:
                hp_mult = 1.9 + self.wave * 0.05
                speed_mult = 1.06
                reward_mult = 1.45
                tier = "elite"
                color = (255, 164, 106)
                split_count = 0
                movement_mode = "ground"
                armor = 0.07
            else:
                hp_mult = 1.0
                speed_mult = 1.0
                reward_mult = 1.0
                tier = "normal"
                color = ENEMY_COLOR
                split_count = 0
                movement_mode = "ground"
                armor = 0.0

            # Keep troopers as a visible frontline enemy in most waves.
            if i % 4 == 0 and tier == "normal":
                hp_mult = 1.4 + self.wave * 0.036
                speed_mult = 1.24
                reward_mult = 1.24
                tier = "soldier"
                color = (255, 210, 127)
                split_count = 0
                movement_mode = "ground"
                armor = 0.09

            # Keep a periodic mini-spike so each wave still has pressure moments.
            if i % 5 == 4:
                hp_mult *= 1.2

            self.spawn_queue.append(
                {
                    "hp": int(self.base_enemy_hp * hp_mult),
                    "speed_mult": speed_mult,
                    "reward": int(self.enemy_reward * reward_mult),
                    "tier": tier,
                    "color": color,
                    "split_count": split_count,
                    "movement_mode": movement_mode,
                    "armor": armor,
                }
            )

        self.set_status(f"Wave {self.wave} started", ms=900)

    def spawn_enemy(self, spec):
        movement_mode = spec.get("movement_mode", "ground")
        if movement_mode == "water":
            path_points = self.water_path_points
        elif movement_mode == "air":
            path_points = self.air_path_points
        else:
            path_points = self.path_points

        start_x, start_y = path_points[0]
        tier = spec.get("tier", "normal")
        radius = 14 if tier == "super_tank" else (11 if tier == "tank" else 10)
        if tier == "plane":
            radius = 9
        elif tier == "ship":
            radius = 12
        enemy = {
            "x": start_x,
            "y": start_y,
            "path_idx": 0,
            "path_points": path_points,
            "hp": spec["hp"],
            "max_hp": spec["hp"],
            "speed": self.base_enemy_speed * spec["speed_mult"] * random.uniform(0.94, 1.08),
            "radius": radius,
            "reward": spec["reward"],
            "tier": tier,
            "color": spec["color"],
            "split_count": spec.get("split_count", 0),
            "movement_mode": movement_mode,
            "armor": spec.get("armor", 0.0),
        }
        self.enemies.append(enemy)

    def spawn_split_tanks(self, enemy):
        split_count = enemy.get("split_count", 0)
        if split_count <= 0:
            return

        tank_hp = int(self.base_enemy_hp * (2.8 + self.wave * 0.08))
        tank_reward = int(self.enemy_reward * 1.8)
        for _ in range(split_count):
            spawned = {
                "x": enemy["x"] + random.uniform(-8, 8),
                "y": enemy["y"] + random.uniform(-8, 8),
                "path_idx": enemy["path_idx"],
                "path_points": self.path_points,
                "hp": tank_hp,
                "max_hp": tank_hp,
                "speed": self.base_enemy_speed * 0.84 * random.uniform(0.95, 1.07),
                "radius": 11,
                "reward": tank_reward,
                "tier": "tank",
                "color": (198, 112, 255),
                "split_count": 0,
                "movement_mode": "ground",
                "armor": 0.15,
            }
            self.enemies.append(spawned)

        self.set_status("Super tank split into tanks!", ms=650)

    def place_tower(self, tile, tower_type=None):
        chosen_type = self.selected_tower_type if tower_type is None else tower_type
        if not self.can_place_tower(tile, chosen_type):
            if chosen_type == 2:
                self.set_status("Ship tower can only be placed on water")
            else:
                self.set_status("This tower needs land (not water/path)")
            return

        tower_def = TOWER_TYPES[chosen_type]
        if self.gold < tower_def["cost"]:
            self.set_status("Not enough gold")
            return

        self.gold -= tower_def["cost"]
        cx, cy = tile_center(tile[0], tile[1])
        tower = {
            "tile": tile,
            "x": cx,
            "y": cy,
            "anchor_x": cx,
            "anchor_y": cy,
            "type": chosen_type,
            "level": 1,
            "path_a": 0,
            "path_b": 0,
            "cooldown": random.randint(0, tower_def["cooldown_ms"] // 3),
            "orbit_angle": random.random() * math.tau,
        }
        self.towers.append(tower)
        self.selected_tower = tower
        self.set_status(f"Placed {tower_def['name']}", ms=700)

    def get_tower_at_tile(self, tile):
        if tile is None:
            return None
        for tower in self.towers:
            if tower["tile"] == tile:
                return tower
        return None

    def get_tower_stats(self, tower):
        base = TOWER_TYPES[tower["type"]]
        level = tower.get("level", 1)
        path_a = tower.get("path_a", 0)
        path_b = tower.get("path_b", 0)
        level_bonus = level - 1
        damage_scale = 1 + LEVEL_DAMAGE_SCALE * level_bonus + PATH_A_DAMAGE_SCALE * path_a
        range_scale = 1 + LEVEL_RANGE_SCALE * level_bonus + PATH_B_RANGE_SCALE * path_b
        cooldown_scale = 1 - LEVEL_COOLDOWN_REDUCTION * level_bonus - PATH_A_COOLDOWN_SCALE * path_a

        damage = int(round(base["damage"] * damage_scale))
        rng = int(round(base["range"] * range_scale))
        cooldown = int(round(base["cooldown_ms"] * cooldown_scale))
        cooldown = max(120, cooldown)
        splash = base["splash_radius"]
        if splash > 0 and path_b > 0:
            splash = int(round(splash * (1 + PATH_B_SPLASH_SCALE * path_b)))

        return {
            "name": base["name"],
            "damage": damage,
            "range": rng,
            "cooldown_ms": cooldown,
            "projectile_speed": base["projectile_speed"],
            "splash_radius": splash,
            "color": base["color"],
            "cost": base["cost"],
            "path_a": path_a,
            "path_b": path_b,
            "level": level,
        }

    def get_upgrade_cost(self, tower, path_key):
        base_cost = TOWER_TYPES[tower["type"]]["cost"]
        path_level = tower.get(path_key, 0)
        total_level = tower.get("path_a", 0) + tower.get("path_b", 0)
        return int(base_cost * (0.75 + 0.45 * (path_level + 1) + 0.2 * total_level))

    def try_upgrade_tower_path(self, tower, path_key):
        if tower is None:
            self.set_status("Select a tower first")
            return
        if path_key not in ("path_a", "path_b"):
            return

        if tower[path_key] >= MAX_PATH_LEVEL:
            self.set_status("That path is maxed")
            return

        if tower["path_a"] + tower["path_b"] >= MAX_TOWER_LEVEL:
            self.set_status("Tower is fully upgraded")
            return

        cost = self.get_upgrade_cost(tower, path_key)
        if self.gold < cost:
            self.set_status("Not enough gold to upgrade")
            return

        self.gold -= cost
        tower[path_key] += 1
        tower["level"] = 1 + tower["path_a"] + tower["path_b"]
        self.selected_tower = tower
        path_name = "Path A" if path_key == "path_a" else "Path B"
        self.set_status(
            f"{TOWER_TYPES[tower['type']]['name']} upgraded: {path_name}",
            ms=900,
        )

    def try_upgrade_selected_tower(self):
        self.try_upgrade_tower_path(self.selected_tower, "path_a")

    def update_wave_spawning(self, elapsed_ms):
        if not self.wave_active:
            return

        if self.spawn_queue:
            self.wave_spawn_timer += elapsed_ms
            spawn_every = max(170, 680 - self.wave * 34)
            while self.wave_spawn_timer >= spawn_every and self.spawn_queue:
                self.wave_spawn_timer -= spawn_every
                enemy_spec = self.spawn_queue.pop(0)
                self.spawn_enemy(enemy_spec)

        if not self.spawn_queue and not self.enemies:
            self.wave_active = False
            self.gold += 25 + self.wave * 6
            self.score += self.wave * 100
            self.set_status(f"Wave {self.wave} clear")
            if self.wave >= MAX_WAVES:
                self.victory = True

    def update_enemies(self, dt_sec):
        alive = []
        for enemy in self.enemies:
            path_points = enemy.get("path_points", self.path_points)
            idx = enemy["path_idx"]
            if idx >= len(path_points) - 1:
                self.lives -= 1
                if self.lives <= 0:
                    self.game_over = True
                continue

            tx, ty = path_points[idx + 1]
            dx = tx - enemy["x"]
            dy = ty - enemy["y"]
            dist = math.hypot(dx, dy)
            step = enemy["speed"] * dt_sec

            if dist <= step or dist < 1:
                enemy["x"] = tx
                enemy["y"] = ty
                enemy["path_idx"] += 1
            else:
                enemy["x"] += dx / dist * step
                enemy["y"] += dy / dist * step

            alive.append(enemy)

        self.enemies = alive

    def create_projectile(self, tower, target, damage_scale=1.0):
        tower_def = self.get_tower_stats(tower)
        source_type = tower["type"]
        armor_pen = 0.35 if source_type == 3 else 0.0
        self.projectiles.append(
            {
                "x": tower["x"],
                "y": tower["y"],
                "target": target,
                "speed": tower_def["projectile_speed"],
                "damage": max(1, int(round(tower_def["damage"] * damage_scale))),
                "splash_radius": tower_def["splash_radius"],
                "color": tower_def["color"],
                "source_type": source_type,
                "armor_pen": armor_pen,
            }
        )

    def is_enemy_near_water(self, enemy, radius):
        radius2 = radius * radius
        ex = enemy["x"]
        ey = enemy["y"]
        for wx, wy in self.water_points:
            dx = ex - wx
            dy = ey - wy
            if dx * dx + dy * dy <= radius2:
                return True
        return False

    def find_target_for_tower(self, tower, exclude=None):
        tower_def = self.get_tower_stats(tower)
        tower_type = tower["type"]
        best = None
        best_progress = -1
        r2 = tower_def["range"] * tower_def["range"]

        for enemy in self.enemies:
            if enemy is exclude:
                continue

            # Ship towers focus near-water targets; plane towers can engage globally.
            if tower_type == 2 and not self.is_enemy_near_water(enemy, CELL_SIZE * 2.4):
                continue

            dx = enemy["x"] - tower["x"]
            dy = enemy["y"] - tower["y"]
            d2 = dx * dx + dy * dy
            if d2 > r2:
                continue
            progress = enemy["path_idx"] + (enemy["max_hp"] - enemy["hp"]) * 0.001
            if progress > best_progress:
                best_progress = progress
                best = enemy

        return best

    def apply_damage(self, enemy, damage, armor_pen=0.0):
        armor = max(0.0, enemy.get("armor", 0.0) - armor_pen)
        dealt = max(1, int(round(damage * (1 - armor))))
        enemy["hp"] -= dealt
        if enemy["hp"] <= 0:
            if enemy.get("tier") == "super_tank":
                self.spawn_split_tanks(enemy)
            self.kills += 1
            self.score += 10
            self.gold += enemy["reward"]
            return True
        return False

    def update_towers(self, elapsed_ms):
        for tower in self.towers:
            if tower["type"] == 3:
                tower["orbit_angle"] = (tower.get("orbit_angle", 0.0) + PLANE_ORBIT_SPEED * (elapsed_ms / 1000.0)) % math.tau
                ax = tower.get("anchor_x", tower["x"])
                ay = tower.get("anchor_y", tower["y"])
                tower["x"] = ax + math.cos(tower["orbit_angle"]) * PLANE_ORBIT_RADIUS
                tower["y"] = ay + math.sin(tower["orbit_angle"]) * PLANE_ORBIT_RADIUS
            else:
                tower["x"] = tower.get("anchor_x", tower["x"])
                tower["y"] = tower.get("anchor_y", tower["y"])

        if not self.enemies:
            for tower in self.towers:
                tower["cooldown"] = max(0, tower["cooldown"] - elapsed_ms)
            return

        for tower in self.towers:
            tdef = self.get_tower_stats(tower)
            tower["cooldown"] = max(0, tower["cooldown"] - elapsed_ms)
            if tower["cooldown"] > 0:
                continue

            target = self.find_target_for_tower(tower)
            if target is None:
                continue

            self.create_projectile(tower, target)
            if tower["type"] == 3:
                second = self.find_target_for_tower(tower, exclude=target)
                if second is not None:
                    self.create_projectile(tower, second, damage_scale=0.72)
            tower["cooldown"] = tdef["cooldown_ms"]

    def update_projectiles(self, dt_sec):
        active = []
        for p in self.projectiles:
            target = p["target"]
            if target not in self.enemies:
                continue

            dx = target["x"] - p["x"]
            dy = target["y"] - p["y"]
            dist = math.hypot(dx, dy)
            step = p["speed"] * dt_sec

            if dist <= step or dist < 2:
                hit_damage = p["damage"]
                if p.get("source_type") == 2 and target.get("tier") in ("tank", "super_tank"):
                    hit_damage = int(round(hit_damage * 1.25))
                if p["splash_radius"] <= 0:
                    self.apply_damage(target, hit_damage, armor_pen=p.get("armor_pen", 0.0))
                else:
                    radius2 = p["splash_radius"] * p["splash_radius"]
                    for enemy in list(self.enemies):
                        ex = enemy["x"] - target["x"]
                        ey = enemy["y"] - target["y"]
                        if ex * ex + ey * ey <= radius2:
                            splash_damage = hit_damage
                            if p.get("source_type") == 2 and enemy.get("tier") in ("tank", "super_tank"):
                                splash_damage = int(round(splash_damage * 1.2))
                            self.apply_damage(enemy, splash_damage, armor_pen=p.get("armor_pen", 0.0))
                continue

            p["x"] += dx / dist * step
            p["y"] += dy / dist * step
            active.append(p)

        self.projectiles = active

    def cleanup_dead_enemies(self):
        self.enemies = [e for e in self.enemies if e["hp"] > 0]

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEMOTION:
                self.hover_tile = world_to_tile(*event.pos)
                self.drag_mouse = event.pos
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.game_over or self.victory:
                    continue
                self.drag_mouse = event.pos
                tile = world_to_tile(*event.pos)

                for path_key, rect in self.upgrade_button_rects.items():
                    if rect.collidepoint(event.pos):
                        self.try_upgrade_tower_path(self.selected_tower, path_key)
                        tile = None
                        break

                # Tower click: select for path upgrades.
                if tile is not None:
                    existing = self.get_tower_at_tile(tile)
                    if existing is not None:
                        self.selected_tower = existing
                        stats = self.get_tower_stats(existing)
                        self.set_status(f"Selected {stats['name']} Lv {existing['level']}", ms=700)
                        continue
                    else:
                        self.selected_tower = None

                # Start drag if a tower card is clicked.
                started_drag = False
                for tower_type, rect in self.tower_card_rects.items():
                    if rect.collidepoint(event.pos):
                        self.dragging_tower_type = tower_type
                        self.selected_tower_type = tower_type
                        self.set_status(f"Drag {TOWER_TYPES[tower_type]['name']} to place", ms=700)
                        started_drag = True
                        break

                if not started_drag and tile is not None:
                    self.set_status("Drag a tower card from panel to place", ms=900)

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.drag_mouse = event.pos
                if self.dragging_tower_type is not None and not (self.game_over or self.victory):
                    tile = world_to_tile(*event.pos)
                    if tile is not None:
                        self.place_tower(tile, tower_type=self.dragging_tower_type)
                    else:
                        self.set_status("Placement cancelled", ms=600)
                self.dragging_tower_type = None

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                if not (self.game_over or self.victory):
                    self.try_upgrade_selected_tower()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r:
                    self.reset_game()
                if event.key == pygame.K_SPACE:
                    self.start_wave()
                if event.key == pygame.K_p:
                    if not (self.game_over or self.victory):
                        self.paused = not self.paused
                        self.set_status("Paused" if self.paused else "Resumed", ms=700)
                if event.key == pygame.K_f:
                    self.speed_multiplier = 3 if self.speed_multiplier == 1 else 1
                    self.set_status("Speed x3" if self.speed_multiplier == 3 else "Speed x1", ms=700)
                if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    self.selected_tower_type = int(event.unicode)
                    self.dragging_tower_type = None
                if event.key == pygame.K_u and not (self.game_over or self.victory):
                    self.try_upgrade_tower_path(self.selected_tower, "path_a")
                if event.key == pygame.K_i and not (self.game_over or self.victory):
                    self.try_upgrade_tower_path(self.selected_tower, "path_b")

    def update(self, elapsed_ms):
        if self.status_ms > 0:
            self.status_ms = max(0, self.status_ms - elapsed_ms)

        if self.game_over or self.victory or self.paused:
            return

        scaled_ms = elapsed_ms * self.speed_multiplier
        dt_sec = scaled_ms / 1000.0

        self.update_wave_spawning(scaled_ms)
        self.update_towers(scaled_ms)
        self.update_projectiles(dt_sec)
        self.cleanup_dead_enemies()
        self.update_enemies(dt_sec)

    def draw_gradient_bg(self):
        for y in range(WINDOW_HEIGHT):
            t = y / WINDOW_HEIGHT
            r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
            g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
            b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WINDOW_WIDTH, y))

    def draw_pixel_sprite(self, sprite, color, center_x, center_y, pixel_size):
        rows = len(sprite)
        cols = len(sprite[0])
        width = cols * pixel_size
        height = rows * pixel_size
        start_x = int(center_x - width / 2)
        start_y = int(center_y - height / 2)

        shade = (
            clamp(color[0] - 45, 0, 255),
            clamp(color[1] - 45, 0, 255),
            clamp(color[2] - 45, 0, 255),
        )

        for r, bits in enumerate(sprite):
            for c, bit in enumerate(bits):
                if bit != "1":
                    continue
                rect = pygame.Rect(
                    start_x + c * pixel_size,
                    start_y + r * pixel_size,
                    pixel_size,
                    pixel_size,
                )
                pygame.draw.rect(self.screen, color, rect)
                if pixel_size >= 4:
                    pygame.draw.rect(
                        self.screen,
                        shade,
                        (rect.x + pixel_size - 2, rect.y + pixel_size - 2, 2, 2),
                    )

    def draw_grid(self):
        board = pygame.Rect(PLAY_X, PLAY_Y, PLAY_WIDTH, PLAY_HEIGHT)
        pygame.draw.rect(self.screen, (19, 27, 42), board, border_radius=8)

        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                rect = pygame.Rect(
                    PLAY_X + col * CELL_SIZE,
                    PLAY_Y + row * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE,
                )
                if (col, row) in self.water_tiles:
                    color = WATER_A if (row + col) % 2 == 0 else WATER_B
                elif (col, row) in self.path_set:
                    color = PATH_COLOR
                else:
                    color = BUILDABLE_A if (row + col) % 2 == 0 else BUILDABLE_B
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, GRID_COLOR, rect, 1)

        for i in range(len(self.path_tiles) - 1):
            c1, r1 = self.path_tiles[i]
            c2, r2 = self.path_tiles[i + 1]
            x1, y1 = tile_center(c1, r1)
            x2, y2 = tile_center(c2, r2)
            pygame.draw.line(self.screen, PATH_EDGE, (x1, y1), (x2, y2), 10)

        for tile in self.water_path_tiles:
            cx, cy = tile_center(tile[0], tile[1])
            pygame.draw.circle(self.screen, WATER_EDGE, (int(cx), int(cy)), 7, 2)

        if self.hover_tile is not None and not (self.game_over or self.victory):
            hc, hr = self.hover_tile
            hover = pygame.Rect(PLAY_X + hc * CELL_SIZE, PLAY_Y + hr * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            hovered_tower = self.get_tower_at_tile(self.hover_tile)
            preview_type = self.dragging_tower_type if self.dragging_tower_type is not None else self.selected_tower_type
            can_build = self.can_place_tower(self.hover_tile, preview_type)
            if hovered_tower is not None:
                color = (122, 184, 255)
            elif can_build:
                color = (96, 210, 138)
            else:
                color = (215, 105, 105)
            pygame.draw.rect(self.screen, color, hover, 3)

            if hovered_tower is not None:
                t = self.get_tower_stats(hovered_tower)
                cx, cy = tile_center(hc, hr)
                pygame.draw.circle(self.screen, (*t["color"], 55), (int(cx), int(cy)), t["range"], 1)
            elif can_build:
                t = self.get_tower_stats({"type": preview_type, "level": 1})
                cx, cy = tile_center(hc, hr)
                pygame.draw.circle(self.screen, (*t["color"], 55), (int(cx), int(cy)), t["range"], 1)

        if self.selected_tower is not None and self.selected_tower in self.towers:
            tc, tr = self.selected_tower["tile"]
            selected_rect = pygame.Rect(PLAY_X + tc * CELL_SIZE, PLAY_Y + tr * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(self.screen, (255, 232, 125), selected_rect, 3)

            stats = self.get_tower_stats(self.selected_tower)
            pygame.draw.circle(
                self.screen,
                (*stats["color"], 62),
                (int(self.selected_tower["x"]), int(self.selected_tower["y"])),
                stats["range"],
                1,
            )

    def draw_towers(self):
        for tower in self.towers:
            spec = self.get_tower_stats(tower)
            if tower["type"] == 3:
                ax = int(tower.get("anchor_x", tower["x"]))
                ay = int(tower.get("anchor_y", tower["y"]))
                pygame.draw.circle(self.screen, (143, 187, 224), (ax, ay), PLANE_ORBIT_RADIUS, 1)
            self.draw_pixel_sprite(TOWER_SPRITES[tower["type"]], spec["color"], tower["x"], tower["y"], 6)

            if tower["level"] > 1:
                badge = self.small_font.render(f"L{tower['level']}", True, (255, 246, 171))
                self.screen.blit(badge, (int(tower["x"]) - 14, int(tower["y"]) + 13))

    def draw_enemies(self):
        for enemy in self.enemies:
            tier = enemy.get("tier", "normal")
            if tier == "super_tank":
                pixel_size = 7
            elif tier == "tank":
                pixel_size = 6
            elif tier == "soldier":
                pixel_size = 4
            else:
                pixel_size = 5
            sprite = ENEMY_SPRITES.get(tier, ENEMY_SPRITES["normal"])
            self.draw_pixel_sprite(sprite, enemy.get("color", ENEMY_COLOR), enemy["x"], enemy["y"], pixel_size)

            bar_w = 28
            hp_ratio = max(0.0, enemy["hp"] / enemy["max_hp"])
            bx = int(enemy["x"] - bar_w // 2)
            by = int(enemy["y"] - 24)
            pygame.draw.rect(self.screen, HP_BAR_BG, (bx, by, bar_w, 5), border_radius=2)
            pygame.draw.rect(self.screen, HP_BAR_FG, (bx, by, int(bar_w * hp_ratio), 5), border_radius=2)

    def draw_projectiles(self):
        for p in self.projectiles:
            color = SPLASH_COLOR if p["splash_radius"] > 0 else PROJECTILE_COLOR
            pygame.draw.circle(self.screen, color, (int(p["x"]), int(p["y"])), 4)

    def draw_drag_preview(self):
        if self.dragging_tower_type is None:
            return

        mx, my = self.drag_mouse
        spec = self.get_tower_stats({"type": self.dragging_tower_type, "level": 1})
        self.draw_pixel_sprite(TOWER_SPRITES[self.dragging_tower_type], spec["color"], mx, my, 6)

        drop_tile = world_to_tile(mx, my)
        if drop_tile is not None and self.can_place_tower(drop_tile, self.dragging_tower_type):
            cx, cy = tile_center(drop_tile[0], drop_tile[1])
            pygame.draw.circle(self.screen, spec["color"], (int(cx), int(cy)), spec["range"], 1)

    def draw_panel(self):
        panel = pygame.Rect(PANEL_X, PLAY_Y, WINDOW_WIDTH - PANEL_X - 20, PLAY_HEIGHT)
        pygame.draw.rect(self.screen, PANEL_BG, panel, border_radius=10)

        self.tower_card_rects = {}
        self.upgrade_button_rects = {}

        self.screen.blit(self.font.render("TOWER DEFENSE", True, TEXT_COLOR), (PANEL_X + 14, PLAY_Y + 14))
        self.screen.blit(self.small_font.render(f"Wave: {self.wave}/{MAX_WAVES}", True, TEXT_COLOR), (PANEL_X + 14, PLAY_Y + 58))
        self.screen.blit(self.small_font.render(f"Lives: {self.lives}", True, TEXT_COLOR), (PANEL_X + 14, PLAY_Y + 84))
        self.screen.blit(self.small_font.render(f"Gold: {self.gold}", True, TEXT_COLOR), (PANEL_X + 14, PLAY_Y + 110))
        self.screen.blit(self.small_font.render(f"Score: {self.score}", True, TEXT_COLOR), (PANEL_X + 14, PLAY_Y + 136))

        y = PLAY_Y + 184
        for idx in (1, 2, 3):
            tower = TOWER_TYPES[idx]
            selected = idx == self.selected_tower_type or idx == self.dragging_tower_type
            rect = pygame.Rect(PANEL_X + 12, y, WINDOW_WIDTH - PANEL_X - 44, 62)
            self.tower_card_rects[idx] = rect
            border_col = tower["color"] if selected else (85, 99, 130)
            pygame.draw.rect(self.screen, (40, 53, 84), rect, border_radius=8)
            pygame.draw.rect(self.screen, border_col, rect, 2, border_radius=8)

            self.screen.blit(
                self.small_font.render(f"{idx}. {tower['name']}  ${tower['cost']}", True, TEXT_COLOR),
                (rect.x + 10, rect.y + 8),
            )
            if idx == 2:
                sub = "Water-only, bonus vs tanks"
            elif idx == 3:
                sub = "Global target + double shot"
            else:
                sub = f"DMG {tower['damage']}  RNG {tower['range']}  CD {tower['cooldown_ms']}ms"
            self.screen.blit(
                self.small_font.render(sub, True, MUTED_TEXT),
                (rect.x + 10, rect.y + 33),
            )
            y += 72

        info_rect = pygame.Rect(PANEL_X + 12, PLAY_Y + 402, WINDOW_WIDTH - PANEL_X - 44, 166)
        pygame.draw.rect(self.screen, (40, 53, 84), info_rect, border_radius=8)
        pygame.draw.rect(self.screen, (92, 116, 156), info_rect, 2, border_radius=8)

        if self.selected_tower is not None and self.selected_tower in self.towers:
            st = self.get_tower_stats(self.selected_tower)
            next_cost_a = self.get_upgrade_cost(self.selected_tower, "path_a")
            next_cost_b = self.get_upgrade_cost(self.selected_tower, "path_b")
            self.screen.blit(
                self.small_font.render(f"Selected: {st['name']} Lv {self.selected_tower['level']}", True, TEXT_COLOR),
                (info_rect.x + 10, info_rect.y + 10),
            )
            self.screen.blit(
                self.small_font.render(
                    f"DMG {st['damage']}  RNG {st['range']}",
                    True,
                    MUTED_TEXT,
                ),
                (info_rect.x + 10, info_rect.y + 35),
            )
            splash_text = f"SPL {st['splash_radius']}" if st["splash_radius"] > 0 else "SPL -"
            self.screen.blit(
                self.small_font.render(f"CD {st['cooldown_ms']}ms  {splash_text}", True, MUTED_TEXT),
                (info_rect.x + 10, info_rect.y + 57),
            )
            self.screen.blit(
                self.small_font.render(
                    f"Path A Lv {self.selected_tower['path_a']}  Path B Lv {self.selected_tower['path_b']}",
                    True,
                    MUTED_TEXT,
                ),
                (info_rect.x + 10, info_rect.y + 79),
            )

            a_rect = pygame.Rect(info_rect.x + 10, info_rect.y + 106, info_rect.width - 20, 24)
            b_rect = pygame.Rect(info_rect.x + 10, info_rect.y + 136, info_rect.width - 20, 24)
            self.upgrade_button_rects["path_a"] = a_rect
            self.upgrade_button_rects["path_b"] = b_rect

            a_max = self.selected_tower["path_a"] >= MAX_PATH_LEVEL or self.selected_tower["level"] >= MAX_TOWER_LEVEL
            b_max = self.selected_tower["path_b"] >= MAX_PATH_LEVEL or self.selected_tower["level"] >= MAX_TOWER_LEVEL
            a_color = (74, 112, 86) if not a_max else (72, 72, 82)
            b_color = (95, 92, 132) if not b_max else (72, 72, 82)
            pygame.draw.rect(self.screen, a_color, a_rect, border_radius=6)
            pygame.draw.rect(self.screen, b_color, b_rect, border_radius=6)

            a_text = "Path A Max" if a_max else f"Path A: +Dmg/+Rate  ${next_cost_a}"
            b_text = "Path B Max" if b_max else f"Path B: +Range/+Splash  ${next_cost_b}"
            self.screen.blit(
                self.small_font.render(a_text, True, TEXT_COLOR),
                (a_rect.x + 8, a_rect.y + 4),
            )
            self.screen.blit(
                self.small_font.render(b_text, True, TEXT_COLOR),
                (b_rect.x + 8, b_rect.y + 4),
            )
        else:
            self.screen.blit(
                self.small_font.render("Selected: none", True, TEXT_COLOR),
                (info_rect.x + 10, info_rect.y + 10),
            )
            self.screen.blit(
                self.small_font.render("Click tower to select + upgrade", True, MUTED_TEXT),
                (info_rect.x + 10, info_rect.y + 40),
            )
            self.screen.blit(
                self.small_font.render("Drag card from panel to place", True, MUTED_TEXT),
                (info_rect.x + 10, info_rect.y + 62),
            )

    def draw_top_bar(self):
        bar = pygame.Rect(0, 0, WINDOW_WIDTH, 68)
        pygame.draw.rect(self.screen, (19, 27, 42), bar)
        pygame.draw.line(self.screen, (57, 76, 117), (0, 67), (WINDOW_WIDTH, 67), 2)

        title = self.font.render("Pixel Tower Defense", True, TEXT_COLOR)
        self.screen.blit(title, (24, 18))

        mode_text = "Paused" if self.paused else ("Wave Active" if self.wave_active else "Build Phase")
        speed_text = f"Speed x{self.speed_multiplier}"
        self.screen.blit(self.small_font.render(mode_text, True, MUTED_TEXT), (390, 26))
        self.screen.blit(self.small_font.render(speed_text, True, MUTED_TEXT), (520, 26))

        if self.status_ms > 0:
            msg = self.small_font.render(self.status_text, True, (255, 224, 154))
            self.screen.blit(msg, (24, 44))

    def draw_bottom_controls(self):
        footer_h = 34
        y = WINDOW_HEIGHT - footer_h
        bar = pygame.Rect(0, y, WINDOW_WIDTH, footer_h)
        pygame.draw.rect(self.screen, (19, 27, 42), bar)
        pygame.draw.line(self.screen, (57, 76, 117), (0, y), (WINDOW_WIDTH, y), 2)

        controls = (
            "Drag card -> place | Click tower -> select | Click Path A/B to upgrade | "
            "Space wave | P pause | F speed | R restart | Esc quit"
        )
        self.screen.blit(self.small_font.render(controls, True, MUTED_TEXT), (16, y + 8))

    def draw_overlay(self, title, subtitle):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 155))
        self.screen.blit(overlay, (0, 0))

        ts = self.big_font.render(title, True, TEXT_COLOR)
        ss = self.font.render(subtitle, True, TEXT_COLOR)

        self.screen.blit(ts, ts.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 36)))
        self.screen.blit(ss, ss.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20)))

    def draw(self):
        self.draw_gradient_bg()
        self.draw_grid()
        self.draw_towers()
        self.draw_enemies()
        self.draw_projectiles()
        self.draw_drag_preview()
        self.draw_panel()
        self.draw_top_bar()
        self.draw_bottom_controls()

        if self.game_over:
            self.draw_overlay("Defeat", "Press R to restart")
        elif self.victory:
            self.draw_overlay("Victory", "All waves cleared. Press R to play again")

        pygame.display.flip()

    def run(self):
        while True:
            elapsed_ms = self.clock.tick(FPS)
            self.handle_events()
            self.update(elapsed_ms)
            self.draw()


def main():
    game = TowerDefenseGame()
    game.run()


if __name__ == "__main__":
    main()
