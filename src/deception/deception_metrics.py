"""
Deception Metrics Module

Tracks engagement, interest profiling, and deception effectiveness scoring.
Extends the existing DwellTimeTracker with enhanced deception-specific metrics.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class DeceptionInteraction:
    """Represents an interaction with deceptive content"""
    timestamp: datetime
    command: str
    deception_type: str  # 'file', 'directory', 'command_output'
    content_served: str
    interests_triggered: List[str]
    skill_level: str
    engagement_score: float


class DeceptionMetrics:
    """
    Enhanced metrics tracking for deception effectiveness.

    Tracks:
    - Engagement time per deception type
    - Interest profiling (what attackers search for)
    - Success rate of different deception strategies
    - Dwell time improvements from deception
    """

    def __init__(self, data_dir: str = "./data/deception"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Session tracking
        self.sessions: Dict[str, Dict] = {}

        # Deception interactions
        self.interactions: List[DeceptionInteraction] = []

        # Statistics
        self.stats = {
            'total_deception_events': 0,
            'deception_by_type': defaultdict(int),
            'interests_discovered': defaultdict(int),
            'avg_engagement_by_skill': defaultdict(list),
            'dwell_time_improvements': [],
        }

        # Effectiveness tracking
        self.baseline_dwell_times: List[float] = []
        self.deception_dwell_times: List[float] = []

    def start_session(self, session_id: str, ip: str, username: str,
                     skill_level: str = 'unknown') -> None:
        """
        Initialize tracking for a new session.

        Args:
            session_id: Unique session identifier
            ip: Attacker IP address
            username: Username used in session
            skill_level: Detected skill level
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'session_id': session_id,
                'ip': ip,
                'username': username,
                'skill_level': skill_level,
                'start_time': datetime.now(),
                'last_activity': datetime.now(),
                'commands': [],
                'deception_events': 0,
                'interests': set(),
                'engagement_score': 0.0,
                'commands_with_deception': 0,
                'total_commands': 0,
            }

    def record_deception_event(self, session_id: str, command: str,
                              deception_type: str, content_served: str,
                              interests: List[str]) -> None:
        """
        Record a deception event (attacker interacted with fake content).

        Args:
            session_id: Session identifier
            command: Command that triggered deception
            deception_type: Type of deception (file, directory, etc.)
            content_served: Description of content served
            interests: Interest categories triggered
        """
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]
        session['last_activity'] = datetime.now()
        session['deception_events'] += 1
        session['commands'].append(command)
        session['total_commands'] += 1
        session['commands_with_deception'] += 1

        # Track interests
        for interest in interests:
            session['interests'].add(interest)
            self.stats['interests_discovered'][interest] += 1

        # Calculate engagement score for this event
        engagement_score = self._calculate_engagement_score(
            command, deception_type, interests, session['skill_level']
        )
        session['engagement_score'] += engagement_score

        # Create interaction record
        interaction = DeceptionInteraction(
            timestamp=datetime.now(),
            command=command,
            deception_type=deception_type,
            content_served=content_served,
            interests_triggered=interests,
            skill_level=session['skill_level'],
            engagement_score=engagement_score
        )
        self.interactions.append(interaction)

        # Update statistics
        self.stats['total_deception_events'] += 1
        self.stats['deception_by_type'][deception_type] += 1
        self.stats['avg_engagement_by_skill'][session['skill_level']].append(engagement_score)

    def record_command(self, session_id: str, command: str) -> None:
        """
        Record a command that didn't trigger deception.

        Args:
            session_id: Session identifier
            command: Command executed
        """
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]
        session['last_activity'] = datetime.now()
        session['commands'].append(command)
        session['total_commands'] += 1

    def end_session(self, session_id: str) -> Optional[Dict]:
        """
        End a session and calculate final metrics.

        Args:
            session_id: Session identifier

        Returns:
            Session summary with deception effectiveness metrics
        """
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        session['end_time'] = datetime.now()

        # Calculate dwell time
        dwell_time = (session['end_time'] - session['start_time']).total_seconds()
        session['dwell_time'] = dwell_time

        # Calculate deception effectiveness
        deception_rate = (
            session['commands_with_deception'] / session['total_commands']
            if session['total_commands'] > 0 else 0
        )
        session['deception_rate'] = deception_rate

        # Calculate engagement per minute
        if dwell_time > 0:
            session['engagement_per_minute'] = (
                session['engagement_score'] / (dwell_time / 60)
            )
        else:
            session['engagement_per_minute'] = 0

        # Track dwell time for effectiveness comparison
        if deception_rate > 0.5:  # Session had significant deception
            self.deception_dwell_times.append(dwell_time)
        else:
            self.baseline_dwell_times.append(dwell_time)

        # Calculate improvement
        if self.baseline_dwell_times and self.deception_dwell_times:
            avg_baseline = sum(self.baseline_dwell_times) / len(self.baseline_dwell_times)
            avg_deception = sum(self.deception_dwell_times) / len(self.deception_dwell_times)
            improvement = ((avg_deception - avg_baseline) / avg_baseline) * 100 if avg_baseline > 0 else 0
            self.stats['dwell_time_improvements'].append(improvement)

        summary = {
            'session_id': session_id,
            'ip': session['ip'],
            'username': session['username'],
            'skill_level': session['skill_level'],
            'dwell_time': dwell_time,
            'total_commands': session['total_commands'],
            'deception_events': session['deception_events'],
            'deception_rate': deception_rate,
            'interests': list(session['interests']),
            'engagement_score': session['engagement_score'],
            'engagement_per_minute': session['engagement_per_minute'],
        }

        return summary

    def get_effectiveness_report(self) -> Dict:
        """
        Generate comprehensive deception effectiveness report.

        Returns:
            Dictionary with effectiveness metrics
        """
        # Calculate average dwell times
        avg_baseline = (
            sum(self.baseline_dwell_times) / len(self.baseline_dwell_times)
            if self.baseline_dwell_times else 0
        )
        avg_deception = (
            sum(self.deception_dwell_times) / len(self.deception_dwell_times)
            if self.deception_dwell_times else 0
        )

        # Calculate improvement percentage
        improvement = 0
        if avg_baseline > 0:
            improvement = ((avg_deception - avg_baseline) / avg_baseline) * 100

        # Calculate average engagement by skill level
        avg_engagement_by_skill = {}
        for skill, scores in self.stats['avg_engagement_by_skill'].items():
            avg_engagement_by_skill[skill] = sum(scores) / len(scores) if scores else 0

        # Most effective deception types
        deception_effectiveness = {}
        for dtype, count in self.stats['deception_by_type'].items():
            # Calculate average engagement for this type
            type_interactions = [
                i for i in self.interactions if i.deception_type == dtype
            ]
            avg_engagement = (
                sum(i.engagement_score for i in type_interactions) / len(type_interactions)
                if type_interactions else 0
            )
            deception_effectiveness[dtype] = {
                'count': count,
                'avg_engagement': avg_engagement
            }

        return {
            'timestamp': datetime.now().isoformat(),
            'dwell_time_analysis': {
                'avg_baseline_seconds': round(avg_baseline, 2),
                'avg_with_deception_seconds': round(avg_deception, 2),
                'improvement_percentage': round(improvement, 2),
                'baseline_sessions': len(self.baseline_dwell_times),
                'deception_sessions': len(self.deception_dwell_times),
            },
            'engagement_metrics': {
                'total_deception_events': self.stats['total_deception_events'],
                'avg_engagement_by_skill': {
                    k: round(v, 2) for k, v in avg_engagement_by_skill.items()
                },
            },
            'deception_effectiveness': deception_effectiveness,
            'interest_profile': dict(self.stats['interests_discovered']),
            'active_sessions': len(self.sessions),
        }

    def get_session_profile(self, session_id: str) -> Optional[Dict]:
        """
        Get detailed profile for a specific session.

        Args:
            session_id: Session identifier

        Returns:
            Session profile or None if not found
        """
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        return {
            'session_id': session_id,
            'ip': session['ip'],
            'username': session['username'],
            'skill_level': session['skill_level'],
            'duration': (
                (session['last_activity'] - session['start_time']).total_seconds()
            ),
            'total_commands': session['total_commands'],
            'deception_events': session['deception_events'],
            'interests': list(session['interests']),
            'engagement_score': round(session['engagement_score'], 2),
        }

    def get_interest_analysis(self) -> Dict:
        """
        Analyze attacker interests across all sessions.

        Returns:
            Interest analysis report
        """
        # Count unique sessions per interest
        sessions_per_interest = defaultdict(set)
        for session_id, session in self.sessions.items():
            for interest in session['interests']:
                sessions_per_interest[interest].add(session_id)

        # Calculate popularity
        total_sessions = len(self.sessions)
        interest_popularity = {}
        for interest, sessions in sessions_per_interest.items():
            interest_popularity[interest] = {
                'sessions': len(sessions),
                'percentage': round(
                    (len(sessions) / total_sessions * 100) if total_sessions > 0 else 0,
                    2
                ),
                'total_events': self.stats['interests_discovered'][interest],
            }

        # Sort by popularity
        sorted_interests = dict(
            sorted(
                interest_popularity.items(),
                key=lambda x: x[1]['sessions'],
                reverse=True
            )
        )

        return {
            'timestamp': datetime.now().isoformat(),
            'total_sessions_analyzed': total_sessions,
            'interests_by_popularity': sorted_interests,
        }

    def export_json(self, filepath: Optional[str] = None) -> str:
        """
        Export all metrics to JSON.

        Args:
            filepath: Optional file path, defaults to timestamped file

        Returns:
            Path to exported file
        """
        if filepath is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = str(self.data_dir / f'deception_metrics_{timestamp}.json')

        data = {
            'export_timestamp': datetime.now().isoformat(),
            'effectiveness_report': self.get_effectiveness_report(),
            'interest_analysis': self.get_interest_analysis(),
            'sessions': {
                sid: {
                    **session,
                    'start_time': session['start_time'].isoformat(),
                    'last_activity': session['last_activity'].isoformat(),
                    'interests': list(session['interests']),
                }
                for sid, session in self.sessions.items()
            },
            'recent_interactions': [
                {
                    'timestamp': i.timestamp.isoformat(),
                    'command': i.command,
                    'deception_type': i.deception_type,
                    'interests': i.interests_triggered,
                    'skill_level': i.skill_level,
                    'engagement_score': round(i.engagement_score, 2),
                }
                for i in self.interactions[-100:]  # Last 100 interactions
            ],
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        return filepath

    def export_csv_summary(self, filepath: Optional[str] = None) -> str:
        """
        Export session summaries to CSV for easy analysis.

        Args:
            filepath: Optional file path

        Returns:
            Path to exported file
        """
        if filepath is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = str(self.data_dir / f'deception_sessions_{timestamp}.csv')

        import csv

        with open(filepath, 'w', newline='') as f:
            fieldnames = [
                'session_id', 'ip', 'username', 'skill_level', 'duration_seconds',
                'total_commands', 'deception_events', 'deception_rate',
                'engagement_score', 'interests'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for session_id, session in self.sessions.items():
                duration = (
                    session['last_activity'] - session['start_time']
                ).total_seconds()
                deception_rate = (
                    session['commands_with_deception'] / session['total_commands']
                    if session['total_commands'] > 0 else 0
                )

                writer.writerow({
                    'session_id': session_id,
                    'ip': session['ip'],
                    'username': session['username'],
                    'skill_level': session['skill_level'],
                    'duration_seconds': round(duration, 2),
                    'total_commands': session['total_commands'],
                    'deception_events': session['deception_events'],
                    'deception_rate': round(deception_rate, 4),
                    'engagement_score': round(session['engagement_score'], 2),
                    'interests': ';'.join(session['interests']),
                })

        return filepath

    def _calculate_engagement_score(self, command: str, deception_type: str,
                                    interests: List[str], skill_level: str) -> float:
        """
        Calculate engagement score for a deception event.

        Higher scores indicate more valuable engagement (attacker is more interested).

        Args:
            command: Command executed
            deception_type: Type of deception
            interests: Interests triggered
            skill_level: Attacker skill level

        Returns:
            Engagement score (0-10)
        """
        score = 1.0  # Base score

        # Boost for high-value deception types
        type_multipliers = {
            'credentials_file': 3.0,
            'financial_data': 2.5,
            'database_dump': 2.5,
            'config_file': 2.0,
            'ssh_key': 3.0,
            'env_file': 2.5,
            'directory_listing': 1.0,
            'command_output': 1.5,
        }
        score *= type_multipliers.get(deception_type, 1.0)

        # Boost for multiple interests
        score *= (1 + len(interests) * 0.3)

        # Boost for advanced attackers (they're harder to fool)
        skill_multipliers = {
            'novice': 1.0,
            'intermediate': 1.2,
            'advanced': 1.5,
            'expert': 2.0,
        }
        score *= skill_multipliers.get(skill_level, 1.0)

        # Boost for longer commands (more effort)
        if len(command) > 50:
            score *= 1.2

        # Boost for complex commands
        if any(x in command.lower() for x in ['grep', 'find', 'awk', 'sed']):
            score *= 1.3

        # Cap at 10
        return min(score, 10.0)

    def get_rl_reward_bonus(self, session_id: str) -> float:
        """
        Calculate reward bonus for RL agent based on deception effectiveness.

        This integrates with the existing RL framework to provide additional
        rewards when deception is successful.

        Args:
            session_id: Session identifier

        Returns:
            Reward bonus (0-10)
        """
        if session_id not in self.sessions:
            return 0.0

        session = self.sessions[session_id]

        # Base reward on engagement score
        reward = session['engagement_score'] * 0.1

        # Bonus for high deception rate
        if session['total_commands'] > 0:
            deception_rate = session['commands_with_deception'] / session['total_commands']
            if deception_rate > 0.7:
                reward += 2.0
            elif deception_rate > 0.5:
                reward += 1.0

        # Bonus for discovering multiple interests
        reward += len(session['interests']) * 0.5

        # Cap at 10
        return min(reward, 10.0)
