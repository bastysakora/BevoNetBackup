#!/usr/bin/env python3
"""
Mock Network Backup Tool - Fixed Version
Automatically creates config files and works regardless of working directory
"""

import yaml
import json
import logging
import random
import time
from datetime import datetime
from pathlib import Path


class MockNetworkBackupTool:
    def __init__(self, devices_file=None, settings_file=None):
        # Get the project root directory (where this script is located)
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent

        self.setup_logging()

        # Set default file paths if not provided
        if devices_file is None:
            devices_file = self.project_root / "config" / "devices.yaml"
        if settings_file is None:
            settings_file = self.project_root / "config" / "settings.yaml"

        self.load_configs(devices_file, settings_file)
        self.setup_backup_dir()
        self.setup_mock_configs()

    def setup_logging(self):
        """Setup logging"""
        log_file = self.project_root / "network_backup_mock.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_configs(self, devices_file, settings_file):
        """Load device configurations - create them if they don't exist"""
        try:
            # Convert string paths to Path objects if needed
            if isinstance(devices_file, str):
                devices_file = Path(devices_file)
            if isinstance(settings_file, str):
                settings_file = Path(settings_file)

            self.logger.info(f" Looking for config files...")
            self.logger.info(f"   Devices file: {devices_file}")
            self.logger.info(f"   Settings file: {settings_file}")

            # Create config directory if it doesn't exist
            config_dir = devices_file.parent
            config_dir.mkdir(exist_ok=True)

            # Create devices.yaml if it doesn't exist
            if not devices_file.exists():
                self.logger.info(" Creating sample devices.yaml file...")
                self.create_sample_devices_file(devices_file)

            # Create settings.yaml if it doesn't exist
            if not settings_file.exists():
                self.logger.info(" Creating sample settings.yaml file...")
                self.create_sample_settings_file(settings_file)

            # Now load the files
            with open(devices_file, 'r') as f:
                devices_config = yaml.safe_load(f)
                self.devices = devices_config['devices']

            with open(settings_file, 'r') as f:
                self.settings = yaml.safe_load(f)

            self.logger.info(f" Loaded {len(self.devices)} devices from config")

        except Exception as e:
            self.logger.error(f" Failed to load configs: {e}")
            raise

    def create_sample_devices_file(self, devices_file):
        """Create a sample devices.yaml file"""
        sample_devices = {
            'devices': [
                {
                    'name': "core-switch-01",
                    'device_type': "cisco_ios",
                    'host': "192.168.1.10",
                    'username': "admin",
                    'password': "admin123",
                    'secret': "enable123",
                    'site': "Mock Data Center"
                },
                {
                    'name': "distribution-switch-01",
                    'device_type': "cisco_ios",
                    'host': "192.168.1.11",
                    'username': "admin",
                    'password': "admin123",
                    'secret': "enable123",
                    'site': "Mock Distribution"
                },
                {
                    'name': "juniper-firewall-01",
                    'device_type': "juniper_junos",
                    'host': "192.168.1.12",
                    'username': "admin",
                    'password': "admin123",
                    'site': "Mock Perimeter"
                },
                {
                    'name': "arista-leaf-01",
                    'device_type': "arista_eos",
                    'host': "192.168.1.13",
                    'username': "admin",
                    'password': "admin123",
                    'site': "Mock Spine-Leaf"
                }
            ]
        }

        with open(devices_file, 'w') as f:
            yaml.dump(sample_devices, f, default_flow_style=False, indent=2)

        self.logger.info(f" Created sample devices file: {devices_file}")

    def create_sample_settings_file(self, settings_file):
        """Create a sample settings.yaml file"""
        sample_settings = {
            'backup': {
                'backup_dir': "./backups",
                'git_enabled': False,
                'git_auto_commit': False
            },
            'comparison': {
                'ignore_lines': [
                    "! Last configuration change",
                    "! NVRAM config last updated",
                    "!Time:"
                ]
            },
            'notification': {
                'email_enabled': False
            }
        }

        with open(settings_file, 'w') as f:
            yaml.dump(sample_settings, f, default_flow_style=False, indent=2)

        self.logger.info(f" Created sample settings file: {settings_file}")

    def setup_mock_configs(self):
        """Create realistic mock configurations for different device types"""
        self.mock_configs = {
            'cisco_ios': self.generate_cisco_config,
            'juniper_junos': self.generate_juniper_config,
            'arista_eos': self.generate_arista_config
        }

    def generate_cisco_config(self, device_name):
        """Generate realistic Cisco IOS configuration"""
        return f"""!
! Cisco IOS Configuration for {device_name}
! Generated: {datetime.now()}
!
version 15.2
service timestamps debug datetime msec
service timestamps log datetime msec
service password-encryption
!
hostname {device_name}
!
boot-start-marker
boot-end-marker
!
logging buffered 4096 debugging
!
no aaa new-model
!
ip cef
!
no ip domain lookup
ip domain name company.local
!
interface GigabitEthernet0/0
 description Management Interface
 ip address 192.168.1.{random.randint(10, 50)} 255.255.255.0
 negotiation auto
 no shutdown
!
interface GigabitEthernet0/1
 description Uplink to Core
 switchport mode trunk
 switchport trunk native vlan 999
 negotiation auto
 no shutdown
!
interface Vlan1
 ip address 10.1.1.{random.randint(1, 254)} 255.255.255.0
!
line con 0
 logging synchronous
line vty 0 4
 login local
 transport input ssh
!
ntp server 10.1.1.10
!
end
"""

    def generate_juniper_config(self, device_name):
        """Generate realistic Juniper JunOS configuration"""
        return f"""# Juniper JunOS Configuration for {device_name}
# Generated: {datetime.now()}

system {{
    host-name {device_name};
    root-authentication {{
        encrypted-password "$1$abc123"; ## SECRET-DATA
    }}
    services {{
        ssh;
        netconf {{
            ssh;
        }}
    }}
    syslog {{
        user * {{
            any emergency;
        }}
        file messages {{
            any notice;
            authorization info;
        }}
    }}
    ntp {{
        server 10.1.1.10;
    }}
}}

interfaces {{
    ge-0/0/0 {{
        unit 0 {{
            family inet {{
                address 192.168.1.{random.randint(10, 50)}/24;
            }}
        }}
    }}
    ge-0/0/1 {{
        unit 0 {{
            family ethernet-switching {{
                port-mode trunk;
                vlan {{
                    members [1-100];
                }}
            }}
        }}
    }}
}}

protocols {{
    lldp {{
        interface all;
    }}
}}

security {{
    zones {{
        security-zone trust {{
            interfaces {{
                ge-0/0/0.0;
            }}
        }}
    }}
}}
"""

    def generate_arista_config(self, device_name):
        """Generate realistic Arista EOS configuration"""
        return f"""!
! Arista EOS Configuration for {device_name}
! Generated: {datetime.now()}
!
hostname {device_name}
!
username admin privilege 15 secret admin123
!
interface Management1
   description Management Interface
   ip address 192.168.1.{random.randint(10, 50)}/24
   no shutdown
!
interface Ethernet1
   description Uplink to Core
   switchport mode trunk
   switchport trunk native vlan 999
   no shutdown
!
interface Ethernet2
   description Server Access
   switchport access vlan 10
   no shutdown
!
ip routing
!
vlan 10
   name Servers
!
vlan 20
   name Users
!
ntp server 10.1.1.10
!
management ssh
   client source interface Management1
   no shutdown
!
end
"""

    def setup_backup_dir(self):
        """Create backup directory"""
        backup_dir_path = self.project_root / self.settings['backup']['backup_dir']
        backup_dir_path.mkdir(exist_ok=True)
        self.backup_dir = backup_dir_path
        self.logger.info(f" Backup directory: {self.backup_dir}")

    def simulate_connection_delay(self):
        """Simulate real network connection delay"""
        delay = random.uniform(0.5, 2.0)
        time.sleep(delay)

    def connect_to_device(self, device):
        """Simulate SSH connection to device"""
        try:
            self.logger.info(f" Connecting to {device['name']} ({device['host']})...")
            self.simulate_connection_delay()

            # Simulate occasional connection failures (10% chance)
            if random.random() < 0.1:
                raise Exception("Simulated connection timeout")

            self.logger.info(f" Successfully connected to {device['name']}")
            return {"connected": True, "device": device}

        except Exception as e:
            self.logger.error(f" Connection failed for {device['name']}: {str(e)}")
            return None

    def get_device_config(self, connection, device_type):
        """Retrieve mock configuration from device"""
        try:
            self.simulate_connection_delay()  # Simulate config retrieval time

            device_name = connection["device"]["name"]
            config_generator = self.mock_configs.get(device_type, self.generate_cisco_config)
            config = config_generator(device_name)

            # Simulate occasional config retrieval failures (5% chance)
            if random.random() < 0.05:
                raise Exception("Simulated config retrieval error")

            return config

        except Exception as e:
            self.logger.error(f" Error retrieving config: {str(e)}")
            return None

    def backup_single_device(self, device):
        """Backup configuration for a single device"""
        self.logger.info(f" Starting backup for {device['name']}...")

        connection = self.connect_to_device(device)
        if not connection:
            return False

        try:
            # Get configuration
            config = self.get_device_config(connection, device['device_type'])
            if not config:
                return False

            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{device['name']}_{timestamp}.cfg"
            filepath = self.backup_dir / filename

            # Save configuration to file
            with open(filepath, 'w') as f:
                f.write(config)

            self.logger.info(f" Successfully backed up {device['name']} to {filename}")

            # Save config info to JSON
            config_info = {
                'device': device['name'],
                'filename': filename,
                'timestamp': datetime.now().isoformat(),
                'size': len(config),
                'type': 'mock_backup'
            }

            info_file = self.backup_dir / f"{device['name']}_info.json"
            with open(info_file, 'w') as f:
                json.dump(config_info, f, indent=2)

            return True

        except Exception as e:
            self.logger.error(f" Error during backup of {device['name']}: {str(e)}")
            return False

    def backup_all_devices(self):
        """Backup configurations for all devices"""
        results = {
            'success': [],
            'failed': [],
            'timestamp': datetime.now().isoformat(),
            'total_devices': len(self.devices),
            'type': 'mock_backup'
        }

        print(f"\n Starting MOCK backup of {len(self.devices)} devices...")
        print(" This is simulating real device behavior")

        for device in self.devices:
            if self.backup_single_device(device):
                results['success'].append({
                    'name': device['name'],
                    'host': device['host']
                })
            else:
                results['failed'].append({
                    'name': device['name'],
                    'host': device['host']
                })

        # Save overall results
        results_file = self.backup_dir / "backup_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

        # Print summary
        print(f"\n Mock Backup Summary:")
        print(f" Successful: {len(results['success'])}")
        print(f" Failed: {len(results['failed'])}")

        if results['failed']:
            print(f"Failed devices: {[d['name'] for d in results['failed']]}")

        print(f"\n Mock configs saved to: {self.backup_dir}")
        print(" Check the .cfg files to see realistic network configurations!")

        return results


def main():
    print(" Starting Mock Network Backup Tool")
    print("=" * 50)
    print(" SIMULATION MODE - No real devices needed!")
    print("   • Realistic config generation")
    print("   • Connection delay simulation")
    print("   • Occasional failure simulation")
    print("=" * 50)

    try:
        # Create mock backup tool instance
        backup_tool = MockNetworkBackupTool()

        # Backup all devices
        results = backup_tool.backup_all_devices()

        print(f"\n Mock backup process completed!")
        print(f" Check the 'backups' folder for realistic config files")
        print(f" Check 'network_backup_mock.log' for detailed logs")

    except Exception as e:
        print(f" Critical error: {str(e)}")
        logging.error(f"Critical error: {str(e)}")


if __name__ == "__main__":
    main()