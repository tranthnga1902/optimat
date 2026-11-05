export function useWallClasses(current?: string) {
  return Array.from(new Set(["110", "220", ...(current ? [current] : [])]));
}
