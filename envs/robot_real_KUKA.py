import numpy as np
import utilities as util
from envs.robot import PoseHandlerMixin

# modules for interfacing with RSI and FT sensor
from arlrtk.interfaces import GenericUDPInterface
from arlrtk.interfaces import GenericUDPRemoteConfig
from arlrtk.interfaces import GenericTCPClientInterface
from arlrtk.interfaces import GenericTCPClientConfig

PROTOCOL = 'UDP'


class RobotReal(PoseHandlerMixin):

    def __init__(self):

        super().__init__()

        # Connect the interfaces
        if PROTOCOL == 'TCP':
            self.interface = GenericTCPClientInterface(**GenericTCPClientConfig)
        else:  # PROTOCOL == 'UDP'
            self.interface = GenericUDPInterface(**GenericUDPRemoteConfig)

    @staticmethod
    def decompose_incoming_data(data):
        position = data[:3]
        rotation = data[3:7]
        force_torque = data[7:]

        return [position, rotation, force_torque]

    def get_member_pose(self):
        self.interface.receive()
        data_in = self.interface.message_in.values
        values = self.decompose_incoming_data(data_in)
        position_m = values[0]
        rotation_quat = values[1]
        # util.prGreen('pos, orn: {}'.format(position_m + rotation_quat))

        return position_m, rotation_quat

    def get_target_pose(self):
        # At world origin
        return [0, 0, 0], util.xyzw_by_euler([0, 0, 0], 'sxyz')

    def get_force_torque(self):
        data_in = self.interface.message_in.values
        values = self.decompose_incoming_data(data_in)
        force_torque = values[2]
        # util.prGreen('FT reading: {}'.format(force_torque))

        return force_torque

    def apply_action_relative_pose_in_member_frame(self, velocity, time_step, done):
        # pybullet oddity:
        #   - mysterious 5-time relationship between velocity command and getBaseVelocity
        #   - rotational velocity along x and y axis don't obey the right-hand rule
        linear = np.multiply(velocity[0:3], 0.2)  # m/s
        rotational = np.multiply(np.array([- velocity[3], - velocity[4], velocity[5]]), 0.2)  # rad/s
        relative_pos = np.multiply(linear, time_step)
        relative_orn = np.multiply(rotational, time_step)  # angles around x, y, z

        data_out = list(relative_pos) + list(relative_orn) + [done]

        self.interface.send(data_out)

    def apply_action_relative_position_in_member_frame(self, velocity, time_step, done):
        # pybullet oddity: mysterious 5-time relationship between velocity command and getBaseVelocity
        linear = np.multiply(velocity, 0.2)  # m/s
        relative_pos = np.multiply(linear, time_step)

        data_out = list(relative_pos) + [0, 0, 0] + [done]

        self.interface.send(data_out)
