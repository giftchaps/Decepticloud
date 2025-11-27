#!/usr/bin/env python3
"""
System verification test for DeceptiCloud
Tests all components before running full experiment
"""
import os
import sys
import time
import requests
import socket

def test_docker_honeypots():
    """Test that Docker honeypots are running and accessible"""
    print("=== Testing Docker Honeypots ===")
    
    # Test web honeypot
    try:
        response = requests.get('http://localhost', timeout=5)
        if response.status_code == 200 and 'Admin Login' in response.text:
            print("✅ Web honeypot: WORKING")
        else:
            print("❌ Web honeypot: Response invalid")
            return False
    except Exception as e:
        print(f"❌ Web honeypot: {e}")
        return False
    
    # Test SSH honeypot port
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('localhost', 2222))
        sock.close()
        if result == 0:
            print("✅ SSH honeypot: LISTENING on port 2222")
        else:
            print("❌ SSH honeypot: Port 2222 not accessible")
            return False
    except Exception as e:
        print(f"❌ SSH honeypot: {e}")
        return False
    
    return True

def test_python_imports():
    """Test that all required Python modules can be imported"""
    print("\n=== Testing Python Imports ===")
    
    modules = [
        ('torch', 'PyTorch for RL agent'),
        ('numpy', 'NumPy for arrays'),
        ('paramiko', 'SSH client'),
        ('boto3', 'AWS SDK'),
        ('src.agent', 'DQN Agent'),
        ('src.environment', 'Cloud Environment'),
        ('src.attacker', 'Attacker module')
    ]
    
    for module, description in modules:
        try:
            __import__(module)
            print(f"✅ {module}: OK ({description})")
        except ImportError as e:
            print(f"❌ {module}: FAILED - {e}")
            return False
    
    return True

def test_environment_creation():
    """Test creating the CloudHoneynetEnv in dry-run mode"""
    print("\n=== Testing Environment Creation ===")
    
    try:
        from src.environment import CloudHoneynetEnv
        from src.agent import DQNAgent
        
        # Test dry-run environment
        env = CloudHoneynetEnv(
            host="localhost", 
            user="test", 
            key_file="test.pem", 
            dry_run=True
        )
        print("✅ Environment creation: OK")
        
        # Test agent creation
        agent = DQNAgent(state_size=2, action_size=3)
        print("✅ Agent creation: OK")
        
        # Test basic interaction
        state = env.reset()
        action = agent.act(state)
        next_state, reward, done = env.step(action)
        print(f"✅ Basic interaction: OK (action={action}, reward={reward})")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment test: {e}")
        return False

def test_attack_simulation():
    """Test attack simulation against honeypots"""
    print("\n=== Testing Attack Simulation ===")
    
    try:
        # Test web attack
        login_data = {'username': 'admin', 'password': 'test123'}
        response = requests.post('http://localhost/login', data=login_data, timeout=5)
        if response.status_code == 401:
            print("✅ Web attack simulation: OK (login rejected as expected)")
        else:
            print(f"❌ Web attack simulation: Unexpected response {response.status_code}")
            return False
            
        # Test SSH attack (just connection test)
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect('localhost', port=2222, username='test', password='test', timeout=5)
            print("❌ SSH attack simulation: Login succeeded (should fail)")
            return False
        except paramiko.AuthenticationException:
            print("✅ SSH attack simulation: OK (login rejected as expected)")
        except Exception as e:
            print(f"✅ SSH attack simulation: OK (connection handled: {e})")
        finally:
            ssh.close()
            
        return True
        
    except Exception as e:
        print(f"❌ Attack simulation: {e}")
        return False

def main():
    """Run all system tests"""
    print("=== DeceptiCloud System Verification ===")
    print("=" * 50)
    
    tests = [
        test_docker_honeypots,
        test_python_imports,
        test_environment_creation,
        test_attack_simulation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("*** ALL TESTS PASSED! System is ready for experiments. ***")
        print("\nNext steps:")
        print("1. Set environment variables:")
        print("   $env:EC2_HOST = 'your-ec2-ip'")
        print("   $env:EC2_KEY_FILE = 'path/to/key.pem'")
        print("2. Run experiment: python main.py")
        return True
    else:
        print("*** Some tests failed. Fix issues before running experiments. ***")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)