import createNextIntlPlugin from 'next-intl/plugin';

// 1. Initialize the next-intl plugin wrapper
const withNextIntl = createNextIntlPlugin();

/** @type {import('next').NextConfig} */
const nextConfig = {
  // 2. Preserve your existing configurations
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
};

// 3. Chain the plugin wrapper with your base config and use the ES Module export
export default withNextIntl(nextConfig);