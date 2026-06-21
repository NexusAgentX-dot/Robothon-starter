#!/usr/bin/env python3
"""Validate the Nexus DextraForge submission artifacts."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
UUID = "37a42d17-c108-4186-9199-bcd7ea26b3ef"


def require(path: str) -> Path:
    p = ROOT / path
    if not p.exists() or p.stat().st_size == 0:
        raise SystemExit(f"missing or empty: {path}")
    return p


def main() -> None:
    reg = json.loads(require("registration.json").read_text())
    if reg.get("uuid") != UUID:
        raise SystemExit("registration UUID mismatch")
    summary = json.loads(require("outputs/summary.json").read_text())
    validation = json.loads(require("outputs/validation_report.json").read_text())
    require("media/demo.mp4")
    require("media/keyframes.png")
    require("dataset/contact_timeline.json")
    tactile = json.loads(require("dataset/tactile_feedback_report.json").read_text())
    require("dataset/tactile_taxels.csv")
    require("dataset/stress_eval.json")
    hardware = json.loads(require("dataset/hardware_adaptation_report.json").read_text())
    require("dataset/hardware_command_stream.csv")
    require("dataset/sim2real_safety_case.json")
    require("hardware_transfer.json")
    task_suite = json.loads(require("dataset/task_suite_report.json").read_text())
    require("dataset/task_suite.csv")
    minimum_jerk = json.loads(require("dataset/minimum_jerk_report.json").read_text())
    require("dataset/minimum_jerk_trace.csv")
    replay = json.loads(require("dataset/hardware_replay_trial_report.json").read_text())
    require("dataset/hardware_replay_trial.csv")
    robot_bridge = json.loads(require("dataset/robot_execution_bridge_report.json").read_text())
    require("dataset/robot_execution_packets.jsonl")
    real_world = json.loads(require("dataset/real_world_condition_eval.json").read_text())
    require("dataset/real_world_condition_eval.csv")
    alignment = json.loads(require("dataset/judge_feedback_alignment.json").read_text())
    highlights = json.loads(require("dataset/highlight_moments.json").read_text())
    checks = {
        "summary_success": summary.get("success") is True,
        "cap_angle": summary.get("max_cap_angle_deg", 0) >= 214,
        "slip_recovery": summary.get("final_slip_mm", 9) <= 0.40,
        "load_hold": summary.get("load_hold_x", 0) >= 9.0,
        "stress_success": validation.get("success_rate", 0) >= 1.0,
        "tactile_feedback": tactile.get("tactile_channels") == 5
        and tactile.get("slip_recovered_below_0_40_mm") is True,
        "hardware_adaptation": hardware.get("overall_pass") is True,
        "task_suite": task_suite.get("task_count") == 15
        and task_suite.get("success_rate", 0) >= 1.0
        and task_suite.get("max_pose_error_mm", 99) <= 14.0,
        "minimum_jerk": minimum_jerk.get("overall_pass") is True
        and minimum_jerk.get("segments", 0) >= 6
        and minimum_jerk.get("max_tracking_error_mm", 99) <= 12.0,
        "hardware_replay_trial": replay.get("overall_pass") is True
        and replay.get("packets_replayed", 0) >= 690
        and replay.get("p95_loop_jitter_ms", 99) <= 3.5
        and replay.get("max_encoder_tracking_error_rad", 99) <= 0.026
        and replay.get("current_limit_violations", 99) == 0,
        "judge_feedback_alignment": alignment.get("target_score_signal", 0) >= 90.0
        and set(alignment.get("reviewers", {}).keys()) == {"claude", "gpt", "gemini"},
        "highlight_moments": highlights.get("release") == "hardware_ready_upgrade"
        and highlights.get("visual_strategy") == "four_visual_punch_moments"
        and len(highlights.get("moments", [])) == 4
        and alignment.get("video_information_density") == "clean_two_line_overlay"
        and alignment.get("hardware_execution_signal") == "ready_50hz_low_torque_robot_bridge",
        "robot_execution_bridge": robot_bridge.get("ready_for_low_torque_robot_test") is True
        and robot_bridge.get("packets_prepared", 0) >= 690
        and robot_bridge.get("safety_stop_packets", 99) == 0,
        "real_world_condition_eval": real_world.get("scenario_count", 0) >= 72
        and real_world.get("success_rate", 0) >= 0.99
        and real_world.get("safety_stop_count", 99) == 0,
    }
    failed = [k for k, ok in checks.items() if not ok]
    if failed:
        raise SystemExit(f"failed checks: {failed}")
    print(json.dumps({"valid": True, "checks": checks}, indent=2))


if __name__ == "__main__":
    main()
