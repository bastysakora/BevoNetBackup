#!/usr/bin/env python3
"""
Daily Automation Script
Runs the complete backup, comparison, and reporting workflow
To be scheduled via cron (Linux/Mac) or Task Scheduler (Windows)
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import logging

# Add scripts directory to path to import modules
scripts_dir = Path(__file__).parent
project_root = scripts_dir.parent
sys.path.append(str(scripts_dir))

from mock_backup_tool import MockNetworkBackupTool
from diff_checker import ConfigDiffChecker


class DailyAutomation:
    def __init__(self):
        self.setup_logging()
        self.setup_directories()

    def setup_logging(self):
        """Setup comprehensive logging"""
        log_file = project_root / "daily_automation.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_directories(self):
        """Ensure all required directories exist"""
        directories = [
            project_root / "backups",
            project_root / "config_updates",
            project_root / "reports"
        ]

        for directory in directories:
            directory.mkdir(exist_ok=True)

        self.logger.info(" All directories setup complete")

    def run_backup(self):
        """Run the backup process"""
        self.logger.info(" Starting daily backup process...")

        try:
            backup_tool = MockNetworkBackupTool()
            results = backup_tool.backup_all_devices()

            self.logger.info(
                f" Backup completed: {len(results['success'])} successful, {len(results['failed'])} failed")
            return results

        except Exception as e:
            self.logger.error(f" Backup process failed: {e}")
            return None

    def run_comparison(self):
        """Run configuration comparison"""
        self.logger.info(" Starting configuration comparison...")

        try:
            diff_checker = ConfigDiffChecker()
            results = diff_checker.check_all_devices_changes()

            if results:
                # Generate HTML report
                report_path = diff_checker.generate_diff_report(results, "reports/daily_change_report.html")

                # Generate a JSON summary
                summary = {
                    'timestamp': datetime.now().isoformat(),
                    'devices_checked': len(results),
                    'devices_with_changes': len([r for r in results.values() if r['has_changes']]),
                    'devices_unchanged': len([r for r in results.values() if not r['has_changes']]),
                    'details': results
                }

                summary_file = project_root / "reports" / "change_summary.json"
                with open(summary_file, 'w') as f:
                    import json
                    json.dump(summary, f, indent=2)

                self.logger.info(f" Comparison completed: {summary['devices_with_changes']} devices with changes")
                return summary
            else:
                self.logger.warning(" No comparison results generated")
                return None

        except Exception as e:
            self.logger.error(f" Comparison process failed: {e}")
            return None

    def generate_daily_report(self, backup_results, comparison_results):
        """Generate a comprehensive daily report"""
        self.logger.info(" Generating daily report...")

        report_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Daily Network Automation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .summary {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .section {{ margin: 25px 0; padding: 20px; border: 1px solid #bdc3c7; border-radius: 5px; }}
        .success {{ color: #27ae60; }}
        .warning {{ color: #f39c12; }}
        .error {{ color: #e74c3c; }}
        .device-list {{ font-family: monospace; background: #f8f9fa; padding: 10px; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1> Daily Network Automation Report</h1>
        <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

        <div class="summary">
            <h2> Executive Summary</h2>
            <p><strong>Backup Status:</strong> <span class="{'success' if backup_results and len(backup_results.get('failed', [])) == 0 else 'warning'}">
                {len(backup_results.get('success', [])) if backup_results else 0} successful, {len(backup_results.get('failed', [])) if backup_results else 'Unknown'} failed
            </span></p>
            <p><strong>Configuration Changes:</strong> <span class="{'warning' if comparison_results and comparison_results['devices_with_changes'] > 0 else 'success'}">
                {comparison_results['devices_with_changes'] if comparison_results else 0} devices with changes
            </span></p>
        </div>
"""

        # Backup Results Section
        if backup_results:
            report_content += f"""
        <div class="section">
            <h2> Backup Results</h2>
            <p><strong>Total Devices:</strong> {backup_results['total_devices']}</p>
            <p><strong>Successful Backups:</strong> <span class="success">{len(backup_results['success'])}</span></p>
            <p><strong>Failed Backups:</strong> <span class="{'error' if backup_results['failed'] else 'success'}">{len(backup_results['failed'])}</span></p>

            <h3> Successful Devices:</h3>
            <div class="device-list">
"""
            for device in backup_results['success']:
                report_content += f"• {device['name']} ({device['host']})<br>"

            report_content += """
            </div>
"""

            if backup_results['failed']:
                report_content += """
            <h3> Failed Devices:</h3>
            <div class="device-list">
"""
                for device in backup_results['failed']:
                    report_content += f"• {device['name']} ({device['host']})<br>"
                report_content += """
            </div>
"""

        # Comparison Results Section
        if comparison_results:
            report_content += f"""
        </div>
        <div class="section">
            <h2> Configuration Change Analysis</h2>
            <p><strong>Devices Checked:</strong> {comparison_results['devices_checked']}</p>
            <p><strong>Devices with Changes:</strong> <span class="{'warning' if comparison_results['devices_with_changes'] > 0 else 'success'}">{comparison_results['devices_with_changes']}</span></p>
            <p><strong>Devices Unchanged:</strong> <span class="success">{comparison_results['devices_unchanged']}</span></p>

            <h3> Change Details:</h3>
"""
            for device_name, details in comparison_results['details'].items():
                status = " CHANGES" if details['has_changes'] else " No Changes"
                report_content += f'<p><strong>{device_name}:</strong> {status} ({details["change_count"]} changes)</p>'

        report_content += """
        </div>

        <div class="section">
            <h2> Generated Files</h2>
            <ul>
                <li><strong>Backup Files:</strong> Check the 'backups/' directory for device configurations</li>
                <li><strong>Detailed Change Report:</strong> <a href="reports/daily_change_report.html">reports/daily_change_report.html</a></li>
                <li><strong>Change Summary:</strong> <a href="reports/change_summary.json">reports/change_summary.json</a></li>
                <li><strong>Log Files:</strong> Check project root for various log files</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

        report_file = project_root / "reports" / "daily_summary_report.html"
        with open(report_file, 'w') as f:
            f.write(report_content)

        self.logger.info(f" Daily report generated: {report_file}")
        return report_file

    def run_daily_workflow(self):
        """Run the complete daily workflow"""
        start_time = datetime.now()
        self.logger.info(" Starting Daily Automation Workflow")
        self.logger.info("=" * 60)

        # Step 1: Run backups
        backup_results = self.run_backup()

        # Step 2: Run comparison (only if there are backups to compare)
        comparison_results = None
        if backup_results and len(backup_results.get('success', [])) > 0:
            comparison_results = self.run_comparison()
        else:
            self.logger.warning(" Skipping comparison - no successful backups")

        # Step 3: Generate comprehensive report
        report_file = self.generate_daily_report(backup_results, comparison_results)

        # Calculate duration
        duration = datetime.now() - start_time

        # Final summary
        self.logger.info("=" * 60)
        self.logger.info(" Daily Automation Workflow Completed!")
        self.logger.info(f"  Total Duration: {duration.total_seconds():.2f} seconds")
        self.logger.info(f" Main Report: {report_file}")

        print(f"\n{'=' * 60}")
        print(" DAILY AUTOMATION COMPLETE!")
        print(f"{'=' * 60}")
        if backup_results:
            print(f" Backups: {len(backup_results['success'])} {len(backup_results['failed'])}")
        if comparison_results:
            print(f" Changes: {comparison_results['devices_with_changes']} devices with modifications")
        print(f" Reports: {report_file}")
        print(f"⏱  Duration: {duration.total_seconds():.2f} seconds")
        print(f"{'=' * 60}")


def main():
    """Main execution function"""
    print(" BevoNetBackup - Daily Automation")
    print("==========================================")

    try:
        automation = DailyAutomation()
        automation.run_daily_workflow()

    except Exception as e:
        print(f" Daily automation failed: {str(e)}")
        logging.error(f"Daily automation failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()