import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


class TD3CriticNetwork(nn.Module):
    def __init__(self, input_shape, output_shape, n_features, **kwargs):
        super().__init__()

        n_input = input_shape[-1]
        dim_action = kwargs['action_shape'][0]
        dim_state = n_input - dim_action
        n_output = output_shape[0]

        # Assume there are two hidden layers
        assert len(n_features) == 2, 'TD3 critic needs 2 hidden layers'

        self._h1 = nn.Linear(dim_state + dim_action, n_features[0])
        self._h2_s = nn.Linear(n_features[0], n_features[1])
        self._h2_a = nn.Linear(dim_action, n_features[1], bias=False)
        self._h3 = nn.Linear(n_features[1], n_output)

        fan_in_h1, _ = nn.init._calculate_fan_in_and_fan_out(self._h1.weight)
        nn.init.uniform_(self._h1.weight, a=-1 / np.sqrt(fan_in_h1), b=1 / np.sqrt(fan_in_h1))

        fan_in_h2_s, _ = nn.init._calculate_fan_in_and_fan_out(self._h2_s.weight)
        nn.init.uniform_(self._h2_s.weight, a=-1 / np.sqrt(fan_in_h2_s), b=1 / np.sqrt(fan_in_h2_s))

        fan_in_h2_a, _ = nn.init._calculate_fan_in_and_fan_out(self._h2_a.weight)
        nn.init.uniform_(self._h2_a.weight, a=-1 / np.sqrt(fan_in_h2_a), b=1 / np.sqrt(fan_in_h2_a))

        nn.init.uniform_(self._h3.weight, a=-3e-3, b=3e-3)
        
    def forward(self, state, action):
        state = state.float()
        action = action.float()
        state_action = torch.cat((state, action), dim=1)

        features1 = F.relu(self._h1(state_action))
        features2_s = self._h2_s(features1)
        features2_a = self._h2_a(action)
        features2 = F.relu(features2_s + features2_a)

        q = self._h3(features2)
        return torch.squeeze(q)


class TD3ActorNetwork(nn.Module):
    def __init__(self, input_shape, output_shape, n_features, **kwargs):
        super().__init__()

        dim_state = input_shape[0]
        dim_action = output_shape[0]

        self._action_scaling = torch.tensor(kwargs['action_scaling']).to(
            device=torch.device('cuda' if kwargs['use_cuda'] else 'cpu'))

        # Assume there are two hidden layers
        assert len(n_features) == 2, 'DDPG critic needs two hidden layers'

        self._h1 = nn.Linear(dim_state, n_features[0])
        self._h2 = nn.Linear(n_features[0], n_features[1])
        self._h3 = nn.Linear(n_features[1], dim_action)

        fan_in_h1, _ = nn.init._calculate_fan_in_and_fan_out(self._h1.weight)
        nn.init.uniform_(self._h1.weight, a=-1 / np.sqrt(fan_in_h1), b=1 / np.sqrt(fan_in_h1))

        fan_in_h2, _ = nn.init._calculate_fan_in_and_fan_out(self._h2.weight)
        nn.init.uniform_(self._h2.weight, a=-1 / np.sqrt(fan_in_h2), b=1 / np.sqrt(fan_in_h2))

        nn.init.uniform_(self._h3.weight, a=-3e-3, b=3e-3)

    def forward(self, state):
        state = state.float()

        features1 = F.relu(self._h1(state))
        features2 = F.relu(self._h2(features1))
        a = self._h3(features2)

        a = self._action_scaling * torch.tanh(a)

        return a