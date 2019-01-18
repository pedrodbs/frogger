__author__ = 'Pedro Sequeira'

import pygame
import numpy as np
from collections import OrderedDict
from sys import exit
from pygame.constants import K_UP, K_DOWN, K_LEFT, K_RIGHT, QUIT, KEYDOWN
from ple.games.base import PyGameWrapper
from pygame.rect import Rect
from frogger import OBS_SEPARATOR

# constants
HEIGHT = 546
WIDTH = 448
FROG_INIT_POS = [207, 475]
MAX_CAR_TICKS = 60
MAX_LOG_TICK = 30
ACTION_UP_KEY = K_UP
ACTION_DOWN_KEY = K_DOWN
ACTION_LEFT_KEY = K_LEFT
ACTION_RIGHT_KEY = K_RIGHT
ANIMATIONS_PER_MOVE = 4
TXT_COLOR = 220

HIT_CAR_RWD_ATTR = 'hit-car-rwd'
HIT_WATER_RWD_ATTR = 'water-rwd'
TIME_UP_RWD_ATTR = 'time-up-rwd'
NEW_LEVEL_RWD_ATTR = 'level-rwd'
FROG_ARRIVED_RWD_ATTR = 'frog-arrived-rwd'
TICK_RWD_ATTR = 'tick-rwd'


# functions
def draw_list(lst, screen):
    for i in lst:
        i.draw(screen)


def move_list(lst, speed):
    for i in lst:
        i.move(speed)


class Frogger(PyGameWrapper):
    def __init__(self, actions=None, rewards=None, lives=3, speed=3, level=1,
                 num_arrived_frogs=5, max_steps=300, show_stats=True, sound=True):

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

        self.key_pressed = 0
        self.process_events = False
        self.game_init = False

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
        self.car_sprites = []
        self.log_sprite = None
        self.hit_sound = None
        self.water_sound = None
        self.arrived_sound = None
        self.back_sound = None

    def init(self):

        self._init_resources()

        self.key_pressed = 0
        self.process_events = False

        self.cars = []
        self.logs = []
        self.arrived_frogs = []
        self.ticks_cars = [self.rng.randint(0, MAX_CAR_TICKS) for _ in range(5)]
        self.ticks_logs = [self.rng.randint(0, MAX_LOG_TICK) for _ in range(5)]

        self.frog = Frog(FROG_INIT_POS.copy(), self.frog_sprites[ACTION_UP_KEY], self.init_lives, self.frog_sprites)
        self.game = Game(self.init_speed, self.init_level, self.max_steps)

    def getScore(self):
        return self.game.points

    def game_over(self):
        return self.frog.lives == 0

    def step(self, dt):

        # checks 'wait for key' state
        if not self.frog.is_moving:
            self.key_pressed = 0

        # processes events
        if self.process_events:
            self.process_events = False
            for event in pygame.event.get():
                if event.type == QUIT:
                    exit()
                if event.type == KEYDOWN and not self.frog.is_moving:
                    # sets new direction and locks frog movement
                    self.key_pressed = event.key
                    self.frog.update_sprite(self.key_pressed)
                    self.frog.is_moving = True

        # refreshes screen if needed
        pygame.event.pump()

        # checks max moves
        if self.game.steps == 0:
            self.game.points += self.rewards[TIME_UP_RWD_ATTR]
            self.frog.set_dead(self.game)

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

        # show stats
        if self.show_stats:
            text_info1 = self.info_font.render(
                ('Level: {}'.format(self.game.level)), 1, (TXT_COLOR, TXT_COLOR, TXT_COLOR))
            text_info2 = self.info_font.render(
                ('Points: {}'.format(self.game.points)), 1, (TXT_COLOR, TXT_COLOR, TXT_COLOR))
            text_info3 = self.info_font.render(
                ('Moves: {}'.format(self.game.steps)), 1, (TXT_COLOR, TXT_COLOR, TXT_COLOR))
            text_info4 = self.info_font.render(
                ('Lives: {}'.format(self.frog.lives)), 1, (TXT_COLOR, TXT_COLOR, TXT_COLOR))

            self.screen.blit(text_info1, (10, 520))
            self.screen.blit(text_info2, (120, 520))
            self.screen.blit(text_info3, (250, 520))
            self.screen.blit(text_info4, (370, 520))

    def getGameState(self):
        # add game stats and frog info
        obs_list = [self.game.steps,
                    self.game.level,
                    self.game.points,
                    len(self.arrived_frogs),
                    self.frog.lives,
                    self.frog.position[0],
                    self.frog.position[1]]

        # adds cars infos
        for elem in self.cars:
            obs_list.append(elem.position[0])
            obs_list.append(elem.position[1])

        # puts separator before logs infos
        obs_list.append(OBS_SEPARATOR)
        for elem in self.logs:
            obs_list.append(elem.position[0])
            obs_list.append(elem.position[1])

        return np.array(obs_list)

    def _setAction(self, action, last_action):
        super()._setAction(action, last_action)
        self.process_events = True
        self.game.steps -= 1
        self.game.points += self.rewards[TICK_RWD_ATTR]

    def _init_resources(self):
        if self.game_init:
            return

        # fonts
        font_name = pygame.font.get_default_font()
        self.game_font = pygame.font.SysFont(font_name, 72)
        self.info_font = pygame.font.SysFont(font_name, 24)
        self.menu_font = pygame.font.SysFont(font_name, 36)

        # sprites
        self.background = pygame.image.load('./images/bg.png').convert()
        sprite_frog_up = pygame.image.load('./images/sprite_sheets_up.png').convert_alpha()
        sprite_frog_down = pygame.image.load('./images/sprite_sheets_down.png').convert_alpha()
        sprite_frog_left = pygame.image.load('./images/sprite_sheets_left.png').convert_alpha()
        sprite_frog_right = pygame.image.load('./images/sprite_sheets_right.png').convert_alpha()
        self.frog_sprites = {ACTION_UP_KEY: sprite_frog_up,
                             ACTION_DOWN_KEY: sprite_frog_down,
                             ACTION_LEFT_KEY: sprite_frog_left,
                             ACTION_RIGHT_KEY: sprite_frog_right}

        self.sprite_arrived = pygame.image.load('./images/frog_arrived.png').convert_alpha()

        sprite_car1 = pygame.image.load('./images/car1.png').convert_alpha()
        sprite_car2 = pygame.image.load('./images/car2.png').convert_alpha()
        sprite_car3 = pygame.image.load('./images/car3.png').convert_alpha()
        sprite_car4 = pygame.image.load('./images/car4.png').convert_alpha()
        sprite_car5 = pygame.image.load('./images/car5.png').convert_alpha()
        self.car_sprites = [sprite_car1, sprite_car2, sprite_car3, sprite_car4, sprite_car5]

        self.log_sprite = pygame.image.load('./images/tronco.png').convert_alpha()

        # sound effects
        if self.sound:
            self.hit_sound = pygame.mixer.Sound('./sounds/boom.wav')
            self.water_sound = pygame.mixer.Sound('./sounds/agua.wav')
            self.arrived_sound = pygame.mixer.Sound('./sounds/success.wav')
            pygame.mixer.Sound('./sounds/guimo.wav').play(-1)

        pygame.display.set_caption('Frogger')

        self.game_init = True

    def _create_cars(self):
        for i, tick in enumerate(self.ticks_cars):
            self.ticks_cars[i] -= 1
            if tick > 0:
                continue
            if i == 0:
                self.ticks_cars[0] = (40 * self.game.speed) / self.game.level
                position_init = [-55, 436]
                car = Car(position_init, self.car_sprites[i], 'right', 1)
                self.cars.append(car)
            elif i == 1:
                self.ticks_cars[1] = (30 * self.game.speed) / self.game.level
                position_init = [506, 397]
                car = Car(position_init, self.car_sprites[i], 'left', 2)
                self.cars.append(car)
            elif i == 2:
                self.ticks_cars[2] = (40 * self.game.speed) / self.game.level
                position_init = [-80, 357]
                car = Car(position_init, self.car_sprites[i], 'right', 2)
                self.cars.append(car)
            elif i == 3:
                self.ticks_cars[3] = (30 * self.game.speed) / self.game.level
                position_init = [516, 318]
                car = Car(position_init, self.car_sprites[i], 'left', 1)
                self.cars.append(car)
            elif i == 4:
                self.ticks_cars[4] = (50 * self.game.speed) / self.game.level
                position_init = [-56, 280]
                car = Car(position_init, self.car_sprites[i], 'right', 1)
                self.cars.append(car)

    def _destroy_cars(self):
        for i in self.cars:
            if i.position[0] < -80:
                self.cars.remove(i)
            elif i.position[0] > 516:
                self.cars.remove(i)

    def _create_logs(self):
        for i, tick in enumerate(self.ticks_logs):
            self.ticks_logs[i] = self.ticks_logs[i] - 1
            if tick > 0:
                continue
            if i == 0:
                self.ticks_logs[0] = (30 * self.game.speed) / self.game.level
                position_init = [-100, 200]
                log = Log(position_init, self.log_sprite, 'right')
                self.logs.append(log)
            elif i == 1:
                self.ticks_logs[1] = (30 * self.game.speed) / self.game.level
                position_init = [448, 161]
                log = Log(position_init, self.log_sprite, 'left')
                self.logs.append(log)
            elif i == 2:
                self.ticks_logs[2] = (40 * self.game.speed) / self.game.level
                position_init = [-100, 122]
                log = Log(position_init, self.log_sprite, 'right')
                self.logs.append(log)
            elif i == 3:
                self.ticks_logs[3] = (40 * self.game.speed) / self.game.level
                position_init = [448, 83]
                log = Log(position_init, self.log_sprite, 'left')
                self.logs.append(log)
            elif i == 4:
                self.ticks_logs[4] = (20 * self.game.speed) / self.game.level
                position_init = [-100, 44]
                log = Log(position_init, self.log_sprite, 'right')
                self.logs.append(log)

    def _destroy_logs(self):
        for i in self.logs:
            if i.position[0] < -100:
                self.logs.remove(i)
            elif i.position[0] > 448:
                self.logs.remove(i)

    def _frog_on_the_street(self):
        for car in self.cars:
            car_rect = car.rect()
            frog_rect = self.frog.rect()
            if frog_rect.colliderect(car_rect):
                if self.sound:
                    self.hit_sound.play()
                self.frog.set_dead(self.game)
                self.game.points += self.rewards[HIT_CAR_RWD_ATTR]
                break

    def _frog_in_the_lake(self):
        safe = False
        log_dir = ''
        for log in self.logs:
            log_rect = log.rect()
            frog_rect = self.frog.rect()
            if frog_rect.colliderect(log_rect):
                safe = True
                log_dir = log.way
                break

        if not safe:
            if self.sound:
                self.water_sound.play()
            self.frog.set_dead(self.game)
            self.game.points += self.rewards[HIT_WATER_RWD_ATTR]

        else:
            if log_dir == 'right':
                self.frog.position[0] += self.game.speed

            elif log_dir == 'left':
                self.frog.position[0] -= self.game.speed

    def _occupied(self, position):
        return any([fg.position == position for fg in self.arrived_frogs])

    def _check_frog_arrived(self):
        if 33 < self.frog.position[0] < 53 and not self._occupied([43, 7]):
            position_init = [43, 7]
            self._create_arrived(position_init)

        elif 115 < self.frog.position[0] < 135 and not self._occupied([125, 7]):
            position_init = [125, 7]
            self._create_arrived(position_init)

        elif 197 < self.frog.position[0] < 217 and not self._occupied([207, 7]):
            position_init = [207, 7]
            self._create_arrived(position_init)

        elif 279 < self.frog.position[0] < 299 and not self._occupied([289, 7]):
            position_init = [289, 7]
            self._create_arrived(position_init)

        elif 361 < self.frog.position[0] < 381 and not self._occupied([371, 7]):
            position_init = [371, 7]
            self._create_arrived(position_init)
        else:
            self.frog.position[1] = 46
            self.frog.animation_counter = 0
            self.frog.is_moving = False

    def _check_frog_location(self):
        # if frog is crossing the road
        if 241 < self.frog.position[1] < 475:
            self._frog_on_the_street()

        # if frog is in the river river
        elif 40 < self.frog.position[1] < 241:
            self._frog_in_the_lake()

        # frog achieved final position
        elif self.frog.position[1] < 40:
            self._check_frog_arrived()

    def _create_arrived(self, position_init):
        frog_arrived = Object(position_init, self.sprite_arrived)

        if self.sound:
            self.arrived_sound.play()
        self.arrived_frogs.append(frog_arrived)
        self.frog.set_to_initial_position()
        self.frog.animation_counter = 0
        self.frog.is_moving = False
        self.game.points += self.game.level * self.rewards[FROG_ARRIVED_RWD_ATTR]

    def _check_next_level(self):
        if len(self.arrived_frogs) < self.num_arrived_frogs:
            return

        self.arrived_frogs = []
        self.frog.set_to_initial_position()
        self.game.level += 1
        self.game.speed += 1
        self.game.points += self.game.level * self.rewards[NEW_LEVEL_RWD_ATTR]


class Object(object):
    def __init__(self, position, sprite):
        self.sprite = sprite
        self.position = position

    def draw(self, screen):
        screen.blit(self.sprite, tuple(self.position))

    def rect(self):
        return Rect(self.position[0], self.position[1], self.sprite.get_width(), self.sprite.get_height())


class Frog(Object):
    def __init__(self, position, sprite, lives, frog_sprites):
        super().__init__(position, sprite)
        self.frog_sprites = frog_sprites
        self.lives = lives
        self.animation_counter = 0
        self.way = ACTION_UP_KEY
        self.is_moving = False
        self.init_position = position.copy()

    def update_sprite(self, key_pressed):
        if self.way == key_pressed or key_pressed not in self.frog_sprites:
            return
        self.way = key_pressed
        self.sprite = self.frog_sprites[key_pressed]

    def move(self, key_pressed):
        if not self.is_moving:
            return

        if key_pressed == ACTION_UP_KEY:
            if self.position[1] > 39:
                self.position[1] -= 9 if self.animation_counter == ANIMATIONS_PER_MOVE - 1 else 10
        elif key_pressed == ACTION_DOWN_KEY:
            if self.position[1] <= 471:
                self.position[1] += 9 if self.animation_counter == ANIMATIONS_PER_MOVE - 1 else 10
        elif key_pressed == ACTION_LEFT_KEY:
            if self.position[0] > 2:
                self.position[0] -= 11 if self.animation_counter == ANIMATIONS_PER_MOVE - 1 else 10
        elif key_pressed == ACTION_RIGHT_KEY:
            if self.position[0] <= 407:
                self.position[0] += 11 if self.animation_counter == ANIMATIONS_PER_MOVE - 1 else 10

    def animate(self):
        if not self.is_moving:
            return

        self.animation_counter += 1
        if self.animation_counter == ANIMATIONS_PER_MOVE:
            self.animation_counter = 0
            self.is_moving = False

    def set_dead(self, game):
        game.reset_steps()
        self.set_to_initial_position()
        self.lives -= 1
        self.animation_counter = 0
        self.is_moving = False
        self.update_sprite(ACTION_UP_KEY)

    def set_to_initial_position(self):
        self.position = self.init_position.copy()

    def draw(self, screen):
        current_sprite = self.animation_counter * 30
        screen.blit(self.sprite, tuple(self.position), (current_sprite, 0, 30, 30 + current_sprite))

    def rect(self):
        return Rect(self.position[0], self.position[1], 30, 30)


class Car(Object):
    def __init__(self, position, sprite, way, factor):
        super().__init__(position, sprite)
        self.way = way
        self.factor = factor

    def move(self, speed):
        if self.way == 'right':
            self.position[0] = self.position[0] + speed * self.factor
        elif self.way == 'left':
            self.position[0] = self.position[0] - speed * self.factor


class Log(Object):
    def __init__(self, position, sprite, way):
        super().__init__(position, sprite)
        self.way = way

    def move(self, speed):
        if self.way == 'right':
            self.position[0] = self.position[0] + speed
        elif self.way == 'left':
            self.position[0] = self.position[0] - speed


class Game(object):
    def __init__(self, speed, level, max_steps):
        self.speed = speed
        self.level = level
        self.points = 0
        self.steps = self.max_steps = max_steps
        self.gameInit = 0

    def reset_steps(self):
        self.steps = self.max_steps
