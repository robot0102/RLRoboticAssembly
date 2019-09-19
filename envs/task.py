import math
from abc import ABC, abstractmethod

import gym
import numpy as np
from gym import spaces

import utilities as util
from envs.mpose import PoseHandlerMixin

WRITE_CSV = False


class Task(PoseHandlerMixin, ABC, gym.Env):

    def __init__(self,
                 max_steps=None,
                 action_dim=None,
                 step_limit=None,
                 max_vel=None,  # m/sec
                 max_rad=None,  # rad/sec
                 ft_obs_only=None,
                 limit_ft=None):
        super().__init__()

        self._max_step = max_steps
        self._step_limit = step_limit
        # max linear and rotational velocity command
        self._max_vel = max_vel
        self._max_rad = max_rad
        # only use force torque as observation
        self._ft_obs_only = ft_obs_only

        self._time_step = 1. / 250.  # ARL: 1/250  GKR: 1/50
        self._observation = []
        self._env_step_counter = 0
        self._num_success = 0
        self._largeValObservation = 100  # TODO: arbitrary. Pose and FT observations should be different.

        self._limit_force_torque = limit_ft
        self._max_force_torque = [667.233, 667.233, 2001.69, 67.7908, 67.7908, 67.7908]
        self._force_torque_violations = [0.0] * len(self._max_force_torque)
        self._ft_range_ratio = 1

        if self._ft_obs_only:
            self.observation_dim = 6
        elif action_dim > 3:
            self.observation_dim = 13
        else:
            self.observation_dim = 9
        observation_high = np.array([self._largeValObservation] * self.observation_dim)
        self.observation_space = spaces.Box(-observation_high, observation_high)

        self._action_bound = 1
        action_high = np.array([self._action_bound] * action_dim)
        self.action_space = spaces.Box(-action_high, action_high)
        self.action_dim = action_dim

        self.member_pose = []
        self.force_torque = []

        # csv headers
        if WRITE_CSV:
            util.write_csv(["step_member_pose", "pos_X", "pos_Y", "pos_Z", "qX", "qY", "qZ", "qW"], 'member_pose.csv',
                           True)
            util.write_csv(["step_ft", "Fx", "Fy", "Fz", "Tx", "Ty", "Tz"], 'ft_reading.csv', True)
            if self.action_dim == 3:
                util.write_csv(["step_actions", "vel_X", "vel_Y", "vel_Z"], 'data_out.csv', True)
            else:
                util.write_csv(["step_actions", "vel_X", "vel_Y", "vel_Z", "rot_vel_X", "rot_vel_Y", "rot_vel_Z"],
                               'data_out.csv', True)

    @abstractmethod
    def reset(self):
        pass

    def z_dist_to_target(self):
        member_pos = list(self.member_pose[0])
        member_z = member_pos[2]
        target_pos = list(self.get_target_pose()[0])
        target_z = target_pos[2]
        return np.fabs(member_z - target_z)

    def pos_dist_to_target(self):
        self.member_pose = self.get_member_pose()

        # log
        if WRITE_CSV:
            util.write_csv([self._env_step_counter] + self.member_pose[0] + self.member_pose[1], 'member_pose.csv',
                           False)

        member_pos = list(self.member_pose[0])

        target_pose = self.get_target_pose()
        target_pos = list(target_pose[0])

        dist_pos = np.linalg.norm(np.subtract(member_pos, target_pos))
        # util.prGreen("pos dist: {}".format(dist_pos))

        return dist_pos

    def orn_dist_to_target(self):
        member_orn = list(self.member_pose[1])

        target_pose = self.get_target_pose()
        target_orn = list(target_pose[1])

        dist_orn = 1 - (np.dot(member_orn, target_orn)) ** 2
        # util.prGreen("orn dist: {}".format(dist_orn))

        return dist_orn

    def dist_to_target(self):
        dist_pos = self.pos_dist_to_target()
        dist = dist_pos

        if self.action_dim > 3:
            dist_orn = self.orn_dist_to_target()
            dist = dist_pos + dist_orn

        return dist

    def get_extended_observation(self):
        self._observation = []

        if not self._ft_obs_only:
            # get member pose
            if self.action_dim > 3:
                pos, orn = self.member_pose[0], self.member_pose[1]
                # util.prGreen('Euler: {}'.format(util.quat_to_euler(orn, 'sxyz')))
                self._observation.extend(pos)
                self._observation.extend(orn)
            else:
                pos = self.member_pose[0]
                self._observation.extend(pos)

        self.force_torque = self.get_force_torque()
        # util.prGreen(self.force_torque)

        if WRITE_CSV:
            # log_real_force_torque = [v*0.2 for v in self.force_torque]  # real robot
            # util.write_csv([self._env_step_counter] + log_real_force_torque, 'ft_reading.csv', False)
            util.write_csv([self._env_step_counter] + self.force_torque, 'ft_reading.csv', False)

        if self._limit_force_torque:
            self.check_ft_limit(self.force_torque)
        # if self._force_torque_violations != [0]*len(self.force_torque):
        # 	util.prRed(self._force_torque_violations)

        self._observation.extend(self.force_torque)

        return self._observation

    def check_ft_limit(self, force_torque):
        # check force torque against limits
        self._force_torque_violations = Task.check_list_bounds(force_torque,
                                                               np.multiply(self._ft_range_ratio,
                                                                           self._max_force_torque))

    def constrain_velocity_for_ft(self, velocity):
        # stop (only) linear motion along the direction where force torque limit is violated

        force_list = self._force_torque_violations[0:3]
        torque_list = self._force_torque_violations[3:6]
        lin_vel = velocity[0:3]
        axes = ['x', 'y', 'z']

        for i in range(len(force_list)):
            if (force_list[i] != 0) & (np.sign(force_list[i]) != np.sign(lin_vel[i])):
                lin_vel[i] = -0.1 * lin_vel[i]

        for i in range(len(torque_list)):
            if torque_list[i] != 0:
                for j in range(len(torque_list)):
                    if j != i:
                        lin_vel[j] = 0.0

        velocity[0:3] = lin_vel

        return velocity

    def step(self, action):
        if len(action) > 3:
            vel_lin = np.array(action[0:3]) * self._max_vel
            vel_rot = np.array(action[3:6]) * self._max_rad
            velocity = np.append(vel_lin, vel_rot)
        else:
            velocity = np.array(action) * self._max_vel

        if self._limit_force_torque:
            self.constrain_velocity_for_ft(velocity)

        if WRITE_CSV:
            util.write_csv([self._env_step_counter] + list(velocity), 'data_out.csv', False)

        return self.step2(velocity)

    # To be overridden
    def step2(self, velocity):
        self._env_step_counter += 1
        reward, done, num_success = self.reward()
        self._observation = self.get_extended_observation()

        return np.array(self._observation), reward, done, {"num_success": num_success}

    def reward(self):

        done = False

        dist = self.dist_to_target()
        dist_threshold = 0.005
        # z_dist = self.z_dist_to_target()
        # z_dist_threshold = 0.001

        # a basic map function
        start1, stop1, start2, stop2 = dist_threshold, self.max_dist, 0, 1
        shaped_dist = start2 + (stop2 - start2) * ((dist - start1) / (stop1 - start1))
        shaped_dist = max(0, shaped_dist)
        # util.prGreen(shaped_dist)

        reward_dist = - dist
        # reward_dist = max(1, max(0, -math.log2(shaped_dist + 0.001))) - 1
        # if reward_dist >= 1:
        # 	reward_dist *= (1 - self._env_step_counter/self._max_step)

        reward_ft = 0
        # reward_ft = self.reward_force_torque()
        reward = reward_dist + 0.05 * reward_ft
        # util.prRed(reward)

        # util.prGreen(dist)
        if dist < dist_threshold:
            done = True
            reward += 100
            util.prGreen("SUCCESS with " + str(self._env_step_counter) + " steps")
            self._num_success = 1

        if self._step_limit and self._env_step_counter > self._max_step:
            done = True
            util.prRed("FAILED")
            self._num_success = 0

        return reward, done, self._num_success

    def reward_force_torque(self):

        ft_contact_limit = np.multiply(self._max_force_torque, 0.5)  # define contact limit ft as % of max
        # util.prGreen('force torque: {}'.format(self.force_torque))
        indices = Task.check_list_bounds(self.force_torque, ft_contact_limit)
        # util.prGreen(indices)

        max_ft = 0
        for i in range(len(indices)):
            ft_excess_ratio = (indices[i] * self.force_torque[i] - ft_contact_limit[i]) / self._max_force_torque[i]
            if (indices[i] != 0) & (max_ft < ft_excess_ratio):
                max_ft = ft_excess_ratio
        reward_ft = - max_ft

        # experiment with discouraging FT overload with negative reward
        if self._limit_force_torque & (self._force_torque_violations != [0.0] * len(self._force_torque_violations)):
            reward_ft -= 5

        # util.prRed('reward ft: {}'.format(reward_ft))
        return reward_ft

    @staticmethod
    def check_list_bounds(l, l_bounds):
        assert len(l) == len(l_bounds)
        index_list = [0] * len(l)
        for i in range(len(l)):
            if math.fabs(l[i]) >= l_bounds[i]:
                # util.prGreen("index {}: {}".format(i,l[i]))
                index_list[i] = np.sign(l[i])

        # in the form of [0, 0, 1, 0, -1, 0]
        return index_list

    @staticmethod
    def add_gaussian_noise(mean, std, vec):
        noise = np.random.normal(mean, std, np.shape(vec))
        return np.add(vec, noise).tolist()
