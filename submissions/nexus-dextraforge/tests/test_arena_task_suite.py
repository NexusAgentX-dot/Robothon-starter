import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def ensure_summary() -> None:
    if not (ROOT / "outputs" / "summary.json").exists():
        subprocess.run(["python3", "run_demo.py", "--no-video"], cwd=ROOT, check=True)


class ArenaTaskSuiteTest(unittest.TestCase):
    def test_arena_task_suite_reports_15_successful_tasks(self) -> None:
        ensure_summary()
        subprocess.run(["python3", "arena_task_suite.py"], cwd=ROOT, check=True)
        report = json.loads((ROOT / "dataset" / "task_suite_report.json").read_text())

        self.assertEqual(report["task_count"], 15)
        self.assertEqual(report["success_count"], 15)
        self.assertEqual(report["success_rate"], 1.0)
        self.assertLessEqual(report["max_pose_error_mm"], 14.0)
        self.assertGreaterEqual(report["max_cap_rotation_deg"], 224.0)
        self.assertLessEqual(report["final_slip_mm"], 0.40)


if __name__ == "__main__":
    unittest.main()
