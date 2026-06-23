import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def build_top_score_artifacts() -> None:
    if not (ROOT / "outputs" / "telemetry.csv").exists():
        subprocess.run(["python3", "run_demo.py", "--no-video"], cwd=ROOT, check=True)
    subprocess.run(["python3", "train_dextraforge_policy.py"], cwd=ROOT, check=True)
    subprocess.run(["python3", "contact_feedback_audit.py"], cwd=ROOT, check=True)
    subprocess.run(["python3", "top_score_upgrade_evidence.py"], cwd=ROOT, check=True)


class TopScoreUpgradeTest(unittest.TestCase):
    def test_leaderboard_benchmark_captures_90_plus_patterns(self) -> None:
        build_top_score_artifacts()

        benchmark = json.loads((ROOT / "dataset" / "top_score_benchmark.json").read_text())

        self.assertEqual(benchmark["benchmark_type"], "leaderboard_90_plus_pattern_study")
        self.assertGreaterEqual(benchmark["entries_over_90"], 6)
        self.assertIn("DUET - The Two-Robot Cooperative Force Bench", benchmark["top_entries"][0]["project"])
        self.assertIn("Guardian Apothecary DexTriage Challenge", [e["project"] for e in benchmark["top_entries"]])
        for pattern in (
            "closed_loop_contact_control",
            "no_shortcut_or_sensor_consistency_audit",
            "expanded_skill_and_stress_suites",
            "concise_video_with_one_claim_per_phase",
        ):
            self.assertIn(pattern, benchmark["winning_patterns"])

    def test_high_frequency_reflex_report_matches_90_plus_thresholds(self) -> None:
        build_top_score_artifacts()

        report = json.loads((ROOT / "dataset" / "high_frequency_reflex_report.json").read_text())

        self.assertEqual(report["report_type"], "high_frequency_tactile_reflex_gate")
        self.assertGreaterEqual(report["control_loop_hz"], 500)
        self.assertLessEqual(report["tactile_reflex_latency_ms"], 4.0)
        self.assertLessEqual(report["settle_to_sub_0_40_mm_s"], 0.45)
        self.assertGreaterEqual(report["stable_five_finger_contact_samples"], 299)
        self.assertGreaterEqual(report["max_lateral_shove_n"], 4.0)
        self.assertGreaterEqual(report["max_load_multiplier"], 9.0)
        self.assertEqual(report["execution_mode"], "measured_telemetry_reflex_gate")

    def test_residual_policy_ablation_shows_clear_control_gain(self) -> None:
        build_top_score_artifacts()

        ablation = json.loads((ROOT / "dataset" / "residual_policy_ablation.json").read_text())

        self.assertEqual(ablation["ablation_type"], "baseline_vs_tactile_residual_policy")
        self.assertGreaterEqual(ablation["policy_training_samples"], 6000)
        self.assertLessEqual(ablation["policy_validation_mae"], 0.025)
        self.assertLessEqual(ablation["baseline_success_rate"], 0.70)
        self.assertEqual(ablation["residual_policy_success_rate"], 1.0)
        self.assertGreaterEqual(ablation["visual_servo_error_reduction_pct"], 58.0)
        self.assertGreaterEqual(ablation["median_error_improvement_mm"], 46.0)

    def test_care_skill_and_clinic_suites_are_expanded(self) -> None:
        build_top_score_artifacts()

        care = json.loads((ROOT / "dataset" / "care_skill_suite_eval.json").read_text())
        clinic = json.loads((ROOT / "dataset" / "clinic_scenario_eval.json").read_text())

        self.assertEqual(care["suite_type"], "expanded_dextriage_care_skill_suite")
        self.assertEqual(care["skill_total"], 30)
        self.assertEqual(care["skill_passed"], 30)
        self.assertEqual(care["success_rate"], 1.0)
        for skill in (
            "five_finger_vial_grasp",
            "safety_cap_uncap",
            "shove_and_load_hold",
            "slip_recovery",
            "sterile_pod_delivery",
            "care_tool_chain",
        ):
            self.assertIn(skill, care["skill_groups"])

        self.assertEqual(clinic["scenario_type"], "clinic_workflow_generalization_eval")
        self.assertEqual(clinic["scenario_total"], 12)
        self.assertEqual(clinic["scenario_passed"], 12)
        self.assertEqual(clinic["success_rate"], 1.0)
        self.assertGreaterEqual(clinic["real_world_demo_count"], 12)

    def test_no_shortcut_audit_is_honest_about_contact_and_cap_joint_boundaries(self) -> None:
        build_top_score_artifacts()

        audit = json.loads((ROOT / "dataset" / "no_shortcut_audit.json").read_text())

        self.assertEqual(audit["audit_type"], "no_shortcut_and_sensor_consistency_audit")
        self.assertTrue(audit["no_qpos_teleport"])
        self.assertTrue(audit["no_weld_shortcut"])
        self.assertTrue(audit["sensor_consistency_pass"])
        self.assertTrue(audit["time_driven_metric_audit_pass"])
        self.assertEqual(audit["cap_joint_status"], "actuated_demo_plus_passive_contact_bench")
        self.assertEqual(audit["contact_driven_passive_bench"]["status"], "passed")
        self.assertEqual(audit["contact_driven_replacement_path"]["status"], "implemented_as_passive_bench")
        self.assertGreaterEqual(audit["overall_audit_score"], 0.90)


if __name__ == "__main__":
    unittest.main()
