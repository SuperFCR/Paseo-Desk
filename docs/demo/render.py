#!/usr/bin/env python3
"""Render the fictional storyboard on an explicitly selected compute machine.

Python standard library only; requires a headless Chromium browser and ffmpeg.
All browser state and intermediate frames stay inside OUTPUT/.render-work/.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

SCENES = 5
SECONDS_PER_SCENE = 6
WIDTH, HEIGHT = 1280, 720
MAX_BYTES = 10 * 1024 * 1024


def executable(value: str) -> str:
    found = shutil.which(value)
    if not found:
        raise argparse.ArgumentTypeError(f"Executable not found: {value}")
    return str(Path(found).resolve())


def run(command: list[str], *, directory: Path, env: dict[str, str], label: str) -> None:
    log = directory / f"{label}.log"
    with log.open("w", encoding="utf-8") as stream:
        try:
            result = subprocess.run(command, cwd=directory, env=env, stdout=stream,
                                    stderr=subprocess.STDOUT, timeout=180, check=False)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"{label} exceeded 180 seconds; log: {log}") from exc
    if result.returncode:
        tail = log.read_text(encoding="utf-8", errors="replace")[-3000:]
        raise RuntimeError(f"{label} failed ({result.returncode}):\n{tail}")


def check_png(path: Path) -> None:
    with path.open("rb") as stream:
        header = stream.read(24)
    if (len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n"
            or header[12:16] != b"IHDR"
            or struct.unpack(">II", header[16:24]) != (WIDTH, HEIGHT)):
        raise RuntimeError(f"Expected a {WIDTH}x{HEIGHT} PNG: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", required=True, type=executable,
                        help="Path to Chromium / Chrome headless shell")
    parser.add_argument("--ffmpeg", default="ffmpeg", type=executable)
    parser.add_argument("--source", type=Path, default=Path(__file__).with_name("index.html"))
    parser.add_argument("--output", type=Path, required=True,
                        help="Output directory on the target machine")
    parser.add_argument("--keep-work", action="store_true", help="Keep PNG frames and logs for review")
    parser.add_argument("--no-sandbox", action="store_true",
                        help="Only if required by an isolated target environment")
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    final = output / "paseo-phone-mac.mp4"
    if final.exists():
        parser.error(f"Output already exists; use a fresh output directory: {final}")
    work_root = output / ".render-work"
    work_root.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="run-", dir=work_root))
    env = os.environ.copy()
    for key, folder in (("HOME", "home"), ("TMPDIR", "tmp"), ("XDG_CACHE_HOME", "cache"),
                        ("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "data"),
                        ("XDG_RUNTIME_DIR", "runtime")):
        location = work / folder
        location.mkdir(mode=0o700)
        env[key] = str(location)
    env.update({"OMP_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "2", "MKL_NUM_THREADS": "2"})
    success = False
    try:
        for scene in range(1, SCENES + 1):
            frame = work / f"scene-{scene:02d}.png"
            command = [args.browser, "--headless", "--disable-gpu", "--disable-dev-shm-usage",
                       "--no-first-run", "--no-default-browser-check", "--disable-extensions",
                       "--disable-background-networking", "--disable-sync", "--hide-scrollbars",
                       "--force-device-scale-factor=1", "--font-render-hinting=none",
                       "--run-all-compositor-stages-before-draw", "--virtual-time-budget=1500",
                       f"--window-size={WIDTH},{HEIGHT}", f"--user-data-dir={work / 'chrome-profile'}",
                       f"--disk-cache-dir={work / 'chrome-cache'}", f"--screenshot={frame}"]
            if args.no_sandbox:
                command.append("--no-sandbox")
            command.append(f"{source.as_uri()}?scene={scene}&export=1")
            print(f"Rendering scene {scene}/{SCENES}…", flush=True)
            run(command, directory=work, env=env, label=f"chrome-{scene:02d}")
            check_png(frame)
        lines = ["ffconcat version 1.0"]
        for scene in range(1, SCENES + 1):
            lines.extend([f"file scene-{scene:02d}.png", f"duration {SECONDS_PER_SCENE}"])
        # Repeat the final frame so the concat demuxer honors its duration.
        lines.append(f"file scene-{SCENES:02d}.png")
        manifest = work / "scenes.ffconcat"
        manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
        encoded = work / "encoded.mp4"
        print("Encoding 30 seconds of silent H.264 video…", flush=True)
        run([args.ffmpeg, "-hide_banner", "-loglevel", "warning", "-nostdin", "-y",
             "-threads", "2", "-filter_threads", "1", "-filter_complex_threads", "1",
             "-f", "concat", "-safe", "1", "-i", str(manifest),
             "-map", "0:v:0", "-an", "-sn", "-dn", "-c:v", "libx264",
             "-preset", "medium", "-crf", "22", "-threads", "2", "-r", "24",
             "-pix_fmt", "yuv420p", "-t", str(SCENES * SECONDS_PER_SCENE),
             "-map_metadata", "-1", "-map_chapters", "-1", "-movflags", "+faststart",
             str(encoded)], directory=work, env=env, label="ffmpeg")
        size = encoded.stat().st_size
        if size <= 0 or size >= MAX_BYTES:
            raise RuntimeError(f"Unexpected video size ({size} bytes); expected 0–10 MiB.")
        encoded.replace(final)
        success = True
        print(f"Video: {final}\nSize: {size / 1024 / 1024:.2f} MiB")
        return 0
    except (OSError, RuntimeError) as exc:
        print(f"Render failed: {exc}\nWork retained for inspection: {work}", file=sys.stderr)
        return 1
    finally:
        if success and not args.keep_work:
            shutil.rmtree(work)
            try:
                work_root.rmdir()
            except OSError:
                pass
        elif success:
            print(f"Frames / logs: {work}")


if __name__ == "__main__":
    raise SystemExit(main())
