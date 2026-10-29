"""Measure a voiceover recording: what a listener would hear as problems.

Usage: python3 pipeline/analyse_vo.py FILE [FILE ...]

Stdlib only; FFmpeg decodes. For each file, from 10 ms frames of the mono mix:

- speech and pauses: frames more than 12 dB over the quietest decile are speech;
  pauses are runs of at least 250 ms without speech;
- noise floor: the median level inside pauses, away from their edges;
- room decay: after each phrase ends, how fast the level falls, as the time to
  drop 20 dB, tripled to an RT60-style figure. Speech is not an impulse, so this
  is a guide to how live the room sounds, not an acoustic measurement;
- sibilance: the 5 to 10 kHz band against the whole signal, during speech, and
  its loudest 50 ms burst;
- bandwidth: the highest band with real energy (lossy formats cut the top off);
- clipping: samples at or above -0.1 dBFS.
"""

import array
import math
import statistics
import subprocess
import sys

RATE = 48000
FRAME = RATE // 100  # 10 ms


def decode(path: str, af: str = "") -> array.array:
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(RATE)]
    if af:
        cmd += ["-af", af]
    cmd += ["-f", "f32le", "-"]
    data = array.array("f")
    data.frombytes(subprocess.run(cmd, capture_output=True, check=True).stdout)
    return data


def frame_db(x: array.array, frame: int = FRAME) -> list[float]:
    out = []
    for i in range(0, len(x) - frame + 1, frame):
        s = sum(v * v for v in x[i : i + frame]) / frame
        out.append(10 * math.log10(s) if s > 1e-12 else -120.0)
    return out


def runs(flags: list[bool], value: bool) -> list[tuple[int, int]]:
    out, start = [], None
    for i, f in enumerate(flags + [not value]):
        if f == value and start is None:
            start = i
        elif f != value and start is not None:
            out.append((start, i))
            start = None
    return out


def analyse(path: str) -> None:
    x = decode(path)
    db = frame_db(x)
    quiet = sorted(db)[len(db) // 10]
    speech = [d > quiet + 12 for d in db]
    pauses = [(a, b) for a, b in runs(speech, False) if b - a >= 25]
    inner = [db[i] for a, b in pauses for i in range(a + 5, b - 5)]
    floor = statistics.median(inner) if inner else float("nan")
    talk = [d for d, s in zip(db, speech) if s]
    level = statistics.median(talk)
    first = speech.index(True)
    last = len(speech) - speech[::-1].index(True)

    # Decay after each phrase end: frames from the last speech frame until the
    # level is 20 dB lower, where the floor leaves room to see 20 dB.
    decays = []
    for a, b in pauses:
        if a == 0:
            continue
        start = db[a - 1]
        if start - floor < 26:
            continue
        for k in range(a, b):
            if db[k] <= start - 20:
                decays.append((k - a + 1) * 10)
                break
    t20 = statistics.median(decays) if decays else None

    band = decode(path, "highpass=f=5000,highpass=f=5000,lowpass=f=10000,lowpass=f=10000")
    bdb = frame_db(band)
    sib = [b - d for b, d, s in zip(bdb, db, speech) if s]
    sib_burst = max(
        (statistics.mean(bdb[i : i + 5]) - statistics.mean(db[i : i + 5]) for i in range(len(db) - 5) if speech[i]),
        default=float("nan"),
    )

    top = None
    for lo in (20000, 18000, 16000, 14000, 12000, 10000):
        hi = decode(path, f"highpass=f={lo},highpass=f={lo}")
        e = statistics.mean(d for d, s in zip(frame_db(hi), speech) if s)
        if e > level - 50:
            top = lo
            break
    peak = max(abs(v) for v in x)
    clipped = sum(1 for v in x if abs(v) >= 0.9886)  # -0.1 dBFS

    print(f"\n{path}")
    print(f"  duration {len(x) / RATE:.1f} s; speech from {first / 100:.2f} s to {last / 100:.2f} s")
    print(f"  pauses of 250 ms or more inside the speech: " + ", ".join(f"{(b - a) / 100:.2f} s at {a / 100:.2f}" for a, b in pauses if first < a < last))
    print(f"  speech level (median 10 ms frame) {level:.1f} dBFS; noise floor in pauses {floor:.1f} dBFS; gap {level - floor:.1f} dB")
    print(f"  room decay: {'20 dB in %d ms after phrase ends (RT60-style about %.2f s), from %d phrase ends' % (t20, 3 * t20 / 1000, len(decays)) if t20 else 'not measurable (floor too close)'}")
    print(f"  sibilance (5-10 kHz against the whole, in speech): median {statistics.median(sib):.1f} dB, loudest 50 ms burst {sib_burst:+.1f} dB")
    print(f"  bandwidth: energy up to about {top // 1000 if top else '<10'} kHz")
    print(f"  peak {20 * math.log10(peak):.1f} dBFS; samples at or above -0.1 dBFS: {clipped}")


def levels(path: str) -> tuple[float, float]:
    """Integrated loudness (LUFS) and background noise (dBFS: the quietest tenth of
    50 ms frames), for clean_vo.sh to set its gain staging and noise reduction."""
    ebu = subprocess.run(
        # Downmix inside the graph, before measuring: "-ac 1" alone would only
        # apply after it, and two identical stereo channels read 3 dB louder.
        ["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "aformat=channel_layouts=mono,ebur128", "-f", "null", "-"],
        capture_output=True,
        text=True,
    ).stderr
    integrated = float([line for line in ebu.splitlines() if line.strip().startswith("I:")][-1].split()[1])
    db = sorted(frame_db(decode(path), frame=RATE // 20))
    return integrated, db[len(db) // 10]


if __name__ == "__main__":
    if sys.argv[1:2] == ["--levels"]:
        i, noise = levels(sys.argv[2])
        print(f"{i:.1f} {noise:.1f}")
    else:
        for p in sys.argv[1:]:
            analyse(p)
