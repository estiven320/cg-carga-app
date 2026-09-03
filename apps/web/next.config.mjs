/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // react-leaflet 5 se distribuye como ESM; Next lo transpila para el server
  // bundle aunque el componente solo se renderice en cliente.
  transpilePackages: ['react-leaflet', '@react-leaflet/core'],
  eslint: { ignoreDuringBuilds: false },
};

export default nextConfig;
