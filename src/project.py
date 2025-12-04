import pygame
import sys

pygame.init()

# Window size
WIDTH, HEIGHT = 800, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Platformer Final Project")

clock = pygame.time.Clock()
FPS = 60

# --- MAIN MENU FUNCTION ---
def main_menu():
    # Load a pixel-style font (or default if unavailable)
    try:
        title_font = pygame.font.Font("assets/pixel_font.ttf", 72)
        instr_font = pygame.font.Font("assets/pixel_font.ttf", 36)
    except:
        title_font = pygame.font.SysFont(None, 72)
        instr_font = pygame.font.SysFont(None, 36)

    title_text = title_font.render("Knights and Dungeons", True, (255, 255, 255))
    instr_text = instr_font.render("Press ENTER to Start", True, (255, 255, 255))

    waiting = True
    while waiting:
        screen.fill((0, 0, 0))
        screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//2 - 80))
        screen.blit(instr_text, (WIDTH//2 - instr_text.get_width()//2, HEIGHT//2 + 40))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    waiting = False

    # Fade-in effect
    fade = pygame.Surface((WIDTH, HEIGHT))
    fade.fill((0, 0, 0))
    for alpha in range(255, -1, -15):
        fade.set_alpha(alpha)
        screen.fill((20, 20, 30))
        screen.blit(fade, (0, 0))
        pygame.display.flip()
        pygame.time.delay(30)

main_menu()

# World size
LEVEL_WIDTH = 3000
LEVEL_HEIGHT = 480

# --- PLAYER CLASS ---
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 60))
        self.image.fill((50, 180, 255))
        self.rect = self.image.get_rect(topleft=(x, y))

        self.vel_y = 0
        self.speed = 5
        self.jump_power = -15

        self.on_ground = False
        self.jump_count = 0
        self.space_was_pressed = False

        self.health = 3

    def handle_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed

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

    def apply_gravity(self):
        self.vel_y += 0.7
        self.rect.y += self.vel_y

    def update(self, platforms):
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

# --- PLATFORM CLASS ---
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill((120, 80, 40))
        self.rect = self.image.get_rect(topleft=(x, y))

# --- ENEMY CLASS ---
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

    def update(self):
        self.rect.x += self.speed * self.direction
        if self.rect.x > self.start_x + self.patrol_width or self.rect.x < self.start_x:
            self.direction *= -1

# --- GOAL CLASS ---
class Goal(pygame.sprite.Sprite):
    def __init__(self, x, y, w=40, h=40):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill((0, 255, 0))
        self.rect = self.image.get_rect(topleft=(x, y))

# Create player, platforms, enemies, and goal
player = Player(100, 300)

platforms = pygame.sprite.Group()
platform_data = [
    (0, 440, 3000, 40),
    (200, 350, 120, 20),
    (450, 300, 150, 20),
    (800, 250, 120, 20),
    (1100, 200, 150, 20),
    (1400, 330, 120, 20),
    (1700, 280, 120, 20),
    (2000, 220, 180, 20),
    (2300, 350, 120, 20),
    (2600, 300, 150, 20)
]
for p in platform_data:
    platforms.add(Platform(*p))

enemies = pygame.sprite.Group()
enemies.add(Enemy(600, 400, patrol_width=200))
enemies.add(Enemy(1500, 300, patrol_width=150))
enemies.add(Enemy(2400, 320, patrol_width=100))

goal = Goal(LEVEL_WIDTH - 100, 400)

# CAMERA FUNCTION
def get_camera_offset():
    camera_x = player.rect.centerx - WIDTH // 2
    camera_x = max(0, min(camera_x, LEVEL_WIDTH - WIDTH))
    return camera_x

# --- GAME OVER SCREEN ---
def game_over():
    font = pygame.font.SysFont(None, 72)
    text = font.render("GAME OVER", True, (255, 0, 0))
    subtext_retry = pygame.font.SysFont(None, 36).render("Press R to Retry", True, (255, 255, 255))
    subtext_exit = pygame.font.SysFont(None, 36).render("Press Q to Exit", True, (255, 255, 255))
    
    running = True
    while running:
        screen.fill((0, 0, 0))
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - text.get_height()//2 - 30))
        screen.blit(subtext_retry, (WIDTH//2 - subtext_retry.get_width()//2, HEIGHT//2 + 10))
        screen.blit(subtext_exit, (WIDTH//2 - subtext_exit.get_width()//2, HEIGHT//2 + 50))
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Reset game
                    player.rect.topleft = (100, 300)
                    player.health = 3
                    player.vel_y = 0
                    player.jump_count = 0
                    enemies.empty()
                    enemies.add(Enemy(600, 400, patrol_width=200))
                    enemies.add(Enemy(1500, 300, patrol_width=150))
                    enemies.add(Enemy(2400, 320, patrol_width=100))
                    running = False
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

# --- VICTORY SCREEN ---
def victory_screen():
    font = pygame.font.SysFont(None, 72)
    small_font = pygame.font.SysFont(None, 36)
    title_text = font.render("Victory!", True, (0, 255, 0))
    restart_text = small_font.render("Press R to Restart", True, (255, 255, 255))
    exit_text = small_font.render("Press Q to Exit", True, (255, 255, 255))

    waiting = True
    while waiting:
        screen.fill((0, 0, 0))
        screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//2 - 80))
        screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 10))
        screen.blit(exit_text, (WIDTH//2 - exit_text.get_width()//2, HEIGHT//2 + 50))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Reset game
                    player.rect.topleft = (100, 300)
                    player.health = 3
                    player.vel_y = 0
                    player.jump_count = 0
                    enemies.empty()
                    enemies.add(Enemy(600, 400, patrol_width=200))
                    enemies.add(Enemy(1500, 300, patrol_width=150))
                    enemies.add(Enemy(2400, 320, patrol_width=100))
                    waiting = False
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

# --- GAME LOOP ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Update
    player.update(platforms)
    enemies.update()

    # Collisions with enemies
    if pygame.sprite.spritecollide(player, enemies, False):
        player.health -= 1
        player.rect.x -= 50
        if player.health <= 0:
            game_over()

    # Collision with goal
    if player.rect.colliderect(goal.rect):
        victory_screen()

    # Camera offset
    camera_x = get_camera_offset()

    # Draw
    screen.fill((20, 20, 30))
    for platform in platforms:
        screen.blit(platform.image, (platform.rect.x - camera_x, platform.rect.y))
    for enemy in enemies:
        screen.blit(enemy.image, (enemy.rect.x - camera_x, enemy.rect.y))
    screen.blit(player.image, (player.rect.x - camera_x, player.rect.y))
    screen.blit(goal.image, (goal.rect.x - camera_x, goal.rect.y))

    # Draw health
    font = pygame.font.SysFont(None, 36)
    health_text = font.render(f"Health: {player.health}", True, (255, 255, 255))
    screen.blit(health_text, (10, 10))

    pygame.display.flip()
    clock.tick(FPS)
