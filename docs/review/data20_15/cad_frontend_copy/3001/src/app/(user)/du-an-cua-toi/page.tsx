import { ProjectWorkspace } from "./ProjectWorkspace";
export const metadata = { title: "Dự án của tôi" };
export default function Page() {
  return <><p className="mb-4 text-sm">Quản lý dự án / Dự án của tôi</p><ProjectWorkspace/></>;
}
