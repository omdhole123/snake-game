import os
import random
import time
import pygame
import math
try:
    import turtle
except ImportError:
    turtle = None  # Fallback for non-GUI environments

class SnakeGame:
    def __init__(self):
        # Initialize sound
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.sound_enabled = True
            self.load_sounds()
        except Exception:
            self.sound_enabled = False
            print("Sound unavailable - running in silent mode")

        # Fullscreen state
        self.fullscreen = False

        # Game constants
        self.MOVE_DISTANCE = 20
        self.INITIAL_DELAY = 0.1
        self.BORDER_MARGIN = 10
        self.COLLISION_DISTANCE = 18

        # Fruit types
        self.fruit_types = [
            {'name':'apple','shape':'circle','color':'#ff4444','size':0.8,'stem':True},
            {'name':'orange','shape':'circle','color':'#ffa500','size':0.8,'stem':False},
            {'name':'banana','shape':'triangle','color':'yellow','size':1.0,'stem':False},
            {'name':'grape','shape':'circle','color':'purple','size':0.6,'stem':False}
        ]

        # Game state
        self.score = 0
        self.high_score = 0
        self.delay = self.INITIAL_DELAY
        self.segments = []
        self.game_running = True
        self.paused = False
        self.menu_option = 0

        # Setup game if GUI available
        if turtle:
            self.setup_screen()
            self.create_snake()
            self.create_food()
            self.create_golden_apple()
            self.create_scoreboard()
            self.create_pause_menu()
            self.setup_controls()
            self.max_x = self.screen.window_width()//2 - self.BORDER_MARGIN
            self.max_y = self.screen.window_height()//2 - self.BORDER_MARGIN
            self.food_boundary_x = self.screen.window_width()//2 - 40
            self.food_boundary_y = self.screen.window_height()//2 - 40

    def load_sounds(self):
        self.sounds = {}
        base = os.path.dirname(__file__)
        for key in ['eat','golden','gameover','move']:
            path = os.path.join(base, f"{key}.wav")
            if os.path.exists(path):
                self.sounds[key] = pygame.mixer.Sound(path)
        bg = os.path.join(base, 'background.mp3')
        if os.path.exists(bg):
            pygame.mixer.music.load(bg)
            pygame.mixer.music.set_volume(0.2)
            pygame.mixer.music.play(-1)

    def create_beep_sound(self, freq, dur):
        import io, wave, struct
        sr = 22050
        frames = int(sr*dur)
        buf = io.BytesIO()
        with wave.open(buf,'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            for i in range(frames):
                val = int(16000*math.sin(2*math.pi*freq*i/sr))
                fade = 1 - (i/frames)*0.8
                w.writeframes(struct.pack('<h',int(val*fade)))
        buf.seek(0)
        return pygame.mixer.Sound(buf)

    def setup_screen(self):
        self.screen = turtle.Screen()
        self.screen.title("🐍 Snake Game Deluxe 🐍")
        self.screen.bgcolor("#2d5a27")
        self.screen.setup(width=1.0, height=1.0)
        self.screen.tracer(0)
        self.root = self.screen._root
        self.screen.listen()

    def setup_controls(self):
        bindings = [
            ('Up', self.handle_up), ('Down', self.handle_down),
            ('Left', self.handle_left), ('Right', self.handle_right),
            ('w', self.handle_up), ('s', self.handle_down),
            ('a', self.handle_left), ('d', self.handle_right)
        ]
        for key, func in bindings:
            self.screen.onkey(func, key)
        for key in ['space','p','Escape']:
            self.screen.onkey(self.toggle_pause, key)
        self.screen.onkey(self.menu_select, 'Return')
        self.screen.onkey(self.menu_select, 'space')
        self.screen.onkey(self.toggle_fullscreen, 'F11')

    def handle_up(self):
        if self.paused:
            self.menu_up()
        else:
            self.move_up()

    def handle_down(self):
        if self.paused:
            self.menu_down()
        else:
            self.move_down()

    def handle_left(self):
        if not self.paused:
            self.move_left()

    def handle_right(self):
        if not self.paused:
            self.move_right()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.root.attributes('-fullscreen', self.fullscreen)

    def create_snake(self):
        self.head = turtle.Turtle()
        self.head.speed(0)
        self.head.shape('circle')
        self.head.shapesize(1.2, 1.5)
        self.head.color('#4a7c59')
        self.head.penup()
        self.head.goto(0, 0)
        self.head.direction = 'stop'
        self.create_snake_eyes()

    def create_snake_eyes(self):
        self.left_eye = turtle.Turtle(); self.right_eye = turtle.Turtle()
        for eye in (self.left_eye, self.right_eye):
            eye.speed(0)
            eye.shape('circle')
            eye.shapesize(0.3, 0.3)
            eye.color('white')
            eye.penup()
            eye.hideturtle()
        self.left_pupil = turtle.Turtle(); self.right_pupil = turtle.Turtle()
        for pupil in (self.left_pupil, self.right_pupil):
            pupil.speed(0)
            pupil.shape('circle')
            pupil.shapesize(0.15, 0.15)
            pupil.color('black')
            pupil.penup()
            pupil.hideturtle()
        self.update_eyes()

    def update_eyes(self):
        hx, hy = self.head.position()
        d = self.head.direction
        offsets = {
            'up':    [(-8, 8, -8, 10), (8, 8, 8, 10)],
            'down':  [(-8, -8, -8, -10), (8, -8, 8, -10)],
            'left':  [(-8, 8, -10, 8), (-8, -8, -10, -8)],
            'right': [(8, 8, 10, 8), (8, -8, 10, -8)],
            'stop':  [(-8, 5, -8, 5), (8, 5, 8, 5)]
        }
        o1, o2 = offsets.get(d, offsets['stop'])
        self.left_eye.goto(hx + o1[0], hy + o1[1])
        self.left_pupil.goto(hx + o1[2], hy + o1[3])
        self.right_eye.goto(hx + o2[0], hy + o2[1])
        self.right_pupil.goto(hx + o2[2], hy + o2[3])
        for part in (self.left_eye, self.left_pupil, self.right_eye, self.right_pupil):
            part.showturtle()

    def create_food(self):
        self.food = turtle.Turtle()
        self.food.speed(0)
        self.food.penup()
        self.stem = turtle.Turtle()
        self.stem.speed(0)
        self.stem.shape('square')
        self.stem.color('#8b4513')
        self.stem.shapesize(0.1, 0.3)
        self.stem.penup()
        self.food_type = None

    def spawn_food(self):
        f = random.choice(self.fruit_types)
        self.food_type = f['name']
        self.food.shape(f['shape'])
        self.food.color(f['color'])
        self.food.shapesize(f['size'], f['size'])
        if f['stem']:
            self.stem.showturtle()
        else:
            self.stem.hideturtle()
        while True:
            x = random.randint(-self.food_boundary_x, self.food_boundary_x)
            y = random.randint(-self.food_boundary_y, self.food_boundary_y)
            if not any(abs(x - s.xcor()) < 30 and abs(y - s.ycor()) < 30 for s in [self.head] + self.segments):
                break
        self.food.goto(x, y)
        if f['stem']:
            self.stem.goto(x, y + f['size'] * 10)

    def create_golden_apple(self):
        self.golden_apple = turtle.Turtle()
        self.golden_glow = turtle.Turtle()
        for obj, col, sz in [(self.golden_apple, '#ffd700', 1), (self.golden_glow, '#ffff99', 1.3)]:
            obj.speed(0)
            obj.shape('circle')
            obj.color(col)
            obj.shapesize(sz, sz)
            obj.penup()
            obj.hideturtle()

    def spawn_golden_apple(self):
        if random.randint(1, 15) == 1:
            x = random.randint(-self.food_boundary_x, self.food_boundary_x)
            y = random.randint(-self.food_boundary_y, self.food_boundary_y)
            self.golden_glow.goto(x, y)
            self.golden_glow.showturtle()
            self.golden_apple.goto(x, y)
            self.golden_apple.showturtle()

    def create_scoreboard(self):
        self.scoreboard = turtle.Turtle()
        self.scoreboard.speed(0)
        self.scoreboard.color('white')
        self.scoreboard.penup()
        self.scoreboard.hideturtle()
        self.scoreboard.goto(-self.screen.window_width()//2 + 40, self.screen.window_height()//2 - 60)
        self.update_scoreboard()

    def update_scoreboard(self):
        self.scoreboard.clear()
        self.scoreboard.write(
            f'🐍 Score: {self.score} | 🏆 High Score: {self.high_score}',
            align='left', font=('Courier', 16, 'bold')
        )

    def handle_food_collision(self):
        self.play_sound('eat')
        self.spawn_food()
        self.add_segment()
        points = 10
        if self.food_type == 'orange':
            points = 15
        elif self.food_type == 'banana':
            points = 20
        elif self.food_type == 'grape':
            points = 12
        self.score += points
        if self.score > self.high_score:
            self.high_score = self.score
        self.update_scoreboard()
        self.update_speed()
        self.spawn_golden_apple()

    def handle_golden_apple_collision(self):
        self.play_sound('golden')
        self.golden_apple.hideturtle()
        self.golden_glow.hideturtle()
        self.score += 50
        if self.score > self.high_score:
            self.high_score = self.score
        self.update_scoreboard()

    def add_segment(self):
        seg = turtle.Turtle()
        seg.speed(0)
        seg.shape('circle')
        colors = ['#5d8a66', '#4a7c59', '#3e6b4c', '#5d8a66']
        seg.color(colors[len(self.segments) % 4])
        seg.shapesize(0.9, 0.9)
        seg.penup()
        self.segments.append(seg)

    def update_speed(self):
        if self.score >= 300:
            self.delay = 0.06
        elif self.score >= 200:
            self.delay = 0.07
        elif self.score >= 100:
            self.delay = 0.08
        elif self.score >= 50:
            self.delay = 0.09
        else:
            self.delay = self.INITIAL_DELAY

    def reset_game(self):
        self.play_sound('gameover')
        time.sleep(1)
        self.head.goto(0, 0)
        self.head.direction = 'stop'
        self.update_eyes()
        for seg in self.segments:
            seg.hideturtle()
        self.segments.clear()
        self.golden_apple.hideturtle()
        self.golden_glow.hideturtle()
        self.score = 0
        self.delay = self.INITIAL_DELAY
        self.menu_option = 0
        self.update_scoreboard()

    def check_border_collision(self):
        return abs(self.head.xcor()) > self.max_x or abs(self.head.ycor()) > self.max_y

    def check_self_collision(self):
        return any(self.head.distance(s) < self.COLLISION_DISTANCE for s in self.segments)

    def create_pause_menu(self):
        self.pause_title = turtle.Turtle()
        self.pause_instructions = turtle.Turtle()
        self.menu_options = []
        for obj in (self.pause_title, self.pause_instructions):
            obj.speed(0)
            obj.penup()
            obj.hideturtle()
            obj.color('white')
        for _ in range(3):
            opt = turtle.Turtle()
            opt.speed(0)
            opt.color('white')
            opt.penup()
            opt.hideturtle()
            self.menu_options.append(opt)

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.show_pause_menu()
        else:
            self.hide_pause_menu()

    def show_pause_menu(self):
        self.pause_title.goto(0, 150)
        self.pause_title.write('⏸️ GAME PAUSED ⏸️', align='center', font=('Courier', 24, 'bold'))
        self.pause_instructions.goto(0, 120)
        self.pause_instructions.write(
            'Use ↑↓ or W/S to navigate • Enter/Space to select',
            align='center', font=('Arial', 14, 'normal')
        )
        self.update_pause_menu()

    def hide_pause_menu(self):
        self.pause_title.clear()
        self.pause_instructions.clear()
        for opt in self.menu_options:
            opt.clear()

    def update_pause_menu(self):
        texts = ['Resume', 'Restart', 'Quit']
import random
import time
import pygame
import math
try:
    import turtle
except ImportError:
    turtle = None  # Fallback for non-GUI environments

class SnakeGame:
    def __init__(self):
        # Initialize sound
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.sound_enabled = True
            self.load_sounds()
        except Exception:
            self.sound_enabled = False
            print("Sound unavailable - running in silent mode")

        # Fullscreen state
        self.fullscreen = False

        # Game constants
        self.MOVE_DISTANCE = 20
        self.INITIAL_DELAY = 0.1
        self.BORDER_MARGIN = 10
        self.COLLISION_DISTANCE = 18

        # Fruit types
        self.fruit_types = [
            {'name':'apple','shape':'circle','color':'#ff4444','size':0.8,'stem':True},
            {'name':'orange','shape':'circle','color':'#ffa500','size':0.8,'stem':False},
            {'name':'banana','shape':'triangle','color':'yellow','size':1.0,'stem':False},
            {'name':'grape','shape':'circle','color':'purple','size':0.6,'stem':False}
        ]

        # Game state
        self.score = 0
        self.high_score = 0
        self.delay = self.INITIAL_DELAY
        self.segments = []
        self.game_running = True
        self.paused = False
        self.menu_option = 0

        # Setup game if GUI available
        if turtle:
            self.setup_screen()
            self.create_snake()
            self.create_food()
            self.create_golden_apple()
            self.create_scoreboard()
            self.create_pause_menu()
            self.setup_controls()
            self.max_x = self.screen.window_width()//2 - self.BORDER_MARGIN
            self.max_y = self.screen.window_height()//2 - self.BORDER_MARGIN
            self.food_boundary_x = self.screen.window_width()//2 - 40
            self.food_boundary_y = self.screen.window_height()//2 - 40

    def load_sounds(self):
        self.sounds = {}
        base = os.path.dirname(__file__)
        for key in ['eat','golden','gameover','move']:
            path = os.path.join(base, f"{key}.wav")
            if os.path.exists(path):
                self.sounds[key] = pygame.mixer.Sound(path)
        bg = os.path.join(base, 'background.mp3')
        if os.path.exists(bg):
            pygame.mixer.music.load(bg)
            pygame.mixer.music.set_volume(0.2)
            pygame.mixer.music.play(-1)

    def create_beep_sound(self, freq, dur):
        import io, wave, struct
        sr = 22050
        frames = int(sr*dur)
        buf = io.BytesIO()
        with wave.open(buf,'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            for i in range(frames):
                val = int(16000*math.sin(2*math.pi*freq*i/sr))
                fade = 1 - (i/frames)*0.8
                w.writeframes(struct.pack('<h',int(val*fade)))
        buf.seek(0)
        return pygame.mixer.Sound(buf)

    def setup_screen(self):
        self.screen = turtle.Screen()
        self.screen.title("🐍 Snake Game Deluxe 🐍")
        self.screen.bgcolor("#2d5a27")
        self.screen.setup(width=1.0, height=1.0)
        self.screen.tracer(0)
        self.root = self.screen._root
        self.screen.listen()

    def setup_controls(self):
        bindings = [
            ('Up', self.handle_up), ('Down', self.handle_down),
            ('Left', self.handle_left), ('Right', self.handle_right),
            ('w', self.handle_up), ('s', self.handle_down),
            ('a', self.handle_left), ('d', self.handle_right)
        ]
        for key, func in bindings:
            self.screen.onkey(func, key)
        for key in ['space','p','Escape']:
            self.screen.onkey(self.toggle_pause, key)
        self.screen.onkey(self.menu_select, 'Return')
        self.screen.onkey(self.menu_select, 'space')
        self.screen.onkey(self.toggle_fullscreen, 'F11')

    def handle_up(self):
        if self.paused:
            self.menu_up()
        else:
            self.move_up()

    def handle_down(self):
        if self.paused:
            self.menu_down()
        else:
            self.move_down()

    def handle_left(self):
        if not self.paused:
            self.move_left()

    def handle_right(self):
        if not self.paused:
            self.move_right()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.root.attributes('-fullscreen', self.fullscreen)

    def create_snake(self):
        self.head = turtle.Turtle()
        self.head.speed(0)
        self.head.shape('circle')
        self.head.shapesize(1.2, 1.5)
        self.head.color('#4a7c59')
        self.head.penup()
        self.head.goto(0, 0)
        self.head.direction = 'stop'
        self.create_snake_eyes()

    def create_snake_eyes(self):
        self.left_eye = turtle.Turtle(); self.right_eye = turtle.Turtle()
        for eye in (self.left_eye, self.right_eye):
            eye.speed(0)
            eye.shape('circle')
            eye.shapesize(0.3, 0.3)
            eye.color('white')
            eye.penup()
            eye.hideturtle()
        self.left_pupil = turtle.Turtle(); self.right_pupil = turtle.Turtle()
        for pupil in (self.left_pupil, self.right_pupil):
            pupil.speed(0)
            pupil.shape('circle')
            pupil.shapesize(0.15, 0.15)
            pupil.color('black')
            pupil.penup()
            pupil.hideturtle()
        self.update_eyes()

    def update_eyes(self):
        hx, hy = self.head.position()
        d = self.head.direction
        offsets = {
            'up':    [(-8, 8, -8, 10), (8, 8, 8, 10)],
            'down':  [(-8, -8, -8, -10), (8, -8, 8, -10)],
            'left':  [(-8, 8, -10, 8), (-8, -8, -10, -8)],
            'right': [(8, 8, 10, 8), (8, -8, 10, -8)],
            'stop':  [(-8, 5, -8, 5), (8, 5, 8, 5)]
        }
        o1, o2 = offsets.get(d, offsets['stop'])
        self.left_eye.goto(hx + o1[0], hy + o1[1])
        self.left_pupil.goto(hx + o1[2], hy + o1[3])
        self.right_eye.goto(hx + o2[0], hy + o2[1])
        self.right_pupil.goto(hx + o2[2], hy + o2[3])
        for part in (self.left_eye, self.left_pupil, self.right_eye, self.right_pupil):
            part.showturtle()

    def create_food(self):
        self.food = turtle.Turtle()
        self.food.speed(0)
        self.food.penup()
        self.stem = turtle.Turtle()
        self.stem.speed(0)
        self.stem.shape('square')
        self.stem.color('#8b4513')
        self.stem.shapesize(0.1, 0.3)
        self.stem.penup()
        self.food_type = None

    def spawn_food(self):
        f = random.choice(self.fruit_types)
        self.food_type = f['name']
        self.food.shape(f['shape'])
        self.food.color(f['color'])
        self.food.shapesize(f['size'], f['size'])
        if f['stem']:
            self.stem.showturtle()
        else:
            self.stem.hideturtle()
        while True:
            x = random.randint(-self.food_boundary_x, self.food_boundary_x)
            y = random.randint(-self.food_boundary_y, self.food_boundary_y)
            if not any(abs(x - s.xcor()) < 30 and abs(y - s.ycor()) < 30 for s in [self.head] + self.segments):
                break
        self.food.goto(x, y)
        if f['stem']:
            self.stem.goto(x, y + f['size'] * 10)

    def create_golden_apple(self):
        self.golden_apple = turtle.Turtle()
        self.golden_glow = turtle.Turtle()
        for obj, col, sz in [(self.golden_apple, '#ffd700', 1), (self.golden_glow, '#ffff99', 1.3)]:
            obj.speed(0)
            obj.shape('circle')
            obj.color(col)
            obj.shapesize(sz, sz)
            obj.penup()
            obj.hideturtle()

    def spawn_golden_apple(self):
        if random.randint(1, 15) == 1:
            x = random.randint(-self.food_boundary_x, self.food_boundary_x)
            y = random.randint(-self.food_boundary_y, self.food_boundary_y)
            self.golden_glow.goto(x, y)
            self.golden_glow.showturtle()
            self.golden_apple.goto(x, y)
            self.golden_apple.showturtle()

    def create_scoreboard(self):
        self.scoreboard = turtle.Turtle()
        self.scoreboard.speed(0)
        self.scoreboard.color('white')
        self.scoreboard.penup()
        self.scoreboard.hideturtle()
        self.scoreboard.goto(-self.screen.window_width()//2 + 40, self.screen.window_height()//2 - 60)
        self.update_scoreboard()

    def update_scoreboard(self):
        self.scoreboard.clear()
        self.scoreboard.write(
            f'🐍 Score: {self.score} | 🏆 High Score: {self.high_score}',
            align='left', font=('Courier', 16, 'bold')
        )

    def handle_food_collision(self):
        self.play_sound('eat')
        self.spawn_food()
        self.add_segment()
        points = 10
        if self.food_type == 'orange':
            points = 15
        elif self.food_type == 'banana':
            points = 20
        elif self.food_type == 'grape':
            points = 12
        self.score += points
        if self.score > self.high_score:
            self.high_score = self.score
        self.update_scoreboard()
        self.update_speed()
        self.spawn_golden_apple()

    def handle_golden_apple_collision(self):
        self.play_sound('golden')
        self.golden_apple.hideturtle()
        self.golden_glow.hideturtle()
        self.score += 50
        if self.score > self.high_score:
            self.high_score = self.score
        self.update_scoreboard()

    def add_segment(self):
        seg = turtle.Turtle()
        seg.speed(0)
        seg.shape('circle')
        colors = ['#5d8a66', '#4a7c59', '#3e6b4c', '#5d8a66']
        seg.color(colors[len(self.segments) % 4])
        seg.shapesize(0.9, 0.9)
        seg.penup()
        self.segments.append(seg)

    def update_speed(self):
        if self.score >= 300:
            self.delay = 0.06
        elif self.score >= 200:
            self.delay = 0.07
        elif self.score >= 100:
            self.delay = 0.08
        elif self.score >= 50:
            self.delay = 0.09
        else:
            self.delay = self.INITIAL_DELAY

    def reset_game(self):
        self.play_sound('gameover')
        time.sleep(1)
        self.head.goto(0, 0)
        self.head.direction = 'stop'
        self.update_eyes()
        for seg in self.segments:
            seg.hideturtle()
        self.segments.clear()
        self.golden_apple.hideturtle()
        self.golden_glow.hideturtle()
        self.score = 0
        self.delay = self.INITIAL_DELAY
        self.menu_option = 0
        self.update_scoreboard()

    def check_border_collision(self):
        return abs(self.head.xcor()) > self.max_x or abs(self.head.ycor()) > self.max_y

    def check_self_collision(self):
        return any(self.head.distance(s) < self.COLLISION_DISTANCE for s in self.segments)

    def create_pause_menu(self):
        self.pause_title = turtle.Turtle()
        self.pause_instructions = turtle.Turtle()
        self.menu_options = []
        for obj in (self.pause_title, self.pause_instructions):
            obj.speed(0)
            obj.penup()
            obj.hideturtle()
            obj.color('white')
        for _ in range(3):
            opt = turtle.Turtle()
            opt.speed(0)
            opt.color('white')
            opt.penup()
            opt.hideturtle()
            self.menu_options.append(opt)

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.show_pause_menu()
        else:
            self.hide_pause_menu()

    def show_pause_menu(self):
        self.pause_title.goto(0, 150)
        self.pause_title.write('⏸️ GAME PAUSED ⏸️', align='center', font=('Courier', 24, 'bold'))
        self.pause_instructions.goto(0, 120)
        self.pause_instructions.write(
            'Use ↑↓ or W/S to navigate • Enter/Space to select',
            align='center', font=('Arial', 14, 'normal')
        )
        self.update_pause_menu()

    def hide_pause_menu(self):
        self.pause_title.clear()
        self.pause_instructions.clear()
        for opt in self.menu_options:
            opt.clear()

    def update_pause_menu(self):
        texts = ['▶ RESUME', '🔄 RESTART', '❌ QUIT']
        ys = [50, 0, -50]
        for i, opt in enumerate(self.menu_options):
            opt.clear()
            opt.goto(0, ys[i])
            if i == self.menu_option:
                opt.color('yellow')
                opt.write(f'>>> {texts[i]} <<<', align='center', font=('Courier', 18, 'bold'))
            else:
                opt.color('white')
                opt.write(texts[i], align='center', font=('Courier', 16, 'normal'))

    def menu_up(self):
        self.menu_option = (self.menu_option - 1) % 3
        self.play_sound('move')
        self.update_pause_menu()

    def menu_down(self):
        self.menu_option = (self.menu_option + 1) % 3
        self.play_sound('move')
        self.update_pause_menu()

    def menu_select(self):
        self.play_sound('eat')
        if self.menu_option == 0:
            self.toggle_pause()
        elif self.menu_option == 1:
            self.toggle_pause()
            self.reset_game()
        else:
            self.game_running = False

    def move_up(self):
        if self.head.direction != 'down':
            self.head.direction = 'up'
            self.play_sound('move')

    def move_down(self):
        if self.head.direction != 'up':
            self.head.direction = 'down'
            self.play_sound('move')

    def move_left(self):
        if self.head.direction != 'right':
            self.head.direction = 'left'
            self.play_sound('move')

    def move_right(self):
        if self.head.direction != 'left':
            self.head.direction = 'right'
            self.play_sound('move')

    def move_snake(self):
        dirs = {
            'up': (0, self.MOVE_DISTANCE),
            'down': (0, -self.MOVE_DISTANCE),
            'left': (-self.MOVE_DISTANCE, 0),
            'right': (self.MOVE_DISTANCE, 0)
        }
        dx, dy = dirs.get(self.head.direction, (0, 0))
        self.head.goto(self.head.xcor() + dx, self.head.ycor() + dy)
        self.update_eyes()

    def move_body_segments(self):
        for i in range(len(self.segments) - 1, 0, -1):
            x, y = self.segments[i - 1].position()
            self.segments[i].goto(x, y)
        if self.segments:
            self.segments[0].goto(self.head.position())

    def play_sound(self, key):
        if self.sound_enabled and key in self.sounds:
            try:
                self.sounds[key].play()
            except:
                pass

    def run_game(self):
        if not turtle:
            print("Turtle not available in headless env. Exiting.")
            return
        while self.game_running:
            self.screen.update()
            if self.paused:
                time.sleep(0.1)
                continue
            if self.check_border_collision() or self.check_self_collision():
                self.reset_game()
                continue
            if self.head.distance(self.food) < self.COLLISION_DISTANCE:
                self.handle_food_collision()
            if self.golden_apple.isvisible() and self.head.distance(self.golden_apple) < self.COLLISION_DISTANCE:
                self.handle_golden_apple_collision()
            self.move_body_segments()
            self.move_snake()
            time.sleep(self.delay)
        self.screen.bye()

if __name__ == '__main__':
    game = SnakeGame()
    game.run_game()[ ' import os
import random
import time
import pygame
import math
try:
    import turtle
except ImportError:
    turtle = None  # Fallback for non-GUI environments

class SnakeGame:
    def __init__(self):
        # Initialize sound
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.sound_enabled = True
            self.load_sounds()
        except Exception:
            self.sound_enabled = False
            print("Sound unavailable - running in silent mode")

        # Fullscreen state
        self.fullscreen = False

        # Game constants
        self.MOVE_DISTANCE = 20
        self.INITIAL_DELAY = 0.1
        self.BORDER_MARGIN = 10
        self.COLLISION_DISTANCE = 18

        # Fruit types
        self.fruit_types = [
            {'name':'apple','shape':'circle','color':'#ff4444','size':0.8,'stem':True},
            {'name':'orange','shape':'circle','color':'#ffa500','size':0.8,'stem':False},
            {'name':'banana','shape':'triangle','color':'yellow','size':1.0,'stem':False},
            {'name':'grape','shape':'circle','color':'purple','size':0.6,'stem':False}
        ]

        # Game state
        self.score = 0
        self.high_score = 0
        self.delay = self.INITIAL_DELAY
        self.segments = []
        self.game_running = True
        self.paused = False
        self.menu_option = 0

        # Setup game if GUI available
        if turtle:
            self.setup_screen()
            self.create_snake()
            self.create_food()
            self.create_golden_apple()
            self.create_scoreboard()
            self.create_pause_menu()
            self.setup_controls()
            self.max_x = self.screen.window_width()//2 - self.BORDER_MARGIN
            self.max_y = self.screen.window_height()//2 - self.BORDER_MARGIN
            self.food_boundary_x = self.screen.window_width()//2 - 40
            self.food_boundary_y = self.screen.window_height()//2 - 40

    def load_sounds(self):
        self.sounds = {}
        base = os.path.dirname(__file__)
        for key in ['eat','golden','gameover','move']:
            path = os.path.join(base, f"{key}.wav")
            if os.path.exists(path):
                self.sounds[key] = pygame.mixer.Sound(path)
        bg = os.path.join(base, 'background.mp3')
        if os.path.exists(bg):
            pygame.mixer.music.load(bg)
            pygame.mixer.music.set_volume(0.2)
            pygame.mixer.music.play(-1)

    def create_beep_sound(self, freq, dur):
        import io, wave, struct
        sr = 22050
        frames = int(sr*dur)
        buf = io.BytesIO()
        with wave.open(buf,'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            for i in range(frames):
                val = int(16000*math.sin(2*math.pi*freq*i/sr))
                fade = 1 - (i/frames)*0.8
                w.writeframes(struct.pack('<h',int(val*fade)))
        buf.seek(0)
        return pygame.mixer.Sound(buf)

    def setup_screen(self):
        self.screen = turtle.Screen()
        self.screen.title("🐍 Snake Game Deluxe 🐍")
        self.screen.bgcolor("#2d5a27")
        self.screen.setup(width=1.0, height=1.0)
        self.screen.tracer(0)
        self.root = self.screen._root
        self.screen.listen()

    def setup_controls(self):
        bindings = [
            ('Up', self.handle_up), ('Down', self.handle_down),
            ('Left', self.handle_left), ('Right', self.handle_right),
            ('w', self.handle_up), ('s', self.handle_down),
            ('a', self.handle_left), ('d', self.handle_right)
        ]
        for key, func in bindings:
            self.screen.onkey(func, key)
        for key in ['space','p','Escape']:
            self.screen.onkey(self.toggle_pause, key)
        self.screen.onkey(self.menu_select, 'Return')
        self.screen.onkey(self.menu_select, 'space')
        self.screen.onkey(self.toggle_fullscreen, 'F11')

    def handle_up(self):
        if self.paused:
            self.menu_up()
        else:
            self.move_up()

    def handle_down(self):
        if self.paused:
            self.menu_down()
        else:
            self.move_down()

    def handle_left(self):
        if not self.paused:
            self.move_left()

    def handle_right(self):
        if not self.paused:
            self.move_right()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.root.attributes('-fullscreen', self.fullscreen)

    def create_snake(self):
        self.head = turtle.Turtle()
        self.head.speed(0)
        self.head.shape('circle')
        self.head.shapesize(1.2, 1.5)
        self.head.color('#4a7c59')
        self.head.penup()
        self.head.goto(0, 0)
        self.head.direction = 'stop'
        self.create_snake_eyes()

    def create_snake_eyes(self):
        self.left_eye = turtle.Turtle(); self.right_eye = turtle.Turtle()
        for eye in (self.left_eye, self.right_eye):
            eye.speed(0)
            eye.shape('circle')
            eye.shapesize(0.3, 0.3)
            eye.color('white')
            eye.penup()
            eye.hideturtle()
        self.left_pupil = turtle.Turtle(); self.right_pupil = turtle.Turtle()
        for pupil in (self.left_pupil, self.right_pupil):
            pupil.speed(0)
            pupil.shape('circle')
            pupil.shapesize(0.15, 0.15)
            pupil.color('black')
            pupil.penup()
            pupil.hideturtle()
        self.update_eyes()

    def update_eyes(self):
        hx, hy = self.head.position()
        d = self.head.direction
        offsets = {
            'up':    [(-8, 8, -8, 10), (8, 8, 8, 10)],
            'down':  [(-8, -8, -8, -10), (8, -8, 8, -10)],
            'left':  [(-8, 8, -10, 8), (-8, -8, -10, -8)],
            'right': [(8, 8, 10, 8), (8, -8, 10, -8)],
            'stop':  [(-8, 5, -8, 5), (8, 5, 8, 5)]
        }
        o1, o2 = offsets.get(d, offsets['stop'])
        self.left_eye.goto(hx + o1[0], hy + o1[1])
        self.left_pupil.goto(hx + o1[2], hy + o1[3])
        self.right_eye.goto(hx + o2[0], hy + o2[1])
        self.right_pupil.goto(hx + o2[2], hy + o2[3])
        for part in (self.left_eye, self.left_pupil, self.right_eye, self.right_pupil):
            part.showturtle()

    def create_food(self):
        self.food = turtle.Turtle()
        self.food.speed(0)
        self.food.penup()
        self.stem = turtle.Turtle()
        self.stem.speed(0)
        self.stem.shape('square')
        self.stem.color('#8b4513')
        self.stem.shapesize(0.1, 0.3)
        self.stem.penup()
        self.food_type = None

    def spawn_food(self):
        f = random.choice(self.fruit_types)
        self.food_type = f['name']
        self.food.shape(f['shape'])
        self.food.color(f['color'])
        self.food.shapesize(f['size'], f['size'])
        if f['stem']:
            self.stem.showturtle()
        else:
            self.stem.hideturtle()
        while True:
            x = random.randint(-self.food_boundary_x, self.food_boundary_x)
            y = random.randint(-self.food_boundary_y, self.food_boundary_y)
            if not any(abs(x - s.xcor()) < 30 and abs(y - s.ycor()) < 30 for s in [self.head] + self.segments):
                break
        self.food.goto(x, y)
        if f['stem']:
            self.stem.goto(x, y + f['size'] * 10)

    def create_golden_apple(self):
        self.golden_apple = turtle.Turtle()
        self.golden_glow = turtle.Turtle()
        for obj, col, sz in [(self.golden_apple, '#ffd700', 1), (self.golden_glow, '#ffff99', 1.3)]:
            obj.speed(0)
            obj.shape('circle')
            obj.color(col)
            obj.shapesize(sz, sz)
            obj.penup()
            obj.hideturtle()

    def spawn_golden_apple(self):
        if random.randint(1, 15) == 1:
            x = random.randint(-self.food_boundary_x, self.food_boundary_x)
            y = random.randint(-self.food_boundary_y, self.food_boundary_y)
            self.golden_glow.goto(x, y)
            self.golden_glow.showturtle()
            self.golden_apple.goto(x, y)
            self.golden_apple.showturtle()

    def create_scoreboard(self):
        self.scoreboard = turtle.Turtle()
        self.scoreboard.speed(0)
        self.scoreboard.color('white')
        self.scoreboard.penup()
        self.scoreboard.hideturtle()
        self.scoreboard.goto(-self.screen.window_width()//2 + 40, self.screen.window_height()//2 - 60)
        self.update_scoreboard()

    def update_scoreboard(self):
        self.scoreboard.clear()
        self.scoreboard.write(
            f'🐍 Score: {self.score} | 🏆 High Score: {self.high_score}',
            align='left', font=('Courier', 16, 'bold')
        )

    def handle_food_collision(self):
        self.play_sound('eat')
        self.spawn_food()
        self.add_segment()
        points = 10
        if self.food_type == 'orange':
            points = 15
        elif self.food_type == 'banana':
            points = 20
        elif self.food_type == 'grape':
            points = 12
        self.score += points
        if self.score > self.high_score:
            self.high_score = self.score
        self.update_scoreboard()
        self.update_speed()
        self.spawn_golden_apple()

    def handle_golden_apple_collision(self):
        self.play_sound('golden')
        self.golden_apple.hideturtle()
        self.golden_glow.hideturtle()
        self.score += 50
        if self.score > self.high_score:
            self.high_score = self.score
        self.update_scoreboard()

    def add_segment(self):
        seg = turtle.Turtle()
        seg.speed(0)
        seg.shape('circle')
        colors = ['#5d8a66', '#4a7c59', '#3e6b4c', '#5d8a66']
        seg.color(colors[len(self.segments) % 4])
        seg.shapesize(0.9, 0.9)
        seg.penup()
        self.segments.append(seg)

    def update_speed(self):
        if self.score >= 300:
            self.delay = 0.06
        elif self.score >= 200:
            self.delay = 0.07
        elif self.score >= 100:
            self.delay = 0.08
        elif self.score >= 50:
            self.delay = 0.09
        else:
            self.delay = self.INITIAL_DELAY

    def reset_game(self):
        self.play_sound('gameover')
        time.sleep(1)
        self.head.goto(0, 0)
        self.head.direction = 'stop'
        self.update_eyes()
        for seg in self.segments:
            seg.hideturtle()
        self.segments.clear()
        self.golden_apple.hideturtle()
        self.golden_glow.hideturtle()
        self.score = 0
        self.delay = self.INITIAL_DELAY
        self.menu_option = 0
        self.update_scoreboard()

    def check_border_collision(self):
        return abs(self.head.xcor()) > self.max_x or abs(self.head.ycor()) > self.max_y

    def check_self_collision(self):
        return any(self.head.distance(s) < self.COLLISION_DISTANCE for s in self.segments)

    def create_pause_menu(self):
        self.pause_title = turtle.Turtle()
        self.pause_instructions = turtle.Turtle()
        self.menu_options = []
        for obj in (self.pause_title, self.pause_instructions):
            obj.speed(0)
            obj.penup()
            obj.hideturtle()
            obj.color('white')
        for _ in range(3):
            opt = turtle.Turtle()
            opt.speed(0)
            opt.color('white')
            opt.penup()
            opt.hideturtle()
            self.menu_options.append(opt)

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.show_pause_menu()
        else:
            self.hide_pause_menu()

    def show_pause_menu(self):
        self.pause_title.goto(0, 150)
        self.pause_title.write('⏸️ GAME PAUSED ⏸️', align='center', font=('Courier', 24, 'bold'))
        self.pause_instructions.goto(0, 120)
        self.pause_instructions.write(
            'Use ↑↓ or W/S to navigate • Enter/Space to select',
            align='center', font=('Arial', 14, 'normal')
        )
        self.update_pause_menu()

    def hide_pause_menu(self):
        self.pause_title.clear()
        self.pause_instructions.clear()
        for opt in self.menu_options:
            opt.clear()

    def update_pause_menu(self):
        texts = ['▶ RESUME', '🔄 RESTART', '❌ QUIT']
        ys = [50, 0, -50]
        for i, opt in enumerate(self.menu_options):
            opt.clear()
            opt.goto(0, ys[i])
            if i == self.menu_option:
                opt.color('yellow')
                opt.write(f'>>> {texts[i]} <<<', align='center', font=('Courier', 18, 'bold'))
            else:
                opt.color('white')
                opt.write(texts[i], align='center', font=('Courier', 16, 'normal'))

    def menu_up(self):
        self.menu_option = (self.menu_option - 1) % 3
        self.play_sound('move')
        self.update_pause_menu()

    def menu_down(self):
        self.menu_option = (self.menu_option + 1) % 3
        self.play_sound('move')
        self.update_pause_menu()

    def menu_select(self):
        self.play_sound('eat')
        if self.menu_option == 0:
            self.toggle_pause()
        elif self.menu_option == 1:
            self.toggle_pause()
            self.reset_game()
        else:
            self.game_running = False

    def move_up(self):
        if self.head.direction != 'down':
            self.head.direction = 'up'
            self.play_sound('move')

    def move_down(self):
        if self.head.direction != 'up':
            self.head.direction = 'down'
            self.play_sound('move')

    def move_left(self):
        if self.head.direction != 'right':
            self.head.direction = 'left'
            self.play_sound('move')

    def move_right(self):
        if self.head.direction != 'left':
            self.head.direction = 'right'
            self.play_sound('move')

    def move_snake(self):
        dirs = {
            'up': (0, self.MOVE_DISTANCE),
            'down': (0, -self.MOVE_DISTANCE),
            'left': (-self.MOVE_DISTANCE, 0),
            'right': (self.MOVE_DISTANCE, 0)
        }
        dx, dy = dirs.get(self.head.direction, (0, 0))
        self.head.goto(self.head.xcor() + dx, self.head.ycor() + dy)
        self.update_eyes()

    def move_body_segments(self):
        for i in range(len(self.segments) - 1, 0, -1):
            x, y = self.segments[i - 1].position()
            self.segments[i].goto(x, y)
        if self.segments:
            self.segments[0].goto(self.head.position())

    def play_sound(self, key):
        if self.sound_enabled and key in self.sounds:
            try:
                self.sounds[key].play()
            except:
                pass

    def run_game(self):
        if not turtle:
            print("Turtle not available in headless env. Exiting.")
            return
        while self.game_running:
            self.screen.update()
            if self.paused:
                time.sleep(0.1)
                continue
            if self.check_border_collision() or self.check_self_collision():
                self.reset_game()
                continue
            if self.head.distance(self.food) < self.COLLISION_DISTANCE:
                self.handle_food_collision()
            if self.golden_apple.isvisible() and self.head.distance(self.golden_apple) < self.COLLISION_DISTANCE:
                self.handle_golden_apple_collision()
            self.move_body_segments()
            self.move_snake()
            time.sleep(self.delay)
        self.screen.bye()

if __name__ == '__main__':
    game = SnakeGame()
    game.run_game()['▶ RESUME', '🔄 RESTART', '❌ QUIT']
        ys = [50, 0, -50]
        for i, opt in enumerate(self.menu_options):
            opt.clear()
            opt.goto(0, ys[i])
            if i == self.menu_option:
                opt.color('yellow')
                opt.write(f'>>> {texts[i]} <<<', align='center', font=('Courier', 18, 'bold'))
            else:
                opt.color('white')
                opt.write(texts[i], align='center', font=('Courier', 16, 'normal'))

    def menu_up(self):
        self.menu_option = (self.menu_option - 1) % 3
        self.play_sound('move')
        self.update_pause_menu()

    def menu_down(self):
        self.menu_option = (self.menu_option + 1) % 3
        self.play_sound('move')
        self.update_pause_menu()

    def menu_select(self):
        self.play_sound('eat')
        if self.menu_option == 0:
            self.toggle_pause()
        elif self.menu_option == 1:
            self.toggle_pause()
            self.reset_game()
        else:
            self.game_running = False

    def move_up(self):
        if self.head.direction != 'down':
            self.head.direction = 'up'
            self.play_sound('move')

    def move_down(self):
        if self.head.direction != 'up':
            self.head.direction = 'down'
            self.play_sound('move')

    def move_left(self):
        if self.head.direction != 'right':
            self.head.direction = 'left'
            self.play_sound('move')

    def move_right(self):
        if self.head.direction != 'left':
            self.head.direction = 'right'
            self.play_sound('move')

    def move_snake(self):
        dirs = {
            'up': (0, self.MOVE_DISTANCE),
            'down': (0, -self.MOVE_DISTANCE),
            'left': (-self.MOVE_DISTANCE, 0),
            'right': (self.MOVE_DISTANCE, 0)
        }
        dx, dy = dirs.get(self.head.direction, (0, 0))
        self.head.goto(self.head.xcor() + dx, self.head.ycor() + dy)
        self.update_eyes()

    def move_body_segments(self):
        for i in range(len(self.segments) - 1, 0, -1):
            x, y = self.segments[i - 1].position()
            self.segments[i].goto(x, y)
        if self.segments:
            self.segments[0].goto(self.head.position())

    def play_sound(self, key):
        if self.sound_enabled and key in self.sounds:
            try:
                self.sounds[key].play()
            except:
                pass

    def run_game(self):
        if not turtle:
            print("Turtle not available in headless env. Exiting.")
            return
        while self.game_running:
            self.screen.update()
            if self.paused:
                time.sleep(0.1)
                continue
            if self.check_border_collision() or self.check_self_collision():
                self.reset_game()
                continue
            if self.head.distance(self.food) < self.COLLISION_DISTANCE:
                self.handle_food_collision()
            if self.golden_apple.isvisible() and self.head.distance(self.golden_apple) < self.COLLISION_DISTANCE:
                self.handle_golden_apple_collision()
            self.move_body_segments()
            self.move_snake()
            time.sleep(self.delay)
        self.screen.bye()

if __name__ == '__main__':
    game = SnakeGame()
    game.run_game()
