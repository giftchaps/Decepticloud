#!/usr/bin/env python3
"""
Cowrie Deception Integration

Enhances Cowrie honeypot with adaptive fake content generation.
Intercepts commands and provides convincing fake responses.
"""

import os
import sys
import json
import random
from src.adaptive_deception import deception_engine

class CowrieDeceptionHandler:
    def __init__(self):
        self.fake_filesystem = {}
        self.command_history = []
        print("[Cowrie] Deception handler initialized")
    
    def handle_ls_command(self, path="/"):
        """Handle 'ls' command with fake directory listing"""
        fake_items = deception_engine.generate_fake_directory_listing(path)
        
        # Format as realistic ls output
        output_lines = []
        for item in fake_items:
            if item in ['home', 'var', 'etc', 'tmp', 'opt']:
                output_lines.append(f"drwxr-xr-x 2 root root 4096 Nov 28 12:00 {item}")
            elif '.' in item:  # Files
                size = random.randint(1024, 50000)
                output_lines.append(f"-rw-r--r-- 1 root root {size} Nov 28 12:00 {item}")
            else:  # Directories
                output_lines.append(f"drwxr-xr-x 2 root root 4096 Nov 28 12:00 {item}")
        
        return "\n".join(output_lines)
    
    def handle_cat_command(self, filename):
        """Handle 'cat' command with fake file content"""
        if deception_engine.should_show_fake_content(f"cat {filename}"):
            content = deception_engine.generate_fake_file_content(filename)
            print(f"[Deception] Showing fake content for: {filename}")
            return content
        else:
            return f"cat: {filename}: No such file or directory"
    
    def handle_find_command(self, args):
        """Handle 'find' command with targeted fake results"""
        # Analyze what attacker is looking for
        search_term = " ".join(args).lower()
        
        fake_results = []
        if 'password' in search_term or 'passwd' in search_term:
            fake_results = [
                "/home/admin/.ssh/backup_passwords.txt",
                "/var/backups/mysql_passwords.sql",
                "/etc/shadow.backup"
            ]
        elif 'config' in search_term:
            fake_results = [
                "/etc/apache2/apache2.conf",
                "/home/admin/database.config",
                "/opt/app/production.config"
            ]
        elif 'key' in search_term:
            fake_results = [
                "/home/admin/.ssh/id_rsa",
                "/var/ssl/private/server.key",
                "/etc/ssl/api_keys.txt"
            ]
        else:
            # Generic interesting files
            fake_results = [
                "/home/admin/important_notes.txt",
                "/var/backups/daily_backup.tar.gz",
                "/tmp/temp_data.csv"
            ]
        
        return "\n".join(fake_results[:3])  # Limit to 3 results
    
    def process_command(self, command, args=[]):
        """Main command processor with deception logic"""
        deception_engine.analyze_attacker_behavior(f"{command} {' '.join(args)}")
        
        if command == "ls":
            path = args[0] if args else "/"
            return self.handle_ls_command(path)
        
        elif command == "cat":
            if args:
                return self.handle_cat_command(args[0])
            return "cat: missing file operand"
        
        elif command == "find":
            return self.handle_find_command(args)
        
        elif command in ["head", "tail"]:
            if args:
                content = deception_engine.generate_fake_file_content(args[0])
                lines = content.split('\n')
                if command == "head":
                    return '\n'.join(lines[:10])
                else:
                    return '\n'.join(lines[-10:])
            return f"{command}: missing file operand"
        
        elif command == "grep":
            if len(args) >= 2:
                pattern = args[0]
                filename = args[1]
                content = deception_engine.generate_fake_file_content(filename)
                # Simple grep simulation
                matching_lines = [line for line in content.split('\n') if pattern.lower() in line.lower()]
                return '\n'.join(matching_lines[:5])  # Limit results
            return "grep: missing arguments"
        
        elif command == "pwd":
            return "/home/admin"
        
        elif command == "whoami":
            return "admin"
        
        elif command == "id":
            return "uid=1000(admin) gid=1000(admin) groups=1000(admin),4(adm),24(cdrom),27(sudo)"
        
        else:
            # Default response for unknown commands
            return f"{command}: command not found"

# Global handler instance
deception_handler = CowrieDeceptionHandler()

def create_enhanced_cowrie_config():
    """Create Cowrie configuration with deception integration"""
    config = {
        "filesystem": {
            "fake_files": True,
            "dynamic_content": True
        },
        "deception": {
            "enabled": True,
            "adaptive": True,
            "breadcrumbs": True
        }
    }
    
    with open("cowrie_deception.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("[Config] Enhanced Cowrie configuration created")

if __name__ == "__main__":
    create_enhanced_cowrie_config()
    
    # Test the deception system
    print("\n=== Testing Deception System ===")
    
    test_commands = [
        ("ls", []),
        ("ls", ["desktop"]),
        ("cat", ["passwords.txt"]),
        ("find", ["/", "-name", "*password*"]),
        ("grep", ["admin", "users.txt"])
    ]
    
    for cmd, args in test_commands:
        print(f"\n$ {cmd} {' '.join(args)}")
        result = deception_handler.process_command(cmd, args)
        print(result)
    
    # Show deception metrics
    metrics = deception_engine.get_deception_metrics()
    print(f"\n=== Deception Metrics ===")
    for key, value in metrics.items():
        print(f"{key}: {value}")