import { isAuthRetryableFetchError } from "@supabase/supabase-js";

export function chatLoginErrorMessage(error: unknown): string {
  return isAuthRetryableFetchError(error)
    ? "No se pudo conectar con el servicio de inicio de sesión. Revisa tu conexión y vuelve a intentarlo."
    : "No fue posible iniciar sesión. Revisa tus credenciales.";
}
