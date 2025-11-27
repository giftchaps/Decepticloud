import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque
from .monitoring import monitor

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
        
        print(f"[Agent] Neural network architecture:")
        print(f"  Input: {state_size} -> Hidden: 24 -> Hidden: 24 -> Output: {action_size}")
        print(f"  Total parameters: {sum(p.numel() for p in self.model.parameters())}")
        
        # Learning tracking
        self.episode_rewards = []
        self.learning_started = False
        
        print(f"[Agent] Initialized DQN with state_size={state_size}, action_size={action_size}")
        print(f"[Agent] Starting epsilon={self.epsilon}, will decay to {self.epsilon_min}")

    def _build_model(self):
        model = nn.Sequential(
            nn.Linear(self.state_size, 24),
            nn.ReLU(),
            nn.Linear(24, 24),
            nn.ReLU(),
            nn.Linear(24, self.action_size)
        )
        return model
    
    def get_learning_stats(self):
        """Get current learning statistics"""
        return {
            'epsilon': self.epsilon,
            'memory_size': len(self.memory),
            'learning_started': self.learning_started,
            'total_episodes': len(self.episode_rewards),
            'avg_reward_last_10': np.mean(self.episode_rewards[-10:]) if len(self.episode_rewards) >= 10 else 0
        }

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
        
        # Track when learning actually starts
        if len(self.memory) >= 32 and not self.learning_started:
            self.learning_started = True
            print(f"[Agent] Learning started! Memory size: {len(self.memory)}")

    def act(self, state):
        # Accepts either a 1D state array or a 2D (1, state_size)
        if np.random.rand() <= self.epsilon:
            action = random.randrange(self.action_size)
            print(f"[Agent] Random action: {action} (epsilon={self.epsilon:.3f})")
            return action

        state_arr = np.array(state)
        if state_arr.ndim == 1:
            state_tensor = torch.FloatTensor(state_arr).unsqueeze(0)
        else:
            state_tensor = torch.FloatTensor(state_arr)

        with torch.no_grad():
            act_values = self.model(state_tensor)

        # If batch, pick first; otherwise single
        if act_values.dim() == 2:
            action = torch.argmax(act_values[0]).item()
            q_vals = act_values[0].numpy()
        else:
            action = torch.argmax(act_values).item()
            q_vals = act_values.numpy()
        
        print(f"[Agent] Learned action: {action} (Q-values: {q_vals})")
        return action

    def learn(self, batch_size, episode=0):
        if len(self.memory) < batch_size:
            return

        minibatch = random.sample(self.memory, batch_size)
        total_loss = 0
        q_values = []

        for state, action, reward, next_state, done in minibatch:
            s_arr = np.array(state)
            ns_arr = np.array(next_state)

            s_tensor = torch.FloatTensor(s_arr).unsqueeze(0) if s_arr.ndim == 1 else torch.FloatTensor(s_arr)
            ns_tensor = torch.FloatTensor(ns_arr).unsqueeze(0) if ns_arr.ndim == 1 else torch.FloatTensor(ns_arr)

            target = self.model(s_tensor).clone().detach()
            current_q_values = self.model(s_tensor).detach().numpy().flatten()
            q_values.extend(current_q_values)

            if done:
                target[0][action] = reward
            else:
                t_next = self.model(ns_tensor).detach()
                target[0][action] = reward + self.gamma * torch.max(t_next)

            prediction = self.model(s_tensor)
            loss = self.criterion(prediction, target)
            total_loss += loss.item()

            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        
        # Send learning metrics to CloudWatch
        try:
            avg_loss = total_loss / len(minibatch)
            monitor.send_learning_metrics(
                episode=episode,
                epsilon=self.epsilon,
                loss=avg_loss,
                q_values=q_values
            )
        except Exception as e:
            print(f"Failed to send learning metrics: {e}")
