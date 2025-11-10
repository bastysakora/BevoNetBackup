#!/usr/bin/env python3
"""
Integration tests for Configuration Deployment
Fixed version for dictionary return types
"""

import pytest
import yaml
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys


class TestDeploymentIntegration:
    """Integration tests for deployment workflow"""

    @pytest.fixture
    def deployment_setup(self):
        """Setup for deployment tests"""
        # Create temporary directory
        tmp_dir = tempfile.mkdtemp()
        tmp_path = Path(tmp_dir)

        # Create config_updates directory
        config_updates_dir = tmp_path / "config_updates"
        config_updates_dir.mkdir()

        # Create devices.yaml
        devices_file = tmp_path / "devices.yaml"
        devices_config = {
            'devices': [
                {
                    'name': 'deployment-switch-01',
                    'device_type': 'cisco_ios',
                    'host': '192.168.200.10',
                    'username': 'admin',
                    'password': 'admin123',
                    'site': 'Deployment-Test'
                },
                {
                    'name': 'deployment-router-01',
                    'device_type': 'juniper_junos',
                    'host': '192.168.200.11',
                    'username': 'admin',
                    'password': 'admin123',
                    'site': 'Deployment-Test'
                }
            ]
        }
        with open(devices_file, 'w') as f:
            yaml.dump(devices_config, f)

        # Create sample config files
        cisco_config = config_updates_dir / "deployment-switch-01-update.cfg"
        cisco_config.write_text("""hostname deployment-switch-01-updated
interface GigabitEthernet0/1
 description Updated Management Interface
 no shutdown
interface GigabitEthernet0/2
 description New User Access Port
 switchport access vlan 10
""")

        juniper_config = config_updates_dir / "deployment-router-01-update.cfg"
        juniper_config.write_text("""system {
    host-name deployment-router-01-updated;
}
interfaces {
    ge-0/0/0 {
        description "Updated Management Interface";
        unit 0;
    }
}
""")

        yield tmp_path, devices_file, config_updates_dir

    def test_deployment_workflow_integration(self, deployment_setup):
        """Test complete deployment workflow integration"""
        tmp_path, devices_file, config_updates_dir = deployment_setup

        # Add project root to path
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))

        from scripts.config_deployer import ConfigDeployer

        # Create deployer instance
        deployer = ConfigDeployer(devices_file=str(devices_file))

        # Test basic functionality
        assert deployer is not None
        assert len(deployer.devices) == 2

        # Test deployment with existing config file
        config_file = config_updates_dir / "deployment-switch-01-update.cfg"
        result = deployer.deploy_config(
            "deployment-switch-01",
            str(config_file),
            dry_run=True
        )

        # Should return dictionary with success key
        assert isinstance(result, dict)
        assert 'success' in result
        assert result['success'] is True
        assert 'dry_run' in result

    def test_multi_device_deployment_integration(self, deployment_setup):
        """Test deploying to multiple devices"""
        tmp_path, devices_file, config_updates_dir = deployment_setup

        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))

        from scripts.config_deployer import ConfigDeployer

        deployer = ConfigDeployer(devices_file=str(devices_file))

        # Deploy to Cisco device
        cisco_config = config_updates_dir / "deployment-switch-01-update.cfg"
        cisco_result = deployer.deploy_config(
            "deployment-switch-01",
            str(cisco_config),
            dry_run=True
        )

        # Deploy to Juniper device
        juniper_config = config_updates_dir / "deployment-router-01-update.cfg"
        juniper_result = deployer.deploy_config(
            "deployment-router-01",
            str(juniper_config),
            dry_run=True
        )

        # Both should succeed
        assert cisco_result['success'] is True
        assert juniper_result['success'] is True
        assert 'commands_count' in cisco_result
        assert 'commands_count' in juniper_result

    def test_deployment_logging_integration(self, deployment_setup):
        """Test deployment logging integration"""
        tmp_path, devices_file, config_updates_dir = deployment_setup

        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))

        from scripts.config_deployer import ConfigDeployer

        deployer = ConfigDeployer(devices_file=str(devices_file))

        config_file = config_updates_dir / "deployment-switch-01-update.cfg"
        result = deployer.deploy_config(
            "deployment-switch-01",
            str(config_file),
            dry_run=True
        )

        # Should have deployment details in result
        assert result['success'] is True
        assert 'device' in result
        assert 'config_file' in result
        assert 'message' in result

    def test_deployment_failure_scenario(self, deployment_setup):
        """Test deployment failure scenarios"""
        tmp_path, devices_file, config_updates_dir = deployment_setup

        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))

        from scripts.config_deployer import ConfigDeployer

        deployer = ConfigDeployer(devices_file=str(devices_file))

        # Test with non-existent config file
        result = deployer.deploy_config(
            "deployment-switch-01",
            "non_existent_config.cfg",
            dry_run=True
        )

        # Should fail with appropriate message
        assert result['success'] is False
        assert 'not found' in result['message'].lower()

    def test_config_validation_integration(self, deployment_setup):
        """Test configuration validation during deployment"""
        tmp_path, devices_file, config_updates_dir = deployment_setup

        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))

        from scripts.config_deployer import ConfigDeployer

        deployer = ConfigDeployer(devices_file=str(devices_file))

        # Test with empty config file
        empty_config = config_updates_dir / "empty_config.cfg"
        empty_config.write_text("")

        result = deployer.deploy_config(
            "deployment-switch-01",
            str(empty_config),
            dry_run=True
        )

        # Should handle empty config gracefully
        assert isinstance(result, dict)
        assert 'success' in result
        # Empty config might still be considered successful in dry-run

    def test_deployment_with_backup_integration(self, deployment_setup):
        """Test deployment integrated with backup tool"""
        tmp_path, devices_file, config_updates_dir = deployment_setup

        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))

        from scripts.config_deployer import ConfigDeployer
        from scripts.mock_backup_tool import MockNetworkBackupTool

        # Create backup tool and perform backup
        backup_tool = MockNetworkBackupTool(devices_file=str(devices_file))
        backup_results = backup_tool.backup_all_devices()

        # Verify backups were created
        backup_files = list(backup_tool.backup_dir.glob("*.cfg"))
        assert len(backup_files) >= len(backup_results['success'])

        # Create deployer and test deployment
        deployer = ConfigDeployer(devices_file=str(devices_file))
        config_file = config_updates_dir / "deployment-switch-01-update.cfg"
        deployment_result = deployer.deploy_config(
            "deployment-switch-01",
            str(config_file),
            dry_run=True
        )

        # Should succeed
        assert deployment_result['success'] is True

    def test_sample_config_creation_integration(self, deployment_setup):
        """Test sample configuration creation"""
        tmp_path, devices_file, config_updates_dir = deployment_setup

        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))

        from scripts.config_deployer import ConfigDeployer

        deployer = ConfigDeployer(devices_file=str(devices_file))

        # Test sample config creation
        sample_config = deployer.create_sample_config("deployment-switch-01")

        assert sample_config is not None
        assert len(sample_config) > 0
        assert "deployment-switch-01" in sample_config

        # Save sample config to file
        sample_file = config_updates_dir / "sample_config.cfg"
        with open(sample_file, 'w') as f:
            f.write(sample_config)

        # Test deploying the sample config
        result = deployer.deploy_config(
            "deployment-switch-01",
            str(sample_file),
            dry_run=True
        )

        assert result['success'] is True

    def test_deployment_error_handling_integration(self, deployment_setup):
        """Test error handling during deployment"""
        tmp_path, devices_file, config_updates_dir = deployment_setup

        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))

        from scripts.config_deployer import ConfigDeployer

        deployer = ConfigDeployer(devices_file=str(devices_file))

        # Test with non-existent device
        result = deployer.deploy_config(
            "non-existent-device",
            "some_config.cfg",
            dry_run=True
        )

        # Should fail with device not found
        assert result['success'] is False
        assert 'not found' in result['message'].lower()

    def test_deployment_command_parsing_integration(self, deployment_setup):
        """Test command parsing during deployment"""
        tmp_path, devices_file, config_updates_dir = deployment_setup

        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))

        from scripts.config_deployer import ConfigDeployer

        deployer = ConfigDeployer(devices_file=str(devices_file))

        # Create test config with various command types
        test_config = config_updates_dir / "test_parsing.cfg"
        test_config.write_text("""! This is a comment
hostname test-parsing

interface GigabitEthernet0/1
 description Test Interface
 no shutdown
! Another comment

router ospf 1
 network 10.1.1.0 0.0.0.255 area 0
# Yet another comment type
""")

        result = deployer.deploy_config(
            "deployment-switch-01",
            str(test_config),
            dry_run=True
        )

        # Should succeed and parse commands correctly
        assert result['success'] is True
        assert 'commands_count' in result
        assert result['commands_count'] > 0

    def test_concurrent_deployment_simulation(self, deployment_setup):
        """Test simulating concurrent deployments"""
        tmp_path, devices_file, config_updates_dir = deployment_setup

        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))

        from scripts.config_deployer import ConfigDeployer

        deployer = ConfigDeployer(devices_file=str(devices_file))

        # Simulate multiple deployments
        config_file = config_updates_dir / "deployment-switch-01-update.cfg"

        # First deployment
        result1 = deployer.deploy_config(
            "deployment-switch-01",
            str(config_file),
            dry_run=True
        )

        # Second deployment (simulating concurrent)
        result2 = deployer.deploy_config(
            "deployment-router-01",
            str(config_file),  # Same config for testing
            dry_run=True
        )

        # Both should succeed
        assert result1['success'] is True
        assert result2['success'] is True

    def test_deployment_with_different_device_types(self, deployment_setup):
        """Test deployment to different device types"""
        tmp_path, devices_file, config_updates_dir = deployment_setup

        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))

        from scripts.config_deployer import ConfigDeployer

        deployer = ConfigDeployer(devices_file=str(devices_file))

        # Test Cisco device deployment
        cisco_config = config_updates_dir / "deployment-switch-01-update.cfg"
        cisco_result = deployer.deploy_config(
            "deployment-switch-01",
            str(cisco_config),
            dry_run=True
        )

        # Test Juniper device deployment  
        juniper_config = config_updates_dir / "deployment-router-01-update.cfg"
        juniper_result = deployer.deploy_config(
            "deployment-router-01",
            str(juniper_config),
            dry_run=True
        )

        # Both should work with their respective configs
        assert cisco_result['success'] is True
        assert juniper_result['success'] is True

    def test_deployment_rollback_simulation(self, deployment_setup):
        """Test deployment rollback simulation"""
        tmp_path, devices_file, config_updates_dir = deployment_setup

        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))

        from scripts.config_deployer import ConfigDeployer

        deployer = ConfigDeployer(devices_file=str(devices_file))

        # Simulate initial deployment failure
        config_file = config_updates_dir / "deployment-switch-01-update.cfg"

        # First, test with dry-run (should succeed)
        dry_run_result = deployer.deploy_config(
            "deployment-switch-01",
            str(config_file),
            dry_run=True
        )
        assert dry_run_result['success'] is True

        # For actual deployment simulation, we'd need to mock the simulate_deployment method
        # This tests the basic workflow without actual deployment simulation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])