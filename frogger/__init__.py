__author__ = 'Pedro Sequeira'

import numpy as np
from pygame.constants import K_UP, K_DOWN, K_LEFT, K_RIGHT

# constants
HEIGHT = 546
WIDTH = 440
CELL_WIDTH = 40
CELL_HEIGHT = 39
NUM_COLS = 11
NUM_ROWS = 12
MIN_Y_POS = 46
MAX_Y_POS = 475
MAX_GRASS_Y_POS = 241
FROG_SIZE = 30
FROG_INIT_POS = [200, MAX_Y_POS]
LOGS_INIT_POS = [[-100, 200], [448, 161], [-100, 122], [448, 83], [-100, 44]]
LOGS_INIT_TICKS = [30, 30, 40, 40, 20]
ARRIVAL_POSITIONS = [43, 125, 207, 289, 371]
ARRIVAL_WIDTH = 17
ARRIVAL_POSITION_Y = 7
CARS_INIT_POS = [[-55, 436], [506, 397], [-80, 357], [516, 318], [-56, 280]]
CARS_INIT_TICKS = [40, 30, 40, 30, 50]
CARS_SPEED_FACTORS = [1, 2, 2, 1, 1]
MAX_CAR_TICKS = 60
MAX_LOG_TICK = 30
ACTION_UP_KEY = K_UP
ACTION_DOWN_KEY = K_DOWN
ACTION_LEFT_KEY = K_LEFT
ACTION_RIGHT_KEY = K_RIGHT
ACTION_NO_MOVE_KEY = None
INVALID_ACTION_KEY = -1
ANIMATIONS_PER_MOVE = 4
DEATH_IMAGE_TIME_STEPS = 4
TXT_COLOR = 220

HIT_CAR_RWD_ATTR = 'hit-car-rwd'
HIT_WATER_RWD_ATTR = 'water-rwd'
TIME_UP_RWD_ATTR = 'time-up-rwd'
NO_LIVES_RWD_ATTR = 'no-lives-rwd'
NEW_LEVEL_RWD_ATTR = 'level-rwd'
FROG_ARRIVED_RWD_ATTR = 'frog-arrived-rwd'
TICK_RWD_ATTR = 'tick-rwd'

OBS_SEPARATOR = 9876.54321


class FroggerState(object):
    """
    Corresponds to a description of a Frogger game, including the game elements and the frog, cars and logs positions.
    """

    def __init__(self):
        """
        Creates a new empty frogger state based on the given Frogger instance.
        """
        self.steps = 0
        self.level = 0
        self.points = 0.
        self.lives = 0
        self.arrived_frogs = [False] * len(ARRIVAL_POSITIONS)
        self.frog_info = []
        self.car_infos = []
        self.log_infos = []

    @staticmethod
    def from_game(game, arrived_frogs, frog, cars, logs):
        """
        Creates a new frogger state from the given Frogger game instance.
        :param Game game: the object with the game information.
        :param list arrived_frogs: list of frogs that reached a lily pad.
        :param Frog frog: the current frog.
        :param list cars: list of car objects.
        :param list logs: list of log objects.
        :return FroggerState: the state corresponding to the given Frogger instance.
        """
        game_state = FroggerState()
        game_state.steps = game.steps
        game_state.level = game.level
        game_state.points = game.points
        game_state.lives = frog.lives

        # checks frog arrived indexes
        for arrived_frog in arrived_frogs:
            for i, arrival_x in enumerate(ARRIVAL_POSITIONS):
                if arrived_frog.position[0] == ARRIVAL_POSITIONS[i]:
                    game_state.arrived_frogs[i] = True
                    break

        game_state.car_infos = [game_state._get_obj_info(car) for car in cars]
        game_state.log_infos = [game_state._get_obj_info(log) for log in logs]

        # correct frog width width due to animations
        game_state.frog_info = game_state._get_obj_info(frog)
        game_state.frog_info[2] /= ANIMATIONS_PER_MOVE

        return game_state

    @staticmethod
    def from_observation(obs):
        """
        Creates a frogger state from the given observation.
        :param lst obs: the array with the game observation we want to convert.
        :return FroggerState: the state corresponding to the given observation.
        """
        game_state = FroggerState()
        game_state.steps = int(obs[0])
        game_state.level = int(obs[1])
        game_state.points = obs[2].item()
        game_state.lives = max(0, int(obs[3]))
        game_state.arrived_frogs = obs[4:9].astype(bool).tolist()
        game_state.frog_info = obs[9:14].tolist()

        # reads cars until reaching separator
        idx = 14
        info_size = 5
        while True:
            if obs[idx] == OBS_SEPARATOR:
                break
            game_state.car_infos.append(obs[idx:idx + info_size].tolist())
            idx += info_size

        # reads logs
        for idx in range(idx + 1, len(obs), info_size):
            game_state.log_infos.append(obs[idx:idx + info_size].tolist())

        return game_state

    def to_observation(self):
        """
        Converts the frogger state into a numeric array suitable to represent observation features.
        :return np.array: an array containing all this states' features.
        """

        # add game stats and frog info
        obs_list = [self.steps,
                    self.level,
                    self.points,
                    self.lives]

        obs_list.extend(np.array(self.arrived_frogs, dtype=int))

        # adds frog and car rectangles
        obs_list.extend(self.frog_info)
        for car_rec in self.car_infos:
            obs_list.extend(car_rec)

        # puts separator before logs rectangles
        obs_list.append(OBS_SEPARATOR)
        for log_rec in self.log_infos:
            obs_list.extend(log_rec)

        return np.array(obs_list)

    @staticmethod
    def _get_obj_info(obj):
        """
        Gets the info for the given object, including its position, size and direction key.
        :param Object obj: the object from which to retrieve the coordinates.
        :return list: a list with the object information, namely [x, y, width, height, dir].
        """
        return [obj.position[0], obj.position[1], obj.sprite.get_width(), obj.sprite.get_height(), obj.way]
