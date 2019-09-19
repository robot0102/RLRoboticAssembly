import pybullet as p
import time

import numpy as np
from gym.utils import seeding

# choose the relevant robotic models
from envs.robot_sim_robotless_constraint import RobotSimRobotlessConstraint
from envs.task import Task


class TaskSim(Task):

    def __init__(self,
                 self_collision_enabled=True,
                 renders=False,
                 ft_noise=False,
                 pose_noise=False,
                 action_noise=False,
                 physical_noise=False):

        super().__init__(max_steps=4000,  # 6000
                         action_dim=6,
                         step_limit=True,
                         max_vel=0.008,  # 0.004 # m/sec
                         max_rad=0.002,  # 0.002 # rad/sec
                         ft_obs_only=False,
                         limit_ft=False)

        self._self_collision_enabled = self_collision_enabled
        self._renders = renders

        # parameters to control the level of domain randomization
        self._ft_noise = ft_noise
        self._ft_noise_level = [0.5, 0.5, 0.5, 0.05, 0.05, 0.05]  # N N N Nm Nm Nm
        self._ft_bias_level = [2.0, 2.0, 2.0, 0.2, 0.2, 0.2]  # N N N Nm Nm Nm
        self._ft_bias = 0.0
        self._pose_noise = pose_noise
        self._pos_noise_level = 0.001  # m
        self._orn_noise_level = 0.001  # rad
        self._action_noise = action_noise
        self._action_noise_lin = 0.001  # multiplier for linear translation
        self._action_noise_rot = 0.001  # multiplier for rotation
        self._physical_noise = physical_noise
        self._friction_noise_level = 0.1

        if self._renders:
            cid = p.connect(p.SHARED_MEMORY)
            if (cid < 0):
                cid = p.connect(p.GUI)
            p.resetDebugVisualizerCamera(0.6, 180, -41, [0, 0, 0])
        else:
            p.connect(p.DIRECT)

        # p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0)

        self.seed()

        self.viewer = None

    def reset(self):
        p.resetSimulation()
        p.setPhysicsEngineParameter(numSolverIterations=150, enableFileCaching=0)
        p.setTimeStep(self._time_step)
        p.setGravity(0, 0, 0)

        self.env = RobotSimRobotlessConstraint()
        self.max_dist = self.dist_to_target()
        # util.prGreen("max dist: {}".format(self.max_dist))

        self._env_step_counter = 0
        self.env.enable_force_torque_sensor()
        p.stepSimulation()

        self.correlated_noise()

        self._observation = self.get_extended_observation()
        self.add_observation_noise()

        return np.array(self._observation)

    def __del__(self):
        p.disconnect()

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def get_member_pose(self):
        return self.env.get_member_pose()

    def get_target_pose(self):
        return self.env.get_target_pose()

    def get_force_torque(self):
        return self.env.get_force_torque()

    def correlated_noise(self):
        # force torque sensor bias, sampled at the start of each episode
        if self._ft_noise:
            self._ft_bias = Task.add_gaussian_noise(0.0, self._ft_bias_level, [0] * len(self._ft_bias_level))

        # add some physical noise here
        if self._physical_noise:
            self.env.add_all_friction_noise(self._friction_noise_level)

    def uncorrelated_pose_noise(self, pos, orn):
        if self._pose_noise:
            pos = Task.add_gaussian_noise(0.0, self._pos_noise_level, pos)
            orn_euler = p.getEulerFromQuaternion(orn)
            orn_euler = Task.add_gaussian_noise(0.0, self._orn_noise_level, orn_euler)
            orn = p.getQuaternionFromEuler(orn_euler)

        return pos, orn

    def uncorrelated_position_noise(self, pos):
        if self._pose_noise:
            pos = Task.add_gaussian_noise(0.0, self._pos_noise_level, pos)

        return pos

    def add_ft_noise(self, force_torque):
        if self._ft_noise:
            force_torque = Task.add_gaussian_noise(0.0, self._ft_noise_level, force_torque)
            force_torque = np.add(force_torque, self._ft_bias).tolist()

        return force_torque

    def add_observation_noise(self):
        if not self._ft_obs_only:
            if self.action_dim > 3:
                self._observation[0:3], self._observation[3:7] = self.uncorrelated_pose_noise(self._observation[0:3],
                                                                                              self._observation[3:7])
                self._observation[7:13] = self.add_ft_noise(self._observation[7:13])
            else:
                self._observation[0:3] = self.uncorrelated_position_noise(self._observation[0:3])
                self._observation[3:9] = self.add_ft_noise(self._observation[3:9])
        else:
            self._observation[0:6] = self.add_ft_noise(self._observation[0:6])

    def step2(self, velocity):
        reward, done, num_success = self.reward()

        if not done:
            if self.action_dim > 3:
                self.env.apply_action_pose(velocity, self._time_step)
            else:
                self.env.apply_action_position(velocity, self._time_step)
        else:
            # util.prGreen('End of task')
            if self.action_dim > 3:
                self.env.apply_action_pose([0.0] * 6, self._time_step)
            else:
                self.env.apply_action_position([0.0] * 3, self._time_step)

        p.stepSimulation()
        self._env_step_counter += 1

        if self._renders:
            time.sleep(self._time_step)

        self._observation = self.get_extended_observation()
        self.add_observation_noise()

        return np.array(self._observation), reward, done, {"num_success": num_success}
