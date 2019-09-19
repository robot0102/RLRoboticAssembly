from envs.mpose import PoseHandlerMixin

import roslibpy
import threading
from interfaces import DeepTimberInterfaces
from envs.objects.pose import Pose


class RobotReal(PoseHandlerMixin):

	def __init__(self):

		super().__init__()
		
		### Initialize ABB EGM interfaces
		# ROS connection init using roslibpy
		self.ros_connection = roslibpy.Ros(host='localhost', port=9090)
		self.ros_connection.run()

		# Create deep timber interfaces instance
		self.sync_event = threading.Event()				#event to sync the input of new egm data and the steps of the rollout
		self.deep_interfaces = DeepTimberInterfaces("robot11", self.ros_connection, self.sync_event)
		self.deep_interfaces.wait_ready()
		
		# set target pose
		# NOTE: hardcoded for now
		self._target_pose = Pose([0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0], convention='wxyz')


	def get_member_pose(self):
		return self.deep_interfaces.element_pose().to_lists(convention='xyzw', canonic=True)

	def get_target_pose(self):
		return self._target_pose.to_lists(convention='xyzw', canonic=True)

	def get_force_torque(self):
		return (self.deep_interfaces.ft_unbiased_and_compensated * 10.0).to_list()

	def apply_action_relative_pose_in_member_frame(self, velocity, time_step, done):
		# NOTE: to be tested yet
		pass

		"""
		# pybullet oddity:
		#   - mysterious 5-time relationship between velocity command and getBaseVelocity
		#   - rotational velocity along x and y axis don't obey the right-hand rule
		linear = np.multiply(velocity[0:3], 0.2)  # m/s
		rotational = np.multiply(np.array([- velocity[3], - velocity[4], velocity[5]]), 0.2)  # rad/s
		relative_pos = np.multiply(linear, time_step)
		relative_orn = np.multiply(rotational, time_step)  # angles around x, y, z

		data_out = list(relative_pos) + list(relative_orn) + [done]

		self.interface.send(data_out)
		"""

	def apply_action_relative_position_in_member_frame(self, velocity, time_step, done):
		if done:
			self.deep_interfaces.trigger_hard_stop()
		else:
			vel = list(velocity) + [0, 0, 0]
			self.send_velocity_to_robot(vel)

	def send_velocity_to_robot(self, velocity):
		# SYNC
		self.sync_event.wait()

		# new_vel_lin = velocity[0:3]     # meter/sec
		# new_vel_ang = velocity[3:6]     # angular velocity, radians/sec
		self.deep_interfaces.send_velocity_command(velocity)
