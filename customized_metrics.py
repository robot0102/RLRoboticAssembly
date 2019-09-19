# customized metrics 
import numpy as np 
import utilities as utilis
from collections import deque
import random
import pickle

def on_episode_start(info):
    episode = info["episode"]
    episode.user_data["success"] = 0

def on_episode_step(info):
    pass

def on_episode_end(info):
    episode = info["episode"]
    if len(episode.last_info_for().values()) > 0:
        episode.user_data["success"] = list(episode.last_info_for().values())[0]
        episode.custom_metrics["successful_rate"] = episode.user_data["success"]

#--- parameters for on_sample_end ---#    
step_threshold = 4000 # one step less than the maximum steps. saving all the successful episodes 
step_min = 3000
dir_path = "robot_demo_data/"

def on_sample_end(info):
    
    samples = info["samples"]
    # utilis.prGreen(samples.count);

    # save successful transitions 
    # if samples.count < step_threshold and samples.count > step_min:
    
    # debug_count = 0
    
    # if samples.count < 4001:

    #     memory = deque()

    #     for row in samples.rows():
    #         obs = row["obs"]
    #         action = row["actions"]
    #         reward = row["rewards"]
    #         new_obs = row["new_obs"]
    #         done = row["dones"]
    #         memory.append((obs, action, reward, new_obs, done))
        
    #     # if done:
    #     #     debug_count += 1
    #     # utilis.prGreen(debug_count)

    #     # save transitions
    #     file_name = dir_path + str(random.random())
    #     out_file = open(file_name, 'wb')
    #     pickle.dump(memory, out_file)
    #     out_file.close()
    #     utilis.prGreen("A successful transition is saved, length {}".format(len(memory)))

def on_train_result(info):
    if "successful_rate_mean" in info["result"]["custom_metrics"]:
        info["result"]["successful_rate"] = info["result"]["custom_metrics"]["successful_rate_mean"]