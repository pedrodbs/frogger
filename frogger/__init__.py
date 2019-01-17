__author__ = 'Pedro Sequeira'

CELL_WIDTH = 41
CELL_HEIGHT = 39
OBS_SEPARATOR = 98.7654321


class FroggerState(object):
    """
    Corresponds to a description of a Frogger game, including the game elements and the frog, cars and logs positions.
    """

    def __init__(self):
        self.game_steps = 0
        self.game_level = 0
        self.game_points = 0
        self.num_arrived_frogs = 0
        self.lives = 0
        self.frog_position = [0, 0]
        self.car_positions = []
        self.log_positions = []

    @staticmethod
    def from_observation(obs):
        """
        Reads a game state from the given obs
        :param lst obs: the array with the game obs we want to convert.
        :return FroggerState: the frogger game state corresponding to the given obs.
        """

        state = FroggerState()
        state.game_steps = obs[0]
        state.game_level = obs[1]
        state.game_points = obs[2]
        state.num_arrived_frogs = obs[3]
        state.lives = obs[4]
        state.frog_position = [obs[5], obs[6]]

        idx = 7
        while True:
            if obs[idx] == OBS_SEPARATOR:
                break

            state.car_positions.append([obs[idx], obs[idx + 1]])
            idx += 2

        for idx in range(idx + 1, len(obs), 2):
            state.log_positions.append([obs[idx], obs[idx + 1]])

        return state
