# Nexus DextraForge Hardware Adaptation

Registration UUID: `37a42d17-c108-4186-9199-bcd7ea26b3ef`

This entry is simulation-first and does not claim a physical robot run. The
hardware path is still executable and inspectable: the submitted telemetry is
converted into a 50 Hz command stream, checked against LEAP-style and
Shadow-style hand constraints, replayed through a bench-trial log, and packaged
as a staged low-torque trial protocol with packet samples, pass gates, abort
gates, and an operator checklist.

## Artifacts

- `hardware_transfer.json` maps the 15 simulated joints to hand-facing command packets.
- `dataset/hardware_command_stream.csv` contains 698 replay packets at 50 Hz.
- `dataset/hardware_replay_trial_report.json` summarizes the hardware replay bench trial.
- `dataset/robot_execution_bridge_report.json` summarizes the low-torque robot execution bridge packet export.
- `dataset/hardware_adaptation_path.json` summarizes the refined staged hardware adaptation path.
- `dataset/low_torque_trial_protocol.md` gives the supervised low-torque trial protocol.
- `dataset/robot_trial_acceptance_checklist.csv` lists pass/abort gates for every trial stage.
- `dataset/ros2_joint_trajectory_sample.json` and `dataset/serial_json_packet_sample.json` show bridge-ready packet formats.
- `dataset/real_world_condition_eval.json` summarizes the real-world condition proxy evaluation.
- `dataset/hardware_replay_trial.csv` logs per-packet timing, encoder, current, and safety evidence.
- `dataset/hardware_adaptation_report.json` audits range, velocity, pressure, quantization, and slip-abort limits.
- `dataset/sim2real_safety_case.json` lists startup calibration and emergency-stop conditions.

## Latest Audit Result

- Overall pass: `true`
- Joints checked: `15`
- Packets checked: `698`
- Range violations: `0`
- Rate violations: `0`
- Max joint velocity: `1.122 rad/s` against a `1.8 rad/s` limit
- Max pressure target: `5.9445 N` against a `6.0 N` limit
- Max slip estimate: `2.0925 mm` against a `2.5 mm` abort threshold
- Max 12-bit position quantization error: `0.00022 rad`
- Safety-stop packets: `0`
- Hardware replay trial: `pass`
- Replay packets: `698`
- P95 loop jitter: `< 3.5 ms`
- Max encoder tracking error: `< 0.026 rad`
- Current-limit violations: `0`
- Refined hardware adaptation path: `pass`
- Trial path score: `1.0`
- Low-torque trial stages: `9`

## Low-Torque Trial Path

1. Check artifacts and UUID consistency.
2. Home all 15 joints and record zero offsets with torque disabled.
3. Replay the first 100 packets with motors disabled and watchdog enabled.
4. Enable low-torque single-finger sweeps at 25 percent pressure.
5. Run five-finger mirror replay in free space at 50 percent pressure.
6. Introduce the capped vial and verify stable five-finger contact.
7. Run the cap-twist segment with thumb/index/middle alternation.
8. Inject a mild slip disturbance and verify recovery below 0.42 mm.
9. Archive current, encoder, safety-stop, and packet logs.

Abort on slip above 2.5 mm, pressure above 6.0 N, watchdog timeout above 80 ms,
current above 1.8 A, encoder tracking error above 0.03 rad, or any joint target
outside calibrated limits.

To regenerate the replay evidence:

```bash
python3 hardware_adaptation_audit.py
python3 hardware_replay_trial.py
python3 hardware_adaptation_path.py
```

## Why It Matters For The Challenge

The Robothon task is judged from submitted code and evidence, so this file avoids
overclaiming real hardware. It gives judges a practical transfer bridge: a
bounded command protocol, safety thresholds, tactile feedback substitutes,
real-time replay metrics, a supervised low-torque trial protocol, and
machine-checkable reports generated from the same telemetry as the demo video.
