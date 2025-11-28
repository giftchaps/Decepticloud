#!/usr/bin/env python3
"""
Test RL training with active attack (no container reset)
"""
import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agent import DQNAgent
from main_local import LocalDockerEnvironment

def test_with_active_attack():
    print("=== DeceptiCloud: Active Attack Test ===")
    print("This test assumes you have an active SSH session running")
    print("SSH into: ssh root@localhost -p 2222 (password: admn)")
    print()
    
    # Initialize without resetting containers
    env = LocalDockerEnvironment()
    agent = DQNAgent(state_size=env.state_size, action_size=env.action_size)
    
    print("Testing current state...")
    state = env._get_state()
    print(f"Current state: {state}")
    print(f"Attacker detected: {state[0] == 1}")
    
    if state[0] != 1:
        print("\n❌ No active attack detected!")
        print("Please start an SSH session: ssh root@localhost -p 2222")
        return
    
    print("\n✅ Active attack detected! Starting RL test...")
    
    # Test a few timesteps without resetting
    total_reward = 0
    
    for timestep in range(3):
        print(f"\n--- Timestep {timestep + 1} ---")
        
        # Agent chooses action
        action = agent.act(state)
        
        # Execute action (but don't reset containers)
        if action == 0:
            print("[Action] Would stop honeypots (skipping to preserve attack)")
            reward = -1
            next_state = state  # Keep same state
        elif action == 1:
            print("[Action] SSH honeypot active")
            if state[0] == 1:  # Attacker detected
                reward = 15 + (state[3] * 0.5)  # Bonus for dwell time
                print(f"[Reward] +{reward}: SSH honeypot successfully deceiving attacker!")
            else:
                reward = -2
                print(f"[Reward] -2: SSH honeypot idle")
            next_state = env._get_state()
        elif action == 2:
            print("[Action] Web honeypot active")
            if state[0] == 1:
                reward = -5  # Wrong honeypot type
                print(f"[Reward] -5: Wrong honeypot type for SSH attack")
            else:
                reward = -2
                print(f"[Reward] -2: Web honeypot idle")
            next_state = env._get_state()
        
        # Update agent
        agent.remember(state, action, reward, next_state, False)
        state = next_state
        total_reward += reward
        
        print(f"State: {state}")
        print(f"Cumulative reward: {total_reward}")
        
        time.sleep(2)  # Brief pause
    
    print(f"\n=== Test Complete ===")
    print(f"Total reward: {total_reward}")
    print(f"Final state: {state}")
    
    if total_reward > 0:
        print("✅ SUCCESS: Positive rewards achieved with active attack!")
    else:
        print("❌ Still negative rewards - check attack detection")

if __name__ == "__main__":
    test_with_active_attack()