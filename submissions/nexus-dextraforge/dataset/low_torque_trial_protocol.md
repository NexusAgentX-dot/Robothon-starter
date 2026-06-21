# Nexus DextraForge DexTriage Arena Low-Torque Trial Protocol

This protocol refines the hardware adaptation path for a supervised LEAP/Shadow-style hand trial.
It exports the packet samples, safety gates, and acceptance checklist needed before physical execution.
It does not claim that a completed physical robot run has already occurred.

## Acceptance Summary

- Packets: 698 at 50 Hz
- P95 loop jitter: 2.1724 ms
- Max encoder tracking error: 0.016544 rad
- Max motor current proxy: 1.3922 A
- Safety-stop packets: 0

## Staged Trial Path

### preflight_artifact_check
- Operator step: Confirm command stream, bridge packets, safety case, and replay report are present.
- Pass condition: All artifacts exist and match the registration UUID.
- Abort condition: Any artifact is missing or UUID does not match.
- Artifact: `dataset/hardware_adaptation_path.json`

### joint_zero_calibration
- Operator step: Home all 15 joints, record zero offsets, and keep torque disabled.
- Pass condition: Joint position feedback is stable within 0.01 rad for 2 seconds.
- Abort condition: Any joint reports encoder drift above 0.02 rad.
- Artifact: `hardware_transfer.json`

### motor_disabled_packet_replay
- Operator step: Replay the first 100 packets with motors disabled and watchdog enabled.
- Pass condition: No packet misses the 80 ms watchdog window.
- Abort condition: Any watchdog miss or malformed packet.
- Artifact: `dataset/robot_execution_packets.jsonl`

### low_torque_single_finger_sweep
- Operator step: Enable low-torque mode and sweep thumb/index/middle joints at 25 percent pressure.
- Pass condition: Current stays below 1.8 A and encoder tracking error stays below 0.03 rad.
- Abort condition: Current limit, unexpected contact, or encoder tracking violation.
- Artifact: `dataset/ros2_joint_trajectory_sample.json`

### five_finger_mirror_replay
- Operator step: Replay the full five-finger trajectory in free space at 50 percent pressure.
- Pass condition: 698 packets replay with 0 safety stops and p95 loop jitter below 3.5 ms.
- Abort condition: Any safety stop, current violation, or loop jitter above 3.5 ms.
- Artifact: `dataset/hardware_replay_trial_report.json`

### vial_contact_trial
- Operator step: Introduce a capped vial, close until five-finger contact confidence is stable.
- Pass condition: Normal force remains below 6 N and slip estimate stays below 2.5 mm.
- Abort condition: Pressure above 6 N, slip above 2.5 mm, or contact loss.
- Artifact: `dataset/tactile_feedback_report.json`

### cap_twist_trial
- Operator step: Run the cap-twist segment at low torque with thumb/index/middle alternation.
- Pass condition: Cap rotation target exceeds 216 degrees with no safety-stop packets.
- Abort condition: Cap stalls, contact loss, or any safety stop.
- Artifact: `outputs/summary.json`

### slip_recovery_trial
- Operator step: Inject a mild slip disturbance and verify tactile pressure boost recovery.
- Pass condition: Residual slip recovers to 0.42 mm or lower.
- Abort condition: Slip exceeds 2.5 mm or recovery does not converge.
- Artifact: `dataset/real_world_condition_eval.json`

### post_trial_safety_review
- Operator step: Archive packets, current trace, encoder trace, and safety-stop counter.
- Pass condition: Trial log shows 0 safety stops and all acceptance gates pass.
- Abort condition: Any gate is incomplete or any safety-stop packet occurred.
- Artifact: `dataset/robot_trial_acceptance_checklist.csv`
