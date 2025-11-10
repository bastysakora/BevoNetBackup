#!/usr/bin/env python3
"""
Simple Network Backup Tool - Starter Version
"""

import yaml
import logging
from pathlib import Path


class NetworkBackupTool:
    def __init__(self):
        self.setup_logging()
        self.load_configs()

    def setup_logging(self):
        """Setup basic logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def load_configs(self):
        """Load device configurations"""
        try:
            with open('config/devices.yaml', 'r') as f:
                devices_config = yaml.safe_load(f)
                self.devices = devices_config['devices']

            self.logger.info(f"Loaded {len(self.devices)} devices from config")

            # Print device list to verify
            for device in self.devices:
                print(f" Device: {device['name']} - {device['host']}")

        except Exception as e:
            self.logger.error(f"Failed to load configs: {e}")

    def test_connection(self, device):
        """Test connection to a device (simulated for now)"""
        self.logger.info(f" Testing connection to {device['name']}...")

        # Simulate connection test
        print(f"   Would connect to: {device['host']}")
        print(f"   Device type: {device['device_type']}")
        print(f"   Site: {device['site']}")
        print("    Connection test simulated successfully")

        return True


def main():
    print(" Starting Network Backup Tool...")

    # Create backup tool instance
    backup_tool = NetworkBackupTool()

    # Test connections to all devices
    print("\n Testing device connections:")
    for device in backup_tool.devices:
        backup_tool.test_connection(device)
        print()  # Empty line between devices

    print(" All tests completed! Ready to add real SSH connections.")


if __name__ == "__main__":
    main()