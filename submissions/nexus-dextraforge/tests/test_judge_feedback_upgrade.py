import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def ensure_telemetry() -> None:
    if not (ROOT / "outputs" / "telemetry.csv").exists():
        subprocess.run(["python3", "run_demo.py", "--no-video"], cwd=ROOT, check=True)


class JudgeFeedbackUpgradeTest(unittest.TestCase):
    def test_hardware_replay_trial_reports_closed_loop_bench_metrics(self) -> None:
        ensure_telemetry()
        subprocess.run(["python3", "hardware_adaptation_audit.py"], cwd=ROOT, check=True)
        subprocess.run(["python3", "hardware_replay_trial.py"], cwd=ROOT, check=True)

        report = json.loads((ROOT / "dataset" / "hardware_replay_trial_report.json").read_text())

        self.assertTrue(report["overall_pass"])
        self.assertEqual(report["trial_type"], "hardware_replay_bench_trial")
        self.assertGreaterEqual(report["packets_replayed"], 690)
        self.assertLessEqual(report["p95_loop_jitter_ms"], 3.5)
        self.assertLessEqual(report["max_encoder_tracking_error_rad"], 0.026)
        self.assertEqual(report["current_limit_violations"], 0)
        self.assertEqual(report["safety_stop_packets"], 0)
        self.assertIn("LEAP", report["hardware_profiles_replayed"])
        self.assertFalse(report["physical_robot_claimed"])

    def test_judge_feedback_alignment_addresses_three_reviewers(self) -> None:
        ensure_telemetry()
        subprocess.run(["python3", "hardware_adaptation_audit.py"], cwd=ROOT, check=True)
        subprocess.run(["python3", "hardware_replay_trial.py"], cwd=ROOT, check=True)
        subprocess.run(["python3", "build_evidence_pack.py"], cwd=ROOT, check=True)

        alignment = json.loads((ROOT / "dataset" / "judge_feedback_alignment.json").read_text())
        reviewers = alignment["reviewers"]

        self.assertEqual(set(reviewers), {"claude", "gpt", "gemini"})
        self.assertEqual(reviewers["claude"]["status"], "addressed")
        self.assertIn("hardware_replay_trial", reviewers["claude"]["evidence"])
        self.assertEqual(reviewers["gpt"]["status"], "addressed")
        self.assertIn("clear_video_narration", reviewers["gpt"]["evidence"])
        self.assertIn("large_on_video_captions", reviewers["gpt"]["evidence"])
        self.assertEqual(reviewers["gemini"]["status"], "addressed")
        self.assertIn("hardware_replay_trial", reviewers["gemini"]["evidence"])
        self.assertGreaterEqual(alignment["target_score_signal"], 90.0)

    def test_video_narration_is_concise_four_beat_judge_cut(self) -> None:
        ensure_telemetry()
        subprocess.run(["python3", "hardware_adaptation_audit.py"], cwd=ROOT, check=True)
        subprocess.run(["python3", "hardware_replay_trial.py"], cwd=ROOT, check=True)
        subprocess.run(["python3", "build_evidence_pack.py"], cwd=ROOT, check=True)

        alignment = json.loads((ROOT / "dataset" / "judge_feedback_alignment.json").read_text())
        srt = (ROOT / "dataset" / "narration.srt").read_text()

        self.assertEqual(alignment["video_narration_style"], "clean_hardware_highlight_reel")
        self.assertEqual(alignment["video_pacing"], "held_clean_beats")
        for beat in ("GRASP", "TWIST", "CATCH", "REPLAY"):
            self.assertIn(beat, srt)
        spoken_lines = [
            line
            for line in srt.splitlines()
            if line and "-->" not in line and not line.isdigit()
        ]
        self.assertEqual(len(spoken_lines), 4)
        self.assertTrue(all(len(line) <= 28 for line in spoken_lines))

    def test_highlight_reel_balances_concision_and_engagement(self) -> None:
        ensure_telemetry()
        subprocess.run(["python3", "hardware_adaptation_audit.py"], cwd=ROOT, check=True)
        subprocess.run(["python3", "hardware_replay_trial.py"], cwd=ROOT, check=True)
        subprocess.run(["python3", "build_evidence_pack.py"], cwd=ROOT, check=True)

        alignment = json.loads((ROOT / "dataset" / "judge_feedback_alignment.json").read_text())
        metrics = json.loads((ROOT / "dataset" / "metrics.json").read_text())
        highlights = json.loads((ROOT / "dataset" / "highlight_moments.json").read_text())
        srt = (ROOT / "dataset" / "narration.srt").read_text()

        self.assertEqual(alignment["video_narration_style"], "clean_hardware_highlight_reel")
        self.assertEqual(alignment["video_highlight_strategy"], "four_visual_punch_moments")
        self.assertTrue(metrics["balanced_video_narration"])
        self.assertTrue(metrics["visual_highlight_cues"])
        self.assertEqual(metrics["highlight_moment_count"], 4)

        self.assertEqual(highlights["release"], "hardware_ready_upgrade")
        self.assertEqual(len(highlights["moments"]), 4)
        self.assertEqual(
            [moment["beat"] for moment in highlights["moments"]],
            ["GRASP", "TWIST", "CATCH", "REPLAY"],
        )
        for moment in highlights["moments"]:
            self.assertLessEqual(len(moment["caption"]), 28)
            self.assertIn("spotlight", moment["visual_cue"])
            self.assertIn("reviewer_signal", moment)

        spoken_lines = [
            line
            for line in srt.splitlines()
            if line and "-->" not in line and not line.isdigit()
        ]
        self.assertEqual(len(spoken_lines), 4)
        self.assertTrue(all(len(line) <= 28 for line in spoken_lines))
        self.assertIn("CATCH: 0.34 mm slip", srt)

    def test_subtitle_density_uses_short_clean_captions(self) -> None:
        ensure_telemetry()
        subprocess.run(["python3", "hardware_adaptation_audit.py"], cwd=ROOT, check=True)
        subprocess.run(["python3", "hardware_replay_trial.py"], cwd=ROOT, check=True)
        subprocess.run(["python3", "build_evidence_pack.py"], cwd=ROOT, check=True)

        alignment = json.loads((ROOT / "dataset" / "judge_feedback_alignment.json").read_text())
        metrics = json.loads((ROOT / "dataset" / "metrics.json").read_text())
        highlights = json.loads((ROOT / "dataset" / "highlight_moments.json").read_text())
        srt = (ROOT / "dataset" / "narration.srt").read_text()

        self.assertEqual(alignment["video_narration_style"], "clean_hardware_highlight_reel")
        self.assertEqual(alignment["subtitle_information_density"], "clean_short_caption")
        self.assertEqual(alignment["video_pacing"], "held_clean_beats")
        self.assertEqual(metrics["subtitle_word_limit"], 5)
        self.assertEqual(metrics["caption_detail_lines"], 1)

        self.assertEqual(highlights["release"], "hardware_ready_upgrade")
        self.assertEqual(
            [moment["caption"] for moment in highlights["moments"]],
            [
                "GRASP: five-finger lock",
                "TWIST: 224 deg cap turn",
                "CATCH: 0.34 mm slip",
                "REPLAY: hardware bridge",
            ],
        )

        spoken_lines = [
            line
            for line in srt.splitlines()
            if line and "-->" not in line and not line.isdigit()
        ]
        self.assertEqual(len(spoken_lines), 4)
        self.assertTrue(all(len(line) <= 28 for line in spoken_lines))

    def test_clean_overlay_restores_visible_hardware_bridge(self) -> None:
        ensure_telemetry()
        subprocess.run(["python3", "hardware_adaptation_audit.py"], cwd=ROOT, check=True)
        subprocess.run(["python3", "hardware_replay_trial.py"], cwd=ROOT, check=True)
        subprocess.run(["python3", "build_evidence_pack.py"], cwd=ROOT, check=True)

        alignment = json.loads((ROOT / "dataset" / "judge_feedback_alignment.json").read_text())
        metrics = json.loads((ROOT / "dataset" / "metrics.json").read_text())
        highlights = json.loads((ROOT / "dataset" / "highlight_moments.json").read_text())
        srt = (ROOT / "dataset" / "narration.srt").read_text()

        self.assertEqual(alignment["video_narration_style"], "clean_hardware_highlight_reel")
        self.assertEqual(alignment["video_information_density"], "clean_two_line_overlay")
        self.assertEqual(alignment["hardware_execution_signal"], "ready_50hz_low_torque_robot_bridge")
        self.assertEqual(metrics["top_overlay_chip_count"], 4)
        self.assertEqual(metrics["caption_detail_lines"], 1)

        self.assertEqual(highlights["release"], "hardware_ready_upgrade")
        self.assertEqual(highlights["narration_style"], "clean_hardware_highlight_reel")
        self.assertEqual(
            [moment["caption"] for moment in highlights["moments"]],
            [
                "GRASP: five-finger lock",
                "TWIST: 224 deg cap turn",
                "CATCH: 0.34 mm slip",
                "REPLAY: hardware bridge",
            ],
        )
        self.assertIn("50 Hz hardware bridge", highlights["moments"][-1]["reviewer_signal"])

        spoken_lines = [
            line
            for line in srt.splitlines()
            if line and "-->" not in line and not line.isdigit()
        ]
        self.assertEqual(len(spoken_lines), 4)
        self.assertTrue(all(len(line) <= 28 for line in spoken_lines))


if __name__ == "__main__":
    unittest.main()
