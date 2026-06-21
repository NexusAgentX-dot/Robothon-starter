import json
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_PATTERN = re.compile(r"\bv\d+\b", re.IGNORECASE)


def build_artifacts() -> None:
    if not (ROOT / "outputs" / "telemetry.csv").exists():
        subprocess.run(["python3", "run_demo.py", "--no-video"], cwd=ROOT, check=True)
    subprocess.run(["python3", "build_evidence_pack.py"], cwd=ROOT, check=True)


class HardwareReadyUpgradeTest(unittest.TestCase):
    def test_public_titles_do_not_include_version_suffixes(self) -> None:
        build_artifacts()

        registration = json.loads((ROOT / "registration.json").read_text())
        summary = json.loads((ROOT / "outputs" / "summary.json").read_text())
        manifest = json.loads((ROOT / "submission_manifest.json").read_text())
        scorecard = json.loads((ROOT / "rubric_scorecard.json").read_text())
        readme_title = (ROOT / "README.md").read_text().splitlines()[0]
        judge_title = (ROOT / "JUDGE_BRIEF.md").read_text().splitlines()[0]

        title_values = [
            registration["project_name"],
            summary["project"],
            manifest["project"],
            scorecard["project"],
            readme_title,
            judge_title,
        ]
        for title in title_values:
            self.assertNotRegex(title, VERSION_PATTERN)
        self.assertEqual(registration["project_name"], "Nexus DextraForge DexTriage Arena")

    def test_real_world_condition_eval_is_machine_checkable(self) -> None:
        build_artifacts()

        report = json.loads((ROOT / "dataset" / "real_world_condition_eval.json").read_text())

        self.assertEqual(report["evaluation_type"], "real_world_condition_proxy_eval")
        self.assertFalse(report["physical_robot_claimed"])
        self.assertGreaterEqual(report["scenario_count"], 72)
        self.assertEqual(report["success_count"], report["scenario_count"])
        self.assertGreaterEqual(report["success_rate"], 0.99)
        self.assertLessEqual(report["worst_final_slip_mm"], 0.42)
        self.assertGreaterEqual(report["worst_cap_rotation_deg"], 216.0)
        self.assertEqual(report["safety_stop_count"], 0)
        for axis in ("cap_friction", "vial_diameter", "pose_offset", "sensor_dropout", "payload", "lighting"):
            self.assertIn(axis, report["stress_axes"])

    def test_robot_execution_bridge_is_ready_for_low_torque_trial(self) -> None:
        build_artifacts()

        report = json.loads((ROOT / "dataset" / "robot_execution_bridge_report.json").read_text())
        packet_path = ROOT / "dataset" / "robot_execution_packets.jsonl"

        self.assertTrue(packet_path.exists())
        self.assertEqual(report["bridge_type"], "leap_shadow_low_torque_execution_bridge")
        self.assertFalse(report["physical_robot_claimed"])
        self.assertTrue(report["ready_for_low_torque_robot_test"])
        self.assertGreaterEqual(report["packets_prepared"], 690)
        self.assertLessEqual(report["max_command_delta_rad"], 0.035)
        self.assertEqual(report["watchdog_timeout_ms"], 80)
        self.assertEqual(report["safety_stop_packets"], 0)
        self.assertIn("ros2_joint_trajectory", report["transport_profiles"])
        self.assertIn("serial_json", report["transport_profiles"])
        self.assertIn("dataset/robot_execution_packets.jsonl", report["artifacts"])


if __name__ == "__main__":
    unittest.main()
