__author__ = 'Pedro Sequeira'

import os
import numpy as np
from gym import Env, spaces
from gym.envs import register
from ple import PLE
from frogger.ple import Frogger, HEIGHT, WIDTH, ANIMATIONS_PER_MOVE

FROGGER_ENTRY_POINT_STR = 'frogger.gym:FroggerEnv'
MAX_EPISODE_STEPS_ATTR = 'wrapper_config.TimeLimit.max_episode_steps'

FPS_ATTR = 'fps'
DISPLAY_SCREEN_ATTR = 'display_screen'
ADD_NOOP_ACTION_ATTR = 'add_noop_action'
ACTIONS_ATTR = 'actions'
REWARDS_ATTR = 'rewards'
LIVES_ATTR = 'lives'
SPEED_ATTR = 'speed'
LEVEL_ATTR = 'level'
NUM_ARRIVED_FROGS_ATTR = 'num_arrived_frogs'
MAX_STEPS_ATTR = 'max_steps'
FORCE_FPS_ATTR = 'force_fps'
SHOW_STATS_ATTR = 'show_stats'
SOUND_ATTR = 'sound'

DEFAULT_MAX_STEPS = 300
DEFAULT_LIVES = 3
DEFAULT_GYM_ENV_ID = 'Frogger-v0'

# default profile
register(
    id=DEFAULT_GYM_ENV_ID,
    kwargs={MAX_STEPS_ATTR: DEFAULT_MAX_STEPS, LIVES_ATTR: DEFAULT_LIVES},
    entry_point=FROGGER_ENTRY_POINT_STR,
    tags={MAX_EPISODE_STEPS_ATTR: DEFAULT_MAX_STEPS * DEFAULT_LIVES},
    nondeterministic=False,
)


class FroggerEnv(Env):
    metadata = {'render.modes': ['human', 'rgb_array']}

    def __init__(self, fps=30, display_screen=True, add_noop_action=False, actions=None, rewards=None,
                 lives=3, speed=3, level=1, num_arrived_frogs=5, max_steps=1000, force_fps=False,
                 show_stats=True, sound=True):
        self.metadata['video.frames_per_second'] = fps

        # set headless mode if not displaying to screen
        if not display_screen:
            os.environ['SDL_VIDEODRIVER'] = 'dummy'

        # open up a game state to communicate with emulator
        game = Frogger(actions=actions, rewards=rewards, lives=lives, speed=speed, level=level,
                       num_arrived_frogs=num_arrived_frogs, max_steps=max_steps,
                       show_stats=show_stats, sound=sound)

        self.game_state = PLE(game, fps=fps, display_screen=display_screen, force_fps=not force_fps,
                              add_noop_action=add_noop_action)
        self.game_state.init()

        self._action_set = self.game_state.getActionSet()
        self.action_space = spaces.Discrete(len(self._action_set))
        self.observation_space = \
            spaces.Box(low=0, high=255, shape=self.game_state.game.getGameState().shape, dtype=np.uint8)

        self.previous_score = 0.
        self.last_action = None
        self.monitor = None

    def step(self, a):

        action = None if a is None else self._action_set[a]
        reward = 0.
        terminal = self.game_state.game_over()

        if not terminal:

            # sets action, activating necessary keys for PyGame
            self._set_action(action)

            # performs several updates to the game per action (move)
            for i in range(ANIMATIONS_PER_MOVE):
                if not self.game_state.force_fps:
                    self.game_state.game.tick(self.game_state.fps)
                self.game_state.game.step(0)
                self.game_state._draw_frame()

                # trick to update external Gym Monitor (frames within action) if one was provided
                if self.monitor is not None and i < ANIMATIONS_PER_MOVE - 1:
                    self.monitor.video_recorder.capture_frame()

            # gets total reward collected by this action
            reward = self._get_reward()

        state = self.game_state.game.getGameState()
        terminal = self.game_state.game_over()

        return state, reward, terminal, {}

    def reset(self):
        self.previous_score = 0.
        self.last_action = None
        self.game_state.reset_game()
        return self.game_state.game.getGameState()

    def render(self, mode='human', close=False):
        return self._get_image()

    def seed(self, seed=None):
        rng = self.game_state.rng = self.game_state.game.rng = np.random.RandomState(0 if seed is None else seed)
        self.game_state.init()
        return rng

    def _get_reward(self):
        cur_score = self.game_state.score()
        reward = cur_score - self.previous_score
        self.previous_score = cur_score
        return reward

    def _set_action(self, action):
        # if action is not None:
        self.game_state.game._setAction(action, self.last_action)
        self.last_action = action

    def _get_image(self):
        image_rotated = np.fliplr(
            np.rot90(self.game_state.getScreenRGB(), 3))  # Hack to fix the rotated image returned by ple
        return image_rotated

    @property
    def _n_actions(self):
        return len(self._action_set)
