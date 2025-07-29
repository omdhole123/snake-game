import pygame
import sys
import random
import math

# === Initialization ===
pygame.init()
WIDTH, HEIGHT = 640, 480
CELL_SIZE     = 30
SCALE_FACTOR  = 1.25
SCALED_SIZE   = int(CELL_SIZE * SCALE_FACTOR)

screen     = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Game – Heart Particle Animation")
clock      = pygame.time.Clock()
BASE_SPEED = 12
SPEED      = max(1, BASE_SPEED - 5)

# === Colors & Font ===
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
font  = pygame.font.SysFont("arial", 24);

# === Load & Scale Sprites ===
head_img   = pygame.image.load("assets/snake_head.png").convert_alpha()
tail_img   = pygame.image.load("assets/snake_tail.png").convert_alpha()
apple_img  = pygame.image.load("assets/apple.png").convert_alpha()
heart_img  = pygame.image.load("assets/heart.png").convert_alpha()

head_img   = pygame.transform.scale(head_img,  (SCALED_SIZE, SCALED_SIZE))
tail_img   = pygame.transform.scale(tail_img,  (SCALED_SIZE, SCALED_SIZE))
apple_img  = pygame.transform.scale(apple_img, (SCALED_SIZE, SCALED_SIZE))
heart_img  = pygame.transform.scale(heart_img, (CELL_SIZE, CELL_SIZE))

# === Utility Functions ===
def get_random_food():
    x = random.randint(0, WIDTH  - CELL_SIZE) // CELL_SIZE * CELL_SIZE
    y = random.randint(0, HEIGHT - CELL_SIZE) // CELL_SIZE * CELL_SIZE
    return pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

# === Game Setup ===
snake       = [pygame.Rect(100, 100, CELL_SIZE, CELL_SIZE)]
direction   = pygame.Vector2(CELL_SIZE, 0)
food        = get_random_food()
score       = 0

# particles for heart animation
hearts      = []
HEART_LIFE  = 30  # frames

# === Main Loop ===
while True:
    # Input
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP    and direction.y == 0:
                direction = pygame.Vector2(0, -CELL_SIZE)
            elif event.key == pygame.K_DOWN  and direction.y == 0:
                direction = pygame.Vector2(0,  CELL_SIZE)
            elif event.key == pygame.K_LEFT  and direction.x == 0:
                direction = pygame.Vector2(-CELL_SIZE, 0)
            elif event.key == pygame.K_RIGHT and direction.x == 0:
                direction = pygame.Vector2( CELL_SIZE, 0)

    # Move snake
    new_head = snake[0].copy()
    new_head.move_ip(direction.x, direction.y)
    snake.insert(0, new_head)

    # Eat & spawn hearts
    if new_head.colliderect(food):
        score += 1
        cx = food.left + CELL_SIZE // 2
        cy = food.top  + CELL_SIZE // 2
        # spawn a burst of heart particles
        for _ in range(12):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1.5, 3.5)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            hearts.append({
                'x': cx, 'y': cy,
                'vx': vx, 'vy': vy,
                't': 0
            })
        food = get_random_food()
    else:
        snake.pop()

    # Collision
    if (new_head.left < 0 or new_head.top < 0
        or new_head.right > WIDTH or new_head.bottom > HEIGHT
        or new_head in snake[1:]):
        pygame.quit()
        sys.exit()

    # Draw
    screen.fill(BLACK)
    offset = (SCALED_SIZE - CELL_SIZE) // 2

    # apple
    screen.blit(apple_img, (food.left - offset, food.top - offset))

    # snake: head + body as heart_img
    for idx, segment in enumerate(snake):
        px = segment.left - offset
        py = segment.top  - offset
        if idx == 0:
            screen.blit(head_img, (px, py))
        else:
            prev = snake[idx - 1]
            dx, dy = prev.left - segment.left, prev.top - segment.top
            if dx > 0:   angle = 270
            elif dx < 0: angle = 90
            elif dy > 0: angle = 0
            else:        angle = 180
            img = pygame.transform.rotate(tail_img, angle)
            screen.blit(img, (px, py))

    # heart particles animation
    for heart in hearts[:]:
        heart['t'] += 1
        if heart['t'] > HEART_LIFE:
            hearts.remove(heart)
            continue
        # update position
        heart['x'] += heart['vx']
        heart['y'] += heart['vy']
        # fade out & scale up
        life_ratio = heart['t'] / HEART_LIFE
        alpha = max(255 * (1 - life_ratio), 0)
        scale = 1 + life_ratio  # grow over time
        img = pygame.transform.rotozoom(heart_img, 0, scale)
        img.set_alpha(int(alpha))
        hw, hh = img.get_width() // 2, img.get_height() // 2
        screen.blit(img, (heart['x'] - hw, heart['y'] - hh))

    # score
    sc = font.render(f"PAISE: {score}", True, WHITE)
    screen.blit(sc, (10, 10))

    pygame.display.flip()
    clock.tick(SPEED)
