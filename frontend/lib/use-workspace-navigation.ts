"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { parseWorkspaceRoute, workspaceUrl, type WorkspaceRoute } from "./navigation";
export type Navigate = (
  route: Partial<WorkspaceRoute> & { view: WorkspaceRoute["view"] },
  options?: { replace?: boolean; withinEditor?: boolean; ifCurrentEditor?: string },
) => boolean;
export function useWorkspaceNavigation() {
  const [route, setRoute] = useState(() =>
    parseWorkspaceRoute(typeof window === "undefined" ? "" : window.location.search),
  );
  const routeRef = useRef(route);
  const dirtyRef = useRef(false);
  const setDirty = useCallback((dirty: boolean) => {
    dirtyRef.current = dirty;
  }, []);
  const navigate: Navigate = useCallback((next, options = {}) => {
    if (
      options.ifCurrentEditor &&
      (routeRef.current.view !== "Chatbots" ||
        (routeRef.current.editId ?? (routeRef.current.creating ? "new" : "")) !==
          options.ifCurrentEditor)
    )
      return false;
    if (
      !options.withinEditor &&
      dirtyRef.current &&
      !window.confirm("Tienes cambios sin guardar. ¿Salir y descartarlos?")
    )
      return false;
    if (!options.withinEditor) dirtyRef.current = false;
    const url = workspaceUrl(next);
    if (url !== window.location.pathname + window.location.search) {
      if (options.replace) window.history.replaceState(null, "", url);
      else window.history.pushState(null, "", url);
    }
    const parsed = parseWorkspaceRoute(new URL(url, window.location.origin).search);
    routeRef.current = parsed;
    setRoute(parsed);
    requestAnimationFrame(() => document.getElementById("workspace-content")?.focus());
    return true;
  }, []);
  useEffect(() => {
    function onPopState() {
      const next = parseWorkspaceRoute(window.location.search);
      const sameEditor =
        next.view === "Chatbots" &&
        routeRef.current.view === "Chatbots" &&
        ((next.editId && next.editId === routeRef.current.editId) ||
          (next.creating && routeRef.current.creating));
      if (
        !sameEditor &&
        dirtyRef.current &&
        !window.confirm("Tienes cambios sin guardar. ¿Salir y descartarlos?")
      ) {
        window.history.pushState(null, "", workspaceUrl(routeRef.current));
        return;
      }
      if (!sameEditor) dirtyRef.current = false;
      routeRef.current = next;
      setRoute(next);
    }
    function onBeforeUnload(event: BeforeUnloadEvent) {
      if (dirtyRef.current) {
        event.preventDefault();
        event.returnValue = "";
      }
    }
    window.addEventListener("popstate", onPopState);
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => {
      window.removeEventListener("popstate", onPopState);
      window.removeEventListener("beforeunload", onBeforeUnload);
    };
  }, []);
  return { route, navigate, setDirty };
}
