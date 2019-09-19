"""Registry of algorithm names for `rllib train --run=<alg_name>`"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


def _import_random_agent():
    from ray.rllib.contrib.random_agent.random_agent import RandomAgent
    return RandomAgent

def _import_apex_ddpg_hd():
    from ray.rllib.contrib.apex_ddpg_hd.apex_ddpg_hd import ApexDDPGHDAgent
    return ApexDDPGHDAgent


CONTRIBUTED_ALGORITHMS = {
    "contrib/RandomAgent": _import_random_agent,
    "contrib/APEX_DDPG_HD": _import_apex_ddpg_hd,
}
