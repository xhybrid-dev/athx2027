#!/usr/bin/env bash
# Clean the raw voiceover (scope 6.3) and bring each file to -16 LUFS, true peak
# at or below -1.5 dBTP. The final mix goes to -14 LUFS later, at Gate 4.
#
# Usage: pipeline/clean_vo.sh [-o OUTDIR] [FILE ...]
#        Defaults: every WAV, M4A, FLAC or AIFF in assets/audio/vo/, written to
#        assets/audio/vo-clean/<name>.wav, 48 kHz, 24-bit, mono.
#
# The scope's chain, with what the first test recording (EDIT-LOG, Gate 1) showed
# it needs to work on a real file:
#   1. Mono first. Everything runs on the mono downmix, so what is measured is what
#      is written. (Phones record two identical channels, which read 3 dB louder.)
#   2. Gain staging. Each file is brought to -14 LUFS before the chain, so the
#      compressor's fixed -18 dB threshold sits just under the voice whatever
#      level the recording came in at.
#   3. The noise reducer's floor (afftdn nf) is measured per file, not fixed at
#      -25 dB: set 20 dB above the real noise, it strips detail from the voice.
#   4. A gentle expander after the noise reducer, 8 dB above the measured noise:
#      pauses drop 10 dB, speech is untouched. Compression lifts pauses along
#      with the voice, and without it the hiss between phrases sits only about
#      20 dB under the speech.
#   5. alimiter with level=disabled. By default it turns its output back up by
#      1/limit, so limit=0.89 alone lets peaks return to 0 dBFS.
#   6. Make-up gain to -16 LUFS, then a 4x oversampled limiter for the true-peak
#      ceiling. The gain is measured, applied, and re-measured (up to three
#      times) so the limiter's trim does not leave the file short of -16.
# The de-esser keeps its explicit parameters (Gate 0 correction 10). Everything
# here is a starting point to tune by ear against Jon's real read.

set -euo pipefail
cd "$(dirname "$0")/.."

PRE_TARGET=-14  # LUFS into the chain
TARGET_I=-16    # LUFS out: the voice stem
CEILING_DB=-1.7 # sample-peak limit at 4x oversampling, for a -1.5 dBTP true peak
MONO="aformat=channel_layouts=mono"
CHAIN_REST="deesser=i=0.4:m=0.5:f=0.5:s=o,acompressor=threshold=-18dB:ratio=3:attack=10:release=120,equalizer=f=3500:t=q:w=1:g=2,alimiter=limit=0.89:level=disabled"

OUT=assets/audio/vo-clean
if [[ "${1:-}" == "-o" ]]; then OUT="$2"; shift 2; fi
mkdir -p "$OUT"
shopt -s nullglob nocaseglob
FILES=("$@")
[[ ${#FILES[@]} -eq 0 ]] && FILES=(assets/audio/vo/*.{wav,m4a,flac,aif,aiff})
if [[ ${#FILES[@]} -eq 0 ]]; then
	echo "No voiceover files in assets/audio/vo/ yet."
	exit 0
fi

loudness() { # "I TP" of a filter graph's output: integrated LUFS and true peak dBTP
	ffmpeg -hide_banner -nostats -i "$1" -af "$2,ebur128=peak=true" -f null - 2>&1 |
		awk '/^ *I:/{i=$2} /^ *Peak:/{p=$2} END{print i, p}'
}
calc() { python3 -c "print(f'{$1:.2f}')"; }

for f in "${FILES[@]}"; do
	name=$(basename "${f%.*}").wav
	read -r in_i noise < <(python3 pipeline/analyse_vo.py --levels "$f")
	pre=$(calc "$PRE_TARGET - ($in_i)")
	nf=$(python3 -c "print(min(-20, max(-80, round($noise + $pre))))")
	ceiling=$(python3 -c "print(f'{10 ** ($CEILING_DB / 20):.4f}')")
	gate=$(python3 -c "print(f'{10 ** (($nf + 8) / 20):.5f}')")
	chain="$MONO,volume=${pre}dB,highpass=f=80,afftdn=nf=${nf},agate=threshold=${gate}:range=0.316:ratio=3:attack=5:release=200,$CHAIN_REST"
	limit="aresample=192000,alimiter=limit=${ceiling}:level=disabled:attack=1:release=50,aresample=48000"

	read -r chain_i chain_tp < <(loudness "$f" "$chain")
	gain=$(calc "$TARGET_I - ($chain_i)")
	for _ in 1 2 3; do
		read -r out_i out_tp < <(loudness "$f" "$chain,volume=${gain}dB,$limit")
		python3 -c "import sys; sys.exit(0 if abs($out_i - ($TARGET_I)) <= 0.2 else 1)" && break
		gain=$(calc "$gain + $TARGET_I - ($out_i)")
	done
	ffmpeg -hide_banner -nostats -loglevel error -y -i "$f" -af "$chain,volume=${gain}dB,$limit" \
		-ar 48000 -c:a pcm_s24le "$OUT/$name"
	trim=$(python3 -c "print(f'{max(0, $chain_tp + $gain - ($CEILING_DB)):.1f}')")
	printf '  cleaned %s: in %s LUFS, noise %s dBFS | pre-gain %+.1f dB, nf %s dB, make-up %+.1f dB, limiter trims peaks by up to %s dB | out %s LUFS, %s dBTP -> %s/%s\n' \
		"$(basename "$f")" "$in_i" "$noise" "$pre" "$nf" "$gain" "$trim" "$out_i" "$out_tp" "$OUT" "$name"
done
