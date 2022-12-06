import gymnasium as gym
import numpy as np
import pygame
from gymnasium import spaces

"""
# Coordinate Systems for `.csv` and `print(numpy)`

X points down (rows); Y points right (columns); Z would point outwards.

*--> Y (columns: self.inFile.shape[1])
|
v
X (rows: self.inFile.shape[0])
"""

MAX_WINDOW_WIDTH, MAX_WINDOW_HEIGHT = 1920, 1080
COLOR_BACKGROUND = (0, 0, 0)
COLOR_WALL = (255, 255, 255)
COLOR_ROBOT = (255, 0, 0)

class GridWorldEnv(gym.Env):
    # classic "render_modes" use: "human" (pygame window), "rgb_array" (pygame raw data)
    metadata = {"render_modes": ["text", "pygame"], "render_fps": 4}

    def _2d_to_1d(self, value): # Flatten/ravel
        try:
            self.inFile[value[0]][value[1]]
        except IndexError as e:
            print('GridWorldEnv._2d_to_1d: full exception message:', e)
            print('GridWorldEnv._2d_to_1d: value out of bounds, please review code!')
            quit()
        return value[1]*self.inFile.shape[0] + value[0]

    def __init__(self, render_mode=None):
        # Remember: See "Coordinate Systems for `.csv` and `print(numpy)`", above.
        # hard-coded vars (begin)
        inFileStr = 'map1.csv'
        initX = 2
        initY = 2
        goalX = 7
        goalY = 2
        # hard-coded vars (end)

        self.inFile = np.genfromtxt(inFileStr, delimiter=',')

        try:
            self.inFile[initX][initY]
        except IndexError as e:
            print('GridWorldEnv.__init__: full exception message:', e)
            print('GridWorldEnv.__init__: init out of bounds, please review code!')
            quit()
        self._initial_agent_location = np.array([initX, initY])

        try:
            self.inFile[goalX][goalY] = 3 # The goal (3) is fixed, so we paint it, but the robot (2) moves, so done at render().
        except IndexError as e:
            print('GridWorldEnv.__init__: full exception message:', e)
            print('GridWorldEnv.__init__: goal out of bounds, please review code!')
            quit()

        self.nS = self.inFile.shape[0] * self.inFile.shape[1] # nS: number of states
        self.observation_space = spaces.Discrete(self.nS)

        self._action_to_direction = {
            0: np.array([-1,  0]),  # UP
            1: np.array([-1,  1]),  # UP_RIGHT
            2: np.array([ 0,  1]),  # RIGHT
            3: np.array([ 1,  1]),  # DOWN_RIGHT
            4: np.array([ 1,  0]),  # DOWN
            5: np.array([ 1, -1]),  # DOWN_LEFT
            6: np.array([ 0, -1]),  # LEFT
            7: np.array([-1, -1]),  # UP_LEFT
        }
        self.nA = 8 # nA: number of actions
        self.action_space = spaces.Discrete(self.nA)

        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode

        self.window = None
        self.clock = None

    def _get_obs(self):
        return self._2d_to_1d(self._agent_location)

    def _get_info(self):
        return {}

    def reset(self, seed=None, options=None):
        # We need the following line to seed self.np_random.
        super().reset(seed=seed)

        self._agent_location = self._initial_agent_location

        observation = self._get_obs()
        info = self._get_info()

        self.render()

        return observation, info

    def step(self, action):
        #print('GridWorldEnv.step', action)

        candidate_state = self._agent_location + self._action_to_direction[action]
        try:
            candidate_state_tag = self.inFile[candidate_state[0]][candidate_state[1]]
        except IndexError as e:
            # state preserved
            print('GridWorldEnv.step: full exception message:', e)
            print('GridWorldEnv.step: probably went out of bounds, add some walls on your map!')
            terminated = True
            quit()

        if candidate_state_tag == 0: # free space
            self._agent_location = candidate_state
            reward = 0
            terminated = False
        elif candidate_state_tag == 1: # wall
            # state preserved
            reward = -0.5
            terminated = True
        elif candidate_state_tag == 3: # goal
            self._agent_location = candidate_state
            reward = 1.0
            terminated = True
        else:
            print('GridWorldEnv.step: found wicked tag, please review!')
            terminated = True
            quit()

        observation = self._get_obs()
        info = self._get_info()

        return observation, reward, terminated, False, info

    def render(self):
        #print('GridWorldEnv.render', self.render_mode)
        if self.render_mode == "text":
            return self._render_text()
        if self.render_mode == "pygame": # "human" in tutorial
            return self._render_pygame()
        else: # None
            pass

    def _render_text(self):
        viewer = np.copy(self.inFile) # Force a deep copy for rendering.
        viewer[self._agent_location[0], self._agent_location[1]] = 2
        print(viewer)

    def _render_pygame(self):

        if self.window is None:
            inFileAspectRatio = self.inFile.shape[1] / self.inFile.shape[0]
            print('inFileAspectRatio',inFileAspectRatio)
            maxWindowAspectRatio = MAX_WINDOW_WIDTH / MAX_WINDOW_HEIGHT
            print('maxWindowAspectRatio',maxWindowAspectRatio)
            if inFileAspectRatio == maxWindowAspectRatio:
                self.WINDOW_WIDTH = MAX_WINDOW_WIDTH
                self.WINDOW_HEIGHT = MAX_WINDOW_HEIGHT
            elif inFileAspectRatio > maxWindowAspectRatio:
                print("inFileAspectRatio > maxWindowAspectRatio (panoramic)")
                self.WINDOW_WIDTH = MAX_WINDOW_WIDTH # same
                self.WINDOW_HEIGHT = MAX_WINDOW_WIDTH / inFileAspectRatio
            elif inFileAspectRatio < maxWindowAspectRatio:
                print("inFileAspectRatio > maxWindowAspectRatio (stand)")
                self.WINDOW_HEIGHT = MAX_WINDOW_HEIGHT # same
                self.WINDOW_WIDTH = MAX_WINDOW_HEIGHT * inFileAspectRatio
            pygame.init()
            pygame.display.init()
            self.window = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
            self.cellWidth = self.WINDOW_WIDTH/self.inFile.shape[1]
            self.cellHeight = self.WINDOW_HEIGHT/self.inFile.shape[0]
        if self.clock is None:
            self.clock = pygame.time.Clock()

        canvas = pygame.Surface((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        canvas.fill(COLOR_BACKGROUND)
        for iX in range(self.inFile.shape[0]):
            #print "iX:",iX
            for iY in range(self.inFile.shape[1]):
                #print "* iY:",iY

                #-- Skip box if map indicates a 0
                if self.inFile[iX][iY] == 0:
                    continue
                if self.inFile[iX][iY] == 1:
                    pygame.draw.rect(canvas,
                                     COLOR_WALL,
                                     pygame.Rect( self.cellWidth*iY, self.cellHeight*iX, self.cellWidth, self.cellHeight ))
                if self.inFile[iX][iY] == 3:
                    pygame.draw.rect(canvas, (0,255,0),
                                     pygame.Rect( self.cellWidth*iY, self.cellHeight*iX, self.cellWidth, self.cellHeight ))
                robot = pygame.draw.rect(canvas, COLOR_ROBOT,
                                         pygame.Rect( self.cellWidth*self._agent_location[1]+self.cellWidth/4.0, self.cellHeight*self._agent_location[0]+self.cellHeight/4.0, self.cellWidth/2.0, self.cellHeight/2.0 ))

        # The following line copies our drawings from `canvas` to the
        # visible window.
        self.window.blit(canvas, canvas.get_rect())
        pygame.event.pump()
        pygame.display.update()

        # We need to ensure that human-rendering occurs at the predefined framerate.
        # The following line will automatically add a delay to keep the
        # framerate stable.
        self.clock.tick(self.metadata["render_fps"])

    def close(self):
        print('GridWorldEnv.close')
        if self.window is not None:
            pygame.display.quit()
            pygame.quit()
