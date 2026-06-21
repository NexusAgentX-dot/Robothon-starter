import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def ensure_summary() -> None:
    if not (ROOT / "outputs" / "summary.json").exists():
        subprocess.run(["python3", "run_demo.py", "--no-video"], cwd=ROOT, check=True)


class MinimumJerkControllerTest(unittest.TestCase):
    def test_minimum_jerk_report_has_smoothness_and_tracking_evidence(self) -> None:
        ensure_summary()
        subprocess.run(["python3", "minimum_jerk_controller.py"], cwd=ROOT, check=True)
        report = json.loads((ROOT / "dataset" / "minimum_jerk_report.json").read_text())

        self.assertTrue(report["overall_pass"])
        self.assertEqual(report["trajectory_type"], "minimum_jerk_tactile_impedance")
        self.assertLessEqual(report["max_tracking_error_mm"], 12.0)
        self.assertLessEqual(report["max_normalized_jerk"], 1.0)
        self.assertGreaterEqual(report["segments"], 6)


if __name__ == "__main__":
    unittest.main()
