import pygame
import sys
import random

# === Initialization ===
pygame.init()
WIDTH, HEIGHT = 640, 480
CELL_SIZE = 20
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Game")
clock = pygame.time.Clock()
SPEED = 10

# === Colors ===
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)

# === Snake and Food ===
snake = [pygame.Rect(100, 100, CELL_SIZE, CELL_SIZE)]
direction = pygame.Vector2(CELL_SIZE, 0)

def get_random_food():
    x = random.randint(0, WIDTH - CELL_SIZE) // CELL_SIZE * CELL_SIZE
    y = random.randint(0, HEIGHT - CELL_SIZE) // CELL_SIZE * CELL_SIZE
    return pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

food = get_random_food()

# === Game Loop ===
def game_loop():
    global direction, food
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and direction.y == 0:
                    direction = pygame.Vector2(0, -CELL_SIZE)
                elif event.key == pygame.K_DOWN and direction.y == 0:
                    direction = pygame.Vector2(0, CELL_SIZE)
                elif event.key == pygame.K_LEFT and direction.x == 0:
                    direction = pygame.Vector2(-CELL_SIZE, 0)
                elif event.key == pygame.K_RIGHT and direction.x == 0:
                    direction = pygame.Vector2(CELL_SIZE, 0)

        # Move the snake
        new_head = snake[0].copy()
        new_head.move_ip(direction.x, direction.y)
        snake.insert(0, new_head)

        # Check food collision
        if new_head.colliderect(food):
            food = get_random_food()
        else:
            snake.pop()

        # Collision with walls or self
        if (new_head.left < 0 or new_head.top < 0 or
            new_head.right > WIDTH or new_head.bottom > HEIGHT or
            new_head in snake[1:]):
            pygame.quit()
            sys.exit()

        # Draw everything
        screen.fill(BLACK)
        pygame.draw.rect(screen, RED, food)
        for segment in snake:
            pygame.draw.rect(screen, GREEN, segment)
        pygame.display.flip()
        clock.tick(SPEED)

game_loop()
