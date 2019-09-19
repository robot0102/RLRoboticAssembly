# Basic Insertion Task Environment -- working on real kuka & timber 
# 
# Nov 7th, 2018
# Robotics Lab, Autodesk

import numpy as np

from envs.robot_real_KUKA import RobotReal
from envs.task import Task


class TaskReal(Task):

    def __init__(self):

        super().__init__(max_steps=6000,
                         action_dim=6,
                         step_limit=True,
                         max_vel=0.004,  # m/sec
                         max_rad=0.002,  # rad/sec
                         ft_obs_only=False,
                         limit_ft=False)

        self.env = RobotReal()

    def reset(self):
        self.max_dist = self.dist_to_target()
        self._env_step_counter = 0
        self._observation = self.get_extended_observation()

        return np.array(self._observation)

    def get_member_pose(self):
        return self.env.get_member_pose()

    def get_target_pose(self):
        return self.env.get_target_pose()

    def get_force_torque(self):
        return self.env.get_force_torque()

    def step2(self, velocity):
        reward, done, num_success = self.reward()

        if done:
            if self.action_dim > 3:
                last_velocity = [0.0] * 6
                self.env.apply_action_relative_pose_in_member_frame(last_velocity, self._time_step, 1)
            else:
                last_velocity = [0.0] * 3
                self.env.apply_action_relative_position_in_member_frame(last_velocity, self._time_step, 1)
        else:
            if self.action_dim > 3:
                self.env.apply_action_relative_pose_in_member_frame(velocity, self._time_step, 0)
            else:
                self.env.apply_action_relative_position_in_member_frame(velocity, self._time_step, 0)

        self._env_step_counter += 1

        self._observation = self.get_extended_observation()

        return np.array(self._observation), reward, done, {"num_success": num_success}
