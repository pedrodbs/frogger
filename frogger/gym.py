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

        # set headless mode
        os.environ['SDL_VIDEODRIVER'] = 'dummy'

        # open up a game state to communicate with emulator
        game = Frogger(actions=actions, rewards=rewards, lives=lives, speed=speed, level=level,
                       num_arrived_frogs=num_arrived_frogs, max_steps=max_steps,
                       show_stats=show_stats, sound=sound)

        self.game_state = PLE(game, fps=fps, display_screen=display_screen, force_fps=not force_fps,
                              num_steps=ANIMATIONS_PER_MOVE, add_noop_action=add_noop_action)
        self.game_state.init()

        self._action_set = self.game_state.getActionSet()
        self.action_space = spaces.Discrete(len(self._action_set))
        self.screen_height = HEIGHT
        self.screen_width = WIDTH

        # sets appropriate obs space
        self.observation_space = \
            spaces.Box(low=0, high=255, shape=self.game_state.game.getGameState().shape, dtype=np.uint8)

        self.viewer = None

    def step(self, a):
        reward = self.game_state.act(None if a is None else self._action_set[a])
        state = self.game_state.game.getGameState()
        terminal = self.game_state.game_over()

        return state, reward, terminal, {}

    def reset(self):
        self.game_state.reset_game()
        return self.game_state.game.getGameState()

    def render(self, mode='human', close=False):
        if close:
            if self.viewer is not None:
                self.viewer.close()
                self.viewer = None
            return
        img = self._get_image()
        if mode == 'rgb_array':
            return img
        elif mode == 'human':
            from gym.envs.classic_control import rendering
            if self.viewer is None:
                self.viewer = rendering.SimpleImageViewer()
                self.viewer.imshow(img)

                # also set window size
                self.viewer.window.set_size(self.screen_width, self.screen_height)
            else:
                self.viewer.imshow(img)

    def seed(self, seed=None):
        rng = self.game_state.rng = self.game_state.game.rng = np.random.RandomState(0 if seed is None else seed)
        self.game_state.init()
        return rng

    def _get_image(self):
        image_rotated = np.fliplr(
            np.rot90(self.game_state.getScreenRGB(), 3))  # Hack to fix the rotated image returned by ple
        return image_rotated

    @property
    def _n_actions(self):
        return len(self._action_set)
