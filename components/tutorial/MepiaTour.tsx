"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { driver, type Driver } from "driver.js";
import "driver.js/dist/driver.css";
import { useMepiaAuth } from "@/components/auth/MepiaAuthProvider";
import { PASOS_TUTORIAL } from "./tourSteps";

type Avance = { paso?: number; visto?: boolean };
function leer(clave: string): Avance {
  try {
    const valor = JSON.parse(localStorage.getItem(clave) || "null");
    if (!valor || typeof valor !== "object") return {};
    if (valor.visto === true) return { visto: true };
    if (Number.isInteger(valor.paso) && valor.paso >= 0 && valor.paso < PASOS_TUTORIAL.length) return { paso: valor.paso };
  } catch { /* El recorrido también funciona sin almacenamiento. */ }
  return {};
}
function guardar(clave: string, valor: Avance) {
  try { localStorage.setItem(clave, JSON.stringify(valor)); } catch { /* Preferencia opcional. */ }
}
function visible(selector?: string): HTMLElement | null {
  if (!selector) return null;
  const elemento = document.querySelector<HTMLElement>(selector);
  if (!elemento || !elemento.getClientRects().length || getComputedStyle(elemento).visibility === "hidden") return null;
  return elemento;
}
const esperar = (ms: number) => new Promise<void>(resolve => setTimeout(resolve, ms));
async function esperarElemento(selector: string | undefined, cancelado: () => boolean) {
  if (!selector) return;
  const inicio = Date.now();
  while (!visible(selector) && !cancelado() && Date.now() - inicio < 2500) {
    if (selector.includes("nav") && visible('[data-tour="menu"]')) return;
    await esperar(80);
  }
}
async function ponerSeccion(seccion: number | undefined, cancelado: () => boolean) {
  if (!seccion) return;
  for (let intento = 0; intento < 4 && !cancelado(); intento++) {
    const actual = Number(document.querySelector<HTMLElement>('[data-tour="advanced-config-tabs"]')?.dataset.seccion);
    if (!actual || actual === seccion) return;
    const boton = document.querySelector<HTMLButtonElement>(actual < seccion
      ? '[data-tour="config-siguiente"]' : '[data-tour="config-anterior"]');
    if (!boton || boton.disabled) return;
    // Estos dos controles solo cambian de sección; nunca pulsar Guardar/Analizar/Enviar.
    boton.click();
    await esperar(80);
  }
}

export function MepiaTour() {
  const path = usePathname();
  const router = useRouter();
  const enlaceExplicito = useSearchParams().has("run_id");
  const { session, business, businessesLoading, auditRunId } = useMepiaAuth();
  const clave = session && business ? "mepia.tutorial.v1:" + session.user.id + ":" + business : "";
  const [paso, setPaso] = useState<number | null>(null);
  const [ronda, setRonda] = useState(0);
  const activo = useRef<Driver | null>(null);
  const inicializado = useRef("");
  const navegacion = useRef<string | null>(null);
  const ayuda = useRef<HTMLButtonElement>(null);

  const terminar = useCallback(() => {
    if (clave) guardar(clave, { visto: true });
    navegacion.current = null;
    setPaso(null);
    requestAnimationFrame(() => ayuda.current?.focus());
  }, [clave]);

  const irA = useCallback((indice: number) => {
    if (!clave || !PASOS_TUTORIAL[indice]) return;
    guardar(clave, { paso: indice });
    navegacion.current = PASOS_TUTORIAL[indice].ruta;
    setPaso(indice);
    setRonda(valor => valor + 1);
  }, [clave]);

  useEffect(() => {
    if (!clave || businessesLoading || inicializado.current === clave) return;
    const avance = leer(clave);
    if (avance.paso !== undefined && PASOS_TUTORIAL[avance.paso].ruta === path) {
      inicializado.current = clave;
      irA(avance.paso);
    } else if (!enlaceExplicito && path === "/dashboard") {
      // Al cambiar de negocio, esperar a que la URL deje atrás la corrida anterior.
      inicializado.current = clave;
      if (avance.paso !== undefined) irA(avance.paso);
      else if (!avance.visto) irA(0);
    }
  }, [clave, businessesLoading, enlaceExplicito, path, irA]);

  useEffect(() => {
    if (paso === null || !clave || businessesLoading) return;
    const actual = PASOS_TUTORIAL[paso];
    if (!actual) { terminar(); return; }
    if (path !== actual.ruta) {
      if (navegacion.current !== actual.ruta) { terminar(); return; }
      const conservar = auditRunId && ["/dashboard", "/salud", "/reportes"].includes(actual.ruta);
      router.push(conservar ? actual.ruta + "?run_id=" + encodeURIComponent(auditRunId) : actual.ruta);
      return;
    }
    navegacion.current = null;
    let cancelado = false;
    let tour: Driver | null = null;
    void (async () => {
      await esperarElemento(actual.seccionConfig ? '[data-tour="advanced-config-tabs"]' : actual.elemento, () => cancelado);
      await ponerSeccion(actual.seccionConfig, () => cancelado);
      if (cancelado) return;
      let elemento = visible(actual.elemento);
      if (!elemento && actual.elemento?.includes("nav")) elemento = visible('[data-tour="menu"]');
      let descripcion = actual.texto;
      if (!elemento && actual.sinResultado) {
        elemento = visible('[data-tour="estado"]');
        descripcion = actual.sinResultado;
      } else if (!elemento && actual.elemento) {
        descripcion += " Si todavía no aparece este apartado, primero necesitas los datos o un análisis guardado que lo habilite.";
      }
      tour = driver({
        steps: PASOS_TUTORIAL.map((p, indice) => ({
          ...(indice === paso && elemento ? { element: elemento } : {}),
          popover: { title: p.titulo, description: indice === paso ? descripcion : p.texto },
        })),
        showProgress: true,
        progressText: "{{current}} de {{total}}",
        nextBtnText: "Siguiente",
        prevBtnText: "Anterior",
        doneBtnText: "Terminar",
        popoverClass: "mepia-tour",
        overlayOpacity: 0.65,
        stagePadding: 6,
        stageRadius: 12,
        animate: !window.matchMedia("(prefers-reduced-motion: reduce)").matches,
        disableActiveInteraction: true,
        onNextClick: () => paso + 1 >= PASOS_TUTORIAL.length ? terminar() : irA(paso + 1),
        onPrevClick: () => { if (paso > 0) irA(paso - 1); },
        onPopoverRender: popover => {
          popover.wrapper.setAttribute("role", "dialog");
          popover.wrapper.removeAttribute("aria-labelledby");
          popover.wrapper.setAttribute("aria-label", "Tutorial de MEPIA");
          popover.wrapper.setAttribute("data-mepia-tour-step", String(paso));
          popover.closeButton.setAttribute("aria-label", "Cerrar tutorial");
          popover.nextButton.setAttribute("aria-label", paso === PASOS_TUTORIAL.length - 1 ? "Terminar tutorial" : "Siguiente paso");
          popover.previousButton.setAttribute("aria-label", "Paso anterior");
        },
        onDestroyed: () => { if (!cancelado) terminar(); },
      });
      activo.current = tour;
      tour.drive(paso);
    })();
    return () => {
      cancelado = true;
      tour?.destroy();
      if (activo.current === tour) activo.current = null;
    };
  }, [paso, ronda, path, clave, businessesLoading, auditRunId, router, terminar, irA]);

  return <button ref={ayuda} type="button" data-tour="ayuda" aria-label="Ver tutorial"
    disabled={!clave || businessesLoading} onClick={() => irA(0)}
    className="flex shrink-0 items-center gap-2 rounded-lg border border-white/10 px-3 py-1.5 text-xs text-zinc-300 hover:bg-white/5 disabled:opacity-40"
    title="Ver tutorial">
    <span aria-hidden="true" className="grid h-4 w-4 place-items-center rounded-full border border-current text-[10px] font-semibold">?</span>
    <span className="hidden sm:inline">Tutorial</span>
  </button>;
}
