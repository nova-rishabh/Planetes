/**
 * Fallback source for when IRSA's search (TAP) is down: the SPHEREx DR1 all-sky spectral cube in NASA's open-data copy
 * on AWS (bucket nasa-irsa-spherex, dr1/hips5_cube). It is a HiPS cube: HEALPix order-5 tiles, 512 × 512 pixels
 * (about 9.9″ each) × 102 wavelength planes, all SPHEREx visits combined, in MJy/sr. The bucket allows browser access
 * (Access-Control-Allow-Origin: *) and byte ranges, so only the few kilobytes around a position are fetched.
 *
 * Checked by hand against astropy: tile and pixel from the nested HEALPix index match the tile's own HPX WCS
 * (column = iy mod 512, row = 511 − ix mod 512) at five positions across the sky.
 */

export const CUBE_BASE = "https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/dr1/hips5_cube/hips_20261026/Norder5";
const TILE_ORDER = 5;
const TILE_PX = 512;
const PLANE_BYTES = TILE_PX * TILE_PX * 4;
export const PIXEL_ARCSEC = 9.89;

/** The 102 SPHEREx channels of the cube (its SPECTRAL_CHANNELS table): detector and central wavelength in µm. */
export const CHANNEL_DETECTOR = [
  1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3,
  3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
  5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6,
] as const;
export const CHANNEL_UM: readonly number[] = [
  0.753, 0.771, 0.79, 0.809, 0.828, 0.848, 0.868, 0.889, 0.91, 0.932, 0.955, 0.978, 1.001, 1.025, 1.05, 1.075, 1.102,
  1.113, 1.139, 1.167, 1.195, 1.224, 1.254, 1.284, 1.315, 1.346, 1.378, 1.412, 1.446, 1.481, 1.517, 1.554, 1.592,
  1.631, 1.656, 1.695, 1.735, 1.775, 1.818, 1.861, 1.905, 1.949, 1.995, 2.041, 2.089, 2.139, 2.189, 2.24, 2.292,
  2.345, 2.399, 2.445, 2.506, 2.575, 2.646, 2.719, 2.794, 2.871, 2.951, 3.033, 3.118, 3.204, 3.293, 3.383, 3.476,
  3.57, 3.667, 3.768, 3.833, 3.867, 3.901, 3.935, 3.97, 4.005, 4.04, 4.076, 4.112, 4.148, 4.184, 4.22, 4.257, 4.294,
  4.331, 4.368, 4.405, 4.435, 4.467, 4.5, 4.533, 4.566, 4.6, 4.635, 4.669, 4.704, 4.739, 4.773, 4.808, 4.843, 4.879,
  4.915, 4.951, 4.988,
];

/** Nested HEALPix pixel of (ra, dec) at the given order, as face and in-face (ix, iy). */
export function ang2xyf(order: number, raDeg: number, decDeg: number): { face: number; ix: number; iy: number } {
  const nside = 2 ** order;
  const z = Math.sin((decDeg * Math.PI) / 180);
  const za = Math.abs(z);
  let phi = (raDeg * Math.PI) / 180;
  phi = ((phi % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
  const tt = (phi * 2) / Math.PI; // [0, 4)
  if (za <= 2 / 3) {
    const t1 = nside * (0.5 + tt);
    const t2 = nside * z * 0.75;
    const jp = Math.floor(t1 - t2);
    const jm = Math.floor(t1 + t2);
    const ifp = Math.floor(jp / nside);
    const ifm = Math.floor(jm / nside);
    const face = ifp === ifm ? (ifp | 4) : ifp < ifm ? ifp : ifm + 8;
    return { face, ix: jm & (nside - 1), iy: nside - (jp & (nside - 1)) - 1 };
  }
  const ntt = Math.min(3, Math.floor(tt));
  const tp = tt - ntt;
  const tmp = nside * Math.sqrt(3 * (1 - za));
  const jp = Math.min(nside - 1, Math.floor(tp * tmp));
  const jm = Math.min(nside - 1, Math.floor((1 - tp) * tmp));
  return z >= 0 ? { face: ntt, ix: nside - jm - 1, iy: nside - jp - 1 } : { face: ntt + 8, ix: jp, iy: jm };
}

function interleave(x: number, y: number, bits: number): number {
  let v = 0;
  for (let i = 0; i < bits; i++) v += (((x >> i) & 1) << (2 * i)) + (((y >> i) & 1) << (2 * i + 1));
  return v;
}

/** Which cube tile holds (ra, dec), and the pixel (row from the bottom, column) inside it. */
export function locate(raDeg: number, decDeg: number): { tile: number; row: number; col: number } {
  const sub = Math.log2(TILE_PX); // 9
  const { face, ix, iy } = ang2xyf(TILE_ORDER + sub, raDeg, decDeg);
  const tile = face * 4 ** TILE_ORDER + interleave(ix >> sub, iy >> sub, TILE_ORDER);
  return { tile, row: TILE_PX - 1 - (ix & (TILE_PX - 1)), col: iy & (TILE_PX - 1) };
}

export function tileUrl(tile: number): string {
  return `${CUBE_BASE}/Dir${Math.floor(tile / 10000) * 10000}/Npix${tile}_cube.fits`;
}

async function range(url: string, start: number, end: number, signal?: AbortSignal): Promise<ArrayBuffer> {
  const res = await fetch(url, { headers: { Range: `bytes=${start}-${end}` }, signal });
  if (res.status !== 206 && res.status !== 200) throw new Error(`HTTP ${res.status}`);
  return res.arrayBuffer();
}

/** Byte offset where the IMAGE extension's data starts (after the primary and image headers). */
async function imageOffset(url: string, signal?: AbortSignal): Promise<number> {
  const head = new TextDecoder("latin1").decode(await range(url, 0, 2880 * 5 - 1, signal));
  const ext = head.indexOf("XTENSION", 2880);
  if (ext < 0) throw new Error("No image extension");
  for (let i = ext; i + 80 <= head.length; i += 80) {
    if (head.startsWith("END", i) && head.slice(i + 3, i + 80).trim() === "") return ext + Math.ceil((i - ext + 80) / 2880) * 2880;
  }
  throw new Error("Header not found");
}

async function pool<T>(jobs: (() => Promise<T>)[], n: number): Promise<T[]> {
  const out: T[] = new Array(jobs.length);
  let next = 0;
  await Promise.all(
    Array.from({ length: Math.min(n, jobs.length) }, async () => {
      while (next < jobs.length) {
        const k = next++;
        out[k] = await jobs[k]!();
      }
    }),
  );
  return out;
}

export interface CubeCutout {
  tile: number;
  /** Pixel of the requested position inside the cutout (x from the left, y from the top). */
  target: { x: number; y: number };
  width: number;
  height: number;
  /** Three planes for a colour image (blue, green, red), row-major from the top, MJy/sr. */
  planes: { channel: number; um: number; data: Float32Array }[];
  /** Brightest pixel near the position in every channel, minus the local median: MJy/sr. */
  spectrum: { um: number; detector: number; value: number | null }[];
  /** Offset of that brightest pixel from the requested position, in arcsec. */
  peakOffsetArcsec: number;
}

function rows(buf: ArrayBuffer): Float32Array {
  const v = new DataView(buf);
  const out = new Float32Array(buf.byteLength / 4);
  for (let i = 0; i < out.length; i++) out[i] = v.getFloat32(i * 4, false); // FITS is big-endian
  return out;
}

const COLOUR_UM = [1.25, 2.2, 4.6]; // blue, green, red

/** Real SPHEREx DR1 pixels around (ra, dec) from the open-data cube: a colour cutout and a 102-channel spectrum. */
export async function cubeCutout(raDeg: number, decDeg: number, half = 24, signal?: AbortSignal): Promise<CubeCutout> {
  const { tile, row, col } = locate(raDeg, decDeg);
  const url = tileUrl(tile);
  const base = await imageOffset(url, signal);
  const r0 = Math.max(0, row - half), r1 = Math.min(TILE_PX - 1, row + half);
  const c0 = Math.max(0, col - half), c1 = Math.min(TILE_PX - 1, col + half);
  const width = c1 - c0 + 1, height = r1 - r0 + 1;
  const rowsOf = (p: number, a: number, b: number) => range(url, base + p * PLANE_BYTES + a * TILE_PX * 4, base + p * PLANE_BYTES + (b + 1) * TILE_PX * 4 - 1, signal);

  const pick = COLOUR_UM.map((um) => CHANNEL_UM.reduce((best, w, i) => (Math.abs(w - um) < Math.abs(CHANNEL_UM[best]! - um) ? i : best), 0));
  const planes = await pool(
    pick.map((p) => async () => {
      const all = rows(await rowsOf(p, r0, r1));
      const data = new Float32Array(width * height);
      for (let r = r0; r <= r1; r++) for (let c = c0; c <= c1; c++) data[(r1 - r) * width + (c - c0)] = all[(r - r0) * TILE_PX + c]!;
      return { channel: p, um: CHANNEL_UM[p]!, data };
    }),
    3,
  );

  const sr0 = Math.max(0, row - 2), sr1 = Math.min(TILE_PX - 1, row + 2);
  let offsetSum = 0, offsetN = 0;
  const spectrum = await pool(
    CHANNEL_UM.map((um, p) => async () => {
      const a = rows(await rowsOf(p, sr0, sr1));
      let peak = -Infinity, pr = row, pc = col;
      const bg: number[] = [];
      for (let r = sr0; r <= sr1; r++)
        for (let c = Math.max(0, col - 6); c <= Math.min(TILE_PX - 1, col + 6); c++) {
          const v = a[(r - sr0) * TILE_PX + c]!;
          if (!Number.isFinite(v)) continue;
          bg.push(v);
          if (Math.abs(r - row) <= 2 && Math.abs(c - col) <= 2 && v > peak) { peak = v; pr = r; pc = c; }
        }
      if (!Number.isFinite(peak) || bg.length === 0) return { um, detector: CHANNEL_DETECTOR[p]!, value: null };
      bg.sort((x, y) => x - y);
      offsetSum += Math.hypot(pr - row, pc - col); offsetN++;
      return { um, detector: CHANNEL_DETECTOR[p]!, value: peak - bg[Math.floor(bg.length / 2)]! };
    }),
    6,
  );
  return {
    tile, width, height, planes, spectrum,
    target: { x: col - c0, y: r1 - row },
    peakOffsetArcsec: offsetN ? (offsetSum / offsetN) * PIXEL_ARCSEC : 0,
  };
}
