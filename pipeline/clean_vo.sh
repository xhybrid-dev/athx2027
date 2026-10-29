#!/usr/bin/env bash
# Clean the raw voiceover (scope 6.3), then bring each file to -16 LUFS with a
# two-pass loudnorm. The final mix goes to -14 LUFS later, at Gate 4.
#
# Usage: pipeline/clean_vo.sh [-o OUTDIR] [FILE.wav ...]
#        Defaults: every assets/audio/vo/*.wav, written to assets/audio/vo-clean/
#        under the same name, 48 kHz, 24-bit, mono.
#
# The chain is the scope's, with the de-esser's parameters made explicit
# (Gate 0 correction 10). Tune by ear at Gate 3 against Jon's real read: these
# are starting values, not settled ones.

set -euo pipefail
cd "$(dirname "$0")/.."

CHAIN="highpass=f=80,afftdn=nf=-25,deesser=i=0.4:m=0.5:f=0.5:s=o,acompressor=threshold=-18dB:ratio=3:attack=10:release=120,equalizer=f=3500:t=q:w=1:g=2,alimiter=limit=0.89"
# Voice stem target. True peak sits a little under the mix's -1 dBTP ceiling, so
# the stem has headroom when the music goes under it.
TARGET="I=-16:TP=-1.5:LRA=11"

OUT=assets/audio/vo-clean
if [[ "${1:-}" == "-o" ]]; then OUT="$2"; shift 2; fi
mkdir -p "$OUT"
shopt -s nullglob
FILES=("$@")
[[ ${#FILES[@]} -eq 0 ]] && FILES=(assets/audio/vo/*.wav)
if [[ ${#FILES[@]} -eq 0 ]]; then
	echo "No voiceover files in assets/audio/vo/ yet."
	exit 0
fi

for f in "${FILES[@]}"; do
	name=$(basename "$f")
	# Pass 1: run the chain and measure what loudnorm would have to do.
	measured=$(ffmpeg -hide_banner -nostats -i "$f" -ac 1 -af "$CHAIN,loudnorm=$TARGET:print_format=json" -f null - 2>&1 |
		python3 -c 'import json, re, sys; print(json.dumps(json.loads(re.findall(r"\{[^{}]*\}", sys.stdin.read())[-1])))')
	read -r mi mtp mlra mth off < <(python3 -c '
import json, sys
m = json.loads(sys.argv[1])
print(m["input_i"], m["input_tp"], m["input_lra"], m["input_thresh"], m["target_offset"])' "$measured")
	# Pass 2: the same chain, normalised linearly from the pass 1 measurement.
	# loudnorm works at 192 kHz internally, so resample back to 48 kHz.
	ffmpeg -hide_banner -nostats -loglevel error -y -i "$f" -ac 1 \
		-af "$CHAIN,loudnorm=$TARGET:measured_I=$mi:measured_TP=$mtp:measured_LRA=$mlra:measured_thresh=$mth:offset=$off:linear=true,aresample=48000" \
		-ar 48000 -c:a pcm_s24le "$OUT/$name"
	echo "  cleaned $name (chain output measured $mi LUFS, $mtp dBTP) -> $OUT/$name"
done
