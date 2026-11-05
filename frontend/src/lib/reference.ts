"use client";
// Danh sách tra cứu cho các ô chọn (họ vật liệu, loại xe, lớp tường, mác bê tông, vật liệu chống thấm, cấu kiện thép,
// loại dữ liệu): lấy từ /api/catalog/reference (database), không fix cứng trên web. Tải một lần cho cả phiên.
import { useEffect, useState } from "react";
import { api } from "./api";

export type Reference = {
  families: { id: string; name: string; is_wall: boolean }[];
  vehicles: { id: string; name: string; payload_ton: number }[];
  wall_classes: { id: string; min_mm: number; max_mm: number }[];
  concrete_grades: string[];
  mortar_grades?: string[];
  plaster_thicknesses?: string[];
  screed_thicknesses?: string[];
  waterproof_materials: { id: string; name: string }[];
  steel_elements: { code: string; name: string }[];
  raw_classes?: { code: string; name: string }[];
  data_kinds: string[];
};

let cached: Promise<Reference> | null = null;
const load = () => (cached ??= api<Reference>("/api/catalog/reference").catch((e) => { cached = null; throw e; }));

/** null khi đang tải; lỗi tải trả về qua error. */
export function useReference(): { ref: Reference | null; error: string } {
  const [ref, setRef] = useState<Reference | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let live = true;
    load().then((r) => live && setRef(r), (e) => live && setError((e as Error).message));
    return () => { live = false; };
  }, []);
  return { ref, error };
}

/** Lớp tường bộ nhận dạng dùng (110, 150, 220, 330…). cur: giá trị đang chọn, luôn có trong danh sách kể cả khi đang tải. */
export function useWallClasses(cur?: string): string[] {
  const ids = useReference().ref?.wall_classes.map((c) => c.id) ?? [];
  return cur && !ids.includes(cur) ? [...ids, cur] : ids;
}
