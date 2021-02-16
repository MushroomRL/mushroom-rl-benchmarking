import torch.nn.functional as F
import torch.optim as optim

from mushroom_rl.algorithms.value import DQN
from mushroom_rl.approximators.parametric import TorchApproximator
from mushroom_rl.policy import EpsGreedy
from mushroom_rl.utils.parameters import LinearParameter, Parameter
from mushroom_rl.utils.replay_memory import PrioritizedReplayMemory

from mushroom_rl_benchmark.builders.network import DQNNetwork

from .dqn import DQNBuilder


class PrioritizedDQNBuilder(DQNBuilder):
    def build(self, mdp_info):
        self.approximator_params['input_shape'] = mdp_info.observation_space.shape
        self.approximator_params['output_shape'] = (mdp_info.action_space.n,)
        self.approximator_params['n_actions'] = mdp_info.action_space.n

        replay_memory = PrioritizedReplayMemory(self.alg_params['initial_replay_size'],
            self.alg_params['max_replay_size'], alpha=.6,
            beta=LinearParameter(.4, threshold_value=1, n=50000000 // 4)
        )
        self.alg_params['replay_memory'] = replay_memory
        self.epsilon = LinearParameter(value=1, threshold_value=.05, n=1000000)
        self.epsilon_test = Parameter(value=.01)

        return DQN(mdp_info, self.policy, self.approximator, self.approximator_params, **self.alg_params)

    @classmethod
    def default(cls, lr=.0001, network=DQNNetwork, initial_replay_size=50000, max_replay_size=1000000,
                batch_size=32, target_update_frequency=2500, n_steps_per_fit=1, use_cuda=False, get_default_dict=False):
        defaults = locals()
        policy = EpsGreedy(epsilon=Parameter(value=1.))

        approximator_params = dict(
            network=network,
            optimizer={
                'class': optim.Adam,
                'params': {'lr': lr}},
            loss=F.smooth_l1_loss,
            use_cuda=use_cuda)

        alg_params = dict(
            initial_replay_size=initial_replay_size,
            max_replay_size=max_replay_size,
            batch_size=batch_size,
            target_update_frequency=target_update_frequency
        )

        builder = cls(policy, TorchApproximator, approximator_params, alg_params, n_steps_per_fit)

        if get_default_dict:
            return builder, defaults
        else:
            return builder