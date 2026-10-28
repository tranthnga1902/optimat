import type { NextConfig } from "next";

// API FastAPI (uvicorn optimat.api.main:app); trình duyệt gọi /api/... cùng nguồn, Next chuyển tiếp sang đây.
const API = process.env.OPTIMAT_API ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  cacheComponents: true,
  devIndicators: { position: "bottom-right" }, // nút N của chế độ dev không che cuối menu bên trái
  partialPrefetching: true,
  experimental: {
    proxyTimeout: 300_000, // đọc DWG lớn và tối ưu NSGA-II có thể mất vài phút
    // mặc định 10 MB cắt cụt bản vẽ gửi qua /api; giới hạn thật do API kiểm (MAX_UPLOAD_MB = 50 x MAX_UPLOAD_FILES = 20)
    proxyClientMaxBodySize: "1000mb",
  },
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${API}/api/:path*` },
      { source: "/docs", destination: `${API}/docs` },
      { source: "/openapi.json", destination: `${API}/openapi.json` },
    ];
  },
  turbopack: {
    root: __dirname, // C:\Users\Admin có package-lock.json lạc chỗ: chốt gốc ở thư mục frontend
    rules: {
      "*.css": {
        // chỉ CSS toàn cục của dự án: đưa *.module.css qua đây thì mất tên lớp cục bộ (trang trắng kiểu)
        condition: { all: [{ not: "foreign" }, { not: { path: /\.module\.css$/ } }] },
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
