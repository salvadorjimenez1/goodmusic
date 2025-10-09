import type { NextConfig } from "next";

const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "i.scdn.co",
      },
      {
        protocol: "http",
        hostname: "localhost",
        port: "8000",            // FastAPI dev server
        pathname: "/uploads/**", // allow profile pictures
      },
      {
        protocol: "https",
        hostname: "your-production-domain.com", // <-- change this deploying
        pathname: "/uploads/**",
      },
         {
        protocol: "https",
        hostname: "ui-avatars.com",
      },
    ],
  },
};

module.exports = nextConfig;
