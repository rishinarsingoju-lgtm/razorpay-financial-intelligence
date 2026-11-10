import type { NextConfig } from "next";

const isDev = process.env.NODE_ENV !== "production" && !process.env.VERCEL;

const nextConfig: NextConfig = {
	async rewrites() {
		// Only enable localhost proxy rewrites during local development
		if (!isDev) {
			return [];
		}
		return [
			{
				source: "/api/exceptions",
				destination: "http://127.0.0.1:8009/api/exceptions/",
			},
			{
				source: "/api/settlements",
				destination: "http://127.0.0.1:8009/api/settlements/",
			},
			{
				source: "/api/transactions",
				destination: "http://127.0.0.1:8009/api/transactions/",
			},
			{
				source: "/api/:path*",
				destination: "http://127.0.0.1:8009/api/:path*",
			},
		];
	},
};

export default nextConfig;
