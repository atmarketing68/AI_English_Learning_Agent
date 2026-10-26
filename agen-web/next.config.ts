import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow standalone output for Docker deployment (if needed later)
  output: process.env.DOCKER_BUILD === "1" || process.env.DESKTOP_BUILD === "1" ? "standalone" : undefined,

  // Security headers (backup — also set in vercel.json)
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options",  value: "nosniff" },
          { key: "X-Frame-Options",          value: "DENY" },
          { key: "Referrer-Policy",          value: "strict-origin-when-cross-origin" },
        ],
      },
    ];
  },

  // Allow API images if we add avatars later
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "agen-api.onrender.com",
      },
    ],
  },
};

export default nextConfig;
