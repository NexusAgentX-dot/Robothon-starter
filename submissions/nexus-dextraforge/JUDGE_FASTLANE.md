# Nexus DextraForge DexTriage Arena - Judge Fastlane

Registration UUID: 37a42d17-c108-4186-9199-bcd7ea26b3ef

## Open These First

1. `media/demo.mp4` - 14 second overview with 30/30, 224 deg, 4 ms, and 96/96 chips.
2. `media/passive_cap_audit.png` - passive cap contact-torque visual audit.
3. `dataset/contact_driven_cap_bench.json` - cap actuator removed, tactile torque only.
4. `dataset/no_shortcut_audit.json` - no qpos teleport, no weld shortcut, sensor consistency.
5. `dataset/score_confidence_report.json` - weighted readiness and Wilson lower bounds.
6. `dataset/judge_decision_matrix.json` - rubric questions mapped to exact evidence files.

## Highest-Signal Evidence

- Passive cap contact-torque bench: 227.7 deg.
- No-torque baseline: 0.0 deg.
- No shortcut controls: 0 cap ctrl, 0 qpos teleport.
- Reflex gate: 500 Hz loop, 4 ms tactile gate.
- Expanded evidence scale: 30/30 care skills, 12/12 clinic scenarios, 96/96 stress rollouts, 144/144 real-world proxy grid.
- Local readiness signal: 91.6.
- Weighted readiness score: 0.9599.

## Boundary Disclosure

The main demo keeps a deterministic cap scoring joint for a concise MP4. The passive cap bench removes that cap actuator and verifies the same cap threshold from tactile shear torque, so the no-object-actuator evidence is inspectable rather than implied.
Hardware evidence is packet-level replay plus supervised low-torque readiness; no live hand run is claimed.
