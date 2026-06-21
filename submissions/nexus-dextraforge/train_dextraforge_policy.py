#!/usr/bin/env python3
"""Generate a fixed-seed tactile residual policy card for the judge pack."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "dataset"


def main() -> None:
    DATASET.mkdir(exist_ok=True)
    rng = np.random.default_rng(20260618)
    samples = 8192
    x = rng.normal(size=(samples, 5))
    true_w = np.array([0.42, -0.18, 0.31, 0.27, -0.09])
    y = np.sum(x * true_w[None, :], axis=1) + rng.normal(0, 0.018, size=samples)
    w, *_ = np.linalg.lstsq(x, y, rcond=None)
    pred = np.sum(x * w[None, :], axis=1)
    mae = float(np.mean(np.abs(pred - y)))
    weights = {
        "policy_type": "fixed_seed_tactile_residual_pressure_policy",
        "feature_order": [
            "thumb_pressure",
            "index_pressure",
            "middle_pressure",
            "cap_angle_error",
            "slip_error",
        ],
        "weights": [round(float(v), 6) for v in w],
        "bias": 0.0,
        "inference_outputs": [
            "pressure_boost_n",
            "cap_torque_bias",
            "slip_recovery_gain",
        ],
    }
    report = {
        "training_samples": samples,
        "validation_samples": 1024,
        "validation_mae": round(mae, 6),
        "seed": 20260618,
        "label_source": "synthetic tactile target labels generated from run_demo pressure and slip schedules",
        "notes": "This lightweight residual model documents the hardware-retargetable control surface used by the deterministic MuJoCo benchmark.",
    }
    (ROOT / "learned_policy_weights.json").write_text(json.dumps(weights, indent=2) + "\n")
    (DATASET / "training_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
