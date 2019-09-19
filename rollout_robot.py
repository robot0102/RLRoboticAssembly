#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import json
import os
import pickle

import gym
import ray
from ray.rllib.agents.registry import get_agent_class
from ray.tune.registry import register_env

import envs_launcher as el


def getargs(parser_creator=None):
    parser_creator = parser_creator or argparse.ArgumentParser
    parser = parser_creator(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Roll out a RL agent given a checkpoint.")
    parser.add_argument(
        "checkpoint",
        type=str,
        help="Checkpoint from which to roll out.")
    parser.add_argument(
        "--steps",
        default=100000,
        type=int,
        help="Number of steps to roll out.")
    parser.add_argument(
        "--episodes",
        default=1,
        type=int,
        help="Number of episodes to roll out.")
    parser.add_argument(
        "--out",
        default=None,
        type=str,
        help="Output filename.")
    parser.add_argument(
        "--config",
        default="{}",
        type=json.loads,
        help="Algorithm-specific configuration (e.g. env, hyper-parameters). "
             "Suppresses loading of configuration from checkpoint.")
    args = parser.parse_args()
    return args


def main():
    args = getargs()
    config = args.config
    if not config:
        # Load configuration from file
        config_dir = os.path.dirname(args.checkpoint)
        config_path = os.path.join(config_dir, "params.json")
        if not os.path.exists(config_path):
            config_path = os.path.join(config_dir, "../params.json")
        if not os.path.exists(config_path):
            raise ValueError(
                "Could not find params.json in either the checkpoint dir or "
                "its parent directory.")
        with open(config_path) as f:
            config = json.load(f)

        # if "num_workers" in config:
        #     config["num_workers"] = min(2, config["num_workers"])

        # we don't need multiple workers in evaluation to prevent multiple simulations. 
        if "num_workers" in config:
            del config["num_workers"]

        # --- added by autodesk_rl --- #
        # delete APEX_DDPG hyper-parameters 
        if "human_data_dir" in config["optimizer"]:
            del config["optimizer"]["human_data_dir"]
        if "human_demonstration" in config["optimizer"]:
            del config["optimizer"]["human_demonstration"]
        if "multiple_human_data" in config["optimizer"]:
            del config["optimizer"]["multiple_human_data"]
        if "num_replay_buffer_shards" in config["optimizer"]:
            del config["optimizer"]["num_replay_buffer_shards"]

    ray.init()

    # --- modified by autodesk_rl --- #
    cls = get_agent_class("DDPG")
    agent = cls(env="ROBOTIC_ASSEMBLY", config=config)

    agent.restore(args.checkpoint)
    num_steps = int(args.steps)
    num_episodes = int(args.episodes)
    rollout(agent, "ROBOTIC_ASSEMBLY", num_steps, num_episodes, args.out)


def rollout(agent, env_name, num_steps, num_episodes, out=None):
    if hasattr(agent, "local_evaluator"):
        env = agent.local_evaluator.env
    else:
        env = gym.make(env_name)

    if hasattr(agent, "local_evaluator"):
        state_init = agent.local_evaluator.policy_map[
            "default"].get_initial_state()
    else:
        state_init = []

    use_lstm = True if state_init else False

    if out is not None:
        rollouts = []

    steps = 0
    episodes = 0

    while (steps < (num_steps or steps + 1)) and (episodes < num_episodes):
        if out is not None:
            rollout = []

        state = env.reset()
        # util.prGreen("steps: ".format(steps))

        done = False
        reward_total = 0.0

        # one rollout 
        while not done and steps < (num_steps or steps + 1):
            if use_lstm:
                action, state_init, logits = agent.compute_action(
                    state, state=state_init)
            else:
                action = agent.compute_action(state)
            next_state, reward, done, _ = env.step(action)
            reward_total += reward
            if out is not None:
                rollout.append([state, action, next_state, reward, done])
            steps += 1
            state = next_state

        if out is not None:
            rollouts.append(rollout)
        print("Episode reward", reward_total)
        episodes += 1

    if out is not None:
        pickle.dump(rollouts, open(out, "wb"))


if __name__ == "__main__":
    # -- autodesk_rl -- #
    register_env("ROBOTIC_ASSEMBLY", el.env_creator)  # customized envs
    # -- autodesk_rl -- #
    main()
