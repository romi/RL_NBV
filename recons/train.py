import recons_env 
import numpy as np
import json
import tensorflow as tf
from DDQN.ddqn import DDQN
import os
import time

params=json.load(open("params.json"))

env = recons_env.scanner_env(params)
state_dim = (84, 84, 3)
action_dim = 4
env.reset()

writer = tf.summary.create_file_writer("logs/test")
algo = DDQN(action_dim, state_dim, params["train"])

t0=time.time()
stats = algo.train(env, params["train"]["nb_episodes"], params["train"]["batch_size"], writer)
print("It took", time.time()-t0)

exp_dir = 'test/models/'
if not os.path.exists(exp_dir): os.makedirs(exp_dir)

export_path = exp_dir+'final.h5'
algo.save_weights(export_path)

exp_dir = 'test/stats/'
if not os.path.exists(exp_dir): os.makedirs(exp_dir)
np.savetxt(exp_dir+"test.txt", stats)
