import pybullet as p
import numpy as np
import transforms3d
import utilities as util
from envs.robot_sim import RobotSim
import random

# lap task
INITIAL_POS_ARL = np.array([0.0, 0.0, 0.222])  # top member is 0.034 m above world origin
INITIAL_POS_GKR = np.array([0.0, 0.0, 0.195 + 0.08])
INITIAL_ORN_ARL = util.mat33_to_quat( np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]) )
INITIAL_ORN_GKR = util.mat33_to_quat( np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]]) )
# TARGET_POS = np.array([0, 0, 0])
# TARGET_ORN = np.identity(3)
# TARGET_ORN = np.array([0, 0, 0])

SETUP = 'ARL'

if SETUP == 'ARL':
    INITIAL_POS = INITIAL_POS_ARL
    INITIAL_ORN = INITIAL_ORN_ARL
    URDF_PATH_TOOL = 'envs/urdf/arl/tool'
    URDF_PATH_TARGET = 'envs/urdf/arl/task_lap_90deg'

if SETUP == 'GKR':
    INITIAL_POS = INITIAL_POS_GKR
    INITIAL_ORN = INITIAL_ORN_GKR
    URDF_PATH_TOOL = 'envs/urdf/gkr/tool'
    URDF_PATH_TARGET = 'envs/urdf/gkr/task_lap_90deg'


class RobotSimRobotlessConstraint(RobotSim):

    def __init__(self):

        super().__init__()

        self.uid = p.loadURDF(util.format_urdf_filepath(URDF_PATH_TOOL),
                              basePosition=INITIAL_POS,
                              baseOrientation=INITIAL_ORN,
                              useFixedBase=0)
        self.link_member = 2
        self.link_gripper = 1
        self.link_sensor = 0
        
        # it has to be there to be randomized in training and rollout
        TARGET_ORN = np.array([0, 0, random.uniform(-3.14152/90, 0)])
        TARGET_POS = np.array([random.uniform(-0.002, 0.002), random.uniform(-0.002, 0.002), 0])
        self.target_uid = p.loadURDF(util.format_urdf_filepath(URDF_PATH_TARGET),
                                     basePosition=TARGET_POS,
                                     # baseOrientation=util.mat33_to_quat(TARGET_ORN),
                                     baseOrientation = util.xyzw_by_euler(TARGET_ORN, 'sxyz'),
                                     useFixedBase=1)
        self.link_target = 0

        self.max_force = -1  # 667 = min(force range of FT sensor) in N
        
        # set friction
        """
        p.changeDynamics(self.uid,
                         self.link_member,
                         lateralFriction=1.0)
        p.changeDynamics(self.target_uid,
                         1,
                         lateralFriction=1.0)
        """

        self.base_constraint = p.createConstraint(
            parentBodyUniqueId=self.uid,
            parentLinkIndex=-1,  # base index
            childBodyUniqueId=-1,  # base index
            childLinkIndex=-1,  # base index
            jointType=p.JOINT_FIXED,
            jointAxis=[0, 0, 0],
            parentFramePosition=[0, 0, 0],
            childFramePosition=INITIAL_POS,
            childFrameOrientation=INITIAL_ORN
        )

        self.base_pose = p.getBasePositionAndOrientation(self.uid)
        # util.prGreen("base: {}".format(self.base_pose))
        self.gripper_pose = p.getLinkState(self.uid, self.link_gripper)[4:6]
        # util.prGreen("gripper: {}".format(self.gripper_pose))
        self.member_pose = p.getLinkState(self.uid, self.link_member)[4:6]
        # util.prGreen("member: {}".format(self.member_pose))

        self.from_base_to_member = self.get_f1_to_f2_xform(self.base_pose, self.member_pose)

        for link_index in range(p.getNumJoints(self.uid)):
            self.display_frame_axis(self.uid, link_index)

    def get_member_pose(self):
        base_pose = p.getBasePositionAndOrientation(self.uid)
        member_pose_mat = util.transform_mat(self.from_base_to_member,
                                             util.mat44_by_pos_quat(base_pose[0], base_pose[1]))
        member_pose = util.mat44_to_pos_quat(member_pose_mat)

        return [member_pose[0], member_pose[1]]

    def enable_force_torque_sensor(self):
        # FT sensor is measured at the center of mass in Pybullet
        p.enableJointForceTorqueSensor(self.uid, self.link_sensor)

    def get_force_torque(self):
        # force-torque reading in PyBullet is negated
        return np.multiply(-1, p.getJointState(self.uid, self.link_sensor)[2]).tolist()

    def apply_action_pose(self, velocity, time_step):
        # pybullet oddity: mysterious 5-time relationship between velocity command and getBaseVelocity
        velocity = np.multiply( np.array(velocity), 5.0 )

        relative_pos = np.array(velocity[0:3]) * time_step
        base_pos, base_orn = p.getBasePositionAndOrientation(self.uid)
        new_pos = np.add(np.array(base_pos), relative_pos).tolist()

        ang_vel_quat = [0, velocity[3], velocity[4], velocity[5]]
        new_orn = np.add(base_orn,
                         np.multiply(0.5 * time_step,
                                     util.wxyz_to_xyzw(transforms3d.quaternions.qmult(ang_vel_quat, util.xyzw_to_wxyz(base_orn)))))

        p.changeConstraint(self.base_constraint, new_pos, new_orn, self.max_force)

    def apply_action_position(self, velocity, time_step):
        # pybullet oddity: mysterious 5-time relationship between velocity command and getBaseVelocity
        linear_velocity = np.multiply( np.array(velocity), 5.0 )

        relative_pos = linear_velocity * time_step
        base_pos, base_orn = p.getBasePositionAndOrientation(self.uid)
        new_pos = np.add(np.array(base_pos), relative_pos).tolist()

        p.changeConstraint(self.base_constraint, new_pos, INITIAL_ORN, self.max_force)


