import pygame
import sys

pygame.init()

# Window size
WIDTH, HEIGHT = 800, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Platformer Final Project")

clock = pygame.time.Clock()
FPS = 60

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
        self.jump_count = 0        # 0 = no jumps yet, 1 = jumped once, 2 = double jump used
        self.space_was_pressed = False  # tracks tap vs hold

    def handle_input(self):
        keys = pygame.key.get_pressed()

        # Movement
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed

        # ---- JUMP INPUT LOGIC ----
        space_pressed = keys[pygame.K_SPACE]

        if space_pressed and not self.space_was_pressed:  
            # This triggers ONCE per space bar tap
            if self.on_ground:
                # Normal jump
                self.vel_y = self.jump_power
                self.on_ground = False
                self.jump_count = 1
            elif self.jump_count == 1:
                # Double jump
                self.vel_y = self.jump_power
                self.jump_count = 2

        # Update tracking of key press (for edge detection)
        self.space_was_pressed = space_pressed

    def apply_gravity(self):
        self.vel_y += 0.7
        self.rect.y += self.vel_y

    def update(self, platforms):
        self.handle_input()
        self.apply_gravity()

        self.on_ground = False

        # Landing on Platforms
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0:  
                    # Land on platform
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                    self.jump_count = 0  # reset jumps

        # Keep inside world
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


# Create player
player = Player(100, 300)

# Platform group
platforms = pygame.sprite.Group()

# --- LEVEL DESIGN ---
platform_data = [
    (0, 440, 3000, 40),      # long ground
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


# CAMERA FUNCTION
def get_camera_offset():
    """Camera centers the player on screen while respecting world boundaries."""
    camera_x = player.rect.centerx - WIDTH // 2

    # Keep camera inside world
    camera_x = max(0, min(camera_x, LEVEL_WIDTH - WIDTH))
    return camera_x


# --- GAME LOOP ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Update
    player.update(platforms)

    # Camera offset
    camera_x = get_camera_offset()

    # Draw
    screen.fill((20, 20, 30))

    # Draw platforms with camera shift
    for platform in platforms:
        screen.blit(platform.image, (platform.rect.x - camera_x, platform.rect.y))

    # Draw player with camera shift
    screen.blit(player.image, (player.rect.x - camera_x, player.rect.y))

    pygame.display.flip()
    clock.tick(FPS)
