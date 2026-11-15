import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static export: Vercel serves web/out as plain files. Long jobs live on the Render API, never here.
  output: "export",
  images: { unoptimized: true },
};

export default nextConfig;
