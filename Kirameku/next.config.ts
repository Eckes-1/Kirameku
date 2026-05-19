import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  compress: true,

  allowedDevOrigins: [
    "127.0.0.1",
    "run-agent-6a0be357b96c4d5d18e15a03-mpctkr57-preview.agent-sandbox-bj-a2-gw.trae.cn",
  ],

  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
      {
        source: "/uploads/:path*",
        destination: "http://localhost:8000/uploads/:path*",
      },
      {
        source: "/admin/:path*",
        destination: "http://localhost:8000/admin/:path*",
      },
      {
        source: "/reader3/:path*",
        destination: `${process.env.NOVEL_API_URL || "http://localhost:8085"}/reader3/:path*`,
      },
    ];
  },

  experimental: {
    optimizePackageImports: [
      "framer-motion",
      "lucide-react",
      "@dnd-kit/core",
      "@dnd-kit/sortable",
      "@dnd-kit/utilities",
    ],
  },

  images: {
    formats: ["image/avif", "image/webp"],
    remotePatterns: [
      { protocol: "https", hostname: "static.hiromu.top" },
      { protocol: "https", hostname: "hiromu520.oss-cn-beijing.aliyuncs.com" },
      { protocol: "https", hostname: "picsum.photos" },
      { protocol: "https", hostname: "avatars.githubusercontent.com" },
      { protocol: "http", hostname: "wfqqreader-1252317822.image.myqcloud.com" },
    ],
  },
};

export default nextConfig;
