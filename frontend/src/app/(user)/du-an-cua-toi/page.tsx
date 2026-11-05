import { ProjectWorkspace } from "./ProjectWorkspace";
export const metadata = { title: "Dự án của tôi" };
export default function Page() {
  return <><nav aria-label="Vị trí trang" className="m-0 flex items-center gap-2 text-sm text-muted">Quản lý dự án <span aria-hidden className="text-rule">/</span> <b className="font-semibold text-ink">Dự án của tôi</b></nav><ProjectWorkspace/></>;
}
