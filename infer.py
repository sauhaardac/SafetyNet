from param import params
import gym_boids
import gym
from net.ppo import PPO
from torch.distributions import Categorical
import torch
import matplotlib.pyplot as plt
import numpy as np
import util
import sys
import plot

def run_network(infer, x):
    """ Runs the network to determine action given current state

    Parameters:
        infer (dict): dictionary of infering variables
        x (np.array): current state to input into neural network

    Returns:
        prob (torch.FloatTensor): output of the network, raw softmax distribution
        m (torch.FloatTensor): categorical distribution of output
        u (torch.FloatTensor): actual action selected by the network

    """

    prob = infer['model'].pi(torch.from_numpy(x).float().to(params['device']))
    m = Categorical(prob)
    u = m.sample().item()
    return prob, m, u

def transform_state(x, i):
    """ Transforms the state to make the infering set more varied.

    Shifts the position state in a circle so the agents are forced to
    track a point rather than simply move towards a goal point. This
    is a harder problem to learn.

    Params:
        x (np.array): current state
        i (int): iteration # within the episode

    Returns:
        x_transformed (np.array): augmented/transformed state

    """

    x_transformed = x.copy()
    
    for agent_idx in range(params['n']):
        x_transformed[2 * agent_idx * params['num_dims'] :
                (2 * agent_idx + 1) * params['num_dims'] - 1] -= params['pd'][i, 0]

        x_transformed[2 * agent_idx * params['num_dims'] + 1 :
                (2 * agent_idx + 1) * params['num_dims']] -= params['pd'][i, 1]

        x_transformed[(2 * agent_idx + 1) * params['num_dims']:
                2 * (agent_idx + 1) * params['num_dims'] - 1] -= params['vd'][i, 0]

        x_transformed[(2 * agent_idx + 1) * params['num_dims'] + 1:
                2 * (agent_idx + 1) * params['num_dims']] -= params['vd'][i, 1]

    return x_transformed

def infer(path, label):
    """ Trains an RL model.

    First initializes environment, logging, and machine learning model. Then iterates
    through epochs of infering and prints score intermittently.
    """

    util.set_xd()

    infer = {}
    infer['env'] = gym.make(params['env_name'])
    infer['env'].init(params)
    infer['model'] = PPO(params, infer['env'].observation_space.shape[0]).to(params['device'])
    infer['model'].load_state_dict(torch.load(path))

    x = transform_state(infer['env'].reset(), 0)

    for i in range(1, params['nt']):
        prob, m, u = run_network(infer, x)
        state,_ = infer['env'].step(u)
        x_prime = transform_state(state, i)
        x = x_prime

    x = np.array(infer['env'].get_x())
    plot.plot_lyap(x, params['T'])

if __name__ == '__main__':
    paths = ['0.89-3540.save']
    labels = ['3540 Episodes Lyapunov Reward']
    for i in range(len(paths)):
        infer(f'saves/lyap_test5/{paths[i]}', labels[i])
    plt.savefig('fig.svg')
