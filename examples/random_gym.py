__author__ = 'Pedro Sequeira'

import gym
from gym.wrappers import Monitor
from os import makedirs
from os.path import exists
from frogger.gym import *
from frogger import FroggerState, CELL_WIDTH, CELL_HEIGHT

GYM_ENV_ID = 'Custom-Frogger-v0'

# default profile
register(
    id=GYM_ENV_ID,
    kwargs={MAX_STEPS_ATTR: DEFAULT_MAX_STEPS, LIVES_ATTR: DEFAULT_LIVES, FPS_ATTR: 30, FORCE_FPS_ATTR: True},
    entry_point=FROGGER_ENTRY_POINT_STR,
    tags={MAX_EPISODE_STEPS_ATTR: DEFAULT_MAX_STEPS * DEFAULT_LIVES},
    nondeterministic=False,
)


def clean_console():
    os.system('cls' if os.name == 'nt' else 'clear')


if __name__ == '__main__':

    env = gym.make(GYM_ENV_ID)
    out_dir = 'results_gym_frogger'
    if not exists(out_dir):
        makedirs(out_dir)

    env = Monitor(env, directory=out_dir, force=True)
    env.seed(0)

    action_names = list(env.env.env.game_state.game.actions.keys())

    episode_count = 100
    reward = 0
    done = False

    for i in range(episode_count):
        ob = env.reset()

        t = 0
        while True:
            print(t)
            action = env.action_space.sample()
            obs, reward, done, _ = env.step(action)
            env.render()

            clean_console()
            state = FroggerState.from_observation(obs)
            x = (state.frog_position[0] - 2) / CELL_WIDTH
            y = (state.frog_position[1] - 46) / CELL_HEIGHT
            print('action: ', action_names[action])
            print('frog cell: ({},{})'.format(int(x), int(y)))

            if done:
                break
            t += 1

    env.close()
