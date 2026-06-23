import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def build_contact_driven_artifacts() -> None:
    if not (ROOT / "outputs" / "telemetry.csv").exists():
        subprocess.run(["python3", "run_demo.py", "--no-video"], cwd=ROOT, check=True)
    subprocess.run(["python3", "contact_feedback_audit.py"], cwd=ROOT, check=True)
    subprocess.run(["python3", "contact_driven_cap_bench.py"], cwd=ROOT, check=True)
    subprocess.run(["python3", "top_score_upgrade_evidence.py"], cwd=ROOT, check=True)


class ContactDrivenCapUpgradeTest(unittest.TestCase):
    def test_passive_cap_bench_removes_cap_actuator_and_uses_tactile_torque(self) -> None:
        build_contact_driven_artifacts()

        report = json.loads((ROOT / "dataset" / "contact_driven_cap_bench.json").read_text())
        trace = ROOT / "dataset" / "contact_driven_cap_trace.csv"
        passive_scene = ROOT / "scene_contact_driven_cap.xml"

        self.assertTrue(trace.exists())
        self.assertTrue(passive_scene.exists())
        self.assertEqual(report["bench_type"], "contact_driven_passive_cap_bench")
        self.assertTrue(report["cap_actuator_removed"])
        self.assertTrue(report["free_or_passive_object_joint"])
        self.assertEqual(report["cap_ctrl_command_count"], 0)
        self.assertEqual(report["qpos_teleport_count"], 0)
        self.assertEqual(report["torque_source"], "thumb_index_middle_tactile_shear")
        self.assertGreaterEqual(report["applied_torque_samples"], 300)
        self.assertGreaterEqual(report["max_cap_rotation_deg"], 214.0)
        self.assertLessEqual(report["final_slip_mm"], 0.40)
        self.assertTrue(report["overall_pass"])

    def test_no_shortcut_audit_promotes_contact_driven_bench(self) -> None:
        build_contact_driven_artifacts()

        audit = json.loads((ROOT / "dataset" / "no_shortcut_audit.json").read_text())

        self.assertEqual(audit["cap_joint_status"], "actuated_demo_plus_passive_contact_bench")
        self.assertEqual(audit["contact_driven_passive_bench"]["status"], "passed")
        self.assertGreaterEqual(audit["contact_driven_passive_bench"]["max_cap_rotation_deg"], 214.0)
        self.assertEqual(audit["contact_driven_passive_bench"]["cap_ctrl_command_count"], 0)
        self.assertGreaterEqual(audit["overall_audit_score"], 0.96)


if __name__ == "__main__":
    unittest.main()
