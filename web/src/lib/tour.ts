/** Cues the guided tour sends to the player, so each stop shows what it explains instead of only pointing at it. */
export type TourCue = "rest" | "play" | "blink" | "stars";

export const TOUR_EVENT = "planetes:tour";

export function sendCue(cue: TourCue) {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent<TourCue>(TOUR_EVENT, { detail: cue }));
}

/** `?tour=1` on a viewer link starts the tour once the frames are ready. */
export function wantsTour(params: URLSearchParams): boolean {
  return params.get("tour") === "1";
}
