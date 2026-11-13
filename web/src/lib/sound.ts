/**
 * Sonified time-lapse (D1.7): hear each frame. Pitch follows the frame's wavelength (short infrared = high note,
 * long = low), loudness follows how bright the target pixel is in that frame. Off until the user turns it on
 * (browsers only allow audio after a click anyway).
 */

const LO_UM = 0.75;
const HI_UM = 5.0;
const HIGH_HZ = 880; // A5 at 0.75 µm
const LOW_HZ = 220; // A3 at 5 µm

/** Wavelength -> pitch on a log scale, so each detector spans a similar musical interval. */
export function pitchHz(wavelengthUm: number | null | undefined): number {
  if (wavelengthUm == null || !Number.isFinite(wavelengthUm)) return 440;
  const t = (Math.log(Math.min(Math.max(wavelengthUm, LO_UM), HI_UM)) - Math.log(LO_UM)) / (Math.log(HI_UM) - Math.log(LO_UM));
  return HIGH_HZ * Math.pow(LOW_HZ / HIGH_HZ, t);
}

/** Grey level 0..255 of the target pixel -> gain 0.03..0.25 (never silent, never loud). */
export function gainFor(grey: number | null): number {
  if (grey == null || !Number.isFinite(grey)) return 0.08;
  return 0.03 + (Math.min(Math.max(grey, 0), 255) / 255) * 0.22;
}

let ctx: AudioContext | null = null;

function audio(): AudioContext | null {
  if (typeof window === "undefined") return null;
  const Ctor = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!Ctor) return null;
  ctx ??= new Ctor();
  if (ctx.state === "suspended") void ctx.resume();
  return ctx;
}

/** A short soft tone (sine with a quick attack and decay). */
export function tone(freqHz: number, gain: number, durationS = 0.14, type: OscillatorType = "sine"): void {
  const ac = audio();
  if (!ac) return;
  const t0 = ac.currentTime;
  const osc = ac.createOscillator();
  const amp = ac.createGain();
  osc.type = type;
  osc.frequency.setValueAtTime(freqHz, t0);
  amp.gain.setValueAtTime(0, t0);
  amp.gain.linearRampToValueAtTime(gain, t0 + 0.01);
  amp.gain.exponentialRampToValueAtTime(0.0001, t0 + durationS);
  osc.connect(amp).connect(ac.destination);
  osc.start(t0);
  osc.stop(t0 + durationS + 0.02);
}

/** The blink tick: a short click so A/B flips are audible. */
export const tick = (): void => tone(1600, 0.05, 0.03, "square");
