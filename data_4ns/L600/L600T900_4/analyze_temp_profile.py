import re
from pathlib import Path
from typing import List, Tuple, Dict

import numpy as np
import matplotlib.pyplot as plt


def parse_temperature_txt(filepath: str) -> List[Dict[str, np.ndarray]]:
    """
    Parse LAMMPS ave/chunk Temperature.txt style output.

    Returns a list of frames, each frame is a dict:
    {
        "timestep": int,
        "nchunks": int,
        "x": np.ndarray,
        "temp": np.ndarray
    }
    """
    frames = []
    path = Path(filepath)

    with path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip comments / empty lines
        if not line or line.startswith("#"):
            i += 1
            continue

        parts = line.split()
        # Expect header line like: timestep nchunks total-count
        if len(parts) == 3:
            try:
                timestep = int(float(parts[0]))
                nchunks = int(float(parts[1]))
                # total_count = float(parts[2])  # not used
            except ValueError:
                i += 1
                continue

            x_vals = []
            temp_vals = []

            # Read next nchunks lines
            for j in range(i + 1, min(i + 1 + nchunks, len(lines))):
                chunk_line = lines[j].strip()
                if not chunk_line or chunk_line.startswith("#"):
                    continue
                chunk_parts = chunk_line.split()
                if len(chunk_parts) < 4:
                    continue

                # Format:
                # chunk_id, coord1, ncount, v_atemp
                try:
                    x = float(chunk_parts[1])
                    temp = float(chunk_parts[3])
                except ValueError:
                    continue

                x_vals.append(x)
                temp_vals.append(temp)

            if x_vals and temp_vals:
                frames.append({
                    "timestep": timestep,
                    "nchunks": nchunks,
                    "x": np.array(x_vals, dtype=float),
                    "temp": np.array(temp_vals, dtype=float),
                })

            i += 1 + nchunks
        else:
            i += 1

    if not frames:
        raise ValueError(f"No valid frames found in file: {filepath}")

    return frames


def linear_fit_in_range(x: np.ndarray, y: np.ndarray, fit_min: float, fit_max: float) -> Dict[str, float]:
    """
    Perform linear fit y = m*x + b within fit_min <= x <= fit_max.
    """
    mask = (x >= fit_min) & (x <= fit_max)
    x_fit = x[mask]
    y_fit = y[mask]

    if len(x_fit) < 2:
        raise ValueError("Not enough data points in fitting range.")

    coeffs = np.polyfit(x_fit, y_fit, 1)
    slope, intercept = coeffs

    # R^2
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


def plot_profile_with_fit(
    x: np.ndarray,
    y: np.ndarray,
    fit_result: Dict[str, float],
    title: str,
    outpath: str
) -> None:
    """
    Plot temperature profile and fitted line.
    """
    plt.figure(figsize=(8, 5))
    plt.plot(x, y, marker="o", linestyle="-", linewidth=1, markersize=4, label="Temperature profile")
    plt.plot(
        fit_result["x_fit"],
        fit_result["y_pred"],
        linestyle="--",
        linewidth=2,
        label=(
            f'Fit: y = {fit_result["slope"]:.6f} x + {fit_result["intercept"]:.3f}\n'
            f'R² = {fit_result["r2"]:.4f}'
        )
    )
    plt.xlabel("x (Å)")
    plt.ylabel("Temperature (K)")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(outpath, dpi=300)
    plt.close()


def analyze_temperature_file(
    filepath: str,
    fit_min: float,
    fit_max: float,
    output_prefix: str = None
) -> None:
    """
    Main analysis:
    - parse file
    - analyze last frame
    - analyze average of last 4 frames
    - print results
    - save plots
    """
    frames = parse_temperature_txt(filepath)

    if output_prefix is None:
        output_prefix = Path(filepath).stem

    last_frame = frames[-1]
    n_avg = min(4, len(frames))
    last_frames = frames[-n_avg:]

    # Assume x grid is same across frames
    x_last1 = last_frame["x"]
    y_last1 = last_frame["temp"]

    x_last4 = last_frames[-1]["x"]
    y_last4avg = np.mean([fr["temp"] for fr in last_frames], axis=0)

    fit_last1 = linear_fit_in_range(x_last1, y_last1, fit_min, fit_max)
    fit_last4avg = linear_fit_in_range(x_last4, y_last4avg, fit_min, fit_max)

    # Print summary
    print("=" * 60)
    print(f"File: {filepath}")
    print(f"Total frames found: {len(frames)}")
    print(f"Fitting range: {fit_min} to {fit_max} Å")
    print("=" * 60)

    print("\n[Last 1 frame]")
    print(f"Timestep: {last_frame['timestep']}")
    print(f"Slope     = {fit_last1['slope']:.6f} K/Å")
    print(f"Intercept = {fit_last1['intercept']:.6f} K")
    print(f"R^2       = {fit_last1['r2']:.6f}")

    print("\n[Last 4-frame average]" if len(frames) >= 4 else "\n[Average of all available frames]")
    print(f"Frames used: {n_avg}")
    print(f"Slope     = {fit_last4avg['slope']:.6f} K/Å")
    print(f"Intercept = {fit_last4avg['intercept']:.6f} K")
    print(f"R^2       = {fit_last4avg['r2']:.6f}")

    # Save plots
    plot_profile_with_fit(
        x_last1,
        y_last1,
        fit_last1,
        title=f"{output_prefix} - Last frame",
        outpath=f"{output_prefix}_last1_fit.png",
    )

    plot_profile_with_fit(
        x_last4,
        y_last4avg,
        fit_last4avg,
        title=f"{output_prefix} - Last {n_avg} frame average",
        outpath=f"{output_prefix}_last4avg_fit.png",
    )

    print("\nSaved plots:")
    print(f"  {output_prefix}_last1_fit.png")
    print(f"  {output_prefix}_last4avg_fit.png")


if __name__ == "__main__":
    # ===== USER SETTINGS =====
    filepath = "Temperature.txt"
    fit_min = 145.0
    fit_max = 455.0
    output_prefix = "L600_T900_4ns"
    # =========================

    analyze_temperature_file(
        filepath=filepath,
        fit_min=fit_min,
        fit_max=fit_max,
        output_prefix=output_prefix
    )