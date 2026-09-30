import {createHash} from 'node:crypto';
import {readFileSync, writeFileSync} from 'node:fs';
import {inflateRawSync} from 'node:zlib';
import {disassemble, hasBatchim, romanize} from 'es-hangul';

// Builds backfire's region list from the Ministry of the Interior and Safety's
// legal-district code list (see the record beside the ZIP). With --check it
// compares the committed list and writes nothing.
const ZIP =
  'packages/backfire/vendor/legal-district-codes/legal-district-codes.zip';
const ZIP_SHA256 =
  '44b96f4a86ad102057463a05aae8842f1d706d3e9e69d2dfc409023bf75ca56b';
const OUT = 'packages/backfire/src/backfire_education/regions.json';
// Longest first, so 통합특별시 wins over 특별시. The value is the romanized
// unit joined with a hyphen; a null unit is spelled out by the detector.
const UNITS: [string, string | null][] = [
  ['통합특별시', null],
  ['특별자치시', null],
  ['특별자치도', null],
  ['특별시', null],
  ['광역시', null],
  ['직할시', null],
  ['도', 'do'],
  ['시', 'si'],
  ['군', 'gun'],
  ['구', 'gu'],
];
// es-hangul adds the compound-word ㄴ (안양 -> annyang), which place names
// do not have (Anyang), so also spell the text split at each such boundary.
const NIEUN = /^ㅇ[ㅣㅑㅕㅛㅠ]/;
function spellings(text: string) {
  const parts = [...text].reduce<string[]>(
    (all, char, i) => {
      if (i > 0 && hasBatchim(text[i - 1]) && NIEUN.test(disassemble(char)))
        all.push('');
      all[all.length - 1] += char;
      return all;
    },
    [''],
  );
  return new Set([romanize(text), parts.map(romanize).join('')]);
}
const cap = (text: string) =>
  [...spellings(text)].map(word => word[0].toUpperCase() + word.slice(1));

// The archive holds one deflated file; read it through the central directory.
function unzip(zip: Buffer) {
  const end = zip.lastIndexOf(Buffer.from([0x50, 0x4b, 5, 6]));
  const entry = zip.readUInt32LE(end + 16);
  if (zip.readUInt16LE(entry + 10) !== 8) throw new Error('not deflated');
  const local = zip.readUInt32LE(entry + 42);
  const start =
    local + 30 + zip.readUInt16LE(local + 26) + zip.readUInt16LE(local + 28);
  return inflateRawSync(
    zip.subarray(start, start + zip.readUInt32LE(entry + 20)),
  );
}

function forms(name: string) {
  const [korean, unit] = UNITS.find(([ending]) => name.endsWith(ending)) ?? [
    '',
    null,
  ];
  const stem = name.slice(0, name.length - korean.length);
  const result = [name];
  for (const spoken of cap(stem)) {
    if (unit) result.push(`${spoken}-${unit}`);
    if (stem.length >= 2) result.push(spoken);
  }
  if (korean === '도' && /[남북]$/.test(stem)) {
    const side = stem.endsWith('남') ? 'South' : 'North';
    result.push(...cap(stem.slice(0, -1)).map(rest => `${side} ${rest}`));
    result.push(...cap(stem[0] + stem.slice(-1)));
  }
  return result;
}

function build() {
  const zip = readFileSync(ZIP);
  if (createHash('sha256').update(zip).digest('hex') !== ZIP_SHA256)
    throw new Error(`${ZIP} does not match its pinned hash`);
  const names = new Set<string>();
  const text = new TextDecoder('euc-kr').decode(unzip(zip));
  for (const line of text.split(/\r?\n/).slice(1)) {
    const [code, full] = line.split('\t');
    if (!/^\d\d(00000000|\d\d\d00000)$/.test(code ?? '')) continue;
    const parts = full.trim().split(/\s+/);
    for (const part of parts.length === 1 ? parts : parts.slice(1))
      names.add(part);
  }
  const all = new Set([...names].flatMap(forms));
  return JSON.stringify([...all].sort(), null, 2) + '\n';
}

const args = process.argv.slice(2);
const out = args.find(arg => !arg.startsWith('--')) ?? OUT;
const generated = build();
if (!args.includes('--check')) {
  writeFileSync(out, generated);
} else if (readFileSync(out, 'utf8') !== generated) {
  console.error(`${out} is out of date; run npm run backfire:regions`);
  process.exitCode = 1;
}
