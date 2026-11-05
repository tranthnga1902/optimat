"use client";
// Ô nhập chỉ báo khi người dùng chốt giá trị (sự kiện "change" gốc: rời ô, Enter, nút tăng giảm) như trang cũ,
// để mỗi lần sửa là một bước hoàn tác và việc gõ dở không bị dựng lại. onCommit trả chuỗi thì ô hiện chuỗi đó.
import { useEffect, useLayoutEffect, useRef, type InputHTMLAttributes } from "react";

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, "value" | "defaultValue" | "onChange"> & {
  value: string;
  onCommit: (el: HTMLInputElement) => string | void;
};

export function ChangeInput({ value, onCommit, ...rest }: Props) {
  const ref = useRef<HTMLInputElement>(null), commit = useRef(onCommit);
  useLayoutEffect(() => { commit.current = onCommit; });
  useEffect(() => { if (ref.current) ref.current.value = value; }, [value]);
  useEffect(() => {
    const el = ref.current!;
    const h = () => { const v = commit.current(el); if (typeof v === "string") el.value = v; };
    el.addEventListener("change", h);
    return () => el.removeEventListener("change", h);
  }, []);
  return <input ref={ref} defaultValue={value} {...rest} />;
}
