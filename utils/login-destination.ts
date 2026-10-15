/** Destinos internos conocidos; nunca redirigir a un origen suministrado por el cliente. */
export function loginDestination(value: string | null): string {
  if (!value || !value.startsWith("/") || value.startsWith("//") || /[\\\r\n]/.test(value)) return "/";
  try {
    const url = new URL(value, "https://mepia.invalid");
    if (url.origin !== "https://mepia.invalid" || !["/", "/dashboard", "/upload", "/onboarding", "/chat", "/salud", "/reportes"].includes(url.pathname)) return "/";
    return url.pathname + url.search;
  } catch { return "/"; }
}
