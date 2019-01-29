__author__ = 'Pedro Sequeira'

import gym
import pygame
from os import makedirs
from os.path import exists
from collections import OrderedDict
from gym.wrappers import Monitor
from frogger import FroggerState, CELL_WIDTH, CELL_HEIGHT, ACTION_LEFT_KEY, ACTION_RIGHT_KEY, ACTION_UP_KEY, \
    ACTION_DOWN_KEY
from frogger.gym import *

GAME_GYM_ID = 'Frogger-Custom-v0'
NAX_STEPS = 300
NUM_ARRIVED_FROGS = 2
ACTIONS = OrderedDict([
    ('up', ACTION_UP_KEY),
    ('down', ACTION_DOWN_KEY),
    ('left', ACTION_LEFT_KEY),
    ('right', ACTION_RIGHT_KEY)])

register(
    id=GAME_GYM_ID,
    kwargs={MAX_STEPS_ATTR: NAX_STEPS, LIVES_ATTR: DEFAULT_LIVES, ACTIONS_ATTR: ACTIONS,
            NUM_ARRIVED_FROGS_ATTR: NUM_ARRIVED_FROGS, FORCE_FPS_ATTR: True, FPS_ATTR: 20, DISPLAY_SCREEN_ATTR: True},
    entry_point=FROGGER_ENTRY_POINT_STR,
    tags={MAX_EPISODE_STEPS_ATTR: NAX_STEPS * DEFAULT_LIVES},
    nondeterministic=False,
)


def clean_console():
    os.system('cls' if os.name == 'nt' else 'clear')


def process_keys():
    # prevent events from going to the game
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()
        if event.type == pygame.KEYDOWN:
            pressed.add(event.key)


if __name__ == '__main__':
    env = gym.make(GAME_GYM_ID)
    out_dir = 'results_gym_frogger'
    if not exists(out_dir):
        makedirs(out_dir)

    env = Monitor(env, directory=out_dir, force=True, video_callable=lambda _: True)
    env.seed(0)
    env.env.env.monitor = env

    action_set = list(ACTIONS.values())
    action_names = list(ACTIONS.keys())

    pressed = set()

    window_still_open = True
    while window_still_open:

        obs = env.reset()

        total_reward = 0
        total_time_steps = 0
        done = False
        while not done:

            process_keys()
            actionList = list(pressed)
            action = actionList[0] if len(actionList) == 1 else None if len(actionList) == 0 else actionList
            action_index = None

            if action is not None:
                for i in range(len(ACTIONS)):
                    if action_set[i] is not None:
                        if type(action) == int:
                            if action_set[i] == action:
                                action_index = i
                                break
                        elif type(action_set[i]) != int:
                            if set(action_set[i]) == set(action):
                                action_index = i
                                break

            if action_index is not None:
                print('action: ', action_names[action_index])
            obs, rwd, done, info = env.step(action_index)

            pressed = set()

            if rwd != 0 and action_index is not None:
                print('reward {}'.format(rwd))

            clean_console()
            state = FroggerState.from_observation(obs)
            x = (state.frog_info[0] - 2) / CELL_WIDTH
            y = (state.frog_info[1] - 46) / CELL_HEIGHT
            print('frog pos: ({},{})'.format(state.frog_info[0], state.frog_info[1]))
            print('frog cell: ({},{})'.format(x, y))

            total_reward += rwd
            total_time_steps += 1
            window_still_open = env.render() is not None

        print('time steps: {}, total reward: {}'.format(total_time_steps, total_reward))
