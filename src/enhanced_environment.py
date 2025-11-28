"""
Enhanced Cloud Honeynet Environment with Adaptive Deception

Extends the base CloudHoneynetEnv with deception metrics and enhanced rewards.
"""

import numpy as np
import json
import os
import sys
from pathlib import Path

# Add deception module to path
sys.path.insert(0, str(Path(__file__).parent))

from .environment import CloudHoneynetEnv
from .deception.cowrie_integration import CowrieIntegration
from .deception.command_interceptor import CommandInterceptor


class EnhancedCloudHoneynetEnv(CloudHoneynetEnv):
    """
    Enhanced environment that integrates adaptive deception with the RL framework.

    Extends the base environment with:
    - Deception effectiveness metrics
    - Enhanced reward function based on attacker engagement
    - Skill level detection and profiling
    - Interest-based deception strategies
    """

    def __init__(self, *args, deception_data_dir='./data/deception', **kwargs):
        """
        Initialize enhanced environment.

        Args:
            *args: Arguments for base CloudHoneynetEnv
            deception_data_dir: Directory for deception system data
            **kwargs: Keyword arguments for base CloudHoneynetEnv
        """
        super().__init__(*args, **kwargs)

        # Initialize deception system
        self.deception_data_dir = Path(deception_data_dir)
        self.deception_data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Cowrie integration for log monitoring
        cowrie_log = str(self.deception_data_dir / 'cowrie_local.json')
        self.cowrie_integration = CowrieIntegration(
            log_file=cowrie_log,
            data_dir=str(self.deception_data_dir)
        )

        # Track deception-enhanced sessions
        self.session_metrics = {}
        self.total_deception_events = 0
        self.deception_rewards_accumulated = 0.0

        # Enhanced state size (adds deception metrics)
        # Original: [ssh_attack, web_attack, current_honeypot]
        # Enhanced: [ssh_attack, web_attack, current_honeypot, deception_active, engagement_score]
        self.state_size = 5

        print("[Enhanced Environment] Adaptive deception system initialized")

    def _get_enhanced_state(self, base_state):
        """
        Enhance base state with deception metrics.

        Args:
            base_state: Base state [ssh_attack, web_attack, current_honeypot]

        Returns:
            Enhanced state with deception metrics
        """
        ssh_attack, web_attack, current_honeypot = base_state

        # Get deception metrics
        deception_active = 1 if self.total_deception_events > 0 else 0

        # Calculate average engagement score across active sessions
        engagement_score = 0.0
        active_sessions = self.cowrie_integration.active_sessions

        if active_sessions:
            total_engagement = 0.0
            count = 0

            for session_id in active_sessions.keys():
                metrics = self.cowrie_integration.get_session_metrics(session_id)
                if metrics:
                    total_engagement += metrics.get('engagement_score', 0.0)
                    count += 1

            if count > 0:
                engagement_score = min(total_engagement / count / 10.0, 1.0)  # Normalize to 0-1

        return np.array([
            ssh_attack,
            web_attack,
            current_honeypot,
            deception_active,
            engagement_score
        ], dtype=np.float32)

    def _process_cowrie_logs(self):
        """
        Process Cowrie logs to extract deception metrics.

        Returns:
            Dictionary with deception statistics
        """
        stats = {
            'new_sessions': 0,
            'deception_events': 0,
            'engagement_score': 0.0,
            'skill_levels': {},
            'interests': {},
        }

        # Check if Cowrie is running
        if not self._check_container_health('cowrie_honeypot'):
            return stats

        # Read recent Cowrie logs
        cmd = "docker exec cowrie_honeypot cat /cowrie/var/log/cowrie/cowrie.json 2>/dev/null | tail -n 50 || echo ''"
        log_data, err = self._execute_command(cmd)

        if not log_data or not log_data.strip():
            return stats

        # Process each log entry
        for line in log_data.strip().split('\n'):
            if not line:
                continue

            try:
                entry = json.loads(line)
                session_id = entry.get('session')

                # Track new sessions
                if entry.get('eventid') == 'cowrie.session.connect':
                    stats['new_sessions'] += 1

                # Process commands for deception
                elif entry.get('eventid') == 'cowrie.command.input':
                    command = entry.get('input', '')
                    src_ip = entry.get('src_ip', 'unknown')
                    username = self.cowrie_integration.active_sessions.get(
                        session_id, {}
                    ).get('username', 'unknown')

                    # Process through deception system
                    response, intercepted = self.cowrie_integration.get_command_response(
                        session_id, command, src_ip, username
                    )

                    if intercepted:
                        stats['deception_events'] += 1
                        self.total_deception_events += 1

                    # Get session metrics
                    metrics = self.cowrie_integration.get_session_metrics(session_id)
                    if metrics:
                        stats['engagement_score'] += metrics.get('engagement_score', 0.0)

                        skill_level = metrics.get('skill_level', 'unknown')
                        stats['skill_levels'][skill_level] = stats['skill_levels'].get(skill_level, 0) + 1

                        for interest in metrics.get('interests', []):
                            stats['interests'][interest] = stats['interests'].get(interest, 0) + 1

            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"[Warning] Error processing log entry: {e}")
                continue

        return stats

    def _calculate_deception_reward(self, stats):
        """
        Calculate reward bonus based on deception effectiveness.

        Args:
            stats: Deception statistics from log processing

        Returns:
            Reward value
        """
        reward = 0.0

        # Reward for deception events (attacker engaged with fake content)
        reward += stats['deception_events'] * 0.5

        # Reward for engagement score
        reward += stats['engagement_score'] * 0.1

        # Bonus for diverse skill levels (honeypot is fooling different attackers)
        num_skill_levels = len(stats['skill_levels'])
        if num_skill_levels > 1:
            reward += num_skill_levels * 0.5

        # Bonus for discovering attacker interests (intelligence gathering)
        num_interests = len(stats['interests'])
        reward += num_interests * 0.3

        # Bonus for fooling advanced attackers (harder to deceive)
        if 'advanced' in stats['skill_levels']:
            reward += stats['skill_levels']['advanced'] * 1.0
        if 'expert' in stats['skill_levels']:
            reward += stats['skill_levels']['expert'] * 2.0

        return reward

    def step(self, action):
        """
        Execute action and return enhanced state with deception rewards.

        Args:
            action: Action to execute (0=stop, 1=cowrie, 2=web)

        Returns:
            Tuple of (next_state, reward, done)
        """
        # Execute base environment step
        base_state, base_reward, done = super().step(action)

        # Process deception metrics
        deception_stats = self._process_cowrie_logs()

        # Calculate deception reward bonus
        deception_reward = self._calculate_deception_reward(deception_stats)
        self.deception_rewards_accumulated += deception_reward

        # Combine rewards
        total_reward = base_reward + deception_reward

        # Enhance state
        enhanced_state = self._get_enhanced_state(base_state)

        # Log deception metrics
        if deception_stats['deception_events'] > 0:
            print(f"[Deception] Events: {deception_stats['deception_events']}, "
                  f"Engagement: {deception_stats['engagement_score']:.2f}, "
                  f"Reward: +{deception_reward:.2f}")

        return enhanced_state, total_reward, done

    def reset(self):
        """Reset environment and deception tracking."""
        base_state = super().reset()

        # Reset deception metrics for new episode
        self.session_metrics = {}
        self.total_deception_events = 0
        self.deception_rewards_accumulated = 0.0

        # Return enhanced state
        return self._get_enhanced_state(base_state)

    def get_deception_report(self):
        """
        Get comprehensive deception effectiveness report.

        Returns:
            Dictionary with deception metrics
        """
        report = self.cowrie_integration.get_effectiveness_report()

        # Add environment-specific metrics
        report['environment_metrics'] = {
            'total_deception_events': self.total_deception_events,
            'accumulated_deception_rewards': round(self.deception_rewards_accumulated, 2),
            'active_sessions': len(self.cowrie_integration.active_sessions),
        }

        return report

    def export_deception_metrics(self, episode_num=None):
        """
        Export deception metrics to file.

        Args:
            episode_num: Optional episode number for filename

        Returns:
            Tuple of (json_path, csv_path)
        """
        # Export via Cowrie integration
        json_path = self.cowrie_integration.export_metrics('json')
        csv_path = self.cowrie_integration.export_metrics('csv')

        # Also save environment-specific summary
        if episode_num is not None:
            summary_path = self.deception_data_dir / f'episode_{episode_num}_summary.json'
            with open(summary_path, 'w') as f:
                json.dump(self.get_deception_report(), f, indent=2)

            print(f"[Deception] Metrics exported: {summary_path}")

        return json_path, csv_path

    def __del__(self):
        """Cleanup and export final metrics."""
        try:
            # Export final metrics
            self.export_deception_metrics()
        except Exception as e:
            print(f"[Warning] Error exporting final metrics: {e}")

        # Call parent cleanup
        super().__del__()
