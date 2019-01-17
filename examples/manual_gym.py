__author__ = 'Pedro Sequeira'

import gym
from collections import OrderedDict
from frogger import FroggerState, CELL_WIDTH, CELL_HEIGHT
from frogger.ple import ACTION_LEFT_KEY, ACTION_RIGHT_KEY, ACTION_UP_KEY, ACTION_DOWN_KEY
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
            NUM_ARRIVED_FROGS_ATTR: NUM_ARRIVED_FROGS, FORCE_FPS_ATTR: True, FPS_ATTR: 15},
    entry_point=FROGGER_ENTRY_POINT_STR,
    tags={MAX_EPISODE_STEPS_ATTR: NAX_STEPS * DEFAULT_LIVES},
    nondeterministic=False,
)


def clean_console():
    os.system('cls' if os.name == 'nt' else 'clear')


def convert_key(key):
    if key == 65362:
        key = 273
    elif key == 65364:
        key = 274
    elif key == 65361:
        key = 276
    elif key == 65363:
        key = 275
    elif key == 65505:
        key = 304
    return key


def key_press(key, _):
    key = convert_key(key)
    pressed.add(key)


if __name__ == '__main__':
    env = gym.make(GAME_GYM_ID)
    action_set = list(ACTIONS.values())
    action_names = list(ACTIONS.keys())

    pressed = set()
    released = set()

    env.render()
    env.unwrapped.viewer.window.on_key_press = key_press

    window_still_open = True
    while window_still_open:

        obs = env.reset()

        total_reward = 0
        total_time_steps = 0
        done = False
        while not done:

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
            x = (state.frog_position[0] - 2) / CELL_WIDTH
            y = (state.frog_position[1] - 46) / CELL_HEIGHT
            print('frog pos: ({},{})'.format(state.frog_position[0], state.frog_position[1]))
            print('frog cell: ({},{})'.format(x, y))

            total_reward += rwd
            total_time_steps += 1
            window_still_open = env.render()

        print('time steps: {}, total reward: {}'.format(total_time_steps, total_reward))
