__author__ = 'Pedro Sequeira'

import pygame
from collections import OrderedDict
from sys import exit
from os.path import dirname, abspath, join
from pygame.constants import QUIT, KEYDOWN
from ple.games.base import PyGameWrapper
from pygame.rect import Rect
from frogger import *


# functions
def draw_list(lst, screen):
    for i in lst:
        i.draw(screen)


def move_list(lst, speed):
    for i in lst:
        i.move(speed)


class Frogger(PyGameWrapper):
    def __init__(self, actions=None, rewards=None, lives=3, speed=3, level=1,
                 num_arrived_frogs=5, max_steps=60, show_stats=True, sound=True):

        if actions is None:
            actions = OrderedDict([
                ('up', ACTION_UP_KEY),
                ('down', ACTION_DOWN_KEY),
                ('left', ACTION_LEFT_KEY),
                ('right', ACTION_RIGHT_KEY)])

        super().__init__(WIDTH, HEIGHT, actions=actions)

        if rewards is None:
            rewards = {
                HIT_CAR_RWD_ATTR: -20.,
                HIT_WATER_RWD_ATTR: -20.,
                TIME_UP_RWD_ATTR: -20.,
                NO_LIVES_RWD_ATTR: -50,
                NEW_LEVEL_RWD_ATTR: 100.,
                FROG_ARRIVED_RWD_ATTR: 30.,
                TICK_RWD_ATTR: -1.
            }
        self.rewards = rewards

        self.max_steps = max_steps
        self.init_level = level
        self.init_speed = speed
        self.init_lives = lives
        self.num_arrived_frogs = num_arrived_frogs
        self.show_stats = show_stats
        self.sound = sound

        self.key_pressed = INVALID_ACTION_KEY
        self.process_events = False
        self.game_init = False

        self.dead_counter = 0
        self.dead_object = None

        self.frog = Frog(FROG_INIT_POS.copy(), None, self.init_lives, {})
        self.game = Game(self.init_speed, self.init_level, self.max_steps)

        self.cars = []
        self.logs = []
        self.arrived_frogs = []
        self.ticks_cars = []
        self.ticks_logs = []

        # declaration of graphical elements
        self.game_font = None
        self.info_font = None
        self.menu_font = None
        self.background = None
        self.frog_sprites = {}
        self.sprite_arrived = None
        self.frog_life_sprite = None
        self.sprite_drowned = None
        self.sprite_time_up = None
        self.sprite_crash = None
        self.car_sprites = []
        self.log_sprite = None
        self.hit_sound = None
        self.water_sound = None
        self.arrived_sound = None
        self.back_sound = None

    def init(self):

        self._init_resources()

        self.key_pressed = INVALID_ACTION_KEY
        self.process_events = False

        self.dead_counter = 0
        self.dead_object = None

        self.cars = []
        self.logs = []
        self.arrived_frogs = []
        self.ticks_cars = [self.rng.randint(0, MAX_CAR_TICKS) for _ in range(5)]
        self.ticks_logs = [self.rng.randint(0, MAX_LOG_TICK) for _ in range(5)]

        self.frog = Frog(FROG_INIT_POS.copy(), self.frog_sprites[ACTION_UP_KEY], self.init_lives, self.frog_sprites)
        self.game = Game(self.init_speed, self.init_level, self.max_steps)

        self.screen.blit(self.background, (0, 0))
        self.frog.draw(self.screen)
        if self.show_stats:
            self._draw_stats()
        pygame.display.flip()

    def getScore(self):
        return self.game.points

    def game_over(self):
        return self.frog.lives == 0

    @staticmethod
    def _is_valid_key(key):
        return key == ACTION_LEFT_KEY or \
               key == ACTION_RIGHT_KEY or \
               key == ACTION_UP_KEY or \
               key == ACTION_DOWN_KEY or \
               key == ACTION_NO_MOVE_KEY

    def step(self, dt):

        # ignore if game is over, needs re-init
        if self.game_over():
            return

        # checks 'wait for key' state
        if not self.frog.is_moving:
            self.key_pressed = INVALID_ACTION_KEY

        # processes events
        if self.process_events:

            self.process_events = False
            for event in pygame.event.get():
                if event.type == QUIT:
                    exit()
                if event.type == KEYDOWN and not self.frog.is_moving and self._is_valid_key(event.key):
                    self.key_pressed = event.key

                    # sets new direction and locks frog movement
                    if self.key_pressed != ACTION_NO_MOVE_KEY:
                        self.frog.update_sprite(self.key_pressed)
                        self.frog.is_moving = True

        # refreshes screen if needed
        pygame.event.pump()

        # checks max moves
        if self.game.steps == 0:
            self.game.points += self._get_reward(TIME_UP_RWD_ATTR)
            self._set_death_sprite(self.sprite_time_up)
            self.frog.set_dead(self.game, self._get_reward(NO_LIVES_RWD_ATTR))

        self._create_cars()
        self._create_logs()

        move_list(self.cars, self.game.speed)
        move_list(self.logs, self.game.speed)

        self.screen.blit(self.background, (0, 0))

        draw_list(self.cars, self.screen)
        draw_list(self.logs, self.screen)
        draw_list(self.arrived_frogs, self.screen)

        self.frog.move(self.key_pressed)
        self.frog.animate()
        self.frog.draw(self.screen)

        self._destroy_cars()
        self._destroy_logs()

        self._check_frog_location()
        self._check_next_level()

        # checks death image
        if self.dead_counter > 0:
            self.dead_object.draw(self.screen)
            self.dead_counter -= 1
            if self.dead_counter == 0:
                self.dead_object = None

        # show stats
        if self.show_stats:
            self._draw_stats()

    def _set_death_sprite(self, sprite):
        self.dead_object = Object(self.frog.position.copy(), sprite, ACTION_DOWN_KEY)
        self.dead_counter = DEATH_IMAGE_TIME_STEPS

    def _draw_stats(self):
        level_text_info = self.info_font.render(
            ('Level: {}'.format(self.game.level)), 1, (TXT_COLOR, TXT_COLOR, TXT_COLOR))
        points_text_info = self.info_font.render(
            ('Points: {}'.format(self.game.points)), 1, (TXT_COLOR, TXT_COLOR, TXT_COLOR))
        moves_text_info = self.info_font.render(
            ('Moves: {}'.format(self.game.steps)), 1, (TXT_COLOR, TXT_COLOR, TXT_COLOR))
        # lives_text_info = self.info_font.render(
        #     ('Lives: {}'.format(self.frog.lives)), 1, (TXT_COLOR, TXT_COLOR, TXT_COLOR))
        self.screen.blit(level_text_info, (10, 520))
        self.screen.blit(moves_text_info, (100, 520))
        self.screen.blit(points_text_info, (220, 520))
        # self.screen.blit(lives_text_info, (370, 520))
        for i in range(self.frog.lives - 1):
            self.screen.blit(self.frog_life_sprite,
                             (WIDTH - 4 - (i + 1) * (self.sprite_arrived.get_width() + 4), 513))

    def getGameState(self):
        return FroggerState.from_game(
            self.game, self.arrived_frogs, self.frog, self.cars, self.logs).to_observation()

    def _setAction(self, action, last_action):
        super()._setAction(action, last_action)
        self.process_events = True
        self.game.steps -= 1
        self.game.points += self._get_reward(TICK_RWD_ATTR)

    def _get_reward(self, rwd_attr):
        return self.rewards[rwd_attr] if rwd_attr in self.rewards else 0.

    @staticmethod
    def _load_img(base_dir, img_path):
        return pygame.image.load(join(base_dir, img_path))

    @staticmethod
    def _load_sound(base_dir, sound_path):
        return pygame.mixer.Sound(join(base_dir, sound_path))

    def _init_resources(self):
        if self.game_init:
            return

        # fonts
        font_name = pygame.font.get_default_font()
        self.game_font = pygame.font.SysFont(font_name, 72)
        self.info_font = pygame.font.SysFont(font_name, 24)
        self.menu_font = pygame.font.SysFont(font_name, 36)

        # to allow running game from any script
        _dir = dirname(abspath(join(__file__, '..')))

        # sprites
        self.background = self._load_img(_dir, 'images/bg.png').convert()
        sprite_frog_up = self._load_img(_dir, 'images/sprite_sheets_up.png').convert_alpha()
        sprite_frog_down = self._load_img(_dir, 'images/sprite_sheets_down.png').convert_alpha()
        sprite_frog_left = self._load_img(_dir, 'images/sprite_sheets_left.png').convert_alpha()
        sprite_frog_right = self._load_img(_dir, 'images/sprite_sheets_right.png').convert_alpha()
        self.frog_sprites = {ACTION_UP_KEY: sprite_frog_up,
                             ACTION_DOWN_KEY: sprite_frog_down,
                             ACTION_LEFT_KEY: sprite_frog_left,
                             ACTION_RIGHT_KEY: sprite_frog_right}

        self.sprite_arrived = self._load_img(_dir, 'images/frog_arrived.png').convert_alpha()
        self.frog_life_sprite = pygame.transform.rotate(self.sprite_arrived, 180)
        self.sprite_drowned = self._load_img(_dir, 'images/splash.png').convert_alpha()
        self.sprite_time_up = self._load_img(_dir, 'images/clock.png').convert_alpha()
        self.sprite_crash = self._load_img(_dir, 'images/burst.png').convert_alpha()

        sprite_car1 = self._load_img(_dir, 'images/car1.png').convert_alpha()
        sprite_car2 = self._load_img(_dir, 'images/car2.png').convert_alpha()
        sprite_car3 = self._load_img(_dir, 'images/car3.png').convert_alpha()
        sprite_car4 = self._load_img(_dir, 'images/car4.png').convert_alpha()
        sprite_car5 = self._load_img(_dir, 'images/car5.png').convert_alpha()
        self.car_sprites = [sprite_car1, sprite_car2, sprite_car3, sprite_car4, sprite_car5]

        self.log_sprite = self._load_img(_dir, 'images/tronco.png').convert_alpha()

        # sound effects
        if self.sound:
            self.hit_sound = self._load_sound(_dir, 'sounds/boom.wav')
            self.water_sound = self._load_sound(_dir, 'sounds/agua.wav')
            self.arrived_sound = self._load_sound(_dir, 'sounds/success.wav')
            self._load_sound(_dir, 'sounds/guimo.wav').play(-1)

        pygame.display.set_caption('Frogger')

        self.game_init = True

    def _create_cars(self):
        for i, tick in enumerate(self.ticks_cars):
            self.ticks_cars[i] -= 1
            if tick > 0:
                continue

            # adds a new car in this row
            self.ticks_cars[i] = (CARS_INIT_TICKS[i] * self.game.speed) / self.game.level
            car = Car(CARS_INIT_POS[i].copy(), self.car_sprites[i], ACTION_RIGHT_KEY if i % 2 == 0 else ACTION_LEFT_KEY,
                      CARS_SPEED_FACTORS[i])
            self.cars.append(car)

    def _destroy_cars(self):
        for i in self.cars:
            if i.position[0] < -80 or i.position[0] > 516:
                self.cars.remove(i)

    def _create_logs(self):
        for i, tick in enumerate(self.ticks_logs):
            self.ticks_logs[i] -= 1
            if tick > 0:
                continue

            # adds a new log in this row
            self.ticks_logs[i] = (LOGS_INIT_TICKS[i] * self.game.speed) / self.game.level
            log = Log(LOGS_INIT_POS[i].copy(), self.log_sprite, ACTION_RIGHT_KEY if i % 2 == 0 else ACTION_LEFT_KEY)
            self.logs.append(log)

    def _destroy_logs(self):
        for i in self.logs:
            if i.position[0] < -100 or i.position[0] > 448:
                self.logs.remove(i)

    def _frog_on_the_road(self):
        for car in self.cars:
            car_rect = car.rect()
            frog_rect = self.frog.rect()
            if frog_rect.colliderect(car_rect):
                if self.sound:
                    self.hit_sound.play()
                self._set_death_sprite(self.sprite_crash)
                self.frog.set_dead(self.game, self._get_reward(NO_LIVES_RWD_ATTR))
                self.game.points += self._get_reward(HIT_CAR_RWD_ATTR)
                break

    def _frog_in_the_river(self):

        # checks for collision with any log (frog is safe)
        safe = False
        log_dir = None
        for log in self.logs:
            log_rect = log.rect()
            frog_rect = self.frog.rect()
            if frog_rect.colliderect(log_rect):
                safe = True
                log_dir = log.way
                break

        if safe:
            # otherwise update position according to log movement
            if log_dir == ACTION_RIGHT_KEY:
                self.frog.position[0] += self.game.speed

            elif log_dir == ACTION_LEFT_KEY:
                self.frog.position[0] -= self.game.speed

            # checks frog out-of-bounds (assume fell on water)
            safe = - FROG_SIZE < self.frog.position[0] < WIDTH

        if not safe:
            # if frog is in the water
            if self.sound:
                self.water_sound.play()
            self._set_death_sprite(self.sprite_drowned)
            self.frog.set_dead(self.game, self._get_reward(NO_LIVES_RWD_ATTR))
            self.game.points += self._get_reward(HIT_WATER_RWD_ATTR)

    def _occupied(self, position):
        return any([fg.position == position for fg in self.arrived_frogs])

    def _check_frog_arrived(self):
        # checks if frog jumps to any lily pad
        for arrival_x in ARRIVAL_POSITIONS:
            arrive_pos = [arrival_x, ARRIVAL_POSITION_Y]
            if not self._occupied(arrive_pos) and \
                    arrival_x - ARRIVAL_WIDTH < self.frog.position[0] < arrival_x + ARRIVAL_WIDTH:
                self._create_arrived(arrive_pos)
                return

        # otherwise put's frog back in log
        self.frog.position[1] = MIN_Y_POS
        self.frog.animation_counter = 0
        self.frog.is_moving = False

    def _check_frog_location(self):

        # check if frog achieved final position
        if self.frog.position[1] < MIN_Y_POS:
            self._check_frog_arrived()

        # if frog is crossing the road
        if MAX_GRASS_Y_POS < self.frog.position[1] < MAX_Y_POS:
            self._frog_on_the_road()

        # if frog is in the river
        elif MIN_Y_POS <= self.frog.position[1] < MAX_GRASS_Y_POS:
            self._frog_in_the_river()

    def _create_arrived(self, position_init):
        frog_arrived = Object(position_init, self.sprite_arrived, ACTION_DOWN_KEY)

        if self.sound:
            self.arrived_sound.play()
        self.arrived_frogs.append(frog_arrived)
        self.frog.set_to_initial_position()
        self.frog.animation_counter = 0
        self.frog.is_moving = False
        self.game.points += self.game.level * self._get_reward(FROG_ARRIVED_RWD_ATTR)

    def _check_next_level(self):
        if len(self.arrived_frogs) < self.num_arrived_frogs:
            return

        self.arrived_frogs = []
        self.frog.set_to_initial_position()
        self.game.reset_steps()
        self.game.level += 1
        self.game.speed += 1
        self.game.points += self.game.level * self._get_reward(NEW_LEVEL_RWD_ATTR)


class Object(object):
    def __init__(self, position, sprite, way):
        self.sprite = sprite
        self.position = position
        self.way = way

    def draw(self, screen):
        screen.blit(self.sprite, tuple(self.position))

    def rect(self):
        return Rect(self.position[0], self.position[1], self.sprite.get_width(), self.sprite.get_height())


class Frog(Object):
    def __init__(self, position, sprite, lives, frog_sprites):
        super().__init__(position, sprite, ACTION_UP_KEY)
        self.frog_sprites = frog_sprites
        self.lives = lives
        self.animation_counter = 0
        self.is_moving = False
        self.init_position = position.copy()

    def update_sprite(self, key_pressed):
        if key_pressed not in self.frog_sprites:
            return
        self.way = key_pressed
        self.sprite = self.frog_sprites[key_pressed]

    def move(self, key_pressed):
        if not self.is_moving:
            return

        if key_pressed == ACTION_UP_KEY and self.position[1] >= MIN_Y_POS:
            self.position[1] -= 9 if self.animation_counter == ANIMATIONS_PER_MOVE - 1 else 10
        elif key_pressed == ACTION_DOWN_KEY and self.position[1] <= MAX_Y_POS:
            y_delta = 9 if self.animation_counter == ANIMATIONS_PER_MOVE - 1 else 10
            self.position[1] = min(MAX_Y_POS, self.position[1] + y_delta)
        elif key_pressed == ACTION_LEFT_KEY and self.position[0] > 0:
            self.position[0] = max(0, self.position[0] - CELL_WIDTH / ANIMATIONS_PER_MOVE)
        elif key_pressed == ACTION_RIGHT_KEY and self.position[0] < WIDTH - CELL_WIDTH:
            self.position[0] = min(WIDTH - CELL_WIDTH, self.position[0] + CELL_WIDTH / ANIMATIONS_PER_MOVE)

    def animate(self):
        if not self.is_moving:
            return

        self.animation_counter += 1
        if self.animation_counter == ANIMATIONS_PER_MOVE:
            self.animation_counter = 0
            self.is_moving = False

    def set_dead(self, game, no_lives_rwd):
        self.lives -= 1

        # checks no more lives, adds reward
        if self.lives == 0:
            game.points += no_lives_rwd
            return

        # otherwise reset frog
        game.reset_steps()
        self.set_to_initial_position()
        self.animation_counter = 0
        self.is_moving = False

    def set_to_initial_position(self):
        self.position = self.init_position.copy()

    def draw(self, screen):
        current_sprite = self.animation_counter * FROG_SIZE
        screen.blit(self.sprite, tuple(self.position), (current_sprite, 0, FROG_SIZE, FROG_SIZE + current_sprite))

    def rect(self):
        return Rect(self.position[0], self.position[1], FROG_SIZE, FROG_SIZE)


class Car(Object):
    def __init__(self, position, sprite, way, factor):
        super().__init__(position, sprite, way)
        self.factor = factor

    def move(self, speed):
        if self.way == ACTION_RIGHT_KEY:
            self.position[0] += speed * self.factor
        elif self.way == ACTION_LEFT_KEY:
            self.position[0] -= speed * self.factor


class Log(Object):
    def __init__(self, position, sprite, way):
        super().__init__(position, sprite, way)

    def move(self, speed):
        if self.way == ACTION_RIGHT_KEY:
            self.position[0] += speed
        elif self.way == ACTION_LEFT_KEY:
            self.position[0] -= speed


class Game(object):
    def __init__(self, speed, level, max_steps):
        self.speed = speed
        self.level = level
        self.points = 0
        self.steps = self.max_steps = max_steps
        self.gameInit = 0

    def reset_steps(self):
        self.steps = self.max_steps
