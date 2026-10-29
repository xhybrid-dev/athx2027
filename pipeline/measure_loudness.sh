#!/usr/bin/env bash
# Loudness report (EBU R128, via FFmpeg's ebur128 with true peak): integrated
# loudness, loudness range and true peak for each file.
#
# Usage: pipeline/measure_loudness.sh FILE ...
#        pipeline/measure_loudness.sh --target -14 -1 FILE ...
#            also fail any file whose integrated loudness is more than 1 LU from
#            the target, or whose true peak is above the ceiling (scope 8: the
#            final mix is -14 LUFS +/- 1, true peak at or below -1 dBTP).

set -uo pipefail

TARGET_I="" CEILING=""
if [[ "${1:-}" == "--target" ]]; then TARGET_I="$2"; CEILING="$3"; shift 3; fi
[[ $# -eq 0 ]] && { sed -n '2,10p' "$0"; exit 2; }

status=0
printf '  %-40s %10s %8s %10s\n' file "LUFS (I)" "LRA" "dBTP"
for f in "$@"; do
	summary=$(ffmpeg -hide_banner -nostats -i "$f" -filter_complex ebur128=peak=true -f null - 2>&1 | sed -n '/Summary:/,$p')
	i=$(awk '/^ *I:/{print $2; exit}' <<<"$summary")
	lra=$(awk '/^ *LRA:/{print $2; exit}' <<<"$summary")
	tp=$(awk '/^ *Peak:/{print $2; exit}' <<<"$summary")
	verdict=""
	if [[ -n "$TARGET_I" ]]; then
		verdict=$(python3 -c '
import sys
i, tp, target, ceiling = map(float, sys.argv[1:])
problems = []
if abs(i - target) > 1: problems.append(f"loudness {i:+.1f} is outside {target:+.0f} +/- 1")
if tp > ceiling: problems.append(f"true peak {tp:+.1f} is above {ceiling:+.0f}")
print("FAIL: " + "; ".join(problems) if problems else "ok")' "$i" "$tp" "$TARGET_I" "$CEILING")
		[[ "$verdict" == ok ]] || status=1
	fi
	printf '  %-40s %10s %8s %10s  %s\n' "$(basename "$f")" "$i" "$lra" "$tp" "$verdict"
done
exit $status
