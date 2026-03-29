#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import List, Dict

import numpy as np
import matplotlib.pyplot as plt


# ---------- Global plotting style ----------
FIG_W = 8
FIG_H = 5.2
DPI = 300

TITLE_SIZE = 12
LABEL_SIZE = 11
TICK_SIZE = 10
LEGEND_SIZE = 9
TEXTBOX_SIZE = 9

LINE_PROFILE_WIDTH = 1.2
LINE_FIT_WIDTH = 2.0
MARKER_SIZE = 3.8


def parse_temperature_txt(filepath: str) -> List[Dict[str, np.ndarray]]:
    frames = []
    path = Path(filepath)

    with path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line or line.startswith("#"):
            i += 1
            continue

        parts = line.split()
        if len(parts) == 3:
            try:
                timestep = int(float(parts[0]))
                nchunks = int(float(parts[1]))
            except ValueError:
                i += 1
                continue

            x_vals = []
            temp_vals = []

            for j in range(i + 1, min(i + 1 + nchunks, len(lines))):
                chunk_line = lines[j].strip()
                if not chunk_line or chunk_line.startswith("#"):
                    continue

                chunk_parts = chunk_line.split()
                if len(chunk_parts) < 4:
                    continue

                try:
                    x = float(chunk_parts[1])
                    temp = float(chunk_parts[3])
                except ValueError:
                    continue

                x_vals.append(x)
                temp_vals.append(temp)

            if x_vals and temp_vals:
                frames.append(
                    {
                        "timestep": timestep,
                        "nchunks": nchunks,
                        "x": np.array(x_vals, dtype=float),
                        "temp": np.array(temp_vals, dtype=float),
                    }
                )

            i += 1 + nchunks
        else:
            i += 1

    if not frames:
        raise ValueError(f"No valid frames found in file: {filepath}")

    return frames


def linear_fit_in_range(x: np.ndarray, y: np.ndarray, fit_min: float, fit_max: float):
    mask = (x >= fit_min) & (x <= fit_max)
    x_fit = x[mask]
    y_fit = y[mask]

    if len(x_fit) < 2:
        raise ValueError(
            f"Not enough data points in fitting range {fit_min} to {fit_max} Å."
        )

    slope, intercept = np.polyfit(x_fit, y_fit, 1)

    y_pred = slope * x_fit + intercept
    ss_res = np.sum((y_fit - y_pred) ** 2)
    ss_tot = np.sum((y_fit - np.mean(y_fit)) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan

    return {
        "slope": slope,
        "intercept": intercept,
        "r2": r2,
        "x_fit": x_fit,
        "y_fit": y_fit,
        "y_pred": y_pred,
    }


def parse_output_prefix(prefix: str):
    """
    Try to extract L, T, and time info from output prefix.
    Example: L600_T900_4ns
    """
    L_text = ""
    T_text = ""
    time_text = ""

    parts = prefix.replace("-", "_").split("_")
    for p in parts:
        if p.startswith("L") and p[1:].isdigit():
            L_text = p[1:]
        elif p.startswith("T") and p[1:].isdigit():
            T_text = p[1:]
        elif p.endswith("ns") and p[:-2].isdigit():
            time_text = p

    return L_text, T_text, time_text


def make_title(prefix: str, mode_text: str) -> str:
    L_text, T_text, time_text = parse_output_prefix(prefix)

    pieces = []
    if L_text:
        pieces.append(f"L = {L_text} Å")
    if T_text:
        pieces.append(f"T = {T_text} K")
    if time_text:
        pieces.append(time_text)

    if pieces:
        return ", ".join(pieces) + f", {mode_text}"
    return f"{prefix}, {mode_text}"


def plot_profile_with_fit(x, y, fit_result, fit_min, fit_max, title, outpath):
    plt.figure(figsize=(FIG_W, FIG_H), dpi=DPI)

    plt.plot(
        x, y,
        marker="o",
        linestyle="-",
        linewidth=LINE_PROFILE_WIDTH,
        markersize=MARKER_SIZE,
        label="Temperature profile"
    )

    plt.plot(
        fit_result["x_fit"],
        fit_result["y_pred"],
        linestyle="--",
        linewidth=LINE_FIT_WIDTH,
        label="Linear fit"
    )

    plt.axvline(fit_min, linestyle=":", linewidth=1.2)
    plt.axvline(fit_max, linestyle=":", linewidth=1.2)

    textbox = (
        f"Slope = {fit_result['slope']:.6f} K/Å\n"
        f"Intercept = {fit_result['intercept']:.3f} K\n"
        f"R² = {fit_result['r2']:.4f}\n"
        f"Fit range: {fit_min:.0f}–{fit_max:.0f} Å"
    )

    plt.text(
        0.02, 0.98, textbox,
        transform=plt.gca().transAxes,
        fontsize=TEXTBOX_SIZE,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.9)
    )

    plt.xlabel("x (Å)", fontsize=LABEL_SIZE)
    plt.ylabel("Temperature (K)", fontsize=LABEL_SIZE)
    plt.title(title, fontsize=TITLE_SIZE)
    plt.xticks(fontsize=TICK_SIZE)
    plt.yticks(fontsize=TICK_SIZE)
    plt.legend(loc="lower left", fontsize=LEGEND_SIZE)
    plt.tight_layout()
    plt.savefig(outpath, dpi=DPI)
    plt.close()


def save_summary(
    summary_path: str,
    filepath: str,
    fit_min: float,
    fit_max: float,
    frames_count: int,
    last_timestep: int,
    n_avg: int,
    fit_last1,
    fit_last4avg,
):
    slope1_km = fit_last1["slope"] * 1.0e10
    slope4_km = fit_last4avg["slope"] * 1.0e10

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"File: {filepath}\n")
        f.write(f"Frames found: {frames_count}\n")
        f.write(f"Last timestep: {last_timestep}\n")
        f.write(f"Fitting range: {fit_min} to {fit_max} Å\n\n")

        f.write("[Last 1 frame]\n")
        f.write(f"Slope (K/Å): {fit_last1['slope']:.6f}\n")
        f.write(f"Slope (K/m): {slope1_km:.6e}\n")
        f.write(f"Intercept (K): {fit_last1['intercept']:.6f}\n")
        f.write(f"R^2: {fit_last1['r2']:.6f}\n\n")

        f.write("[Last 4-frame average]\n")
        f.write(f"Frames used: {n_avg}\n")
        f.write(f"Slope (K/Å): {fit_last4avg['slope']:.6f}\n")
        f.write(f"Slope (K/m): {slope4_km:.6e}\n")
        f.write(f"Intercept (K): {fit_last4avg['intercept']:.6f}\n")
        f.write(f"R^2: {fit_last4avg['r2']:.6f}\n")


def main():
    if len(sys.argv) != 5:
        print(
            "Usage:\n"
            "  python analyze_temp_profile_cli.py <Temperature.txt> <fit_min> <fit_max> <output_prefix>\n\n"
            "Example:\n"
            "  python analyze_temp_profile_cli.py Temperature.relax4_4ns_L600T900.txt 145 455 L600_T900_4ns"
        )
        sys.exit(1)

    filepath = sys.argv[1]
    fit_min = float(sys.argv[2])
    fit_max = float(sys.argv[3])
    output_prefix = sys.argv[4]

    frames = parse_temperature_txt(filepath)

    last_frame = frames[-1]
    n_avg = min(4, len(frames))
    last_frames = frames[-n_avg:]

    x_last1 = last_frame["x"]
    y_last1 = last_frame["temp"]

    x_last4 = last_frames[-1]["x"]
    y_last4avg = np.mean([fr["temp"] for fr in last_frames], axis=0)

    fit_last1 = linear_fit_in_range(x_last1, y_last1, fit_min, fit_max)
    fit_last4avg = linear_fit_in_range(x_last4, y_last4avg, fit_min, fit_max)

    slope1_km = fit_last1["slope"] * 1.0e10
    slope4_km = fit_last4avg["slope"] * 1.0e10

    print("=" * 68)
    print(f"File: {filepath}")
    print(f"Frames found: {len(frames)}")
    print(f"Last timestep: {last_frame['timestep']}")
    print(f"Fitting range: {fit_min} to {fit_max} Å")
    print("=" * 68)

    print("\n[Last 1 frame]")
    print(f"Slope (K/Å) : {fit_last1['slope']:.6f}")
    print(f"Slope (K/m) : {slope1_km:.6e}")
    print(f"Intercept(K): {fit_last1['intercept']:.6f}")
    print(f"R^2         : {fit_last1['r2']:.6f}")

    print("\n[Last 4-frame average]" if len(frames) >= 4 else "\n[Average of all available frames]")
    print(f"Frames used : {n_avg}")
    print(f"Slope (K/Å) : {fit_last4avg['slope']:.6f}")
    print(f"Slope (K/m) : {slope4_km:.6e}")
    print(f"Intercept(K): {fit_last4avg['intercept']:.6f}")
    print(f"R^2         : {fit_last4avg['r2']:.6f}")

    plot_profile_with_fit(
        x_last1,
        y_last1,
        fit_last1,
        fit_min,
        fit_max,
        title=make_title(output_prefix, "last frame"),
        outpath=f"{output_prefix}_last1_fit.png",
    )

    plot_profile_with_fit(
        x_last4,
        y_last4avg,
        fit_last4avg,
        fit_min,
        fit_max,
        title=make_title(output_prefix, f"last {n_avg}-frame average"),
        outpath=f"{output_prefix}_last4avg_fit.png",
    )

    summary_path = f"{output_prefix}_fit_summary.txt"
    save_summary(
        summary_path=summary_path,
        filepath=filepath,
        fit_min=fit_min,
        fit_max=fit_max,
        frames_count=len(frames),
        last_timestep=last_frame["timestep"],
        n_avg=n_avg,
        fit_last1=fit_last1,
        fit_last4avg=fit_last4avg,
    )

    print("\nSaved:")
    print(f"  {output_prefix}_last1_fit.png")
    print(f"  {output_prefix}_last4avg_fit.png")
    print(f"  {summary_path}")


if __name__ == "__main__":
    main()