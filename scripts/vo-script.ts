// Writes VO-SCRIPT.md, the recording script for Jon, from src/data/voScript.ts
// and the planned shot times in src/data/sceneTimings.ts. The words live in
// voScript.ts only; this file is generated so the two can never disagree.
//
// npm run vo-script            write VO-SCRIPT.md
// tsx scripts/vo-script.ts --check   exit 1 if VO-SCRIPT.md is out of date (npm run check)

import fs from 'node:fs';
import path from 'node:path';
import {PLANNING_WPM, voById, words, type VoId} from '../src/data/voScript';
import {main, reel, type VideoPlan} from '../src/data/sceneTimings';

const OUT = path.join(import.meta.dirname, '..', 'VO-SCRIPT.md');
const seconds = (n: number) => Math.round((n * 60) / PLANNING_WPM);
const range = (a: string, b: string) => `${a} to ${b}`;

/** Paragraphs in a plan, in order, with the shots that carry each. */
const paragraphs = (video: VideoPlan) => {
	const out: {id: VoId; scene: VideoPlan['scenes'][number]; shots: string[]; start: string; end: string}[] = [];
	for (const scene of video.scenes) {
		for (const shot of scene.shots) {
			if (!shot.vo) continue;
			const last = out.at(-1);
			if (last && last.id === shot.vo) {
				last.shots.push(shot.id);
				last.end = shot.end;
			} else {
				out.push({id: shot.vo, scene, shots: [shot.id], start: shot.start, end: shot.end});
			}
		}
	}
	return out;
};

const block = (p: ReturnType<typeof paragraphs>[number]) => {
	const n = words(voById[p.id].text).length;
	const shots = p.shots.length > 1 ? `shots ${p.shots.join(', ')}` : `shot ${p.shots[0]}`;
	return [
		`**${p.id}** · ${n} words · about ${seconds(n)} s · under ${shots} (${range(p.start, p.end)})`,
		'',
		`> ${voById[p.id].text}`,
		'',
	];
};

const render = (): string => {
	const mainParas = paragraphs(main);
	const reelParas = paragraphs(reel);
	const count = (ps: typeof mainParas) => ps.reduce((a, p) => a + words(voById[p.id].text).length, 0);
	const mainWords = count(mainParas);
	const reelWords = count(reelParas);
	const tc = (s: number) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
	const test = voById['5a'];

	const lines: string[] = [
		'# Voiceover recording script: HYROX or ATHX?',
		'',
		'Generated from `src/data/voScript.ts` by `npm run vo-script`. Change the words there,',
		'never here: `npm run check` fails if this file falls out of date.',
		'',
		`Two reads. The 16:9 main video: ${mainWords} words in nine files, one per scene,`,
		`about ${tc(seconds(mainWords))} of speech at ${PLANNING_WPM} words a minute. The 9:16 cut-down:`,
		`${reelWords} words in one file, about ${tc(seconds(reelWords))}.`,
		'',
		'## First: a 30-second test',
		'',
		`Before the full session, record paragraph **5a** below (${words(test.text).length} words, about`,
		`${seconds(words(test.text).length)} s) in the room and on the mic you will use, and send it over. It goes`,
		'through the clean-up chain first, so a room or mic problem shows up while it can',
		'still be fixed. (The first test, on 29 October, shaped the advice below.)',
		'',
		'## How to record',
		'',
		'- **Mic close to the mouth.** A lav clipped to the chest about a hand-span below',
		'  the chin (a wired lav into the iPhone works), or a dynamic mic a few',
		'  centimetres away. The test, on the phone\'s own mic at a distance, came in',
		'  quiet, with the room only about 22 dB under the voice: a close mic gains',
		'  15 to 20 dB on that, more than any clean-up can.',
		'- **Switch off what hums.** The test picked up a steady low hum at about',
		'  100 Hz (typically a fridge, fan, heater, charger or light fitting). It sits',
		'  in the same range as the voice, so it cannot be filtered out cleanly.',
		'- **Lossless, not compressed.** WAV, 48 kHz, 24-bit, mono is ideal. On an',
		'  iPhone, set Voice Memos\' Audio Quality to Lossless; its .m4a files are fine.',
		'- One file per scene, named as shown, into `assets/audio/vo/` (or send them over).',
		"- Read each scene's paragraphs once, in order, with **two seconds of silence",
		'  between paragraphs**. The edit finds the paragraphs by those silences, so keep',
		'  any pause inside a paragraph well short of two seconds.',
		'- If a paragraph goes wrong, either record the whole scene file again, or record',
		'  just that paragraph as its own file named after it (for example `vo-6b.wav`),',
		'  which replaces it. Do not leave a second attempt inside the scene file.',
		'- Pick one way of saying ATHX and keep it for the whole read.',
		'- The times are targets, not limits: the cut follows your read.',
		'',
		'---',
		'',
		'# Main video (16:9)',
		'',
		'Scenes 2 and 11 have no voice.',
		'',
	];

	let currentScene = '';
	for (const p of mainParas) {
		if (p.scene.id !== currentScene) {
			currentScene = p.scene.id;
			const inScene = mainParas.filter((q) => q.scene.id === p.scene.id);
			const n = inScene.reduce((a, q) => a + words(voById[q.id].text).length, 0);
			lines.push(
				`## Scene ${p.scene.n} · ${p.scene.title} · \`${voById[p.id].file}\``,
				'',
				`${n} words, about ${seconds(n)} s. Lands in ${range(p.scene.shots[0]!.start, p.scene.shots.at(-1)!.end)}.`,
				'',
			);
		}
		lines.push(...block(p));
	}

	lines.push(
		'---',
		'',
		`# 9:16 cut-down · \`${voById.r1.file}\``,
		'',
		'Seven short lines, read in order in one file, with the same two-second gaps.',
		'They are written for the cut-down and differ from the main script.',
		'',
	);
	for (const p of reelParas) lines.push(...block(p));
	return lines.join('\n');
};

const text = render();
if (process.argv.includes('--check')) {
	const current = fs.existsSync(OUT) ? fs.readFileSync(OUT, 'utf8') : '';
	if (current !== text) {
		console.error('VO-SCRIPT.md is out of date: run npm run vo-script');
		process.exit(1);
	}
} else {
	fs.writeFileSync(OUT, text);
	console.log(`wrote ${path.relative(process.cwd(), OUT)}`);
}
