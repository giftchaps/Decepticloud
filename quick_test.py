print("=== DeceptiCloud System Test ===")

# Test 1: Imports
print("1. Testing imports...")
try:
    import torch, numpy, paramiko, boto3, requests
    from src.agent import DQNAgent
    from src.environment import CloudHoneynetEnv
    from src.attacker import run_attacker_thread
    print("   [OK] All imports successful")
except Exception as e:
    print(f"   [ERROR] Import failed: {e}")
    exit(1)

# Test 2: Agent
print("2. Testing agent creation...")
try:
    agent = DQNAgent(state_size=2, action_size=3)
    print("   [OK] DQN Agent created")
except Exception as e:
    print(f"   [ERROR] Agent creation failed: {e}")
    exit(1)

# Test 3: Environment
print("3. Testing environment (dry-run)...")
try:
    env = CloudHoneynetEnv('localhost', 'test', 'test.pem', dry_run=True)
    state = env.reset()
    action = agent.act(state)
    next_state, reward, done = env.step(action)
    print(f"   [OK] Environment test passed (reward={reward})")
except Exception as e:
    print(f"   [ERROR] Environment test failed: {e}")
    exit(1)

# Test 4: Honeypots
print("4. Testing honeypots...")
try:
    r = requests.get('http://localhost', timeout=5)
    if 'Admin Login' in r.text:
        print("   [OK] Web honeypot responding")
    else:
        print("   [ERROR] Web honeypot invalid response")
        exit(1)
except Exception as e:
    print(f"   [ERROR] Web honeypot failed: {e}")
    exit(1)

print()
print("*** ALL TESTS PASSED! ***")
print("System is ready for experiments!")
print()
print("To run experiment:")
print("1. Set: $env:EC2_HOST = 'your-ec2-ip'")
print("2. Set: $env:EC2_KEY_FILE = 'path/to/key.pem'")
print("3. Run: python main.py")