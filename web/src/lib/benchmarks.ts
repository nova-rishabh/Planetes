/**
 * The five baked benchmark targets (docs/03 §7). Only ids and names live here: positions, motions and
 * frames come from the baked files in public/data/targets/{id}/, never from numbers typed into the UI.
 */

export const BENCHMARKS = [
  { id: "barnard", name: "Barnard's Star" },
  { id: "wise0855", name: "WISE 0855−0714" },
  { id: "epsindib", name: "ε Indi Ba/Bb" },
  { id: "rwaur", name: "RW Aurigae" },
  { id: "rdra", name: "R Draconis" },
] as const;

export type BenchmarkId = (typeof BENCHMARKS)[number]["id"];
export const BENCHMARK_IDS: readonly BenchmarkId[] = BENCHMARKS.map((b) => b.id);

export function benchmarkName(id: BenchmarkId): string {
  return BENCHMARKS.find((b) => b.id === id)?.name ?? id;
}
