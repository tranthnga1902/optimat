// Chỉ dùng trong route QA. Trả metadata tổng hợp trong bộ nhớ, không đọc nội dung tệp.
export function useRouter(): {push:(url:string)=>void} { return { push:() => { throw Error("Điều hướng phân tích đã tắt trong mẫu QA."); } }; }
export const fixtureStorage: Pick<Storage,"setItem"> = { setItem:() => { throw Error("Ghi phiên phân tích đã tắt trong mẫu QA."); } };
export async function projectResponse<T>(path: string, options: RequestInit = {}): Promise<T> {
  if (path === "/openapi.json") return {paths:{}} as T;
  if (path === "/api/projects/701/files" && !options.method) return [] as T;
  if (path === "/api/projects/701/files" && options.method === "POST" && options.body instanceof FormData) {
    const file = options.body.get("file"), role = options.body.get("role");
    if (!(file instanceof File) || !role) throw Error("Mẫu QA yêu cầu tệp và vai trò.");
    window.dispatchEvent(new CustomEvent("qa-input-upload",{detail:{name:file.name,role}}));
    return {} as T;
  }
  throw Error("Thao tác ngoài phạm vi mẫu QA.");
}
