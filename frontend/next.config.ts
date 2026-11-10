import type { NextConfig } from "next";

const nextConfig: NextConfig = {
	async rewrites() {
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
