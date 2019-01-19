__author__ = 'Pedro Sequeira'

import numpy as np
from pygame.constants import K_UP, K_DOWN, K_LEFT, K_RIGHT

# constants
HEIGHT = 546
WIDTH = 448
CELL_WIDTH = 41
CELL_HEIGHT = 39
FROG_INIT_POS = [207, 475]
ARRIVAL_POSITIONS = [43, 125, 207, 289, 371]
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
        self.game_steps = 0
        self.game_level = 0
        self.game_points = 0.
        self.lives = 0
        self.arrived_frogs = [0] * len(ARRIVAL_POSITIONS)
        self.frog_rec = []
        self.car_recs = []
        self.log_recs = []

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
        game_state.game_steps = game.steps
        game_state.game_level = game.level
        game_state.game_points = game.points
        game_state.lives = frog.lives

        # checks frog arrived indexes
        for arrived_frog in arrived_frogs:
            for i, arrival_x in enumerate(ARRIVAL_POSITIONS):
                if arrived_frog.position[0] == ARRIVAL_POSITIONS[i]:
                    game_state.arrived_frogs[i] = 1
                    break

        game_state.car_recs = [game_state._get_rect(car) for car in cars]
        game_state.log_recs = [game_state._get_rect(log) for log in logs]

        # correct frog rectangle width due to animations
        game_state.frog_rec = game_state._get_rect(frog)
        game_state.frog_rec[2] /= ANIMATIONS_PER_MOVE

        return game_state

    @staticmethod
    def from_observation(obs):
        """
        Creates a frogger state from the given observation.
        :param lst obs: the array with the game observation we want to convert.
        :return FroggerState: the state corresponding to the given observation.
        """
        game_state = FroggerState()
        game_state.game_steps = int(obs[0])
        game_state.game_level = int(obs[1])
        game_state.game_points = obs[2].item()
        game_state.lives = int(obs[3])
        game_state.arrived_frogs = obs[4:9].astype(int).tolist()
        game_state.frog_rec = obs[9:13].tolist()

        # reads cars until reaching separator
        idx = 13
        while True:
            if obs[idx] == OBS_SEPARATOR:
                break
            game_state.car_recs.append(obs[idx:idx + 4].tolist())
            idx += 4

        # reads logs
        for idx in range(idx + 1, len(obs), 4):
            game_state.log_recs.append(obs[idx:idx + 4].tolist())

        return game_state

    def to_observation(self):
        """
        Converts the frogger state into a numeric array suitable to represent observation features.
        :return np.array: an array containing all this states' features.
        """

        # add game stats and frog info
        obs_list = [self.game_steps,
                    self.game_level,
                    self.game_points,
                    self.lives]

        obs_list.extend(self.arrived_frogs)

        # adds frog and car rectangles
        obs_list.extend(self.frog_rec)
        for car_rec in self.car_recs:
            obs_list.extend(car_rec)

        # puts separator before logs rectangles
        obs_list.append(OBS_SEPARATOR)
        for log_rec in self.log_recs:
            obs_list.extend(log_rec)

        return np.array(obs_list)

    @staticmethod
    def _get_rect(obj):
        """
        Gets the rectangle coordinates for the given object.
        :param Object obj: the object from which to retrieve the coordinates.
        :return list: a list with the rectangle coordinates ([x, y, w, h]) of the object.
        """
        return [obj.position[0], obj.position[1], obj.sprite.get_width(), obj.sprite.get_height()]
