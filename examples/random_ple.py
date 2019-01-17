__author__ = 'Pedro Sequeira'

import os
import numpy as np
from ple import PLE
from frogger import FroggerState, CELL_WIDTH, CELL_HEIGHT
from frogger.ple import Frogger, ANIMATIONS_PER_MOVE


def clean_console():
    os.system('cls' if os.name == 'nt' else 'clear')


if __name__ == '__main__':

    game = Frogger(sound=False)
    p = PLE(game, fps=30, display_screen=True, force_fps=False, num_steps=ANIMATIONS_PER_MOVE, add_noop_action=False)

    p.init()
    action_set = p.getActionSet()
    action_names = list(game.actions.keys())
    reward = 0.0

    episode_count = 100
    for i in range(episode_count):

        t = 0
        while True:
            action = action_set[np.random.randint(0, len(action_set))]
            reward = p.act(action)
            obs = p.getGameState()

            clean_console()
            state = FroggerState.from_observation(obs)
            x = (state.frog_position[0] - 2) / CELL_WIDTH
            y = (state.frog_position[1] - 46) / CELL_HEIGHT
            print('action: ', action_names[action_set.index(action)])
            print('frog cell: ({},{})'.format(x, y))

            t += 1
            if p.game_over():
                p.reset_game()
                break
