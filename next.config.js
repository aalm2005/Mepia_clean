/** @type {import('next').NextConfig} */
const nextConfig = {
  distDir: process.env.MEPIA_NEXT_DIST_DIR || ".next",
  devIndicators: false,
  async redirects() {
    return [{ source: "/", destination: "/dashboard", permanent: false }];
  },
};

module.exports = nextConfig;
