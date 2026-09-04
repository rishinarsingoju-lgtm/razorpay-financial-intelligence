import type { NextConfig } from "next";

const nextConfig: NextConfig = {
	async rewrites() {
		return [
			{
				source: "/backend-api/api/exceptions",
				destination: "http://127.0.0.1:8009/api/exceptions/",
			},
			{
				source: "/backend-api/api/settlements",
				destination: "http://127.0.0.1:8009/api/settlements/",
			},
			{
				source: "/backend-api/api/transactions",
				destination: "http://127.0.0.1:8009/api/transactions/",
			},
			{
				source: "/backend-api/:path*",
				destination: "http://127.0.0.1:8009/:path*",
			},
		];
	},
};

export default nextConfig;
