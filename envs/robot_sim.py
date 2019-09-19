import pybullet as p

import numpy as np

import utilities as util
from envs.mpose import PoseHandlerMixin


class RobotSim(PoseHandlerMixin):

    def __init__(self):
        super().__init__()

        # To be overwritten
        self.uid = 0
        self.link_member = 0
        self.link_gripper = 0
        self.link_sensor = 0
        self.target_uid = 0
        self.link_target = 0

    @staticmethod
    def get_f1_to_f2_xform(pose_from, pose_to):
        # util.prGreen('base pose: {}'.format(self.pose_from))
        # util.prGreen('member pose: {}'.format(self.pose_to))
        from_f1_to_f2 = util.get_relative_xform(util.mat44_by_pos_quat(pose_from[0], pose_from[1]),
                                                util.mat44_by_pos_quat(pose_to[0], pose_to[1]))
        return from_f1_to_f2

    @staticmethod
    def display_frame_axis(body_uid, link_index, line_length=0.05):
        # Red: X axis, Green: Y axis, Blue: Z axis

        p.addUserDebugLine([0, 0, 0], [line_length, 0, 0], [1, 0, 0],
                           parentObjectUniqueId=body_uid, parentLinkIndex=link_index)
        p.addUserDebugLine([0, 0, 0], [0, line_length, 0], [0, 1, 0],
                           parentObjectUniqueId=body_uid, parentLinkIndex=link_index)
        p.addUserDebugLine([0, 0, 0], [0, 0, line_length], [0, 0, 1],
                           parentObjectUniqueId=body_uid, parentLinkIndex=link_index)

    def get_member_pose(self):
        pass

    def get_target_pose(self):
        return p.getLinkState(self.target_uid, self.link_target)[4:6]

    def get_force_torque(self):
        pass

    def add_all_friction_noise(self, noise_level):
        self.__add_body_friction_noise(self.target_uid, self.link_target, noise_level)
        self.__add_body_friction_noise(self.uid, self.link_member, noise_level)

    def enable_force_torque_sensor(self):
        pass

    def apply_action_pose(self, velocity, time_step):
        pass

    def apply_action_position(self, velocity, time_step):
        pass

    @staticmethod
    def __add_body_friction_noise(uid, link, noise_level):
        dynamics = p.getDynamicsInfo(uid, link)
        noise_range = np.fabs(dynamics[1]) * noise_level
        friction_noise = np.random.normal(0, noise_range)
        p.changeDynamics(uid, link, lateralFriction=dynamics[1] + friction_noise)
