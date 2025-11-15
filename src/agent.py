import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
import os
from collections import deque

class DQNAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        
        # Experience Replay
        self.memory = deque(maxlen=2000)
        
        # Hyperparameters
        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        
        # Model
        self.model = self._build_model()
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        self.criterion = nn.MSELoss()

    def _build_model(self):
        model = nn.Sequential(
            nn.Linear(self.state_size, 24),
            nn.ReLU(),
            nn.Linear(24, 24),
            nn.ReLU(),
            nn.Linear(24, self.action_size)
        )
        return model

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        # Accepts either a 1D state array or a 2D (1, state_size)
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)

        state_arr = np.array(state)
        if state_arr.ndim == 1:
            state_tensor = torch.FloatTensor(state_arr).unsqueeze(0)
        else:
            state_tensor = torch.FloatTensor(state_arr)

        with torch.no_grad():
            act_values = self.model(state_tensor)

        # If batch, pick first; otherwise single
        if act_values.dim() == 2:
            return torch.argmax(act_values[0]).item()
        return torch.argmax(act_values).item()

    def learn(self, batch_size):
        if len(self.memory) < batch_size:
            return

        minibatch = random.sample(self.memory, batch_size)

        for state, action, reward, next_state, done in minibatch:
            s_arr = np.array(state)
            ns_arr = np.array(next_state)

            s_tensor = torch.FloatTensor(s_arr).unsqueeze(0) if s_arr.ndim == 1 else torch.FloatTensor(s_arr)
            ns_tensor = torch.FloatTensor(ns_arr).unsqueeze(0) if ns_arr.ndim == 1 else torch.FloatTensor(ns_arr)

            target = self.model(s_tensor).clone().detach()

            if done:
                target[0][action] = reward
            else:
                t_next = self.model(ns_tensor).detach()
                target[0][action] = reward + self.gamma * torch.max(t_next)

            prediction = self.model(s_tensor)
            loss = self.criterion(prediction, target)

            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def save(self, filepath):
        """Save model weights and training parameters to file.

        Args:
            filepath: Path to save the model (e.g., 'models/dqn_agent.pth')
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'state_size': self.state_size,
            'action_size': self.action_size,
            'gamma': self.gamma,
            'epsilon_min': self.epsilon_min,
            'epsilon_decay': self.epsilon_decay,
            'learning_rate': self.learning_rate
        }
        torch.save(checkpoint, filepath)
        print(f"Model saved to {filepath}")

    def load(self, filepath):
        """Load model weights and training parameters from file.

        Args:
            filepath: Path to load the model from
        """
        if not os.path.exists(filepath):
            print(f"Error: Model file {filepath} not found")
            return False

        checkpoint = torch.load(filepath)

        # Verify state and action sizes match
        if checkpoint['state_size'] != self.state_size or checkpoint['action_size'] != self.action_size:
            print(f"Error: Model architecture mismatch. Expected state_size={self.state_size}, action_size={self.action_size}")
            print(f"       Got state_size={checkpoint['state_size']}, action_size={checkpoint['action_size']}")
            return False

        # Load model and optimizer states
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])

        # Load hyperparameters
        self.epsilon = checkpoint['epsilon']
        self.gamma = checkpoint.get('gamma', self.gamma)
        self.epsilon_min = checkpoint.get('epsilon_min', self.epsilon_min)
        self.epsilon_decay = checkpoint.get('epsilon_decay', self.epsilon_decay)
        self.learning_rate = checkpoint.get('learning_rate', self.learning_rate)

        print(f"Model loaded from {filepath} (epsilon={self.epsilon:.4f})")
        return True
