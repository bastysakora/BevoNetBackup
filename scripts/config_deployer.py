#!/usr/bin/env python3
"""
Configuration Deployer - For deploying configs to network devices
Fixed version with proper device handling
"""

import yaml
import logging
from pathlib import Path


class ConfigDeployer:
    def __init__(self, devices_file=None):
        self.setup_logging()
        self.project_root = Path(__file__).parent.parent
        self.devices = {}  # Always a dictionary

        if devices_file:
            self.devices = self.load_devices(devices_file)

    def setup_logging(self):
        """Setup basic logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def load_devices(self, devices_file):
        """Load devices from YAML file - returns dictionary"""
        try:
            with open(devices_file, 'r') as f:
                config = yaml.safe_load(f)
                devices_list = config.get('devices', [])
                # Convert list of devices to dictionary for easier lookup
                return {device['name']: device for device in devices_list}
        except Exception as e:
            self.logger.error(f"Error loading devices: {e}")
            return {}

    def find_device(self, device_name):
        """Find device by name - returns device dict or None"""
        return self.devices.get(device_name)

    def deploy_config(self, device_name, config_file, dry_run=True):
        """Deploy configuration to device - returns dictionary result"""
        try:
            # Find device
            device = self.find_device(device_name)
            if not device:
                return {
                    'success': False,
                    'message': f"Device '{device_name}' not found in inventory",
                    'device': device_name
                }

            # Check if config file exists
            config_path = Path(config_file)
            if not config_path.exists():
                return {
                    'success': False,
                    'message': f"Config file '{config_file}' not found",
                    'device': device_name,
                    'config_file': config_file
                }

            # Read configuration file
            try:
                with open(config_path, 'r') as f:
                    config_content = f.read()
                    config_commands = [line.strip() for line in config_content.splitlines()
                                       if line.strip() and not line.startswith('!') and not line.startswith('#')]
            except Exception as e:
                return {
                    'success': False,
                    'message': f"Error reading config file: {str(e)}",
                    'device': device_name,
                    'config_file': config_file
                }

            if dry_run:
                # Dry-run simulation
                return {
                    'success': True,
                    'message': f"DRY-RUN: Would deploy {len(config_commands)} commands to {device_name}",
                    'device': device_name,
                    'config_file': config_file,
                    'commands_count': len(config_commands),
                    'commands_preview': config_commands[:5],  # First 5 commands
                    'dry_run': True
                }
            else:
                # Actual deployment simulation
                return self.simulate_deployment(device, config_commands, config_file)

        except Exception as e:
            return {
                'success': False,
                'message': f"Deployment error: {str(e)}",
                'device': device_name,
                'config_file': config_file
            }

    def simulate_deployment(self, device, config_commands, config_file):
        """Simulate actual configuration deployment"""
        try:
            self.logger.info(f"Deploying {len(config_commands)} commands to {device['name']} ({device['host']})")

            # Simulate deployment process
            successful_commands = []
            failed_commands = []

            for i, command in enumerate(config_commands, 1):
                # Simulate 90% success rate for commands
                import random
                if random.random() < 0.9:
                    successful_commands.append(command)
                    self.logger.debug(f"  ✅ Command {i}: {command}")
                else:
                    failed_commands.append(command)
                    self.logger.warning(f"  ❌ Command {i} failed: {command}")

            success_rate = len(successful_commands) / len(config_commands) if config_commands else 1.0

            if failed_commands:
                return {
                    'success': False,
                    'message': f"Deployment partially failed: {len(failed_commands)}/{len(config_commands)} commands failed",
                    'device': device['name'],
                    'config_file': config_file,
                    'commands_total': len(config_commands),
                    'commands_successful': len(successful_commands),
                    'commands_failed': len(failed_commands),
                    'success_rate': success_rate,
                    'failed_commands': failed_commands[:10]  # First 10 failed commands
                }
            else:
                return {
                    'success': True,
                    'message': f"Configuration successfully deployed to {device['name']}",
                    'device': device['name'],
                    'config_file': config_file,
                    'commands_total': len(config_commands),
                    'commands_successful': len(successful_commands),
                    'success_rate': success_rate,
                    'commands_sent': successful_commands[:10]  # First 10 commands
                }

        except Exception as e:
            return {
                'success': False,
                'message': f"Deployment simulation failed: {str(e)}",
                'device': device['name'],
                'config_file': config_file
            }

    def create_sample_config(self, device_name):
        """Create sample configuration for a device"""
        device = self.find_device(device_name)
        if not device:
            return f"! Device {device_name} not found"

        device_type = device.get('device_type', 'cisco_ios')

        if device_type == 'cisco_ios':
            return f"""!
! Sample configuration for {device_name}
!
hostname {device_name}
!
interface GigabitEthernet0/1
 description Management Interface
 no shutdown
!
line vty 0 4
 login local
 transport input ssh
!
end
"""
        elif device_type == 'juniper_junos':
            return f"""#
# Sample configuration for {device_name}
#
system {{
    host-name {device_name};
    root-authentication {{
        encrypted-password "$1$abc123"; ## SECRET-DATA
    }}
}}
interfaces {{
    ge-0/0/0 {{
        unit 0 {{
            family inet {{
                address 192.168.1.100/24;
            }}
        }}
    }}
}}
"""
        else:
            return f"! Sample configuration for {device_name}\n! Device type: {device_type}"

    def get_device_list(self):
        """Get list of device names (for compatibility with tests that expect a list)"""
        return list(self.devices.keys())


def main():
    """Main function for testing"""
    print("Configuration Deployer - Test Mode")

    # Example usage without devices file
    deployer = ConfigDeployer()

    # Test with empty devices
    print("Testing with empty devices...")
    result = deployer.deploy_config("test-device", "nonexistent.txt", dry_run=True)
    print(f"Deployment result: {result}")

    # Create a sample config for a fictional device
    sample_config = deployer.create_sample_config("test-device")
    print("\nSample configuration for fictional device:")
    print(sample_config)


if __name__ == "__main__":
    main()