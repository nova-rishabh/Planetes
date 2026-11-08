// Next.js 16 removed `next lint`; ESLint runs directly with eslint-config-next's flat configs.
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const config = [
  ...nextVitals,
  ...nextTs,
  { ignores: [".next/**", "out/**", "node_modules/**", "next-env.d.ts", "src/types/contracts.ts"] },
];

export default config;
