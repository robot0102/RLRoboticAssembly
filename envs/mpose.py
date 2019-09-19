from abc import ABC, abstractmethod


class PoseHandlerMixin(ABC):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def get_member_pose(self):
        pass

    @abstractmethod
    def get_target_pose(self):
        pass

    @abstractmethod
    def get_force_torque(self):
        pass
