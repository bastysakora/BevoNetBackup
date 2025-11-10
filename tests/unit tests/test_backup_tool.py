#!/usr/bin/env python3
"""
Unit tests for Mock Network Backup Tool
Compatible with the current working mock_backup_tool.py
"""

import pytest
import yaml
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os


class TestMockNetworkBackupTool:
    """Test cases for MockNetworkBackupTool"""

    def test_initialization(self):
        """Test that the tool initializes correctly with default paths"""
        from scripts.mock_backup_tool import MockNetworkBackupTool

        # This should work without any parameters
        tool = MockNetworkBackupTool()

        assert tool is not None
        assert hasattr(tool, 'devices')
        assert hasattr(tool, 'settings')
        assert hasattr(tool, 'backup_dir')
        assert len(tool.devices) > 0

    def test_config_creation(self, temp_dir):
        """Test that config files are created when they don't exist"""
        from scripts.mock_backup_tool import MockNetworkBackupTool

        devices_file = temp_dir / "devices.yaml"
        settings_file = temp_dir / "settings.yaml"

        # Files should not exist initially
        assert not devices_file.exists()
        assert not settings_file.exists()

        # Create tool instance - should create the files
        tool = MockNetworkBackupTool(
            devices_file=devices_file,
            settings_file=settings_file
        )

        # Files should now exist
        assert devices_file.exists()
        assert settings_file.exists()

        # Verify devices were loaded
        assert len(tool.devices) > 0

    def test_sample_devices_creation(self, temp_dir):
        """Test sample devices file creation"""
        from scripts.mock_backup_tool import MockNetworkBackupTool

        devices_file = temp_dir / "test_devices.yaml"

        # Create tool instance which should create the file
        tool = MockNetworkBackupTool(devices_file=devices_file)

        # Verify file was created and has correct content
        with open(devices_file, 'r') as f:
            config = yaml.safe_load(f)

        assert 'devices' in config
        assert len(config['devices']) > 0

        # Verify device structure
        device = config['devices'][0]
        assert 'name' in device
        assert 'device_type' in device
        assert 'host' in device
        assert 'username' in device

    def test_backup_directory_creation(self, temp_dir):
        """Test that backup directory is created"""
        from scripts.mock_backup_tool import MockNetworkBackupTool

        # Create custom settings with temp backup dir
        settings_file = temp_dir / "settings.yaml"
        backup_dir = temp_dir / "test_backups"

        custom_settings = {
            'backup': {
                'backup_dir': str(backup_dir),
                'git_enabled': False,
                'git_auto_commit': False
            }
        }

        with open(settings_file, 'w') as f:
            yaml.dump(custom_settings, f)

        # Create tool instance
        tool = MockNetworkBackupTool(settings_file=settings_file)

        # Backup directory should be created
        assert tool.backup_dir.exists()
        assert tool.backup_dir == backup_dir

    def test_cisco_config_generation(self):
        """Test Cisco IOS configuration generation"""
        from scripts.mock_backup_tool import MockNetworkBackupTool

        tool = MockNetworkBackupTool()

        test_device_name = "test-cisco-switch"
        config = tool.generate_cisco_config(test_device_name)

        # Verify key elements in Cisco config
        assert "Cisco IOS Configuration" in config
        assert test_device_name in config
        assert "hostname" in config
        assert "interface" in config
        assert "GigabitEthernet" in config

    def test_juniper_config_generation(self):
        """Test Juniper JunOS configuration generation"""
        from scripts.mock_backup_tool import MockNetworkBackupTool

        tool = MockNetworkBackupTool()

        test_device_name = "test-juniper-fw"
        config = tool.generate_juniper_config(test_device_name)

        # Verify key elements in Juniper config
        assert "Juniper JunOS Configuration" in config
        assert test_device_name in config
        assert "system" in config
        assert "host-name" in config
        assert "interfaces" in config

    def test_arista_config_generation(self):
        """Test Arista EOS configuration generation"""
        from scripts.mock_backup_tool import MockNetworkBackupTool

        tool = MockNetworkBackupTool()

        test_device_name = "test-arista-leaf"
        config = tool.generate_arista_config(test_device_name)

        # Verify key elements in Arista config
        assert "Arista EOS Configuration" in config
        assert test_device_name in config
        assert "hostname" in config
        assert "interface" in config
        assert "Management1" in config

    def test_successful_device_backup(self, temp_dir):
        """Test successful backup of a single device"""
        from scripts.mock_backup_tool import MockNetworkBackupTool

        # Create test device
        test_device = {
            'name': 'test-backup-device',
            'device_type': 'cisco_ios',
            'host': '192.168.1.100',
            'username': 'admin',
            'password': 'test123'
        }

        # Create devices file with test device
        devices_file = temp_dir / "devices.yaml"
        with open(devices_file, 'w') as f:
            yaml.dump({'devices': [test_device]}, f)

        # Create settings with temp backup dir
        settings_file = temp_dir / "settings.yaml"
        backup_dir = temp_dir / "backups"

        with open(settings_file, 'w') as f:
            yaml.dump({
                'backup': {
                    'backup_dir': str(backup_dir),
                    'git_enabled': False,
                    'git_auto_commit': False
                }
            }, f)

        # Create tool instance
        tool = MockNetworkBackupTool(
            devices_file=devices_file,
            settings_file=settings_file
        )

        # Mock the connection to always succeed
        with patch.object(tool, 'connect_to_device') as mock_connect, \
                patch.object(tool, 'get_device_config') as mock_config:
            mock_connect.return_value = {"connected": True, "device": test_device}
            mock_config.return_value = "! Test configuration content"

            # Perform backup
            result = tool.backup_single_device(test_device)

            assert result is True
            assert mock_connect.called
            assert mock_config.called

    def test_backup_all_devices(self, temp_dir):
        """Test backing up all devices"""
        from scripts.mock_backup_tool import MockNetworkBackupTool

        # Create test devices
        test_devices = [
            {
                'name': 'device1',
                'device_type': 'cisco_ios',
                'host': '192.168.1.1',
                'username': 'admin',
                'password': 'test123'
            },
            {
                'name': 'device2',
                'device_type': 'juniper_junos',
                'host': '192.168.1.2',
                'username': 'admin',
                'password': 'test123'
            }
        ]

        # Create config files
        devices_file = temp_dir / "devices.yaml"
        settings_file = temp_dir / "settings.yaml"
        backup_dir = temp_dir / "backups"

        with open(devices_file, 'w') as f:
            yaml.dump({'devices': test_devices}, f)

        with open(settings_file, 'w') as f:
            yaml.dump({
                'backup': {
                    'backup_dir': str(backup_dir),
                    'git_enabled': False,
                    'git_auto_commit': False
                }
            }, f)

        # Create tool instance
        tool = MockNetworkBackupTool(
            devices_file=devices_file,
            settings_file=settings_file
        )

        # Mock the backup process
        with patch.object(tool, 'backup_single_device') as mock_backup:
            mock_backup.return_value = True

            results = tool.backup_all_devices()

            # Should be called for each device
            assert mock_backup.call_count == len(test_devices)

            # Check results structure
            assert 'success' in results
            assert 'failed' in results
            assert 'total_devices' in results
            assert results['total_devices'] == len(test_devices)

    def test_config_file_parsing(self, temp_dir):
        """Test that config files are parsed correctly"""
        from scripts.mock_backup_tool import MockNetworkBackupTool

        # Create specific test configs
        test_devices = {
            'devices': [
                {
                    'name': 'parsing-test-1',
                    'device_type': 'cisco_ios',
                    'host': '10.1.1.1',
                    'username': 'testuser',
                    'password': 'testpass',
                    'site': 'Test Site'
                }
            ]
        }

        # Use a backup path within the temp directory
        backup_dir = temp_dir / "custom_backup_path"
        test_settings = {
            'backup': {
                'backup_dir': str(backup_dir),  # Use temp directory path
                'git_enabled': True,
                'git_auto_commit': True
            }
        }

        devices_file = temp_dir / "devices.yaml"
        settings_file = temp_dir / "settings.yaml"

        with open(devices_file, 'w') as f:
            yaml.dump(test_devices, f)

        with open(settings_file, 'w') as f:
            yaml.dump(test_settings, f)

        # Create tool instance
        tool = MockNetworkBackupTool(
            devices_file=devices_file,
            settings_file=settings_file
        )

        # Verify parsing
        assert len(tool.devices) == 1
        assert tool.devices[0]['name'] == 'parsing-test-1'
        assert tool.settings['backup']['git_enabled'] is True
        # Also verify the backup directory was set correctly
        assert tool.backup_dir == backup_dir

    def test_mock_configs_setup(self):
        """Test that mock config generators are properly set up"""
        from scripts.mock_backup_tool import MockNetworkBackupTool

        tool = MockNetworkBackupTool()

        # Verify mock configs dictionary is set up
        assert hasattr(tool, 'mock_configs')
        assert 'cisco_ios' in tool.mock_configs
        assert 'juniper_junos' in tool.mock_configs
        assert 'arista_eos' in tool.mock_configs

        # Verify they are callable functions
        assert callable(tool.mock_configs['cisco_ios'])
        assert callable(tool.mock_configs['juniper_junos'])
        assert callable(tool.mock_configs['arista_eos'])


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


def test_main_function():
    """Test that main function can be called without errors"""
    from scripts.mock_backup_tool import main

    # This should run without raising exceptions
    # We'll mock the actual backup to avoid file operations
    with patch('scripts.mock_backup_tool.MockNetworkBackupTool') as MockTool:
        mock_instance = MagicMock()
        mock_instance.backup_all_devices.return_value = {
            'success': [], 'failed': [], 'total_devices': 0
        }
        MockTool.return_value = mock_instance

        # Call main - should not raise exceptions
        main()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])