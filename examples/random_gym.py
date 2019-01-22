__author__ = 'Pedro Sequeira'

import gym
from gym.wrappers import Monitor
from os import makedirs
from os.path import exists
from frogger import FroggerState, CELL_WIDTH, CELL_HEIGHT
from frogger.gym import *

GYM_ENV_ID = 'Custom-Frogger-v0'

# default profile
register(
    id=GYM_ENV_ID,
    kwargs={MAX_STEPS_ATTR: DEFAULT_MAX_STEPS, LIVES_ATTR: DEFAULT_LIVES, FPS_ATTR: 4, FORCE_FPS_ATTR: False,
            SOUND_ATTR: False, DISPLAY_SCREEN_ATTR: False},
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

    env = Monitor(env, directory=out_dir, force=True, video_callable=lambda _: True)
    env.seed(0)
    env.env.env.monitor = env

    action_names = list(env.env.env.game_state.game.actions.keys())

    episode_count = 100
    reward = 0
    done = False

    for i in range(episode_count):
        ob = env.reset()

        t = 0
        while True:

            action = env.action_space.sample()
            obs, reward, done, _ = env.step(action)
            env.render()

            clean_console()
            state = FroggerState.from_observation(obs)
            x = (state.frog_rec[0] - 2) / CELL_WIDTH
            y = (state.frog_rec[1] - 46) / CELL_HEIGHT
            print('time:', t)
            print('action:', action_names[action])
            print('frog cell: ({},{})'.format(int(x), int(y)))

            if done:
                break
            t += 1

    env.close()
