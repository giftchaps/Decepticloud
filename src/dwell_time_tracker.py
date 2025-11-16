"""
Dwell Time Tracker for DeceptiCloud

Tracks how long attackers interact with honeypots before detecting deception
or leaving. Longer dwell time = better deception = more intelligence gathered.

Key metrics:
- Session duration
- Commands executed
- Detection indicators (attempts to identify honeypot)
- Data exfiltration attempts
- Lateral movement attempts
"""
import time
import json
import logging
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DwellTimeTracker:
    """
    Track dwell time and session quality for honeypot interactions.

    Provides metrics to measure honeypot effectiveness beyond simple
    "number of connections" - focuses on depth of engagement.
    """

    def __init__(self):
        """Initialize dwell time tracker."""
        self.sessions = {}
        self.completed_sessions = []

        # Patterns that indicate attacker is checking for honeypot
        self.detection_patterns = [
            # Direct honeypot checks
            'cowrie', 'kippo', 'dionaea', 'honeypot', 'honeynet',

            # Process inspection
            'ps aux | grep python', 'ps aux | grep cowrie',
            '/proc/self/cwd', '/proc/self/exe',

            # Filesystem checks
            'ls -la /proc', 'find / -name "*cowrie*"',
            'find / -name "*honey*"',

            # Python detection
            'python -c', 'import os',

            # Virtual environment detection
            'lscpu | grep -i virtual', 'dmidecode',
            'cat /sys/class/dmi/id/product_name',

            # Network checks
            'netstat -an | grep -v ESTABLISHED',
            'ss -tulpn',

            # Unusual commands suggesting testing
            'echo $((1+1))', 'expr 1 + 1',
        ]

        # High-value attacker activities
        self.high_value_activities = [
            # Credential harvesting
            'cat /etc/passwd', 'cat /etc/shadow',
            'cat .aws/credentials', 'cat .ssh/id_rsa',

            # Lateral movement
            'ssh ', 'scp ', 'nc ',

            # Persistence
            'crontab', 'systemctl', 'service',
            'echo', 'wget', 'curl',

            # Data exfiltration
            'tar', 'zip', 'base64',

            # Privilege escalation
            'sudo', 'su -',
        ]

    def session_start(self, session_id: str, source_ip: str,
                     session_type: str = 'ssh') -> None:
        """
        Record the start of a new session.

        Args:
            session_id: Unique session identifier
            source_ip: Attacker's IP address
            session_type: Type of session ('ssh' or 'web')
        """
        self.sessions[session_id] = {
            'session_id': session_id,
            'source_ip': source_ip,
            'session_type': session_type,
            'start_time': time.time(),
            'start_timestamp': datetime.utcnow().isoformat(),
            'commands': [],
            'web_requests': [],
            'detection_indicators': [],
            'high_value_activities': [],
            'bytes_uploaded': 0,
            'bytes_downloaded': 0,
            'unique_commands': set(),
            'status': 'active'
        }

        logger.info(f"[DwellTime] Session started: {session_id} from {source_ip} ({session_type})")

    def log_command(self, session_id: str, command: str) -> None:
        """
        Log a command executed during the session.

        Args:
            session_id: Session identifier
            command: Command executed by attacker
        """
        if session_id not in self.sessions:
            logger.warning(f"[DwellTime] Unknown session: {session_id}")
            return

        session = self.sessions[session_id]
        timestamp = time.time()

        # Record command
        session['commands'].append({
            'command': command,
            'timestamp': timestamp,
            'time_since_start': timestamp - session['start_time']
        })

        session['unique_commands'].add(command.split()[0] if command else '')

        # Check for detection attempts
        if any(pattern in command.lower() for pattern in self.detection_patterns):
            session['detection_indicators'].append({
                'command': command,
                'timestamp': timestamp,
                'pattern': 'honeypot_detection'
            })
            logger.warning(f"[DwellTime] Detection attempt in {session_id}: {command}")

        # Check for high-value activities
        if any(activity in command.lower() for activity in self.high_value_activities):
            session['high_value_activities'].append({
                'command': command,
                'timestamp': timestamp,
                'activity_type': 'credential_access'  # Simplified categorization
            })
            logger.info(f"[DwellTime] High-value activity in {session_id}: {command}")

    def log_web_request(self, session_id: str, path: str, method: str = 'GET',
                       status_code: int = 200) -> None:
        """
        Log a web request during the session.

        Args:
            session_id: Session identifier
            path: Requested URL path
            method: HTTP method
            status_code: Response status code
        """
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]
        timestamp = time.time()

        session['web_requests'].append({
            'path': path,
            'method': method,
            'status_code': status_code,
            'timestamp': timestamp,
            'time_since_start': timestamp - session['start_time']
        })

        # Check for suspicious paths (enumeration/scanning)
        suspicious_paths = [
            '.git', '.env', '.aws', 'config.json', 'credentials',
            '../', '..\\', '/etc/passwd', 'phpMyAdmin',
            'wp-admin', 'admin', 'login'
        ]

        if any(sp in path for sp in suspicious_paths):
            session['high_value_activities'].append({
                'path': path,
                'timestamp': timestamp,
                'activity_type': 'sensitive_path_access'
            })

    def log_data_transfer(self, session_id: str, bytes_up: int = 0,
                         bytes_down: int = 0) -> None:
        """
        Log data transfer (file uploads/downloads).

        Args:
            session_id: Session identifier
            bytes_up: Bytes uploaded to honeypot
            bytes_down: Bytes downloaded from honeypot
        """
        if session_id not in self.sessions:
            return

        session = self.sessions[session_id]
        session['bytes_uploaded'] += bytes_up
        session['bytes_downloaded'] += bytes_down

    def session_end(self, session_id: str, reason: str = 'disconnect') -> Dict:
        """
        Mark session as ended and calculate metrics.

        Args:
            session_id: Session identifier
            reason: Reason for session end

        Returns:
            Session metrics dictionary
        """
        if session_id not in self.sessions:
            logger.warning(f"[DwellTime] Cannot end unknown session: {session_id}")
            return {}

        session = self.sessions[session_id]
        end_time = time.time()

        # Calculate dwell time
        dwell_time_seconds = end_time - session['start_time']
        dwell_time_minutes = dwell_time_seconds / 60

        # Determine if honeypot was detected
        detected = len(session['detection_indicators']) > 0

        # Calculate engagement score (0-100)
        engagement_score = self._calculate_engagement_score(session, dwell_time_minutes)

        # Build metrics
        metrics = {
            'session_id': session_id,
            'source_ip': session['source_ip'],
            'session_type': session['session_type'],
            'start_time': session['start_timestamp'],
            'end_time': datetime.utcnow().isoformat(),
            'dwell_time_seconds': dwell_time_seconds,
            'dwell_time_minutes': dwell_time_minutes,
            'commands_executed': len(session['commands']),
            'unique_commands': len(session['unique_commands']),
            'web_requests': len(session['web_requests']),
            'high_value_activities': len(session['high_value_activities']),
            'detection_indicators': len(session['detection_indicators']),
            'honeypot_detected': detected,
            'bytes_uploaded': session['bytes_uploaded'],
            'bytes_downloaded': session['bytes_downloaded'],
            'engagement_score': engagement_score,
            'end_reason': reason
        }

        # Store completed session
        self.completed_sessions.append(metrics)

        # Remove from active sessions
        del self.sessions[session_id]

        logger.info(f"[DwellTime] Session ended: {session_id}")
        logger.info(f"  Dwell time: {dwell_time_minutes:.1f} min")
        logger.info(f"  Commands: {metrics['commands_executed']}")
        logger.info(f"  Detected: {detected}")
        logger.info(f"  Engagement score: {engagement_score}/100")

        return metrics

    def _calculate_engagement_score(self, session: Dict, dwell_time_minutes: float) -> int:
        """
        Calculate engagement score (0-100) based on session quality.

        Higher score = better honeypot performance (attacker engaged deeply)

        Args:
            session: Session data
            dwell_time_minutes: Session duration in minutes

        Returns:
            Engagement score (0-100)
        """
        score = 0

        # Dwell time component (0-40 points)
        if dwell_time_minutes > 30:
            score += 40
        elif dwell_time_minutes > 15:
            score += 30
        elif dwell_time_minutes > 5:
            score += 20
        elif dwell_time_minutes > 2:
            score += 10

        # Commands/requests executed (0-20 points)
        total_interactions = len(session['commands']) + len(session['web_requests'])
        if total_interactions > 50:
            score += 20
        elif total_interactions > 20:
            score += 15
        elif total_interactions > 10:
            score += 10
        elif total_interactions > 5:
            score += 5

        # High-value activities (0-30 points)
        hva_count = len(session['high_value_activities'])
        if hva_count > 10:
            score += 30
        elif hva_count > 5:
            score += 20
        elif hva_count > 2:
            score += 10

        # Penalty for detection (0-20 points lost)
        if len(session['detection_indicators']) > 0:
            score -= 20
            score = max(0, score)  # Don't go negative

        # Data transfer bonus (0-10 points)
        total_bytes = session['bytes_uploaded'] + session['bytes_downloaded']
        if total_bytes > 10000:
            score += 10
        elif total_bytes > 1000:
            score += 5

        return min(100, score)  # Cap at 100

    def get_statistics(self) -> Dict:
        """
        Get aggregate statistics across all completed sessions.

        Returns:
            Dictionary with aggregate metrics
        """
        if not self.completed_sessions:
            return {
                'total_sessions': 0,
                'message': 'No completed sessions yet'
            }

        dwell_times = [s['dwell_time_minutes'] for s in self.completed_sessions]
        engagement_scores = [s['engagement_score'] for s in self.completed_sessions]
        detected_count = sum(1 for s in self.completed_sessions if s['honeypot_detected'])

        return {
            'total_sessions': len(self.completed_sessions),
            'active_sessions': len(self.sessions),
            'avg_dwell_time_minutes': sum(dwell_times) / len(dwell_times),
            'max_dwell_time_minutes': max(dwell_times),
            'min_dwell_time_minutes': min(dwell_times),
            'avg_engagement_score': sum(engagement_scores) / len(engagement_scores),
            'detection_rate': (detected_count / len(self.completed_sessions)) * 100,
            'total_commands': sum(s['commands_executed'] for s in self.completed_sessions),
            'total_high_value_activities': sum(s['high_value_activities'] for s in self.completed_sessions)
        }

    def export_sessions_to_json(self, filepath: str) -> None:
        """
        Export all completed sessions to JSON file.

        Args:
            filepath: Path to output file
        """
        data = {
            'export_timestamp': datetime.utcnow().isoformat(),
            'statistics': self.get_statistics(),
            'sessions': self.completed_sessions
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"[DwellTime] Exported {len(self.completed_sessions)} sessions to {filepath}")


# Global tracker instance
_tracker = None


def get_tracker() -> DwellTimeTracker:
    """Get global dwell time tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = DwellTimeTracker()
    return _tracker


if __name__ == "__main__":
    # Test the dwell time tracker
    logging.basicConfig(level=logging.INFO)

    tracker = DwellTimeTracker()

    # Simulate a session
    tracker.session_start('test-session-1', '203.0.113.45', 'ssh')
    time.sleep(1)

    # Simulate attacker commands
    tracker.log_command('test-session-1', 'whoami')
    time.sleep(0.5)
    tracker.log_command('test-session-1', 'cat /etc/passwd')  # High value
    time.sleep(0.5)
    tracker.log_command('test-session-1', 'ps aux | grep python')  # Detection attempt
    time.sleep(0.5)

    # End session
    metrics = tracker.session_end('test-session-1')

    print("\nSession Metrics:")
    print(json.dumps(metrics, indent=2))

    print("\nStatistics:")
    print(json.dumps(tracker.get_statistics(), indent=2))
