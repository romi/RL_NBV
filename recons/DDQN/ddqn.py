import sys
import random
import numpy as np

from tqdm import tqdm
from .agent import Agent
from random import random, randrange

from memory_buffer import MemoryBuffer
import tensorflow as tf
import time

import os

class DDQN:
    """ Deep Q-Learning Main Algorithm
    """

    def __init__(self, action_dim, state_dim, params):
        """ Initialization
        """
        # session = K.get_session()
        # Environment and DDQN parameters
        self.with_per = params["with_per"]
        self.action_dim = action_dim
        self.state_dim = state_dim

        self.lr = 2.5e-4
        self.gamma = 0.95
        self.epsilon = params["epsilon"]
        self.epsilon_decay = params["epsilon_decay"]
        self.epsilon_minimum = 0.05
        self.buffer_size = 10000
        self.tau = 1.0
        self.agent = Agent(self.state_dim, action_dim, self.lr, self.tau, params["dueling"])
        # Memory Buffer for Experience Replay
        self.buffer = MemoryBuffer(self.buffer_size, self.with_per)

        exp_dir = 'test/models/'
        if not os.path.exists(exp_dir):
            os.makedirs(exp_dir)
        self.export_path = exp_dir+'/lala.h5'
        self.save_interval = params["save_interval"]

    def policy_action(self, s):
        """ Apply an espilon-greedy policy to pick next action
        """
        if random() <= self.epsilon:
            return randrange(self.action_dim)
        else:
            return np.argmax(self.agent.predict(s)[0])

    def train_agent(self, batch_size):
        """ Train Q-network on batch sampled from the buffer
        """
        # Sample experience from memory buffer (optionally with PER)
        s, a, r, d, new_s, idx = self.buffer.sample_batch(batch_size)

        # Apply Bellman Equation on batch samples to train our DDQN
        q = self.agent.predict(s)
        next_q = self.agent.predict(new_s)
        q_targ = self.agent.target_predict(new_s)

        for i in range(s.shape[0]):
            old_q = q[i, a[i]]
            if d[i]:
                q[i, a[i]] = r[i]
            else:
                next_best_action = np.argmax(next_q[i,:])
                q[i, a[i]] = r[i] + self.gamma * q_targ[i, next_best_action]
            if(self.with_per):
                # Update PER Sum Tree
                self.buffer.update(idx[i], abs(old_q - q[i, a[i]]))
        # Train on batch
        self.agent.fit(s, q)
        # Decay epsilon
        if self.epsilon_decay>self.epsilon_minimum:
            self.epsilon *= self.epsilon_decay
        else:
            self.epsilon = self.epsilon_minimum

    def train(self, env, nb_episodes, batch_size, writer):
        """ Main DDQN Training Algorithm
        """

        results = []
        tqdm_e = tqdm(range(nb_episodes), desc='Score', leave=True, unit=" episodes")

        for e in tqdm_e:
            # Reset episode
            t, cumul_reward, done  = 0, 0, False
            old_state = env.reset()
            
            t0=time.time()
            while not done:
                # Actor picks an action (following the policy)
                a = self.policy_action(old_state)
                # Retrieve new state, reward, and whether the state is terminal
                new_state, r, done, _ = env.step(a)
                print("Step %s in episode %s, cumul_reward: %s reward: %s"%(t, e, cumul_reward,r))
                # Memorize for experience replay
                self.memorize(old_state, a, r, done, new_state)
                # Update current state
                old_state = new_state
                cumul_reward += r
                t += 1
                # Train DDQN and transfer weights to target network
                if (self.buffer.size() > batch_size):
                    self.train_agent(batch_size)
                    self.agent.transfer_weights()
            print("it took % s at episode %s"%(time.time()-t0,e))
            
            if (e%10==0)&(e!=0):        
               # Gather stats every episode for plotting
               mean, stdev, n = self.gather_stats(env)
               results.append([e, mean, stdev, n])

            with writer.as_default():
               tf.summary.scalar('score', cumul_reward, step=e)
            writer.flush()
            
            # Display score
            tqdm_e.set_description("Score: " + str(cumul_reward))
            tqdm_e.refresh()
            if (e%self.save_interval == 0)&(e!=0):
                self.save_weights(self.export_path,e)
            t0=time.time()    
        return results

    def memorize(self, state, action, reward, done, new_state):
        """ Store experience in memory buffer
        """
        if(self.with_per):
            q_val = self.agent.predict(state)
            q_val_t = self.agent.target_predict(new_state)
            next_best_action = np.argmax(q_val)
            new_val = reward + self.gamma * q_val_t[0, next_best_action]
            td_error = abs(new_val - q_val)[0]
        else:
            td_error = 0
        self.buffer.memorize(state, action, reward, done, new_state, td_error)

    def save_weights(self, path, ep = 10000):
        self.agent.save(path)

    def load_weights(self, path):
        self.agent.load_weights(path)

    def gather_stats(self,env):
       score = []
       n_steps=[]
       for k in range(10):
          old_state = env.reset()
          cumul_r, t, done = 0,0, False
          while not done:
             a = self.policy_action(old_state)
             old_state, r, done, _ = env.step(a)
             cumul_r += r
             t+=1
          score.append(cumul_r)
          n_steps.append(t)
       return np.mean(np.array(score)), np.std(np.array(score)), np.mean(n_steps)
