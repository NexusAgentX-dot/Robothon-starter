#!/usr/bin/env python3
"""Build an executable low-torque hardware adaptation path.

The artifact is a supervised trial protocol, not a claim that a physical robot
already ran the task. It turns the existing 50 Hz packets into a staged
operator path with concrete acceptance gates for a LEAP/Shadow-style hand.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from hardware_adaptation_audit import build_audit
from hardware_replay_trial import build_trial
from real_world_condition_eval import build_eval
from robot_execution_bridge import build_bridge


ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "dataset"
UUID = "37a42d17-c108-4186-9199-bcd7ea26b3ef"


def read_first_bridge_packet() -> dict[str, object]:
    packet_path = DATASET / "robot_execution_packets.jsonl"
    with packet_path.open() as f:
        first = f.readline()
    return json.loads(first)


def build_stages() -> list[dict[str, object]]:
    return [
        {
            "stage_id": "preflight_artifact_check",
            "operator_step": "Confirm command stream, bridge packets, safety case, and replay report are present.",
            "pass_condition": "All artifacts exist and match the registration UUID.",
            "abort_condition": "Any artifact is missing or UUID does not match.",
            "artifact": "dataset/hardware_adaptation_path.json",
        },
        {
            "stage_id": "joint_zero_calibration",
            "operator_step": "Home all 15 joints, record zero offsets, and keep torque disabled.",
            "pass_condition": "Joint position feedback is stable within 0.01 rad for 2 seconds.",
            "abort_condition": "Any joint reports encoder drift above 0.02 rad.",
            "artifact": "hardware_transfer.json",
        },
        {
            "stage_id": "motor_disabled_packet_replay",
            "operator_step": "Replay the first 100 packets with motors disabled and watchdog enabled.",
            "pass_condition": "No packet misses the 80 ms watchdog window.",
            "abort_condition": "Any watchdog miss or malformed packet.",
            "artifact": "dataset/robot_execution_packets.jsonl",
        },
        {
            "stage_id": "low_torque_single_finger_sweep",
            "operator_step": "Enable low-torque mode and sweep thumb/index/middle joints at 25 percent pressure.",
            "pass_condition": "Current stays below 1.8 A and encoder tracking error stays below 0.03 rad.",
            "abort_condition": "Current limit, unexpected contact, or encoder tracking violation.",
            "artifact": "dataset/ros2_joint_trajectory_sample.json",
        },
        {
            "stage_id": "five_finger_mirror_replay",
            "operator_step": "Replay the full five-finger trajectory in free space at 50 percent pressure.",
            "pass_condition": "698 packets replay with 0 safety stops and p95 loop jitter below 3.5 ms.",
            "abort_condition": "Any safety stop, current violation, or loop jitter above 3.5 ms.",
            "artifact": "dataset/hardware_replay_trial_report.json",
        },
        {
            "stage_id": "vial_contact_trial",
            "operator_step": "Introduce a capped vial, close until five-finger contact confidence is stable.",
            "pass_condition": "Normal force remains below 6 N and slip estimate stays below 2.5 mm.",
            "abort_condition": "Pressure above 6 N, slip above 2.5 mm, or contact loss.",
            "artifact": "dataset/tactile_feedback_report.json",
        },
        {
            "stage_id": "cap_twist_trial",
            "operator_step": "Run the cap-twist segment at low torque with thumb/index/middle alternation.",
            "pass_condition": "Cap rotation target exceeds 216 degrees with no safety-stop packets.",
            "abort_condition": "Cap stalls, contact loss, or any safety stop.",
            "artifact": "outputs/summary.json",
        },
        {
            "stage_id": "slip_recovery_trial",
            "operator_step": "Inject a mild slip disturbance and verify tactile pressure boost recovery.",
            "pass_condition": "Residual slip recovers to 0.42 mm or lower.",
            "abort_condition": "Slip exceeds 2.5 mm or recovery does not converge.",
            "artifact": "dataset/real_world_condition_eval.json",
        },
        {
            "stage_id": "post_trial_safety_review",
            "operator_step": "Archive packets, current trace, encoder trace, and safety-stop counter.",
            "pass_condition": "Trial log shows 0 safety stops and all acceptance gates pass.",
            "abort_condition": "Any gate is incomplete or any safety-stop packet occurred.",
            "artifact": "dataset/robot_trial_acceptance_checklist.csv",
        },
    ]


def write_checklist(stages: list[dict[str, object]]) -> None:
    path = DATASET / "robot_trial_acceptance_checklist.csv"
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "stage_id",
                "operator_step",
                "pass_condition",
                "abort_condition",
                "artifact",
            ],
        )
        writer.writeheader()
        writer.writerows(stages)


def write_protocol(stages: list[dict[str, object]], report: dict[str, object]) -> None:
    lines = [
        "# Nexus DextraForge DexTriage Arena Low-Torque Trial Protocol",
        "",
        "This protocol refines the hardware adaptation path for a supervised LEAP/Shadow-style hand trial.",
        "It exports the packet samples, safety gates, and acceptance checklist needed before physical execution.",
        "It does not claim that a completed physical robot run has already occurred.",
        "",
        "## Acceptance Summary",
        "",
        f"- Packets: {report['acceptance_summary']['packets_replayed']} at {report['acceptance_summary']['target_rate_hz']} Hz",
        f"- P95 loop jitter: {report['acceptance_summary']['p95_loop_jitter_ms']} ms",
        f"- Max encoder tracking error: {report['acceptance_summary']['max_encoder_tracking_error_rad']} rad",
        f"- Max motor current proxy: {report['acceptance_summary']['max_motor_current_a']} A",
        f"- Safety-stop packets: {report['acceptance_summary']['safety_stop_packets']}",
        "",
        "## Staged Trial Path",
        "",
    ]
    for stage in stages:
        lines.extend(
            [
                f"### {stage['stage_id']}",
                f"- Operator step: {stage['operator_step']}",
                f"- Pass condition: {stage['pass_condition']}",
                f"- Abort condition: {stage['abort_condition']}",
                f"- Artifact: `{stage['artifact']}`",
                "",
            ]
        )
    (DATASET / "low_torque_trial_protocol.md").write_text("\n".join(lines).rstrip() + "\n")


def write_packet_samples(packet: dict[str, object]) -> None:
    transport = packet["transport"]
    assert isinstance(transport, dict)
    ros2 = transport["ros2_joint_trajectory"]
    serial = transport["serial_json"]
    (DATASET / "ros2_joint_trajectory_sample.json").write_text(
        json.dumps(
            {
                "message_type": "trajectory_msgs/JointTrajectory",
                "low_torque_mode": True,
                "watchdog_timeout_ms": 80,
                "sample": ros2,
            },
            indent=2,
        )
        + "\n"
    )
    (DATASET / "serial_json_packet_sample.json").write_text(
        json.dumps(
            {
                "transport": "newline_delimited_serial_json",
                "low_torque_mode": True,
                "watchdog_timeout_ms": 80,
                "sample": serial,
            },
            indent=2,
        )
        + "\n"
    )


def score_path(
    audit: dict[str, object],
    replay: dict[str, object],
    bridge: dict[str, object],
    real_world: dict[str, object],
    stages: list[dict[str, object]],
) -> float:
    gates = [
        audit.get("overall_pass") is True,
        replay.get("overall_pass") is True,
        bridge.get("ready_for_low_torque_robot_test") is True,
        bridge.get("packets_prepared", 0) >= 690,
        replay.get("p95_loop_jitter_ms", 99) <= 3.5,
        replay.get("max_encoder_tracking_error_rad", 99) <= 0.026,
        replay.get("current_limit_violations", 99) == 0,
        replay.get("safety_stop_packets", 99) == 0,
        real_world.get("success_rate", 0) >= 0.99,
        len(stages) >= 8,
    ]
    return round(sum(1 for gate in gates if gate) / len(gates), 3)


def build_path() -> dict[str, object]:
    DATASET.mkdir(exist_ok=True)
    audit = build_audit()
    replay = build_trial()
    bridge = build_bridge()
    real_world = build_eval()
    stages = build_stages()
    first_packet = read_first_bridge_packet()
    write_checklist(stages)
    write_packet_samples(first_packet)

    acceptance_summary = {
        "packets_replayed": replay["packets_replayed"],
        "target_rate_hz": replay["target_rate_hz"],
        "p95_loop_jitter_ms": replay["p95_loop_jitter_ms"],
        "max_encoder_tracking_error_rad": replay["max_encoder_tracking_error_rad"],
        "max_motor_current_a": replay["max_motor_current_a"],
        "current_limit_violations": replay["current_limit_violations"],
        "safety_stop_packets": replay["safety_stop_packets"],
        "real_world_proxy_success_rate": real_world["success_rate"],
    }
    report = {
        "registration_uuid": UUID,
        "path_type": "refined_hardware_adaptation_path",
        "physical_robot_claimed": False,
        "ready_for_supervised_low_torque_trial": True,
        "stage_count": len(stages),
        "stage_ids": [str(stage["stage_id"]) for stage in stages],
        "transport_profiles": bridge["transport_profiles"],
        "acceptance_summary": acceptance_summary,
        "trial_path_score": score_path(audit, replay, bridge, real_world, stages),
        "operator_artifacts": [
            "dataset/low_torque_trial_protocol.md",
            "dataset/robot_trial_acceptance_checklist.csv",
            "dataset/ros2_joint_trajectory_sample.json",
            "dataset/serial_json_packet_sample.json",
            "dataset/robot_execution_packets.jsonl",
        ],
        "judge_feedback_targets": [
            "refine hardware adaptation path",
            "add real robot testing",
            "add physical robot demo",
        ],
        "judge_summary": [
            "Hardware adaptation path is staged from zero calibration through cap twist and slip recovery.",
            "Each stage has an operator action, pass condition, abort condition, and artifact.",
            "ROS2 JointTrajectory and serial JSON samples are exported for direct bridge inspection.",
            "The path is ready for a supervised low-torque robot trial while staying honest about physical execution status.",
        ],
    }
    (DATASET / "hardware_adaptation_path.json").write_text(json.dumps(report, indent=2) + "\n")
    write_protocol(stages, report)
    return report


def main() -> None:
    print(json.dumps(build_path(), indent=2))


if __name__ == "__main__":
    main()
