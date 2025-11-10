#!/usr/bin/env python3
"""
Configuration Diff Checker - For comparing network device configurations
Working version with proper return values
"""

import yaml
import logging
from pathlib import Path
import re
from datetime import datetime


class ConfigDiffChecker:
    def __init__(self, settings_file=None, backup_dir="./backups"):
        self.setup_logging()
        self.ignore_patterns = self.load_ignore_patterns(settings_file)
        self.backup_dir = Path(backup_dir)

    def setup_logging(self):
        """Setup basic logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def load_ignore_patterns(self, settings_file):
        """Load ignore patterns from settings file"""
        default_patterns = [
            '! Last configuration change',
            '! NVRAM config last updated',
            '!Time:',
            '!',
            '#'
        ]

        if settings_file and Path(settings_file).exists():
            try:
                with open(settings_file, 'r') as f:
                    settings = yaml.safe_load(f)
                    return settings.get('comparison', {}).get('ignore_lines', default_patterns)
            except Exception as e:
                self.logger.error(f"Error loading settings: {e}")

        return default_patterns

    def filter_ignored_lines(self, config_content):
        """Filter out lines that match ignore patterns"""
        if not config_content:
            return ""

        lines = config_content.splitlines()
        filtered_lines = []

        for line in lines:
            # Check if line matches any ignore pattern
            ignore_line = False
            for pattern in self.ignore_patterns:
                if line.strip().startswith(pattern):
                    ignore_line = True
                    break

            if not ignore_line:
                filtered_lines.append(line)

        return '\n'.join(filtered_lines)

    def compare_configs(self, config1_path, config2_path, device_name="unknown"):
        """Compare two configuration files and return detailed results"""
        try:
            # Read both config files
            config1_content = Path(config1_path).read_text()
            config2_content = Path(config2_path).read_text()

            # Filter ignored lines
            filtered1 = self.filter_ignored_lines(config1_content)
            filtered2 = self.filter_ignored_lines(config2_content)

            # Split into lines for comparison
            lines1 = filtered1.splitlines()
            lines2 = filtered2.splitlines()

            # Simple line-by-line comparison
            differences = []
            max_lines = max(len(lines1), len(lines2))

            for i in range(max_lines):
                line1 = lines1[i] if i < len(lines1) else ""
                line2 = lines2[i] if i < len(lines2) else ""

                if line1 != line2:
                    differences.append({
                        'line_number': i + 1,
                        'old_value': line1,
                        'new_value': line2
                    })

            # Determine if identical
            identical = len(differences) == 0

            # Create summary
            if identical:
                summary = "Configurations are identical"
            else:
                summary = f"Found {len(differences)} differences"

            return {
                'identical': identical,
                'differences_count': len(differences),
                'summary': summary,
                'differences': differences,
                'device': device_name,
                'config1_file': Path(config1_path).name,
                'config2_file': Path(config2_path).name,
                'comparison_date': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error comparing configs: {e}")
            return {
                'identical': False,
                'differences_count': 0,
                'summary': f"Comparison error: {str(e)}",
                'differences': [],
                'device': device_name,
                'error': str(e)
            }

    def get_all_backups_for_device(self, device_name):
        """Get all backup files for a specific device, sorted by timestamp (newest first)"""
        try:
            if not self.backup_dir.exists():
                return []

            # Find all backup files for the device
            backup_files = list(self.backup_dir.glob(f"{device_name}_*.cfg"))

            # Sort by filename (which contains timestamp) newest first
            backup_files.sort(key=lambda x: x.name, reverse=True)

            return backup_files

        except Exception as e:
            self.logger.error(f"Error getting backups for {device_name}: {e}")
            return []

    def compare_latest_two_backups(self, device_name):
        """Compare the two most recent backups for a device"""
        try:
            backup_files = self.get_all_backups_for_device(device_name)

            if len(backup_files) < 2:
                self.logger.info(
                    f"Only {len(backup_files)} backup(s) found for {device_name} - need at least 2 for comparison")
                return {
                    'error': f"Insufficient backups: {len(backup_files)} found, need at least 2",
                    'device': device_name,
                    'backups_available': len(backup_files)
                }

            latest_backup = backup_files[0]
            previous_backup = backup_files[1]

            self.logger.info(f"Comparing {previous_backup.name} vs {latest_backup.name}")

            # Compare the two backups
            comparison_result = self.compare_configs(
                str(previous_backup),
                str(latest_backup),
                device_name
            )

            # Add backup info to result
            comparison_result.update({
                'backups_compared': {
                    'previous': previous_backup.name,
                    'latest': latest_backup.name
                }
            })

            return comparison_result

        except Exception as e:
            self.logger.error(f"Error comparing backups for {device_name}: {e}")
            return {
                'error': str(e),
                'device': device_name
            }

    def generate_report(self, comparison_result):
        """Generate a human-readable diff report"""
        if not comparison_result:
            return "No comparison results available."

        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("CONFIGURATION COMPARISON REPORT")
        report_lines.append("=" * 60)
        report_lines.append(f"Device: {comparison_result.get('device', 'Unknown')}")
        report_lines.append(f"Date: {comparison_result.get('comparison_date', 'Unknown')}")
        report_lines.append(f"Summary: {comparison_result.get('summary', 'No summary')}")
        report_lines.append("")

        # Add backup file info if available
        if 'backups_compared' in comparison_result:
            backups = comparison_result['backups_compared']
            report_lines.append("Backups Compared:")
            report_lines.append(f"  Previous: {backups.get('previous', 'Unknown')}")
            report_lines.append(f"  Latest: {backups.get('latest', 'Unknown')}")
            report_lines.append("")

        if comparison_result.get('identical', False):
            report_lines.append("✅ Configurations are identical - no changes detected")
        else:
            differences_count = comparison_result.get('differences_count', 0)
            report_lines.append(f"🔍 Found {differences_count} differences:")
            report_lines.append("")

            for diff in comparison_result.get('differences', []):
                report_lines.append(f"Line {diff['line_number']}:")
                if diff['old_value']:
                    report_lines.append(f"  - {diff['old_value']}")
                if diff['new_value']:
                    report_lines.append(f"  + {diff['new_value']}")
                report_lines.append("")

        if 'error' in comparison_result:
            report_lines.append(f"❌ Error: {comparison_result['error']}")

        report_lines.append("=" * 60)

        return '\n'.join(report_lines)


def main():
    """Main function for testing"""
    print("Configuration Diff Checker - Test Mode")

    # Example usage
    checker = ConfigDiffChecker()

    # Test filtering
    test_config = """!
! Last configuration change
hostname test-switch
interface Gi0/1
 no shutdown
!
end"""

    filtered = checker.filter_ignored_lines(test_config)
    print("Filtered configuration:")
    print(filtered)

    # Test comparison with sample files
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        config1 = Path(tmp_dir) / "config1.cfg"
        config2 = Path(tmp_dir) / "config2.cfg"

        config1.write_text("hostname device1\ninterface Gi0/1\n shutdown")
        config2.write_text("hostname device1\ninterface Gi0/1\n no shutdown\ninterface Gi0/2")

        result = checker.compare_configs(str(config1), str(config2), "test-device")
        print("\nComparison result:")
        print(f"Identical: {result['identical']}")
        print(f"Differences: {result['differences_count']}")
        print(f"Summary: {result['summary']}")


if __name__ == "__main__":
    main()