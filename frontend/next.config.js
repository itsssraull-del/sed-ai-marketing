/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  typescript: { ignoreBuildErrors: true },
  eslint: { ignoreDuringBuilds: true },
  images: {
    domains: [
      'localhost',
      's3.amazonaws.com',
      'replicate.delivery',
      'oaidalleapiprodscus.blob.core.windows.net',
      'cdn.ideogram.ai',
    ],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000'}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
