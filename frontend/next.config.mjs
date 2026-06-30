/** @type {import('next').NextConfig} */
const nextConfig = {
  reactCompiler: true,
  output: 'standalone',
  async rewrites() {
    const isDev = process.env.NODE_ENV === 'development';
    const fallbackUrl = isDev ? 'http://127.0.0.1:8000' : 'https://nagarik-backend-909339119086.asia-south1.run.app';
    const backendUrl = process.env.BACKEND_URL || fallbackUrl;
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
