#!/usr/bin/env python3
"""
Test script for DeceptiCloud Enhanced Deception System

This script tests all components of the deception system to ensure
they're working correctly.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from deception.adaptive_deception import AdaptiveDeceptionEngine, SkillLevel, InterestCategory
from deception.content_generator import ContentGenerator
from deception.deception_metrics import DeceptionMetrics
from deception.command_interceptor import CommandInterceptor


def test_adaptive_deception():
    """Test adaptive deception engine."""
    print("\n[TEST] Adaptive Deception Engine")
    print("=" * 60)

    engine = AdaptiveDeceptionEngine()

    # Test session tracking
    engine.track_session('test-1', 'ls -la', '192.168.1.100', 'root')
    engine.track_session('test-1', 'cat /etc/passwd', '192.168.1.100', 'root')
    engine.track_session('test-1', 'find / -name "*.env"', '192.168.1.100', 'root')

    # Get profile
    profile = engine.get_session_profile('test-1')
    print(f"✓ Session profile: {profile['skill_level']}")
    print(f"✓ Interests: {profile['interests']}")
    print(f"✓ Commands: {profile['command_count']}")

    # Test deception strategy
    strategy = engine.get_deception_strategy('test-1')
    print(f"✓ Complexity: {strategy['complexity']}")
    print(f"✓ Breadcrumbs: {len(strategy['breadcrumbs'])}")

    assert profile['command_count'] == 3, "Command count mismatch"
    assert len(profile['interests']) > 0, "No interests detected"

    print("✓ Adaptive Deception Engine: PASS\n")


def test_content_generator():
    """Test content generator."""
    print("\n[TEST] Content Generator")
    print("=" * 60)

    generator = ContentGenerator()

    # Test directory listing
    listing = generator.generate_directory_listing(
        '/home/ubuntu',
        ['credentials', 'financial'],
        'intermediate'
    )
    print(f"✓ Generated directory listing: {len(listing)} characters")
    assert '.ssh' in listing, ".ssh directory not in listing"

    # Test .env file
    env_content = generator.generate_file_content(
        '.env',
        ['credentials'],
        'advanced'
    )
    print(f"✓ Generated .env file: {len(env_content)} characters")
    assert 'AWS_ACCESS_KEY_ID' in env_content, "AWS key not in .env"
    assert 'DB_PASSWORD' in env_content, "DB password not in .env"

    # Test SSH key
    ssh_key = generator.generate_file_content(
        'id_rsa',
        ['credentials'],
        'expert'
    )
    print(f"✓ Generated SSH key: {len(ssh_key)} characters")
    assert 'BEGIN RSA PRIVATE KEY' in ssh_key, "Invalid SSH key format"

    # Test find results
    results = generator.generate_find_results(
        'password',
        ['credentials'],
        'intermediate'
    )
    print(f"✓ Generated find results: {len(results)} files")
    assert len(results) > 0, "No find results generated"

    # Test grep results
    grep_output = generator.generate_grep_results(
        'password',
        '/var/log/app.log',
        ['credentials'],
        'advanced'
    )
    print(f"✓ Generated grep output: {len(grep_output)} characters")
    assert 'PASSWORD' in grep_output or 'password' in grep_output, "No password matches"

    print("✓ Content Generator: PASS\n")


def test_deception_metrics():
    """Test deception metrics."""
    print("\n[TEST] Deception Metrics")
    print("=" * 60)

    metrics = DeceptionMetrics('/tmp/test_deception')

    # Start session
    metrics.start_session('test-1', '192.168.1.100', 'root', 'intermediate')

    # Record events
    metrics.record_deception_event(
        'test-1',
        'cat .env',
        'credentials_file',
        '.env file with AWS keys',
        ['credentials']
    )

    metrics.record_deception_event(
        'test-1',
        'find / -name "password*"',
        'find_results',
        'Fake password files',
        ['credentials']
    )

    metrics.record_command('test-1', 'whoami')

    # End session
    summary = metrics.end_session('test-1')

    print(f"✓ Dwell time: {summary['dwell_time']:.2f}s")
    print(f"✓ Deception events: {summary['deception_events']}")
    print(f"✓ Deception rate: {summary['deception_rate']:.2%}")
    print(f"✓ Engagement score: {summary['engagement_score']:.2f}")

    assert summary['deception_events'] == 2, "Incorrect deception event count"
    assert summary['total_commands'] == 3, "Incorrect total command count"

    # Test effectiveness report
    report = metrics.get_effectiveness_report()
    print(f"✓ Total deception events: {report['engagement_metrics']['total_deception_events']}")

    print("✓ Deception Metrics: PASS\n")


def test_command_interceptor():
    """Test command interceptor."""
    print("\n[TEST] Command Interceptor")
    print("=" * 60)

    interceptor = CommandInterceptor('/tmp/test_deception')

    # Test ls command
    response, intercepted = interceptor.process_command(
        'test-1',
        'ls -la /home/ubuntu',
        '192.168.1.100',
        'root'
    )
    print(f"✓ ls command - Intercepted: {intercepted}")
    if intercepted:
        print(f"  Response length: {len(response)} characters")

    # Test cat command
    response, intercepted = interceptor.process_command(
        'test-1',
        'cat /home/ubuntu/.env',
        '192.168.1.100',
        'root'
    )
    print(f"✓ cat .env - Intercepted: {intercepted}")
    if intercepted and response:
        assert 'AWS' in response or 'DB_' in response, "Invalid .env content"

    # Test find command
    response, intercepted = interceptor.process_command(
        'test-1',
        'find / -name "*.env"',
        '192.168.1.100',
        'root'
    )
    print(f"✓ find command - Intercepted: {intercepted}")

    # Get metrics
    report = interceptor.get_metrics_report()
    print(f"✓ Metrics available: {len(report.keys())} categories")

    print("✓ Command Interceptor: PASS\n")


def test_integration():
    """Test full integration."""
    print("\n[TEST] Full Integration")
    print("=" * 60)

    interceptor = CommandInterceptor('/tmp/test_deception')

    # Simulate attacker session
    commands = [
        'ls -la',
        'pwd',
        'whoami',
        'cat /etc/passwd',
        'find / -name "password*"',
        'grep -r "password" /home',
        'cat ~/.aws/credentials',
        'cat .env',
        'ps aux',
        'netstat -an',
    ]

    session_id = 'integration-test'
    ip = '192.168.1.100'
    username = 'attacker'

    intercepted_count = 0
    for cmd in commands:
        response, intercepted = interceptor.process_command(
            session_id, cmd, ip, username
        )
        if intercepted:
            intercepted_count += 1

    print(f"✓ Processed {len(commands)} commands")
    print(f"✓ Intercepted {intercepted_count} commands")
    print(f"✓ Interception rate: {intercepted_count/len(commands):.1%}")

    # Get final metrics
    profile = interceptor.deception_engine.get_session_profile(session_id)
    print(f"✓ Final skill level: {profile['skill_level']}")
    print(f"✓ Interests discovered: {', '.join(profile['interests'])}")

    # Get RL reward
    reward = interceptor.get_rl_reward(session_id)
    print(f"✓ RL reward bonus: {reward:.2f}")

    assert intercepted_count > 0, "No commands were intercepted"
    assert reward > 0, "No RL reward generated"

    print("✓ Full Integration: PASS\n")


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("DeceptiCloud Enhanced Deception System - Test Suite")
    print("=" * 60)

    try:
        test_adaptive_deception()
        test_content_generator()
        test_deception_metrics()
        test_command_interceptor()
        test_integration()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60 + "\n")
        return 0

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}\n")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
