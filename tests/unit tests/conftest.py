#!/usr/bin/env python3
"""
Pytest configuration for Network Backup Tool tests
"""

import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def sample_devices_config():
    """Sample devices configuration for testing"""
    return {
        'devices': [
            {
                'name': 'test-switch-01',
                'device_type': 'cisco_ios',
                'host': '192.168.1.10',
                'username': 'admin',
                'password': 'test123',
                'site': 'Test-Lab'
            },
            {
                'name': 'test-router-01',
                'device_type': 'juniper_junos',
                'host': '192.168.1.11',
                'username': 'admin',
                'password': 'test123',
                'site': 'Test-Lab'
            }
        ]
    }


@pytest.fixture
def sample_settings_config():
    """Sample settings configuration for testing"""
    return {
        'backup': {
            'backup_dir': './backups',
            'git_enabled': False,
            'git_auto_commit': False
        },
        'comparison': {
            'ignore_lines': [
                '! Last configuration change',
                '! NVRAM config last updated',
                '!Time:'
            ]
        }
    }