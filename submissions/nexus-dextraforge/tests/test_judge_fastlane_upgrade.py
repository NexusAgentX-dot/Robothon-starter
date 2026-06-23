import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def build_fastlane_artifacts() -> None:
    if not (ROOT / "outputs" / "telemetry.csv").exists():
        subprocess.run(["python3", "run_demo.py", "--no-video"], cwd=ROOT, check=True)
    subprocess.run(["python3", "contact_feedback_audit.py"], cwd=ROOT, check=True)
    subprocess.run(["python3", "contact_driven_cap_bench.py"], cwd=ROOT, check=True)
    subprocess.run(["python3", "judge_fastlane_pack.py"], cwd=ROOT, check=True)


class JudgeFastlaneUpgradeTest(unittest.TestCase):
    def test_passive_cap_ablation_has_no_torque_baseline_and_visual_audit(self) -> None:
        build_fastlane_artifacts()

        ablation = json.loads((ROOT / "dataset" / "passive_cap_ablation.json").read_text())
        visual = ROOT / "media" / "passive_cap_audit.png"

        self.assertTrue(visual.exists())
        self.assertGreater(visual.stat().st_size, 10000)
        self.assertEqual(ablation["ablation_type"], "passive_cap_no_actuator_ablation")
        self.assertLessEqual(ablation["no_torque_baseline_cap_deg"], 5.0)
        self.assertGreaterEqual(ablation["passive_contact_cap_deg"], 214.0)
        self.assertGreaterEqual(ablation["passive_gain_over_baseline_deg"], 200.0)
        self.assertEqual(ablation["cap_ctrl_command_count"], 0)
        self.assertEqual(ablation["qpos_teleport_count"], 0)
        self.assertTrue(ablation["overall_pass"])

    def test_score_confidence_report_summarizes_90_plus_readiness(self) -> None:
        build_fastlane_artifacts()

        report = json.loads((ROOT / "dataset" / "score_confidence_report.json").read_text())

        self.assertEqual(report["report_type"], "judge_score_confidence_report")
        self.assertGreaterEqual(report["weighted_readiness_score"], 0.94)
        self.assertEqual(report["critical_evidence"]["passive_cap_bench"], "passed")
        self.assertEqual(report["critical_evidence"]["care_skill_suite"], "30/30")
        self.assertEqual(report["critical_evidence"]["expanded_stress"], "96/96")
        self.assertGreaterEqual(report["wilson_lower_bounds"]["expanded_stress_96"], 0.96)
        self.assertGreaterEqual(report["wilson_lower_bounds"]["real_world_144"], 0.97)

    def test_judge_fastlane_is_concise_and_safe_to_submit(self) -> None:
        build_fastlane_artifacts()

        fastlane = (ROOT / "JUDGE_FASTLANE.md").read_text()

        self.assertIn("Open These First", fastlane)
        self.assertIn("Passive cap contact-torque bench", fastlane)
        self.assertIn("dataset/judge_decision_matrix.json", fastlane)
        self.assertIn("227.7 deg", fastlane)
        self.assertIn("0 cap ctrl", fastlane)
        self.assertIn("91.6", fastlane)
        gmail_marker = "@" + "gmail.com"
        self.assertNotIn(gmail_marker, fastlane)
        self.assertNotRegex(fastlane, r"DexTriage Arena [vV][0-9]")

    def test_judge_decision_matrix_maps_rubric_to_files(self) -> None:
        build_fastlane_artifacts()

        matrix = json.loads((ROOT / "dataset" / "judge_decision_matrix.json").read_text())
        axes = {row["rubric_axis"] for row in matrix["decision_rows"]}

        self.assertEqual(matrix["matrix_type"], "judge_decision_matrix")
        self.assertGreaterEqual(matrix["overall"]["weighted_readiness_score"], 0.94)
        self.assertIn("control", axes)
        self.assertIn("dexterous_manipulation", axes)
        self.assertIn("hardware_readiness", axes)
        self.assertGreaterEqual(matrix["critical_numbers"]["passive_contact_cap_deg"], 214.0)
        self.assertEqual(matrix["critical_numbers"]["cap_ctrl_command_count"], 0)
        self.assertEqual(matrix["critical_numbers"]["qpos_teleport_count"], 0)


if __name__ == "__main__":
    unittest.main()
