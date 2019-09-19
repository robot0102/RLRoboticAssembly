from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ray.rllib.agents.ddpg.ddpg import DDPGAgent, DEFAULT_CONFIG as DDPG_CONFIG
from ray.rllib.agents.dqn.dqn import OPTIMIZER_SHARED_CONFIGS
from ray.rllib.utils.annotations import override
from ray.rllib.utils import merge_dicts

def prGreen(skk): print("\033[92m {}\033[00m" .format(skk))

APEX_DDPG_DEFAULT_CONFIG = merge_dicts(
    DDPG_CONFIG,  # see also the options in ddpg.py, which are also supported
    {
        "optimizer_class": "AsyncReplayOptimizer",
        "optimizer": merge_dicts(
            DDPG_CONFIG["optimizer"], {
                "max_weight_sync_delay": 400,
                "num_replay_buffer_shards": 4,
                "debug": False,
                "human_demonstration": False

            }),
        "n_step": 3,
        "num_gpus": 0,
        "num_workers": 32,
        "buffer_size": 2000000,
        "learning_starts": 50000,
        "train_batch_size": 512,
        "sample_batch_size": 50,
        "max_weight_sync_delay": 400,
        "target_network_update_freq": 500000,
        "timesteps_per_iteration": 25000,
        "per_worker_exploration": True,
        "worker_side_prioritization": True,
        "min_iter_time_s": 30,

        # --- parameters for human demonstrations --- #
        
        # Whether to use human demonstration data
        # "human_demonstration": False,
    },
)

# DDPGHD_OPTIMIZER_SHARED_CONFIGS = merge_dicts(
#    OPTIMIZER_SHARED_CONFIGS,
#    {
#       "human_demonstration",
#    } 
# )


class ApexDDPGHDAgent(DDPGAgent):
    """DDPG variant that uses the Ape-X distributed policy optimizer.

    By default, this is configured for a large single node (32 cores). For
    running in a large cluster, increase the `num_workers` config var.
    """

    _agent_name = "APEX_DDPG_HD"
    _default_config = APEX_DDPG_DEFAULT_CONFIG
    #_optimizer_shared_configs = DDPGHD_OPTIMIZER_SHARED_CONFIGS

    # print out the current config 
    # prGreen(_default_config)

    @override(DDPGAgent)
    def update_target_if_needed(self):
        # Ape-X updates based on num steps trained, not sampled
        if self.optimizer.num_steps_trained - self.last_target_update_ts > \
                self.config["target_network_update_freq"]:
            self.local_evaluator.foreach_trainable_policy(
                lambda p, _: p.update_target())
            self.last_target_update_ts = self.optimizer.num_steps_trained
            self.num_target_updates += 1
