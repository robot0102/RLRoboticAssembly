# envs launcher 


t = 'sim'

if t == 'sim':
    from envs.task_sim import TaskSim
    def env_creator(env_config):
        environment = TaskSim(renders=False,
                            # step_limit=True,
                            # random_box_pos=False,
                            # random_peg_pose=True,
                            # ft_obs_only=False,
                            # limit_ft=False,
                            # ft_noise=False,
                            # pose_noise=False,
                            # action_noise=False,
                            # physical_noise=False
                            )
        return environment


if t == 'real':
    from envs.task_real import TaskReal
    def env_creator(env_config):
        environment = TaskReal(
                            #renders=False,
                            # step_limit=True,
                            # random_box_pos=False,
                            # random_peg_pose=True,
                            # ft_obs_only=False,
                            # limit_ft=False,
                            # ft_noise=False,
                            # pose_noise=False,
                            # action_noise=False,
                            # physical_noise=False
                            )
        return environment


