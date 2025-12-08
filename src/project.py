import pygame
import sys
import random

pygame.init()

# Window size
WIDTH, HEIGHT = 800, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Platformer Final Project")

clock = pygame.time.Clock()
FPS = 60

# --- DAMAGE EFFECTS GLOBALS ---
screen_shake = 0
shake_intensity = 8

red_flash_alpha = 0
RED_FLASH_MAX = 140

# Particle list for enemy hit bursts
particles = []

# ---------------- MAIN MENU ----------------
def main_menu():
    # Load background + title images
    bg = pygame.image.load("assets/Screens/mainMenu.png").convert()
    bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))

    title_img = pygame.image.load("assets/Titles/mainMenu_Title.png").convert_alpha()

    try:
        instr_font = pygame.font.Font("assets/pixel_font.ttf", 36)
    except:
        instr_font = pygame.font.SysFont(None, 36)

    instr_text = instr_font.render("Press ENTER to Start", True, (255, 255, 255))

    waiting = True
    while waiting:
        screen.blit(bg, (0, 0))
        screen.blit(title_img, (WIDTH - title_img.get_width() - 20, 20))
        screen.blit(instr_text, (WIDTH//2 - instr_text.get_width()//2, HEIGHT//2 + 120))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                waiting = False

    # Fade in transition
    fade = pygame.Surface((WIDTH, HEIGHT))
    fade.fill((0, 0, 0))
    for alpha in range(255, -1, -15):
        fade.set_alpha(alpha)
        screen.blit(bg, (0, 0))
        screen.blit(fade, (0, 0))
        pygame.display.flip()
        pygame.time.wait(30)

main_menu()

# World size
LEVEL_WIDTH = 3000
LEVEL_HEIGHT = 480

# ---------------- PLAYER ----------------
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 60))
        self.normal_color = (50, 180, 255)
        self.attack_color = (180, 0, 255)
        self.dead_color = (120, 120, 120)
        self.image.fill(self.normal_color)
        self.rect = self.image.get_rect(topleft=(x, y))

        self.vel_y = 0
        self.speed = 5
        self.jump_power = -15

        self.on_ground = False
        self.jump_count = 0
        self.space_was_pressed = False

        self.health = 3

        self.is_attacking = False
        self.attack_timer = 0
        self.attack_cooldown = 200

        self.invincible = False
        self.invincible_timer = 0
        self.knockback_timer = 0
        self.knockback_dir = 0

        self.dead = False
        self.death_timer = 0

    def handle_input(self):
        if self.dead:
            return
        keys = pygame.key.get_pressed()
        if self.knockback_timer <= 0:
            if keys[pygame.K_LEFT]:
                self.rect.x -= self.speed
            if keys[pygame.K_RIGHT]:
                self.rect.x += self.speed
        else:
            self.rect.x += 10 * self.knockback_dir

        space_pressed = keys[pygame.K_SPACE]
        if space_pressed and not self.space_was_pressed:
            if self.on_ground:
                self.vel_y = self.jump_power
                self.on_ground = False
                self.jump_count = 1
            elif self.jump_count == 1:
                self.vel_y = self.jump_power
                self.jump_count = 2
        self.space_was_pressed = space_pressed

        if keys[pygame.K_x] and not self.is_attacking:
            self.is_attacking = True
            self.attack_timer = pygame.time.get_ticks()

    def take_damage(self, source_x):
        global screen_shake, red_flash_alpha
        if self.invincible or self.dead:
            return
        self.health -= 1
        self.invincible = True
        self.invincible_timer = 90
        self.knockback_dir = -1 if source_x > self.rect.centerx else 1
        self.knockback_timer = 18
        screen_shake = 14
        red_flash_alpha = RED_FLASH_MAX
        if self.health <= 0:
            self.dead = True
            self.death_timer = 60

    def apply_gravity(self):
        self.vel_y += 0.7
        self.rect.y += self.vel_y

    def update(self, platforms):
        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False

        if self.knockback_timer > 0:
            self.knockback_timer -= 1

        if self.dead:
            self.image.fill(self.dead_color)
            self.vel_y += 1.0
            self.rect.y += self.vel_y
            self.death_timer -= 1
            if self.death_timer <= 0:
                game_over()
            return

        self.handle_input()
        self.apply_gravity()
        self.on_ground = False

        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                    self.jump_count = 0

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > LEVEL_WIDTH:
            self.rect.right = LEVEL_WIDTH

        if self.is_attacking:
            if pygame.time.get_ticks() - self.attack_timer > self.attack_cooldown:
                self.is_attacking = False

        if self.is_attacking:
            self.image.fill(self.attack_color)
        else:
            if self.invincible and (pygame.time.get_ticks() // 120) % 2 == 0:
                self.image.fill((120, 140, 180))
            else:
                self.image.fill(self.normal_color)

# ---------------- PLATFORM ----------------
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill((120, 80, 40))
        self.rect = self.image.get_rect(topleft=(x, y))

# ---------------- ENEMY ----------------
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, patrol_width=100, speed=2):
        super().__init__()
        self.image = pygame.Surface((40, 40))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.start_x = x
        self.patrol_width = patrol_width
        self.speed = speed
        self.direction = 1
        self.dead_anim = 0

    def update(self):
        if self.dead_anim > 0:
            self.dead_anim -= 1
            self.rect.y += 2
            return
        self.rect.x += self.speed * self.direction
        if self.rect.x > self.start_x + self.patrol_width or self.rect.x < self.start_x:
            self.direction *= -1

    def flash_and_kill(self):
        for _ in range(12):
            vx = random.uniform(-4, 4)
            vy = random.uniform(-4, -1)
            particles.append({
                "x": self.rect.centerx,
                "y": self.rect.centery,
                "vx": vx,
                "vy": vy,
                "life": random.randint(20, 35),
                "size": random.randint(2, 5)
            })
        self.dead_anim = 1

# ---------------- COLLECTIBLE ----------------
class Collectible(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill((255, 255, 0))
        self.rect = self.image.get_rect(topleft=(x, y))

# ---------------- VICTORY BLOCK ----------------
class VictoryBlock(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()

        # Load victory gate sprite
        self.image = pygame.image.load("assets/interactibles/victory_Gate.png").convert_alpha()
        self.rect = self.image.get_rect(topleft=(x, y))

# ---------------- SCENE FUNCTIONS ----------------
def game_over():
    bg = pygame.image.load("assets/Screens/gameOver.png").convert()
    bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
    title_img = pygame.image.load("assets/Titles/gameOver_Title.png").convert_alpha()
    font_small = pygame.font.SysFont(None, 36)
    retry = font_small.render("Press R to Retry", True, (255, 255, 255))
    exit_game = font_small.render("Press Q to Exit", True, (255, 255, 255))
    running = True
    while running:
        screen.blit(bg, (0, 0))
        screen.blit(title_img, (WIDTH//2 - title_img.get_width()//2, 40))
        screen.blit(retry, (WIDTH//2 - retry.get_width()//2, HEIGHT//2))
        screen.blit(exit_game, (WIDTH//2 - exit_game.get_width()//2, HEIGHT//2 + 40))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset_game()
                    return
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

def victory_screen():
    bg = pygame.image.load("assets/Screens/Victory.png").convert()
    bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))

    title_img = pygame.image.load("assets/Titles/Victory_Title.png").convert_alpha()

    font_small = pygame.font.SysFont(None, 36)
    restart = font_small.render("Press R to Restart", True, (255, 255, 255))
    exit_game = font_small.render("Press Q to Exit", True, (255, 255, 255))

    waiting = True
    while waiting:
        screen.blit(bg, (0, 0))

        # Center VICTORY title image at top
        screen.blit(title_img, (WIDTH//2 - title_img.get_width()//2, 40))

        # Buttons
        screen.blit(restart, (WIDTH//2 - restart.get_width()//2, HEIGHT//2))
        screen.blit(exit_game, (WIDTH//2 - exit_game.get_width()//2, HEIGHT//2 + 40))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset_game()
                    waiting = False
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

# ---------------- RESET GAME ----------------
def reset_game():
    global collected_count, particles, screen_shake, red_flash_alpha
    player.rect.topleft = (100, 300)
    player.health = 3
    player.vel_y = 0
    player.jump_count = 0
    player.invincible = False
    player.invincible_timer = 0
    player.knockback_timer = 0
    player.dead = False
    player.death_timer = 0
    player.is_attacking = False

    enemies.empty()
    enemies.add(Enemy(600, 400, 200))
    enemies.add(Enemy(1500, 300, 150))
    enemies.add(Enemy(2400, 320, 100))

    collectibles.empty()
    for pos in collectible_positions:
        collectibles.add(Collectible(*pos))

    collected_count = 0
    particles = []
    screen_shake = 0
    red_flash_alpha = 0

# ---------------- CREATE WORLD ----------------
player = Player(100, 300)

platforms = pygame.sprite.Group()
platform_data = [
    (0, 440, 3000, 40),             # Ground

    # Section 1
    (350, 330, 150, 20),
    
    # Section 2
    (700, 300, 130, 20), 
    (900, 240, 130, 20),

    # Section 3 (Skeleton Gauntlet)
    (1300, 260, 250, 20), 
    (1600, 200, 180, 20),

    # Section 4 (Final Stretch)
    (2100, 320, 220, 20), 
    (2400, 280, 150, 20),
]

for p in platform_data:
    platforms.add(Platform(*p))

enemies = pygame.sprite.Group()

# Section 1 enemy
enemies.add(Enemy(360, 290, patrol_width=80, speed=2))  

# Section 2 enemy guarding the jump gap * second
enemies.add(Enemy(890, 200, patrol_width=100, speed=2))

# Section 3 – Skeleton Gauntlet * third
enemies.add(Enemy(1350, 220, patrol_width=160, speed=2))
enemies.add(Enemy(1590, 160, patrol_width=120, speed=2.4))

# Section 4 – last enemy before gate * fourth
enemies.add(Enemy(2120, 280, patrol_width=150, speed=3))


collectible_positions = [
    (390, 300),    # Section 1 platform

    (930, 210),    # Section 2 – higher platform

    (1350, 230),   # Section 3 – left side
    (1550, 170),   # Section 3 – upper platform collectible

    (2450, 250),   # Section 4 – final collectible
]


collectibles = pygame.sprite.Group()
for pos in collectible_positions:
    collectibles.add(Collectible(*pos))

collected_count = 0

victory_block = VictoryBlock(2800, 360)

# ---------------- LOAD DUNGEON BACKGROUND ----------------
dungeon_bg = pygame.image.load("assets/background/map_Background_.png").convert()
dungeon_bg = pygame.transform.scale(dungeon_bg, (LEVEL_WIDTH, LEVEL_HEIGHT))

# ---------------- CAMERA ----------------
def get_camera_offset(shake_x=0, shake_y=0):
    camera_x = player.rect.centerx - WIDTH // 2
    camera_x = max(0, min(camera_x, LEVEL_WIDTH - WIDTH))
    return camera_x + shake_x, 0 + shake_y

# ---------------- MAIN GAME LOOP ----------------
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Update
    player.update(platforms)
    enemies.update()

    hit_list = pygame.sprite.spritecollide(player, collectibles, True)
    if hit_list:
        collected_count += len(hit_list)

    for enemy in enemies.copy():
        if player.is_attacking:
            attack_range = pygame.Rect(0, 0, 50, 40)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                attack_range.topleft = (player.rect.left - 50, player.rect.centery - 20)
            else:
                attack_range.topleft = (player.rect.right, player.rect.centery - 20)
            if attack_range.colliderect(enemy.rect):
                for _ in range(12):
                    particles.append({
                        "x": enemy.rect.centerx + random.uniform(-8,8),
                        "y": enemy.rect.centery + random.uniform(-8,8),
                        "vx": random.uniform(-4, 4),
                        "vy": random.uniform(-6, -1),
                        "life": random.randint(20, 40),
                        "size": random.randint(2, 5)
                    })
                enemies.remove(enemy)
                continue

        if player.rect.colliderect(enemy.rect) and not player.invincible and not player.is_attacking:
            player.take_damage(enemy.rect.centerx)

    if player.rect.colliderect(victory_block.rect) and collected_count == len(collectible_positions):
        victory_screen()

    if screen_shake > 0:
        screen_shake -= 1

    for p in particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.15
        p["life"] -= 1
        p["vx"] *= 0.99
        if p["life"] <= 0:
            particles.remove(p)

    shake_x = 0
    shake_y = 0
    if screen_shake > 0:
        shake_x = random.randint(-shake_intensity, shake_intensity)
        shake_y = random.randint(-shake_intensity//2, shake_intensity//2)
    camera_x, camera_y = get_camera_offset(shake_x, shake_y)

    # ---------------- DRAW ----------------
    # Parallax background (moves slower)
    parallax_x = -camera_x * 0.5
    screen.blit(dungeon_bg, (parallax_x, -camera_y))

    for platform in platforms:
        screen.blit(platform.image, (platform.rect.x - camera_x + shake_x, platform.rect.y - camera_y + shake_y))
    for enemy in enemies:
        screen.blit(enemy.image, (enemy.rect.x - camera_x + shake_x, enemy.rect.y - camera_y + shake_y))
    for c in collectibles:
        screen.blit(c.image, (c.rect.x - camera_x + shake_x, c.rect.y - camera_y + shake_y))
    screen.blit(victory_block.image, (victory_block.rect.x - camera_x + shake_x, victory_block.rect.y - camera_y + shake_y))
    screen.blit(player.image, (player.rect.x - camera_x + shake_x, player.rect.y - camera_y + shake_y))

    for p in particles:
        alpha = max(0, min(255, int(255 * (p["life"] / 40))))
        surf = pygame.Surface((p["size"], p["size"]), pygame.SRCALPHA)
        surf.fill((255, 255, 255, alpha))
        screen.blit(surf, (p["x"] - camera_x + shake_x, p["y"] - camera_y + shake_y))

    if red_flash_alpha > 0:
        flash_surface = pygame.Surface((WIDTH, HEIGHT))
        flash_surface.fill((255, 0, 0))
        flash_surface.set_alpha(int(red_flash_alpha))
        screen.blit(flash_surface, (0, 0))
        red_flash_alpha = max(0, red_flash_alpha - 6)

    heart_size = 18
    heart_gap = 6
    for i in range(3):
        x = 10 + i * (heart_size + heart_gap)
        y = 10
        color = (220, 20, 60) if i < player.health else (80, 80, 80)
        pygame.draw.rect(screen, color, (x, y, heart_size, heart_size), 0, border_radius=4)

    key_size = 18
    key_gap = 6
    for i in range(len(collectible_positions)):
        x = 10 + i * (key_size + key_gap)
        y = 40
        color = (255, 215, 0) if i < collected_count else (120, 120, 60)
        pygame.draw.rect(screen, color, (x, y, key_size, key_size), 0, border_radius=4)

    pygame.display.flip()
    clock.tick(FPS)
