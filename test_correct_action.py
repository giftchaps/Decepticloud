#!/usr/bin/env python3
"""
Test with correct honeypot action
"""
import sys, os
sys.path.insert(0, 'src')
from main_local import LocalDockerEnvironment

def test_correct_action():
    print("=== Testing Correct Honeypot Action ===")
    
    env = LocalDockerEnvironment()
    state = env._get_state()
    
    print(f"Current state: {state}")
    print(f"Attacker detected: {state[0] == 1}")
    
    if state[0] == 1:
        print("\n✅ SSH attack detected!")
        print("Testing Action 1 (SSH honeypot)...")
        
        # Simulate correct action
        reward = 15 + (state[3] * 0.5)  # Base reward + dwell time bonus
        print(f"Expected reward: +{reward}")
        print("This would be: SSH honeypot successfully deceiving attacker!")
        
        print("\nTesting Action 2 (Web honeypot)...")
        reward = -5  # Wrong honeypot type
        print(f"Expected reward: {reward}")
        print("This would be: Wrong honeypot type for SSH attack")
        
    else:
        print("❌ No active attack - start SSH session first")

if __name__ == "__main__":
    test_correct_action()