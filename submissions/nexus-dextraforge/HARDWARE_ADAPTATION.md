# Nexus DextraForge Hardware Adaptation

Registration UUID: `37a42d17-c108-4186-9199-bcd7ea26b3ef`

This entry is simulation-first and does not claim a physical robot run. The
hardware path is still executable and inspectable: the submitted telemetry is
converted into a 50 Hz command stream, checked against LEAP-style and
Shadow-style hand constraints, and replayed through a bench-trial log that
tracks loop jitter, encoder error, motor-current margin, and safety stops.

## Artifacts

- `hardware_transfer.json` maps the 15 simulated joints to hand-facing command packets.
- `dataset/hardware_command_stream.csv` contains 698 replay packets at 50 Hz.
- `dataset/hardware_replay_trial_report.json` summarizes the hardware replay bench trial.
- `dataset/robot_execution_bridge_report.json` summarizes the low-torque robot execution bridge packet export.
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

## Replay Plan

1. Home all 15 joints and run a low-pressure vial touch check.
2. Replay `dataset/hardware_command_stream.csv` in dry-run mode with motors disabled.
3. Enable low-torque mode and monitor motor current or fingertip taxels.
4. Estimate cap friction from the first 20 degrees of twist.
5. Enable slip recovery only after stable five-finger contact.
6. Abort on slip above 2.5 mm, pressure above 6.0 N, watchdog timeout above 80 ms, or any joint target outside calibrated limits.

To regenerate the replay evidence:

```bash
python3 hardware_adaptation_audit.py
python3 hardware_replay_trial.py
```

## Why It Matters For The Challenge

The Robothon task is judged from submitted code and evidence, so this file avoids
overclaiming real hardware. It gives judges a practical transfer bridge: a
bounded command protocol, safety thresholds, tactile feedback substitutes,
real-time replay metrics, and machine-checkable reports generated from the same
telemetry as the demo video.
