#!/usr/bin/env python3
"""
Test the enhanced deception system
"""

import sys
import os
import random

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from adaptive_deception import deception_engine
from cowrie_deception_config import deception_handler

def test_deception_system():
    print("=== DeceptiCloud Enhanced Deception Test ===")
    print("Simulating attacker behavior and adaptive responses\n")
    
    # Simulate attacker session
    attacker_commands = [
        ("ls", []),
        ("ls", ["desktop"]),
        ("cat", ["passwords.txt"]),
        ("find", ["/", "-name", "*password*"]),
        ("cat", ["bank_accounts.xlsx"]),
        ("grep", ["admin", "users.txt"]),
        ("ls", ["credentials"]),
        ("cat", ["ssh_keys.pem"])
    ]
    
    print("🎭 Starting adaptive deception simulation...\n")
    
    for i, (cmd, args) in enumerate(attacker_commands, 1):
        print(f"--- Command {i} ---")
        full_cmd = f"{cmd} {' '.join(args)}"
        print(f"Attacker: $ {full_cmd}")
        
        # Process command through deception system
        result = deception_handler.process_command(cmd, args)
        print(f"System Response:")
        print(result)
        
        # Show deception analysis
        metrics = deception_engine.get_deception_metrics()
        print(f"📊 Deception Status: {metrics['deception_effectiveness']}% effective")
        print(f"🎯 Interests: {', '.join(deception_engine.attacker_profile['interests'])}")
        print(f"🧠 Skill Level: {deception_engine.attacker_profile['skill_level']}")
        print()
    
    print("=== Final Deception Analysis ===")
    final_metrics = deception_engine.get_deception_metrics()
    
    print(f"Commands Analyzed: {final_metrics['commands_analyzed']}")
    print(f"Interests Identified: {final_metrics['interests_identified']}")
    print(f"Behavior Pattern: {final_metrics['behavior_pattern']}")
    print(f"Skill Level: {final_metrics['skill_level']}")
    print(f"Deception Effectiveness: {final_metrics['deception_effectiveness']}%")
    
    print("\n🎯 Deception Strategy:")
    interests = deception_engine.attacker_profile['interests']
    if 'credentials' in interests:
        print("  ✓ Showing fake credentials to maintain engagement")
    if 'financial' in interests:
        print("  ✓ Displaying fake financial data as bait")
    if 'system' in interests:
        print("  ✓ Revealing fake system configurations")
    
    print(f"\n🕒 Estimated Dwell Time Extension: +{len(attacker_commands) * 30} seconds")
    print("✅ Enhanced deception system operational!")

if __name__ == "__main__":
    test_deception_system()