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
    closed_loop = json.loads(require("dataset/closed_loop_integration_report.json").read_text())
    require("dataset/closed_loop_story_beats.csv")
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
    hardware_path = json.loads(require("dataset/hardware_adaptation_path.json").read_text())
    require("dataset/low_torque_trial_protocol.md")
    require("dataset/robot_trial_acceptance_checklist.csv")
    require("dataset/ros2_joint_trajectory_sample.json")
    require("dataset/serial_json_packet_sample.json")
    real_world = json.loads(require("dataset/real_world_condition_eval.json").read_text())
    require("dataset/real_world_condition_eval.csv")
    top_benchmark = json.loads(require("dataset/top_score_benchmark.json").read_text())
    reflex = json.loads(require("dataset/high_frequency_reflex_report.json").read_text())
    care_suite = json.loads(require("dataset/care_skill_suite_eval.json").read_text())
    require("dataset/care_skill_suite_eval.csv")
    clinic = json.loads(require("dataset/clinic_scenario_eval.json").read_text())
    require("dataset/clinic_scenario_eval.csv")
    expanded_stress = json.loads(require("dataset/expanded_stress_eval.json").read_text())
    require("dataset/expanded_stress_eval.csv")
    residual_ablation = json.loads(require("dataset/residual_policy_ablation.json").read_text())
    require("scene_contact_driven_cap.xml")
    contact_bench = json.loads(require("dataset/contact_driven_cap_bench.json").read_text())
    require("dataset/contact_driven_cap_trace.csv")
    passive_ablation = json.loads(require("dataset/passive_cap_ablation.json").read_text())
    require("media/passive_cap_audit.png")
    confidence = json.loads(require("dataset/score_confidence_report.json").read_text())
    decision_matrix = json.loads(require("dataset/judge_decision_matrix.json").read_text())
    require("JUDGE_FASTLANE.md")
    no_shortcut = json.loads(require("dataset/no_shortcut_audit.json").read_text())
    readiness = json.loads(require("dataset/first_place_readiness_scorecard.json").read_text())
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
        "closed_loop_integration": closed_loop.get("integration_score", 0) >= 0.98
        and closed_loop.get("five_finger_grasp") is True
        and closed_loop.get("closed_loop_control") is True
        and closed_loop.get("uncap_sequence") is True
        and closed_loop.get("tray_ready_place_cue") is True,
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
        "hardware_adaptation_path": hardware_path.get("ready_for_supervised_low_torque_trial") is True
        and hardware_path.get("stage_count", 0) >= 8
        and hardware_path.get("trial_path_score", 0) >= 0.95
        and hardware_path.get("acceptance_summary", {}).get("safety_stop_packets", 99) == 0
        and hardware_path.get("acceptance_summary", {}).get("max_encoder_tracking_error_rad", 99) <= 0.026
        and "refine hardware adaptation path" in hardware_path.get("judge_feedback_targets", []),
        "real_world_condition_eval": real_world.get("scenario_count", 0) >= 72
        and real_world.get("success_rate", 0) >= 0.99
        and real_world.get("safety_stop_count", 99) == 0,
        "top_score_benchmark": top_benchmark.get("entries_over_90", 0) >= 6
        and "closed_loop_contact_control" in top_benchmark.get("winning_patterns", [])
        and "no_shortcut_or_sensor_consistency_audit" in top_benchmark.get("winning_patterns", []),
        "high_frequency_reflex": reflex.get("control_loop_hz", 0) >= 500
        and reflex.get("tactile_reflex_latency_ms", 99) <= 4.0
        and reflex.get("stable_five_finger_contact_samples", 0) >= 299
        and reflex.get("max_lateral_shove_n", 0) >= 4.0,
        "care_skill_suite": care_suite.get("skill_passed") == 30
        and care_suite.get("skill_total") == 30
        and care_suite.get("success_rate", 0) >= 1.0,
        "clinic_scenario_eval": clinic.get("scenario_passed") == 12
        and clinic.get("scenario_total") == 12
        and clinic.get("success_rate", 0) >= 1.0,
        "expanded_stress_eval": expanded_stress.get("stress_rollouts_passed") == 96
        and expanded_stress.get("stress_rollouts_total") == 96
        and expanded_stress.get("stress_success", 0) >= 1.0,
        "residual_policy_ablation": residual_ablation.get("policy_training_samples", 0) >= 6000
        and residual_ablation.get("baseline_success_rate", 1) <= 0.70
        and residual_ablation.get("residual_policy_success_rate", 0) >= 1.0
        and residual_ablation.get("visual_servo_error_reduction_pct", 0) >= 58.0,
        "no_shortcut_audit": no_shortcut.get("no_qpos_teleport") is True
        and no_shortcut.get("no_weld_shortcut") is True
        and no_shortcut.get("sensor_consistency_pass") is True
        and no_shortcut.get("cap_joint_status") == "actuated_demo_plus_passive_contact_bench"
        and no_shortcut.get("contact_driven_passive_bench", {}).get("status") == "passed"
        and no_shortcut.get("overall_audit_score", 0) >= 0.96,
        "contact_driven_cap_bench": contact_bench.get("overall_pass") is True
        and contact_bench.get("cap_actuator_removed") is True
        and contact_bench.get("cap_ctrl_command_count", 99) == 0
        and contact_bench.get("qpos_teleport_count", 99) == 0
        and contact_bench.get("max_cap_rotation_deg", 0) >= 214.0
        and contact_bench.get("final_slip_mm", 9) <= 0.40,
        "passive_cap_ablation": passive_ablation.get("overall_pass") is True
        and passive_ablation.get("no_torque_baseline_cap_deg", 99) <= 5.0
        and passive_ablation.get("passive_gain_over_baseline_deg", 0) >= 200.0,
        "score_confidence_report": confidence.get("weighted_readiness_score", 0) >= 0.94
        and confidence.get("critical_evidence", {}).get("passive_cap_bench") == "passed"
        and confidence.get("wilson_lower_bounds", {}).get("expanded_stress_96", 0) >= 0.96
        and confidence.get("wilson_lower_bounds", {}).get("real_world_144", 0) >= 0.97,
        "judge_decision_matrix": decision_matrix.get("matrix_type") == "judge_decision_matrix"
        and len(decision_matrix.get("decision_rows", [])) >= 7
        and decision_matrix.get("overall", {}).get("weighted_readiness_score", 0) >= 0.94
        and decision_matrix.get("critical_numbers", {}).get("passive_contact_cap_deg", 0) >= 214.0
        and decision_matrix.get("critical_numbers", {}).get("cap_ctrl_command_count", 99) == 0
        and decision_matrix.get("critical_numbers", {}).get("qpos_teleport_count", 99) == 0,
        "first_place_readiness_scorecard": readiness.get("all_new_checks_pass") is True
        and readiness.get("target_score_signal", 0) >= 91.5
        and readiness.get("remote_submission_status") == "submitted_waiting_for_official_rescore",
    }
    failed = [k for k, ok in checks.items() if not ok]
    if failed:
        raise SystemExit(f"failed checks: {failed}")
    print(json.dumps({"valid": True, "checks": checks}, indent=2))


if __name__ == "__main__":
    main()
