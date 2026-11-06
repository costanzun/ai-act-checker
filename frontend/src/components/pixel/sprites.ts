// Original pixel-art mascots, drawn as character maps.
// Each map is a list of rows; every character is one pixel, "." is transparent.
// Portraits are 32x32 and symmetric: only the left 16 columns are written, `mirror()` builds the right half.
// No imports: this file is also loaded by Node scripts that render previews.

export const PALETTE: Record<string, string> = {
  K: "#141414", // outline
  // schnauzer, salt and pepper
  D: "#474c55",
  G: "#7e848e",
  L: "#b9bec6",
  W: "#f4f4f0",
  // doberman, black and tan
  B: "#2b2c36",
  H: "#4b4d60",
  T: "#d9822b",
  t: "#a65a1c",
  // shared accents
  P: "#ff8fa8",
  p: "#d9577a",
  w: "#ffffff",
  R: "#ee3b2b",
  r: "#a8180f",
  Y: "#ffd23f",
  y: "#c99a00",
  C: "#9fdcff",
  c: "#5aa7e0",
  S: "#e9e4d8",
  s: "#bdb5a2",
  Z: "#141414",
};

export interface Layer {
  rows: string[];
  x?: number;
  y?: number;
  /** CSS class on the layer group, used for frame animation (blink, wag, bob). */
  cls?: string;
}

export interface Sprite {
  w: number;
  h: number;
  layers: Layer[];
}

/** Left half -> full row: the left half followed by its reverse. */
export const mirror = (half: string[]) => half.map((r) => r + [...r].reverse().join(""));

/** Horizontal runs of one colour, so a 32x32 sprite needs a few hundred rects at most. */
export function runs(layer: Layer): { x: number; y: number; w: number; c: string }[] {
  const out: { x: number; y: number; w: number; c: string }[] = [];
  const ox = layer.x ?? 0;
  const oy = layer.y ?? 0;
  layer.rows.forEach((row, y) => {
    let x = 0;
    while (x < row.length) {
      const ch = row[x];
      if (ch === "." || ch === " " || !PALETTE[ch]) { x++; continue; }
      let e = x + 1;
      while (e < row.length && row[e] === ch) e++;
      out.push({ x: ox + x, y: oy + y, w: e - x, c: PALETTE[ch] });
      x = e;
    }
  });
  return out;
}

// ---------------------------------------------------------------- schnauzer

const SCHNAUZER_HALF = [
  "................",
  "................",
  "................",
  "........KKKKKKKK",
  "...KKKKKKKGGGGGG",
  "..KDGGGGGDKGGLGG",
  "..KDDDDDDDKGGGGG",
  "...KDDDDDDKGGGLG",
  "....KDDDDDKGLGGG",
  ".....KDDDKGGGGGG",
  ".....KDDKGWWWWGG",
  ".....KKKGWWWWWWL",
  ".....KGWWWLGGGGG",
  ".....KGLGGKWGGGG",
  ".....KGGGGKKGGLL",
  ".....KGGGGGGGLLL",
  ".....KGWWGGGLLKK",
  ".....KWWWWWLLKKK",
  "....KWWWWWWWLKKK",
  "....KLWWWWWWWWWK",
  "....KLWWWWWWWWLW",
  "....KLWWWWWWWWLW",
  "....KLLWWWWWWWWL",
  "....KDLWWWWWWWWW",
  "....KDLLWWWWWWWL",
  "...KDDKLWWWLWWWW",
  "..KDDDGKLWWWWWWW",
  ".KDDDGGGKLWKWWLW",
  ".KDDGGGGGKKGKWKK",
  "KDDGGGGLGGGGLGGG",
  "KDGGGGLGGGGGGLGG",
  "KDGGGLGGGGGGGGGG",
];

// ---------------------------------------------------------------- doberman

const DOBERMAN_HALF = [
  "......K.........",
  ".....KHK........",
  ".....KHBK.......",
  "....KHHBK.......",
  "....KHHBBK......",
  "....KHHBBK......",
  "....KHHBBBK.....",
  "....KHHBBBK.....",
  "....KHBBBBBKKKKK",
  "....KHBBBBBBBBBB",
  ".....KBBBBBBBHBB",
  ".....KBBBTTBBBBB",
  ".....KBBBBBBBBBB",
  ".....KBBBKWBBBBB",
  ".....KBBBKKBBBBB",
  "......KBTBBBBBBB",
  "......KTTTBBBBBB",
  "......KTTTTBBBBB",
  ".....KBKTTTTBBBB",
  ".....KBKTTTTTBBB",
  ".....KBBKTTTTTBB",
  ".....KBBKTTTTKKK",
  ".....KBBBKTTKHKK",
  ".....KBBBKTTTKKK",
  ".....KBBBBKTTTTK",
  ".....KBBBBKtTTTT",
  ".....KBBBBBKtttt",
  "....KBBBBBBBKKKK",
  "...KBBBBBTTBBBBB",
  "..KBBBBBTTTBBBBB",
  "..KBBBBBTTTBBBBB",
  ".KBBBBBBBBBBBBBB",
];

export const BASE = {
  schnauzer: mirror(SCHNAUZER_HALF),
  doberman: mirror(DOBERMAN_HALF),
};

/** A symmetric face patch: left half only, placed at row `y`. */
const face = (y: number, half: string[], cls?: string): Layer => ({ rows: mirror(half), y, cls });

// ---------------------------------------------------------------- expressions

const SCH = {
  blink: face(13, ["..........GG....", ".........KKK...."], "px-blink"),
  happyEyes: face(13, ["..........KK....", ".........KGGK..."]),
  closedEyes: face(13, ["..........GG....", ".........KKK...."]),
  sadEyes: face(12, [".........GGG....", "..........GG....", ".........KKK...."]),
  glasses: face(12, [
    ".......KKKKKKK..",
    "......KKCCKwCKKK",
    ".......KCCKKCK..",
    ".......KKKKKKK..",
  ]),
  glassesBlink: face(13, ["........CCCC....", "........CKKK...."], "px-blink"),
  smile: face(20, [
    "...........KKKKK",
    "...........KpPPP",
    "............KPPP",
    ".............KKK",
  ]),
  frown: face(21, ["............KKKK", "...........K...."]),
};

const DOB = {
  blink: face(13, [".........BB.....", ".........KK....."], "px-blink"),
  stern: face(11, [
    "........TTB.....",
    "..........TT....",
    ".........BB.....",
    ".........KK.....",
  ]),
  teeth: face(24, ["...........Kwwww", "............KKKK"]),
  alert: face(10, [
    ".........TT.....",
    ".........BB.....",
    "................",
    "........wKw.....",
    "........wKK.....",
  ]),
  worried: face(11, [
    ".........BTT....",
    "........TT......",
    ".........BB.....",
    ".........KK.....",
  ]),
  frown: face(24, ["............KKKK", "...........K...."]),
  calm: face(13, [".........BB.....", ".........KK....."]),
};

// ---------------------------------------------------------------- props

const STOP = [
  "...KKKKK...",
  "..KRRRRRK..",
  ".KRRRRRRRK.",
  "KRRRRRRRRRK",
  "KRwwwwwwwRK",
  "KRwwwwwwwRK",
  "KRRRRRRRRRK",
  ".KRRRRRRRK.",
  "..KRRRRRK..",
  "...KKKKK...",
];

const WARNING = [
  ".....K.....",
  "....KYK....",
  "....KYK....",
  "...KYKYK...",
  "...KYKYK...",
  "..KYYKYYK..",
  "..KYYYYYK..",
  ".KYYYKYYYK.",
  ".KYYYYYYYK.",
  "KKKKKKKKKKK",
];

const BUBBLE = [
  ".KKKKKKK.",
  "KwwwwwwwK",
  "KwwwKwwwK",
  "KwwwKwwwK",
  "KwwwKwwwK",
  "KwwwwwwwK",
  "KwwwKwwwK",
  "KwwwwwwwK",
  ".KKwKKKK.",
  "..KwK....",
  "..KK.....",
];

const ZZ = [
  "....wwwww",
  ".......w.",
  "......w..",
  ".....w...",
  "....wwwww",
  "www......",
  "..w......",
  ".w.......",
  "www......",
];

const SPARKLE = [".w.", "www", ".w."];
const DROP = [".K.", "KCK", "KCK", ".K."];

const MAGNIFIER = [
  "..KKK....",
  ".KCCwK...",
  "KCCCCwK..",
  "KCCCCCK..",
  "KCCCCCK..",
  ".KCCCK...",
  "..KKKKK..",
  "......KtK",
  ".......KK",
];

const PAPER = [
  "KKKKKKK..",
  "KSSSSSKK.",
  "KSKKKSSsK",
  "KSSSSSSSK",
  "KSKKKKKSK",
  "KSSSSSSSK",
  "KSKKKKSSK",
  "KsssssssK",
  "KKKKKKKKK",
];

// ---------------------------------------------------------------- full body (side view, facing right)

const SIDE_BODY = [
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "......KKKKKKKKKKKKKKKKKK..........",
  ".....KGDDDDDDDDDDDDDDDDGK.........",
  ".....KDDDDDDDDDDDDDDDLLLGK........",
  "....KGGGGLGGGLGGGLGGLLLLLK........",
  "....KGGGGGGDGGGDGGGDGLLLLK........",
  "....KGGGGGGGGGGGGGGGGLLLLK........",
  "....KGGGGGGGGGGGGGGGGLLLLK........",
  "....KGGGLLLLLLLLLLLLLLLLLK........",
  ".....KGGGKLLLLLLLLDDDLLLK.........",
  ".....KGGGKDDDKKKKKDDDLLLK.........",
  ".....KGGGKDDDK...KDDDLWLK.........",
  ".....KGGGKDDDK...KDDDLLWK.........",
  ".....KGGGKDDDK...KDDDLLLK.........",
  ".....KWWWWLLLLK..KLLLWWWWK........",
  "......KKKKKKKK....KKKKKKK.........",
];

const SIDE_BODY_PAW = [
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "......KKKKKKKKKKKKKKKKKK..........",
  ".....KGDDDDDDDDDDDDDDDDGK.........",
  ".....KDDDDDDDDDDDDDDDLLLGK........",
  "....KGGGGLGGGLGGGLGGLLLLLK........",
  "....KGGGGGGDGGGDGGGDGLLLLK....KKK.",
  "....KGGGGGGGGGGGGGGGGLLLLKKKKKWWWK",
  "....KGGGGGGGGGGGGGGGGLLLLLLLLLWWWK",
  "....KGGGLLLLLLLLLLLLLLLLLLLWLLWWWK",
  ".....KGGGKLLLLLLLLDDDLLLLKKKKKKKK.",
  ".....KGGGKDDDKKKKKDDDKKKK.........",
  ".....KGGGKDDDK...KDDDK............",
  ".....KGGGKDDDK...KDDDK............",
  ".....KGGGKDDDK...KDDDK............",
  ".....KWWWWLLLLK..KLLLLK...........",
  "......KKKKKKKK....KKKK............",
];

const SIDE_HEAD = [
  "....................KKKKKKKK......",
  "...................KGDDDDDDGK.....",
  "...................KDDDLGLGGK.....",
  "...................KDDDDWWWWWKK...",
  "...................KKDDDLWWWWWWKK.",
  "...................KGKDDGGKKGGGKK.",
  "..................KDGGKDKGKwLLLLK.",
  "..................KDGGGKGWWWWWWWWK",
  "..................KDDGGGGLWWWWLLWK",
  "..................KDDGGGGLWWWWWWWK",
  "..................KDDGGGGLWWWWWWWK",
  "..................KDDGGGGKWWWWWWWK",
  "...................KKKKKKKWKWKWKWK",
  "..........................K.K.K.K.",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
];

const SIDE_HEAD_DOWN = [
  "..................................",
  "....................KKKKKKKK......",
  "...................KGDDDDDDGK.....",
  "...................KDDDLGLGGK.....",
  "...................KDDDDWWWWWKK...",
  "...................KKDDDLWWWWWWKK.",
  "...................KGKDDGGKKGGGKK.",
  "..................KDGGKDKGKwLLLLK.",
  "..................KDGGGKGWWWWWWWWK",
  "..................KDDGGGGLWWWWLLWK",
  "..................KDDGGGGLWWWWWWWK",
  "..................KDDGGGGLWWWWWWWK",
  "...................KKKKKKKWWWWWWWK",
  ".........................KWKWKWKWK",
  "..........................K.K.K.K.",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
];

const SIDE_TAIL_A = [
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "....K.............................",
  "...KDK............................",
  "...KGDK...........................",
  "...KGGK...........................",
  "...KGGK...........................",
  "...KGGK...........................",
  "....KK............................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
];

const SIDE_TAIL_B = [
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..KK..............................",
  ".KDDK.............................",
  "..KGGK............................",
  "..KGGK............................",
  "..KGGGK...........................",
  "...KKK............................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
  "..................................",
];

const QMARK = [
  ".....KKKKKKKK.....",
  "...KKwwwwwwwwKK...",
  "..KwwwwwwwwwwwwKK.",
  ".KwwwwwwwwwwwwwwsK",
  "KwwwwwwsssswwwwwsK",
  "KwwwwwsKKKKswwwwsK",
  "KwwwwwsK...KwwwwsK",
  ".KsssssK..KwwwwwsK",
  "..KKKKK..KwwwwwssK",
  "........KwwwwwwsK.",
  ".......KwwwwwwsK..",
  "......KwwwwwwsK...",
  "......KwwwwwsK....",
  "......KwwwwwsK....",
  "......KwwwwwsK....",
  ".......KsssssK....",
  ".......KKKKKK.....",
  "......KwwwwwsK....",
  "......KwwwwwsK....",
  "......KwwwwwsK....",
  ".......KsssssK....",
  "........KKKKK.....",
];

// ---------------------------------------------------------------- scenes

/** Every state of the app has its own dog. */
export type SceneKey =
  | "prohibited" | "high_risk" | "limited_risk" | "minimal_risk" | "out_of_scope"
  | "questions" | "loading" | "error" | "hello_schnauzer" | "hello_doberman" | "logo";

const at = (rows: string[], x: number, y: number, cls?: string): Layer => ({ rows, x, y, cls });
const shift = (layers: Layer[], dx: number, dy: number): Layer[] =>
  layers.map((l) => ({ ...l, x: (l.x ?? 0) + dx, y: (l.y ?? 0) + dy }));
const dog = (k: keyof typeof BASE, ...extra: Layer[]): Layer[] => [{ rows: BASE[k] }, ...extra];

export const SCENES: Record<SceneKey, Sprite> = {
  // Doberman on guard: angled brows, narrowed eyes, teeth, a stop sign.
  prohibited: { w: 32, h: 32, layers: [...dog("doberman", DOB.stern, DOB.teeth), at(STOP, 21, 22)] },
  // Doberman on alert: brows up, eyes to the side, a warning sign.
  high_risk: { w: 32, h: 32, layers: [...dog("doberman", DOB.alert, DOB.blink), at(WARNING, 21, 22)] },
  // Schnauzer in reading glasses with something to tell you.
  limited_risk: { w: 32, h: 32, layers: [...shift(dog("schnauzer", SCH.glasses, SCH.glassesBlink), 0, 3), at(BUBBLE, 23, 0, "px-bob")] },
  // Happy schnauzer, eyes closed, tongue out.
  minimal_risk: { w: 32, h: 32, layers: [...shift(dog("schnauzer", SCH.happyEyes, SCH.smile), 0, 2), at(SPARKLE, 2, 3, "px-twinkle"), at(SPARKLE, 27, 1, "px-twinkle-2")] },
  // Not our business: the schnauzer naps.
  out_of_scope: { w: 32, h: 32, layers: [...shift(dog("schnauzer", SCH.closedEyes), 0, 3), at(ZZ, 22, 0, "px-float")] },
  // Something broke: worried doberman, eyes shut, a drop of sweat.
  error: { w: 32, h: 32, layers: [...dog("doberman", DOB.worried, DOB.frown), at(DROP, 27, 12, "px-bob")] },
  // Full body: the schnauzer raises a paw at a giant question mark.
  questions: {
    w: 54, h: 24,
    layers: [at(SIDE_TAIL_A, 2, 0, "px-f1"), at(SIDE_TAIL_B, 2, 0, "px-f2"), at(SIDE_BODY_PAW, 2, 0), at(SIDE_HEAD, 2, 0), at(QMARK, 35, 2)],
  },
  // Full body: the schnauzer sniffs through the law, tail going.
  loading: {
    w: 48, h: 24,
    layers: [
      at(SIDE_TAIL_A, 0, 0, "px-f1"), at(SIDE_TAIL_B, 0, 0, "px-f2"), at(SIDE_BODY, 0, 0),
      at(SIDE_HEAD, 0, 0, "px-s1"), at(SIDE_HEAD_DOWN, 0, 0, "px-s2"),
      at(PAPER, 36, 14), at(MAGNIFIER, 38, 4, "px-bob"),
    ],
  },
  hello_schnauzer: { w: 32, h: 32, layers: dog("schnauzer", SCH.blink) },
  hello_doberman: { w: 32, h: 32, layers: dog("doberman", DOB.blink) },
  logo: { w: 32, h: 32, layers: dog("schnauzer") },
};


