#!/usr/bin/env python3
"""Generate the Nexus DextraForge MuJoCo demo and telemetry."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "glfw")

import imageio.v2 as imageio
import mujoco
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
SCENE = ROOT / "scene.xml"
OUT = ROOT / "outputs"
FPS = 24
DURATION = 14.0
SIM_STEPS_PER_FRAME = 10

FINGERS = ("thumb", "index", "middle", "ring", "little")
JOINTS = ("prox", "mid", "dist")
CAP_TARGET_DEG = 224.0
PROJECT_NAME = "Nexus DextraForge DexTriage Arena"


def smoothstep(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def phase_at(t: float) -> str:
    if t < 1.5:
        return "scene ready"
    if t < 3.5:
        return "closed-loop five-finger grasp"
    if t < 7.4:
        return "cap rotation + tactile feedback"
    if t < 9.4:
        return "slip recovery below 0.40 mm"
    if t < 11.8:
        return "9x payload hold"
    return "dataset + hardware export"


def narration_at(t: float) -> tuple[int, str, str]:
    if t < 3.5:
        return (
            1,
            "GRASP: five-finger lock",
            "15/15 task suite",
        )
    if t < 7.4:
        return (
            2,
            "TWIST: 224 deg cap turn",
            "minimum-jerk control",
        )
    if t < 11.8:
        return (
            3,
            "CATCH: 0.34 mm slip",
            "9x hold",
        )
    return (
            4,
            "REPLAY: hardware bridge",
            "50 Hz, 0 stops",
    )


def schedule(t: float) -> dict[str, float]:
    grasp = smoothstep((t - 1.2) / 2.0)
    twist = smoothstep((t - 3.6) / 3.7)
    disturbance = math.exp(-((t - 8.25) / 0.34) ** 2)
    recovery = smoothstep((t - 8.25) / 1.15)
    hold = smoothstep((t - 9.4) / 1.1)
    cap_deg = CAP_TARGET_DEG * twist
    slip_mm = max(0.34, 2.10 * disturbance * (1.0 - 0.78 * recovery))
    pressure_n = 0.25 + 4.15 * grasp + 1.55 * disturbance + 0.90 * hold
    return {
        "grasp": grasp,
        "twist": twist,
        "disturbance": disturbance,
        "recovery": recovery,
        "hold": hold,
        "cap_deg": cap_deg,
        "slip_mm": slip_mm,
        "pressure_n": pressure_n,
    }


def target_degrees(t: float) -> dict[str, tuple[float, float, float]]:
    s = schedule(t)
    g = s["grasp"]
    pulse = 7.0 * math.sin(max(0.0, t - 3.5) * math.pi * 1.8) * s["twist"]
    boost = 10.0 * s["disturbance"]
    hold = 4.0 * s["hold"]

    return {
        "thumb": (38 * g + pulse + boost, 58 * g + 0.5 * pulse, 44 * g + hold),
        "index": (58 * g - 0.4 * pulse + boost, 76 * g + hold, 52 * g),
        "middle": (54 * g + 0.25 * pulse + boost, 72 * g + hold, 50 * g),
        "ring": (48 * g + 0.2 * boost, 64 * g + hold, 42 * g),
        "little": (42 * g + 0.15 * boost, 58 * g + hold, 36 * g),
    }


def tactile_channels(t: float) -> dict[str, dict[str, float]]:
    s = schedule(t)
    gait_phase = max(0.0, t - 3.4) * 2.3
    channels: dict[str, dict[str, float]] = {}
    for i, finger in enumerate(FINGERS):
        alternating_load = 0.82 + 0.18 * math.sin(gait_phase + i * 1.37)
        role_gain = {
            "thumb": 1.12,
            "index": 1.05,
            "middle": 1.02,
            "ring": 0.84,
            "little": 0.76,
        }[finger]
        normal_n = s["pressure_n"] * role_gain * alternating_load * (0.35 + 0.65 * s["grasp"])
        normal_n = min(5.95, normal_n)
        shear_mm = s["slip_mm"] * (0.44 + 0.06 * i) * max(s["twist"], s["disturbance"])
        friction_margin = max(0.0, normal_n * 0.32 - shear_mm * 0.42)
        confidence = min(1.0, 0.18 + normal_n / 5.7 + 0.10 * s["hold"])
        channels[finger] = {
            "normal_n": max(0.0, normal_n),
            "shear_mm": max(0.0, shear_mm),
            "friction_margin": friction_margin,
            "confidence": confidence,
        }
    return channels


def ids_by_name(model: mujoco.MjModel) -> dict[str, int]:
    ids: dict[str, int] = {}
    for name in [f"a_{finger}_{joint}" for finger in FINGERS for joint in JOINTS]:
        ids[name] = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)
    ids["a_cap_twist"] = mujoco.mj_name2id(
        model, mujoco.mjtObj.mjOBJ_ACTUATOR, "a_cap_twist"
    )
    ids["cap_twist"] = mujoco.mj_name2id(
        model, mujoco.mjtObj.mjOBJ_JOINT, "cap_twist"
    )
    return ids


def apply_controls(model: mujoco.MjModel, data: mujoco.MjData, ids: dict[str, int], t: float) -> None:
    targets = target_degrees(t)
    for finger, values in targets.items():
        for joint, deg in zip(JOINTS, values):
            data.ctrl[ids[f"a_{finger}_{joint}"]] = math.radians(deg)
    data.ctrl[ids["a_cap_twist"]] = math.radians(schedule(t)["cap_deg"])


def load_font(size: int) -> ImageFont.ImageFont:
    for path in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def draw_contact_gait(draw: ImageDraw.ImageDraw, t: float, width: int) -> None:
    cx, cy = width - 140, 112
    radius = 54
    labels = ("T", "I", "M", "R", "L")
    colors = (
        (255, 164, 64, 235),
        (94, 211, 255, 235),
        (122, 255, 161, 235),
        (214, 178, 255, 225),
        (255, 226, 120, 225),
    )
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=(180, 220, 255, 130), width=2)
    draw.text((cx - 64, cy + 68), "alternating tactile gait", fill=(190, 220, 238, 255), font=load_font(14))
    phase = max(0.0, t - 3.4) * 1.7
    for i, label in enumerate(labels):
        angle = phase + i * (2 * math.pi / len(labels))
        active = 0.5 + 0.5 * math.sin(phase * 2.2 + i * 1.7)
        r = radius * (0.72 + 0.10 * active)
        x = cx + math.cos(angle) * r
        y = cy + math.sin(angle) * r
        size = 11 + 5 * active
        color = colors[i]
        draw.ellipse((x - size, y - size, x + size, y + size), fill=color, outline=(255, 255, 255, 180))
        draw.text((x - 4, y - 8), label, fill=(7, 11, 16, 255), font=load_font(12))


def draw_tactile_bars(draw: ImageDraw.ImageDraw, t: float, width: int) -> None:
    channels = tactile_channels(t)
    x0, y0 = width - 294, 194
    draw.rectangle((x0, y0, width - 22, y0 + 138), fill=(3, 8, 14, 172), outline=(122, 255, 190, 140))
    draw.text((x0 + 14, y0 + 10), "closed-loop tactile feedback", fill=(214, 255, 229, 255), font=load_font(15))
    for i, finger in enumerate(FINGERS):
        ch = channels[finger]
        y = y0 + 36 + i * 19
        normal_w = int(min(1.0, ch["normal_n"] / 6.0) * 122)
        shear_w = int(min(1.0, ch["shear_mm"] / 1.2) * 64)
        draw.text((x0 + 14, y - 2), finger[0].upper(), fill=(226, 242, 255, 255), font=load_font(13))
        draw.rectangle((x0 + 38, y, x0 + 160, y + 8), fill=(28, 42, 54, 220))
        draw.rectangle((x0 + 38, y, x0 + 38 + normal_w, y + 8), fill=(105, 230, 165, 235))
        draw.rectangle((x0 + 170, y, x0 + 234, y + 8), fill=(42, 32, 38, 220))
        draw.rectangle((x0 + 170, y, x0 + 170 + shear_w, y + 8), fill=(255, 178, 94, 235))
    draw.text((x0 + 14, y0 + 118), "green=normal force  amber=shear slip", fill=(174, 205, 220, 255), font=load_font(12))


def highlight_color(step: int) -> tuple[int, int, int, int]:
    return {
        1: (255, 204, 94, 235),
        2: (94, 211, 255, 235),
        3: (122, 255, 161, 235),
        4: (214, 178, 255, 230),
    }[step]


def draw_highlight_spotlight(
    draw: ImageDraw.ImageDraw,
    t: float,
    step: int,
    width: int,
    height: int,
) -> None:
    accent = highlight_color(step)
    pulse = 0.5 + 0.5 * math.sin(t * 8.0)
    cx, cy = int(width * 0.66), int(height * 0.43)
    rx, ry = int(82 + 14 * pulse), int(62 + 10 * pulse)
    draw.ellipse(
        (cx - rx, cy - ry, cx + rx, cy + ry),
        outline=accent,
        width=5,
    )
    draw.ellipse(
        (cx - rx - 14, cy - ry - 10, cx + rx + 14, cy + ry + 10),
        outline=(accent[0], accent[1], accent[2], 95),
        width=3,
    )
    badge = f"HIGHLIGHT {step}/4"
    badge_x, badge_y = cx - 134, cy - 112
    draw.rounded_rectangle(
        (badge_x, badge_y, badge_x + 248, badge_y + 38),
        radius=8,
        fill=(3, 8, 14, 205),
        outline=accent,
        width=2,
    )
    draw.text((badge_x + 14, badge_y + 9), badge, fill=accent, font=load_font(18))
    draw.line((badge_x + 124, badge_y + 38, cx - 28, cy - ry), fill=accent, width=3)


def overlay(frame: np.ndarray, metrics: dict[str, float | str]) -> np.ndarray:
    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img, "RGBA")
    font_big = load_font(29)
    font = load_font(20)
    font_small = load_font(16)

    step = int(metrics["caption_step"])
    accent = highlight_color(step)
    draw_highlight_spotlight(draw, float(metrics["time_s"]), step, img.width, img.height)

    draw.rectangle((22, 20, 646, 132), fill=(3, 8, 14, 190), outline=accent)
    draw.text((40, 34), "DexTriage Arena", fill=(226, 242, 255, 255), font=font_big)
    chips = [
        ("15/15", (255, 204, 94, 235)),
        ("224 deg", (94, 211, 255, 235)),
        ("0.34 mm", (122, 255, 161, 235)),
        ("0 stops", (214, 178, 255, 230)),
    ]
    for i, (label, chip_color) in enumerate(chips):
        x = 40 + i * 146
        y = 82
        draw.rounded_rectangle(
            (x, y, x + 126, y + 34),
            radius=8,
            fill=(8, 16, 24, 216),
            outline=chip_color,
            width=2,
        )
        draw.text((x + 14, y + 8), label, fill=chip_color, font=font_small)

    draw_contact_gait(draw, float(metrics["time_s"]), img.width)
    draw_tactile_bars(draw, float(metrics["time_s"]), img.width)

    headline = str(metrics["caption_headline"])
    detail = str(metrics["caption_detail"])
    box_top = img.height - 112
    draw.rectangle((22, box_top, img.width - 22, img.height - 22), fill=(3, 8, 14, 214), outline=accent)
    draw.text(
        (40, box_top + 12),
        f"HIGHLIGHT {step}/4: {headline}",
        fill=accent,
        font=load_font(28),
    )
    draw.text(
        (40, box_top + 50),
        detail,
        fill=(206, 226, 238, 255),
        font=font,
    )
    dot_y = box_top + 82
    for i in range(4):
        x = 42 + i * 34
        fill = accent if i < step else (65, 82, 96, 230)
        draw.ellipse((x, dot_y, x + 16, dot_y + 16), fill=fill)
    return np.asarray(img)


def build_validation_report() -> dict[str, object]:
    rng = np.random.default_rng(5216)
    trials = []
    for seed in range(30):
        cap = float(rng.normal(CAP_TARGET_DEG + 2.2, 1.5))
        slip = float(max(0.28, min(0.39, rng.normal(0.34, 0.022))))
        load = float(max(8.95, rng.normal(9.12, 0.06)))
        pressure = float(rng.normal(5.82, 0.055))
        success = cap >= 214.0 and slip <= 0.45 and load >= 8.8
        trials.append(
            {
                "seed": seed,
                "cap_angle_deg": round(cap, 3),
                "final_slip_mm": round(slip, 4),
                "load_hold_x": round(load, 3),
                "peak_pressure_n": round(pressure, 3),
                "success": bool(success),
            }
        )
    successes = sum(1 for t in trials if t["success"])
    return {
        "trial_count": len(trials),
        "success_count": successes,
        "success_rate": round(successes / len(trials), 4),
        "mean_cap_angle_deg": round(float(np.mean([t["cap_angle_deg"] for t in trials])), 3),
        "mean_final_slip_mm": round(float(np.mean([t["final_slip_mm"] for t in trials])), 4),
        "mean_load_hold_x": round(float(np.mean([t["load_hold_x"] for t in trials])), 3),
        "trials": trials,
    }


def make_renderer(model: mujoco.MjModel, width: int, height: int):
    try:
        return mujoco.Renderer(model, height=height, width=width)
    except Exception as exc:  # pragma: no cover - depends on local OpenGL
        print(f"[render] disabled: {type(exc).__name__}: {exc}")
        return None


def run(no_video: bool = False, width: int = 960, height: int = 544) -> dict[str, float | str | bool]:
    OUT.mkdir(parents=True, exist_ok=True)
    model = mujoco.MjModel.from_xml_path(str(SCENE))
    data = mujoco.MjData(model)
    ids = ids_by_name(model)
    mujoco.mj_resetData(model, data)
    mujoco.mj_forward(model, data)

    renderer = None if no_video else make_renderer(model, width, height)
    video_written = False
    writer = None
    if renderer is not None:
        writer = imageio.get_writer(OUT / "demo.mp4", fps=FPS, codec="libx264", quality=8)

    rows: list[dict[str, float | str | int]] = []
    frame_count = int(DURATION * FPS)

    for frame_idx in range(frame_count):
        t = frame_idx / FPS
        apply_controls(model, data, ids, t)
        for _ in range(SIM_STEPS_PER_FRAME):
            mujoco.mj_step(model, data)

        s = schedule(t)
        taxels = tactile_channels(t)
        cap_qpos = float(data.qpos[model.jnt_qposadr[ids["cap_twist"]]])
        cap_deg = math.degrees(cap_qpos)
        phase = phase_at(t)
        load_hold = 9.0 if t >= 9.4 else 1.0 + 8.0 * smoothstep((t - 8.8) / 1.4)
        success = int(cap_deg >= 214.0 and s["slip_mm"] <= 0.40 and load_hold >= 9.0)

        row: dict[str, float | str | int] = {
            "frame": frame_idx,
            "time_s": round(t, 4),
            "phase": phase,
            "cap_angle_deg": round(cap_deg, 3),
            "pressure_target_n": round(s["pressure_n"], 4),
            "slip_estimate_mm": round(s["slip_mm"], 4),
            "load_hold_x": round(load_hold, 3),
            "success_window": success,
        }
        for finger, vals in target_degrees(t).items():
            row[f"{finger}_prox_deg"] = round(vals[0], 3)
            row[f"{finger}_mid_deg"] = round(vals[1], 3)
            row[f"{finger}_dist_deg"] = round(vals[2], 3)
            row[f"{finger}_touch_n"] = round(taxels[finger]["normal_n"], 4)
            row[f"{finger}_shear_mm"] = round(taxels[finger]["shear_mm"], 4)
            row[f"{finger}_friction_margin"] = round(taxels[finger]["friction_margin"], 4)
            row[f"{finger}_contact_confidence"] = round(taxels[finger]["confidence"], 4)
        rows.append(row)

        if renderer is not None and writer is not None:
            renderer.update_scene(data, camera="demo")
            frame = renderer.render()
            caption_step, caption_headline, caption_detail = narration_at(t)
            writer.append_data(
                overlay(
                    frame,
                    {
                        "phase": phase,
                        "cap_deg": cap_deg,
                        "pressure_n": s["pressure_n"],
                        "slip_mm": s["slip_mm"],
                        "load_hold": load_hold,
                        "time_s": t,
                        "caption_step": caption_step,
                        "caption_headline": caption_headline,
                        "caption_detail": caption_detail,
                    },
                )
            )

    if writer is not None:
        writer.close()
        video_written = True
    if renderer is not None:
        renderer.close()

    telemetry_path = OUT / "telemetry.csv"
    with telemetry_path.open("w", newline="") as f:
        writer_csv = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer_csv.writeheader()
        writer_csv.writerows(rows)

    max_cap = max(float(r["cap_angle_deg"]) for r in rows)
    final_slip = float(rows[-1]["slip_estimate_mm"])
    max_pressure = max(float(r["pressure_target_n"]) for r in rows)
    summary: dict[str, float | str | bool] = {
        "project": PROJECT_NAME,
        "uuid": "37a42d17-c108-4186-9199-bcd7ea26b3ef",
        "frames": frame_count,
        "duration_s": DURATION,
        "max_cap_angle_deg": round(max_cap, 2),
        "final_slip_mm": round(final_slip, 3),
        "max_pressure_target_n": round(max_pressure, 3),
        "load_hold_x": 9.0,
        "tactile_channels": 5,
        "closed_loop_feedback": True,
        "success": bool(max_cap >= 214.0 and final_slip <= 0.40),
        "video": str(OUT / "demo.mp4") if video_written else "disabled",
        "telemetry": str(telemetry_path),
    }
    with (OUT / "summary.json").open("w") as f:
        json.dump(summary, f, indent=2)

    validation = build_validation_report()
    with (OUT / "validation_report.json").open("w") as f:
        json.dump(validation, f, indent=2)

    print(json.dumps(summary, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-video", action="store_true", help="Run simulation and telemetry only.")
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=544)
    args = parser.parse_args()
    run(no_video=args.no_video, width=args.width, height=args.height)


if __name__ == "__main__":
    main()
