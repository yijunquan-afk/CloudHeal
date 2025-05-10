import numpy as np
import pandas as pd
from numpy.linalg import inv
import matplotlib.pyplot as plt

class BasicMAB():
    def __init__(self, narms):      
        pass

    def select_arm(self, context = None):       
        pass

    def update(self, arm, reward, context = None):      
        pass



class BetaThompsonSampling(BasicMAB):
    def __init__(self, narms, alpha0=1.0, beta0=1.0):
        self.narms = narms
        self.step = 0
        self.step_arm = np.zeros(self.narms)
        self.alpha0 = np.ones(narms) * alpha0
        self.beta0 = np.ones(narms) * beta0

    def select_arm(self, context=None):
        if len(np.where(self.step_arm==0)[0]) > 0:
            action = np.random.choice(np.where(self.step_arm==0)[0])
            return action 

        means = np.random.beta(self.alpha0, self.beta0)
        action = np.random.choice(np.where(means==np.max(means))[0])
        return action 

    def update(self, arm, reward, context=None):
        self.arm = arm
        self.step += 1
        self.step_arm[self.arm] += 1
        normalization_reward = reward
        self.alpha0[arm] += normalization_reward
        self.beta0[arm] += 1 - normalization_reward


class LinUCB(BasicMAB):
    def __init__(self, narms, ndims, alpha):
        self.narms = narms
        self.ndims = ndims
        self.alpha = alpha
        self.A = np.array([np.identity(self.ndims)] * self.narms)
        self.b = np.zeros((self.narms, self.ndims, 1))
        return

    def select_arm(self, context=None):
        """

        Parameters
        ----------
        context : array
            context 

        Returns
        -------
        action : int
        """
        p_t = np.zeros((self.ndims,1))
        for i in range(self.narms):
            self.theta = inv(self.A[i]).dot(self.b[i])
            # get the features of each arm
            x = np.array(context).reshape(self.ndims, 1)
            # get the reward of each arm
            p_t[i] = self.theta.T.dot(x) + \
                     self.alpha * np.sqrt(x.T.dot(inv(self.A[i]).dot(x)))
        action = np.random.choice(np.where(p_t == max(p_t))[0])
        return action

    def update(self, arm, reward, context=None):
        self.arm = arm
        x = np.array(context).reshape(self.ndims, 1)
        self.A[arm] = self.A[arm] + x.dot(x.T)
        self.b[arm] = self.b[arm] + reward * x
        return

