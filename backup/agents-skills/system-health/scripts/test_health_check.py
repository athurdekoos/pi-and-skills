"""Tests for system health checker."""
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, mock_open

sys.path.insert(0, os.path.dirname(__file__))
from health_check import (
    SystemHealthChecker, Alert, Severity,
    to_report, to_json, filter_cooled_down, COOLDOWN_FILE,
)


class TestRAMCheck(unittest.TestCase):
    def test_ram_critical_below_500mb(self):
        meminfo = "MemTotal: 7500000 kB\nMemAvailable: 400000 kB\nSwapTotal: 2700000 kB\nSwapFree: 2700000 kB\n"
        checker = SystemHealthChecker()
        with patch("builtins.open", mock_open(read_data=meminfo)):
            checker._check_ram()
        crits = [a for a in checker.alerts if a.check_id == "RAM_CRITICAL"]
        self.assertEqual(len(crits), 1)
        self.assertEqual(crits[0].severity, Severity.EMERGENCY)

    def test_ram_elevated_below_1500mb(self):
        meminfo = "MemTotal: 7500000 kB\nMemAvailable: 1200000 kB\nSwapTotal: 2700000 kB\nSwapFree: 2700000 kB\n"
        checker = SystemHealthChecker()
        with patch("builtins.open", mock_open(read_data=meminfo)):
            checker._check_ram()
        warns = [a for a in checker.alerts if a.check_id == "RAM_ELEVATED"]
        self.assertEqual(len(warns), 1)
        self.assertEqual(warns[0].severity, Severity.WARNING)

    def test_ram_healthy_no_alert(self):
        meminfo = "MemTotal: 7500000 kB\nMemAvailable: 5000000 kB\nSwapTotal: 2700000 kB\nSwapFree: 2700000 kB\n"
        checker = SystemHealthChecker()
        with patch("builtins.open", mock_open(read_data=meminfo)):
            checker._check_ram()
        self.assertEqual(len(checker.alerts), 0)


class TestDiskCheck(unittest.TestCase):
    def test_disk_critical(self):
        checker = SystemHealthChecker()
        fake_stat = os.statvfs_result((4096, 4096, 1000000, 50000, 50000, 100000, 90000, 90000, 0, 255))
        with patch("os.statvfs", return_value=fake_stat):
            checker._check_disk()
        crits = [a for a in checker.alerts if a.check_id == "DISK_CRITICAL"]
        self.assertEqual(len(crits), 1)

    def test_disk_healthy(self):
        checker = SystemHealthChecker()
        fake_stat = os.statvfs_result((4096, 4096, 1000000, 700000, 700000, 100000, 90000, 90000, 0, 255))
        with patch("os.statvfs", return_value=fake_stat):
            checker._check_disk()
        disk_alerts = [a for a in checker.alerts if "DISK" in a.check_id]
        self.assertEqual(len(disk_alerts), 0)


class TestSwapCheck(unittest.TestCase):
    def test_swap_heavy(self):
        meminfo = "MemTotal: 7500000 kB\nMemAvailable: 5000000 kB\nSwapTotal: 2700000 kB\nSwapFree: 1000000 kB\n"
        checker = SystemHealthChecker()
        with patch("builtins.open", mock_open(read_data=meminfo)):
            checker._check_swap()
        swaps = [a for a in checker.alerts if a.check_id == "SWAP_HEAVY"]
        self.assertEqual(len(swaps), 1)
        self.assertEqual(swaps[0].severity, Severity.EMERGENCY)


class TestLoadCheck(unittest.TestCase):
    def test_high_load(self):
        checker = SystemHealthChecker()
        with patch("os.getloadavg", return_value=(6.0, 5.5, 4.0)):
            checker._check_load()
        loads = [a for a in checker.alerts if a.check_id == "LOAD_HIGH"]
        self.assertEqual(len(loads), 1)

    def test_normal_load(self):
        checker = SystemHealthChecker()
        with patch("os.getloadavg", return_value=(1.0, 0.5, 0.3)):
            checker._check_load()
        self.assertEqual(len(checker.alerts), 0)


class TestNodeServerCheck(unittest.TestCase):
    def test_server_down(self):
        checker = SystemHealthChecker()
        with patch("socket.socket") as mock_sock:
            instance = mock_sock.return_value
            instance.connect_ex.return_value = 1  # Connection refused
            checker._check_node_server()
        downs = [a for a in checker.alerts if a.check_id == "NODE_SERVER_DOWN"]
        self.assertEqual(len(downs), 2)  # Both ports


class TestOutputFormatting(unittest.TestCase):
    def test_report_with_alerts(self):
        alerts = [
            Alert("RAM_CRITICAL", Severity.EMERGENCY, "Low RAM", "400 MB", "< 500 MB"),
            Alert("DISK_FILLING", Severity.WARNING, "Disk 80%", "80%", "> 75%"),
        ]
        report = to_report(alerts)
        self.assertIn("RAM_CRITICAL", report)
        self.assertIn("DISK_FILLING", report)
        self.assertIn("EMERGENCY", report)

    def test_report_no_alerts(self):
        report = to_report([])
        self.assertIn("healthy", report)

    def test_json_output(self):
        alerts = [Alert("TEST", Severity.WARNING, "test msg", "val", "thresh")]
        j = json.loads(to_json(alerts))
        self.assertEqual(j["summary"]["warnings"], 1)
        self.assertEqual(len(j["alerts"]), 1)


class TestCooldown(unittest.TestCase):
    def setUp(self):
        self.tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.tmpfile.close()

    def tearDown(self):
        os.unlink(self.tmpfile.name)

    def test_cooldown_filters_recent(self):
        import health_check
        original = health_check.COOLDOWN_FILE
        health_check.COOLDOWN_FILE = type(original)(self.tmpfile.name)

        alerts = [Alert("RAM_CRITICAL", Severity.EMERGENCY, "Low", "400", "500")]

        # First call — should pass through
        result1 = filter_cooled_down(alerts)
        self.assertEqual(len(result1), 1)

        # Second call — should be filtered (cooldown active)
        result2 = filter_cooled_down(alerts)
        self.assertEqual(len(result2), 0)

        health_check.COOLDOWN_FILE = original


class TestEmergencyOnly(unittest.TestCase):
    def test_emergency_only_excludes_info(self):
        checker = SystemHealthChecker()
        # Run full — will have INFO alerts like UPTIME
        all_alerts = checker.run_all()
        emergency_alerts = checker.run_emergency_only()
        info_in_emergency = [a for a in emergency_alerts if a.severity == Severity.INFO]
        self.assertEqual(len(info_in_emergency), 0)


if __name__ == "__main__":
    unittest.main()
