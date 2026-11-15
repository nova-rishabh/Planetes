/**
 * Planet X Reality Check physics (docs/04 §6). Mirror of pipeline/src/planetes/planet_x.py; the tests in
 * planetx.test.ts use the same anchors as pipeline/tests/test_planet_x.py. Scenarios only: never a detection.
 */

const H = 6.62607015e-34;
const C = 299792458;
const KB = 1.380649e-23;
const JY = 1e-26;
const AU_M = 149597870700;
const SUN_T_K = 5772;
const SUN_R_M = 6.957e8;
export const NEPTUNE_RADIUS_KM = 24622;
export const EARTH_RADIUS_KM = 6371;
const NEPTUNE_ALBEDO = 0.41;
const ARCSEC_PER_RAD = 206264.806;
export const SPHEREX_SINGLE_VISIT_AB = 18.5;
export const BANDS_UM = [1.0, 2.0, 3.0, 3.5, 4.0, 4.5, 5.0];

export function vMagnitude(radiusKm: number, albedo: number, rAu: number, deltaAu = rAu): number {
  return (
    7.8 -
    5 * Math.log10(radiusKm / NEPTUNE_RADIUS_KM) -
    2.5 * Math.log10(albedo / NEPTUNE_ALBEDO) +
    5 * Math.log10((rAu * deltaAu) / 29 ** 2)
  );
}

function planckNu(lamUm: number, tK: number): number {
  const nu = C / (lamUm * 1e-6);
  const x = (H * nu) / (KB * tK);
  if (x > 700) return 0;
  return (2 * H * nu ** 3) / C ** 2 / Math.expm1(x);
}

export function reflectedUjy(lamUm: number, radiusKm: number, albedo: number, rAu: number, deltaAu = rAu): number {
  const sun = Math.PI * planckNu(lamUm, SUN_T_K) * (SUN_R_M / AU_M) ** 2;
  return ((sun / rAu ** 2) * albedo * ((radiusKm * 1e3) / (deltaAu * AU_M)) ** 2 * 1e6) / JY;
}

export function internalHeatUjy(lamUm: number, radiusKm: number, deltaAu: number, tK: number): number {
  if (tK <= 0) return 0;
  return ((planckNu(lamUm, tK) * Math.PI * ((radiusKm * 1e3) / (deltaAu * AU_M)) ** 2) * 1e6) / JY;
}

export const abMag = (ujy: number): number => (ujy > 0 ? -2.5 * Math.log10((ujy * 1e-6) / 3631) : Infinity);
export const stackedDepthAb = (single: number, n: number): number => single + 1.25 * Math.log10(Math.max(1, n));
export const sixMonthShiftArcsec = (rAu: number): number => (2 * ARCSEC_PER_RAD) / rAu;

export type BandResult = { um: number; ab: number; heatShare: number; above: boolean };

export function evaluate(radiusKm: number, albedo: number, rAu: number, tK: number, visits: number) {
  const depth = stackedDepthAb(SPHEREX_SINGLE_VISIT_AB, visits);
  const bands: BandResult[] = BANDS_UM.map((um) => {
    const refl = reflectedUjy(um, radiusKm, albedo, rAu);
    const heat = internalHeatUjy(um, radiusKm, rAu, tK);
    const ab = abMag(refl + heat);
    return { um, ab, heatShare: refl + heat > 0 ? heat / (refl + heat) : 0, above: ab <= depth };
  });
  return { v: vMagnitude(radiusKm, albedo, rAu), depth, bands, shiftArcsec: sixMonthShiftArcsec(rAu) };
}
