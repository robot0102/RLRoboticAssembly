# prepare files to rllib
# copy apex ddpg hd to the contri folder in rllib
# replace the replay buffer and async optimizer with our modified version 

from shutil import copyfile 
import os

# create the apex_ddpg_hd folder 
agent_path = "../contrib/apex_ddpg_hd/"
if not os.path.exists(agent_path):
    os.mkdir(agent_path)

# apex_ddpg_hd
agents_src = "_rllib/agents/apex_ddpg_hd/apex_ddpg_hd.py"
agents_dst = "../contrib/apex_ddpg_hd/apex_ddpg_hd.py"
copyfile(agents_src, agents_dst)

# register external agent 
agents_registrt_src = "_rllib/agents/registry.py"
agents_registrt_dst = "../contrib/registry.py"
copyfile(agents_registrt_src, agents_registrt_dst)

# show all the stats in terminal, not just one third designed by Ray 
dqn_src = "_rllib/agents/dqn/dqn.py"
dqn_dst = "../agents/dqn/dqn.py"
copyfile(dqn_src, dqn_dst)

# modifications for the replay buffers
async_src = "_rllib/optimizers/async_replay_optimizer.py"
async_dst = "../optimizers/async_replay_optimizer.py"
copyfile(async_src, async_dst)

buffer_src = "_rllib/optimizers/replay_buffer.py"
buffer_dst = "../optimizers/replay_buffer.py"
copyfile(buffer_src, buffer_dst)

# calculate the custom metrics for one transition, not the historic transitions designed by Ray  
metrics_src = "_rllib/evaluation/metrics.py"
metrics_dst = "../evaluation/metrics.py"
copyfile(metrics_src, metrics_dst) 



