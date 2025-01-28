import pygame
import random
import math
import os

# Renkler & Ayarlar
COLORS = {
    "BLACK": (0, 0, 0),
    "WHITE": (255, 255, 255),
    "YELLOW": (255, 255, 0),
    "RED": (255, 0, 0),
    "BLUE": (0, 0, 255),
    "PINK": (255, 184, 255),
    "CYAN": (0, 255, 255),
    "ORANGE": (255, 184, 82)
}

WIDTH, HEIGHT = 560, 620
BLOCK_SIZE = 20
GRID_WIDTH = WIDTH // BLOCK_SIZE
GRID_HEIGHT = HEIGHT // BLOCK_SIZE

# Sesler
try:
    pygame.mixer.init()
    sound_folder = "sounds"
    eat_sound = pygame.mixer.Sound(os.path.join(sound_folder, "pacman_eat.mp3"))
    power_sound = pygame.mixer.Sound(os.path.join(sound_folder, "power_pellet.mp3"))
    death_sound = pygame.mixer.Sound(os.path.join(sound_folder, "pacman_death.mp3"))
except:
    print("Ses dosyaları yüklenemedi")
    eat_sound = power_sound = death_sound = type('DummySound', (), {'play': lambda: None})()


class PacmanGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Gelişmiş Pac-Man")
        self.clock = pygame.time.Clock()
        self.reset_game()

    def reset_game(self):
        # Orijinal Pac-Man labirentine yakın tasarım ama o sanki daha büyüktü olsun be
        self.maze = [
            "####################",
            "#........#........#",
            "#.##.###.##.###.##.#",
            "#.##.###.##.###.##.#",
            "#..................#",
            "#.##.#.######.#.##.#",
            "#....#...##...#....#",
            "####.###.##.###.####",
            "   #.#    G  #.#   ",
            "####.# ##### #.####",
            "#..................#",
            "#.##.###.##.###.##.#",
            "#..#...........#..#",
            "#.##.#.######.#.##.#",
            "#..................#",
            "####################"
        ]

        # Oyun durumu
        self.score = 0
        self.lives = 3
        self.level = 1
        self.power_time = 0
        self.running = True

        # Pac-Man başlangıç pozisyonu
        self.pacman = {
            "x": 10 * BLOCK_SIZE + BLOCK_SIZE // 2,
            "y": 14 * BLOCK_SIZE + BLOCK_SIZE // 2,  # Düzeltilmiş Y pozisyonu
            "dir": (0, 0),
            "next_dir": (0, 0),
            "speed": 3,
            "mouth_angle": 0,
            "mouth_speed": 0.2
        }

        # Hayaletler
        self.ghosts = [
            {"x": 9 * BLOCK_SIZE, "y": 8 * BLOCK_SIZE, "dir": (0, -1), "color": "RED", "type": "blinky", "speed": 2},
            {"x": 9 * BLOCK_SIZE, "y": 10 * BLOCK_SIZE, "dir": (0, 1), "color": "PINK", "type": "pinky", "speed": 2},
            {"x": 8 * BLOCK_SIZE, "y": 10 * BLOCK_SIZE, "dir": (0, 1), "color": "CYAN", "type": "inky", "speed": 2},
            {"x": 10 * BLOCK_SIZE, "y": 10 * BLOCK_SIZE, "dir": (0, 1), "color": "ORANGE", "type": "clyde", "speed": 2}
        ]

        # Labirent verileri
        self.pellets = set()
        self.power_pellets = set()
        self.walls = set()

        for y, row in enumerate(self.maze):
            for x, char in enumerate(row):
                if char == "#":
                    self.walls.add((x, y))
                elif char == ".":
                    self.pellets.add((x, y))
                elif char == "G":
                    self.power_pellets.add((x, y))

    def can_move(self, x, y, dx, dy):
        new_x = x + dx
        new_y = y + dy

        # Tünel geçişleri
        if new_x < 0:
            new_x = GRID_WIDTH - 1
        elif new_x >= GRID_WIDTH:
            new_x = 0

        return (new_x, new_y) not in self.walls

    def move_pacman(self):
        current_grid = (self.pacman["x"] // BLOCK_SIZE, self.pacman["y"] // BLOCK_SIZE)
        dx, dy = self.pacman["dir"]
        next_dx, next_dy = self.pacman["next_dir"]

        # Yön değişikliği için kontrol
        if next_dx != 0 or next_dy != 0:
            if self.can_move(current_grid[0], current_grid[1], next_dx, next_dy):
                self.pacman["dir"] = (next_dx, next_dy)
                dx, dy = self.pacman["dir"]
                self.pacman["next_dir"] = (0, 0)

        new_x = self.pacman["x"] + dx * self.pacman["speed"]
        new_y = self.pacman["y"] + dy * self.pacman["speed"]

        # Duvara çarpma kontrolü
        grid_x = new_x // BLOCK_SIZE
        grid_y = new_y // BLOCK_SIZE
        if (grid_x, grid_y) not in self.walls:
            self.pacman["x"] = new_x
            self.pacman["y"] = new_y
        else:
            # Duvara hizala
            self.pacman["x"] = current_grid[0] * BLOCK_SIZE + BLOCK_SIZE // 2
            self.pacman["y"] = current_grid[1] * BLOCK_SIZE + BLOCK_SIZE // 2

        # Tünel geçişleri
        if self.pacman["x"] < 0:
            self.pacman["x"] = WIDTH
        elif self.pacman["x"] > WIDTH:
            self.pacman["x"] = 0

    def move_ghost(self, ghost):
        target = (self.pacman["x"], self.pacman["y"])

        if ghost["type"] == "blinky":
            target = (self.pacman["x"], self.pacman["y"])
        elif ghost["type"] == "pinky":
            target = (self.pacman["x"] + self.pacman["dir"][0] * 4 * BLOCK_SIZE,
                      self.pacman["y"] + self.pacman["dir"][1] * 4 * BLOCK_SIZE)
        elif ghost["type"] == "inky":
            pass
        elif ghost["type"] == "clyde":
            distance = math.hypot(ghost["x"] - self.pacman["x"], ghost["y"] - self.pacman["y"])
            if distance > 8 * BLOCK_SIZE:
                target = (self.pacman["x"], self.pacman["y"])
            else:
                target = (0, GRID_HEIGHT)

        best_dir = (0, 0)
        min_dist = float("inf")

        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            if (dx, dy) != (-ghost["dir"][0], -ghost["dir"][1]):
                new_x = ghost["x"] + dx * ghost["speed"]
                new_y = ghost["y"] + dy * ghost["speed"]
                dist = math.hypot(new_x - target[0], new_y - target[1])
                if dist < min_dist and self.can_move(ghost["x"] // BLOCK_SIZE, ghost["y"] // BLOCK_SIZE, dx, dy):
                    min_dist = dist
                    best_dir = (dx, dy)

        ghost["dir"] = best_dir
        ghost["x"] += ghost["dir"][0] * ghost["speed"]
        ghost["y"] += ghost["dir"][1] * ghost["speed"]

        if ghost["x"] < 0:
            ghost["x"] = WIDTH
        elif ghost["x"] > WIDTH:
            ghost["x"] = 0

    def check_collisions(self):
        px = self.pacman["x"] // BLOCK_SIZE
        py = self.pacman["y"] // BLOCK_SIZE

        if (px, py) in self.pellets:
            self.pellets.remove((px, py))
            self.score += 10
            eat_sound.play()

        if (px, py) in self.power_pellets:
            self.power_pellets.remove((px, py))
            self.power_time = 30 * 5
            self.score += 50
            power_sound.play()

        for ghost in self.ghosts:
            if abs(ghost["x"] - self.pacman["x"]) < BLOCK_SIZE // 2 and \
                    abs(ghost["y"] - self.pacman["y"]) < BLOCK_SIZE // 2:
                if self.power_time > 0:
                    ghost["x"] = 9 * BLOCK_SIZE
                    ghost["y"] = 10 * BLOCK_SIZE
                    self.score += 200
                else:
                    self.lives -= 1
                    death_sound.play()
                    if self.lives <= 0:
                        self.running = False
                    else:
                        self.reset_positions()

    def reset_positions(self):
        self.pacman["x"] = 10 * BLOCK_SIZE + BLOCK_SIZE // 2
        self.pacman["y"] = 14 * BLOCK_SIZE + BLOCK_SIZE // 2
        self.pacman["dir"] = (0, 0)
        self.pacman["next_dir"] = (0, 0)

        positions = [(9, 8), (9, 10), (8, 10), (10, 10)]
        for ghost, pos in zip(self.ghosts, positions):
            ghost["x"] = pos[0] * BLOCK_SIZE
            ghost["y"] = pos[1] * BLOCK_SIZE

    def draw_pacman(self):
        angle = 30 * math.sin(math.radians(self.pacman["mouth_angle"]))
        start_angle = math.radians(angle)
        end_angle = math.radians(360 - angle)

        pygame.draw.circle(self.screen, COLORS["YELLOW"],
                           (int(self.pacman["x"]), int(self.pacman["y"])),
                           BLOCK_SIZE // 2)

        points = [
            (self.pacman["x"], self.pacman["y"]),
            (self.pacman["x"] + BLOCK_SIZE // 2 * math.cos(start_angle),
             self.pacman["y"] + BLOCK_SIZE // 2 * math.sin(start_angle)),
            (self.pacman["x"] + BLOCK_SIZE // 2 * math.cos(end_angle),
             self.pacman["y"] + BLOCK_SIZE // 2 * math.sin(end_angle))
        ]
        pygame.draw.polygon(self.screen, COLORS["BLACK"], points)

    def run(self):
        while self.running:
            self.screen.fill(COLORS["BLACK"])

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.pacman["next_dir"] = (0, -1)
                    elif event.key == pygame.K_DOWN:
                        self.pacman["next_dir"] = (0, 1)
                    elif event.key == pygame.K_LEFT:
                        self.pacman["next_dir"] = (-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        self.pacman["next_dir"] = (1, 0)

            self.move_pacman()
            for ghost in self.ghosts:
                self.move_ghost(ghost)
            self.check_collisions()

            # Çizimler
            for y in range(GRID_HEIGHT):
                for x in range(GRID_WIDTH):
                    if (x, y) in self.walls:
                        pygame.draw.rect(self.screen, COLORS["BLUE"],
                                         (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
                    elif (x, y) in self.pellets:
                        pygame.draw.circle(self.screen, COLORS["WHITE"],
                                           (x * BLOCK_SIZE + BLOCK_SIZE // 2,
                                            y * BLOCK_SIZE + BLOCK_SIZE // 2), 2)
                    elif (x, y) in self.power_pellets:
                        pygame.draw.circle(self.screen, COLORS["WHITE"],
                                           (x * BLOCK_SIZE + BLOCK_SIZE // 2,
                                            y * BLOCK_SIZE + BLOCK_SIZE // 2), 5)

            self.draw_pacman()

            for ghost in self.ghosts:
                pygame.draw.circle(self.screen, COLORS[ghost["color"]],
                                   (int(ghost["x"]), int(ghost["y"])), BLOCK_SIZE // 2)
                eye_dir = self.pacman["dir"] if self.power_time <= 0 else (0, -1)
                pygame.draw.circle(self.screen, COLORS["WHITE"],
                                   (int(ghost["x"]) + eye_dir[0] * 5,
                                    int(ghost["y"]) + eye_dir[1] * 5), 4)

            font = pygame.font.Font(None, 36)
            text = font.render(f"Skor: {self.score}  Can: {'♥' * self.lives}", True, COLORS["WHITE"])
            self.screen.blit(text, (10, HEIGHT - 40))

            pygame.display.flip()
            self.clock.tick(30)
            self.pacman["mouth_angle"] += 5
            self.power_time = max(0, self.power_time - 1)

        pygame.quit()


if __name__ == "__main__":
    game = PacmanGame()
    game.run()