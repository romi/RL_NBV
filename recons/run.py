import recons_env 
import numpy as np
import json
import tensorflow as tf
from DDQN.ddqn import DDQN
import os
import time

model_path="test/models/mymodel.h5"

params=json.load(open("params.json"))

env = recons_env.scanner_env(params)
state_dim = (84, 84, 3)
action_dim = 4
state, time = env.reset(), 0

writer = tf.summary.create_file_writer("logs/test")
algo = DDQN(action_dim, state_dim, params["train"])
algo.load_weights(model_path)

state, time, done = env.reset(), 0, False

poses=[]
poses.append([env.theta, env.phi])

while not(done):
   a = algo.policy_action(state)
   state, r, done, _ = env.step(a)
   poses.append([env.theta, env.phi])

json.dump(poses,open('test/poses.json', 'w'))
