import type { Metadata } from "next";
import { Be_Vietnam_Pro, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const font = Be_Vietnam_Pro({ variable: "--font-be-vietnam", subsets: ["latin", "vietnamese"], weight: ["400", "500", "600", "700"] });
// chữ số trên trang kiểm tra bóc tách (--f-num trong do-boc/review.module.css)
const mono = JetBrains_Mono({ variable: "--font-jetbrains", subsets: ["latin", "vietnamese"], weight: ["400", "600"] });

export const metadata: Metadata = {
  title: { default: "OptiMat AI", template: "%s · OptiMat AI" },
  description: "Từ bản vẽ đến phương án vật liệu tối ưu: đo bóc tường, tra giá, tối ưu NSGA-II.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="vi" className={`${font.variable} ${mono.variable}`}>
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
