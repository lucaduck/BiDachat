"use client";
import { useEffect, useRef, useState, type ReactNode } from "react";
import Link from "next/link";
import { Brand } from "@/components/ui/brand";
import { Icon, type IconName } from "@/components/ui/icon";
import {
  EDITOR_STEPS,
  WORKSPACE_VIEWS,
  workspaceUrl,
  type WorkspaceRoute,
} from "@/lib/navigation";
import type { Navigate } from "@/lib/use-workspace-navigation";
import "./admin-shell.css";
import { WorkspaceBrandBanner } from "./workspace-brand-banner";
export const VIEW_DETAILS: Record<
  WorkspaceRoute["view"],
  { title: string; description: string; icon: IconName }
> = {
  Resumen: {
    title: "Resumen operativo",
    description: "Actividad, uso y estado de tus asistentes en un solo lugar.",
    icon: "dashboard",
  },
  Chatbots: {
    title: "Mis chatbots",
    description: "Crea, configura y prueba tus asistentes de análisis.",
    icon: "bot",
  },
  Documentos: {
    title: "Documentos y RAG",
    description: "Fuentes de conocimiento y su estado de procesamiento.",
    icon: "file",
  },
  Métricas: {
    title: "Analítica y métricas",
    description: "Consultas y tiempos de respuesta con datos registrados.",
    icon: "chart",
  },
  Configuración: {
    title: "Configuración del sistema",
    description: "Proveedores, integración y ajustes actuales del servicio.",
    icon: "settings",
  },
};
export function AdminShell({
  route,
  navigate,
  editorName,
  onLogout,
  children,
}: Readonly<{
  route: WorkspaceRoute;
  navigate: Navigate;
  editorName?: string;
  onLogout: () => void;
  children: ReactNode;
}>) {
  const [theme, setTheme] = useState<"light" | "dark">(() =>
    typeof window !== "undefined" && localStorage.getItem("bidachat-theme") === "dark"
      ? "dark"
      : "light",
  );
  const [collapsed, setCollapsed] = useState(
    () =>
      typeof window !== "undefined" &&
      localStorage.getItem("bidachat-sidebar-collapsed") === "true",
  );
  const [open, setOpen] = useState(false);
  const navigation = useRef<HTMLElement>(null);
  const toggle = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("bidachat-theme", theme);
  }, [theme]);
  useEffect(() => {
    localStorage.setItem("bidachat-sidebar-collapsed", String(collapsed));
  }, [collapsed]);
  useEffect(() => {
    if (open) navigation.current?.querySelector<HTMLElement>(".sidebar-nav a")?.focus();
  }, [open]);
  useEffect(() => {
    const media = matchMedia("(min-width: 769px)");
    const close = () => {
      if (media.matches) setOpen(false);
    };
    media.addEventListener("change", close);
    return () => media.removeEventListener("change", close);
  }, []);
  function closeMenu() {
    setOpen(false);
    toggle.current?.focus();
  }
  function link(
    event: React.MouseEvent<HTMLAnchorElement>,
    next: Partial<WorkspaceRoute> & { view: WorkspaceRoute["view"] },
  ) {
    if (
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    )
      return;
    event.preventDefault();
    if (navigate(next)) setOpen(false);
  }
  const editing = route.view === "Chatbots" && (route.editId || route.creating);
  return (
    <div
      className="app-shell"
      data-theme={theme}
      data-sidebar-collapsed={collapsed}
      onKeyDown={(event) => {
        if (!open) return;
        if (event.key === "Escape") {
          event.preventDefault();
          closeMenu();
        }
        if (event.key === "Tab") {
          const items = Array.from(
            navigation.current?.querySelectorAll<HTMLElement>(
              "a,button:not([disabled])",
            ) ?? [],
          ).filter((item) => item.getClientRects().length);
          const first = items[0],
            last = items.at(-1);
          if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last?.focus();
          } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first?.focus();
          }
        }
      }}
    >
      <a
        className="skip-link"
        href="#workspace-content"
        onClick={() =>
          requestAnimationFrame(() =>
            document.getElementById("workspace-content")?.focus(),
          )
        }
      >
        Ir al contenido
      </a>
      <aside
        ref={navigation}
        className={`sidebar ${open ? "sidebar-open" : ""}`}
        id="admin-navigation"
        aria-label="Navegación principal"
      >
        <div className="sidebar-heading">
          <Brand />
          <button
            className="sidebar-collapse"
            type="button"
            title={collapsed ? "Expandir menú lateral" : "Contraer menú lateral"}
            aria-label={collapsed ? "Expandir menú lateral" : "Contraer menú lateral"}
            aria-pressed={collapsed}
            onClick={() => setCollapsed(!collapsed)}
          >
            <Icon name={collapsed ? "panelOpen" : "panelClose"} />
          </button>
        </div>
        <button
          ref={toggle}
          className="menu-toggle"
          type="button"
          aria-expanded={open}
          aria-controls="workspace-navigation"
          onClick={() => setOpen(!open)}
        >
          <Icon name={open ? "close" : "menu"} />
          <span>{open ? "Cerrar menú" : "Menú"}</span>
        </button>
        <nav
          className="sidebar-nav"
          id="workspace-navigation"
          aria-label="Secciones administrativas"
        >
          {WORKSPACE_VIEWS.map((view) => (
            <a
              className="nav-link"
              href={workspaceUrl({ view })}
              key={view}
              title={collapsed ? view : undefined}
              aria-label={view}
              aria-current={route.view === view ? "page" : undefined}
              onClick={(event) => link(event, { view })}
            >
              <Icon name={VIEW_DETAILS[view].icon} />
              <span>{view}</span>
            </a>
          ))}
        </nav>
        <div className="sidebar-watermark" aria-hidden="true" />
        <div className="sidebar-footer">
          <button
            className="nav-link"
            type="button"
            aria-label="Cerrar sesión"
            onClick={onLogout}
          >
            <Icon name="logout" />
            <span>Cerrar sesión</span>
          </button>
          <p>
            BI-DATA<span>Inteligencia de negocios y ciencia de datos</span>
          </p>
        </div>
      </aside>
      {open ? (
        <button
          className="navigation-backdrop"
          type="button"
          aria-label="Cerrar navegación"
          onClick={closeMenu}
        />
      ) : null}
      <div className="workspace-stage">
        <header className="workspace-topbar" inert={open}>
          <span className="topbar-context">
            <Icon name="dashboard" />
            Panel operativo
          </span>
          <div className="topbar-actions">
            <span className="topbar-identity">
              <Icon name="shield" />
              Investigador autorizado
            </span>
            <button
              className="theme-toggle"
              type="button"
              aria-label={
                theme === "light" ? "Activar modo oscuro" : "Activar modo claro"
              }
              aria-pressed={theme === "dark"}
              onClick={() => setTheme(theme === "light" ? "dark" : "light")}
            >
              <Icon name={theme === "light" ? "moon" : "sun"} />
              <span>{theme === "light" ? "Modo oscuro" : "Modo claro"}</span>
            </button>
          </div>
        </header>
        <main
          className="main-content"
          id="workspace-content"
          tabIndex={-1}
          inert={open}
        >
          <header className="page-header">
            <div>
              <nav className="workspace-breadcrumb" aria-label="Ruta de navegación">
                <Link href="/" onClick={(event) => link(event, { view: "Resumen" })}>
                  Panel operativo
                </Link>
                <span aria-hidden="true">›</span>
                {editing ? (
                  <>
                    <a
                      href={workspaceUrl({ view: "Chatbots" })}
                      onClick={(event) => link(event, { view: "Chatbots" })}
                    >
                      Chatbots
                    </a>
                    <span aria-hidden="true">›</span>
                    <span>
                      {editorName ?? (route.creating ? "Nuevo chatbot" : "Chatbot")}
                    </span>
                    <span aria-hidden="true">›</span>
                    <span aria-current="page">{EDITOR_STEPS[route.step]}</span>
                  </>
                ) : (
                  <span aria-current="page">{route.view}</span>
                )}
              </nav>
              <h1>
                {editing
                  ? route.creating
                    ? "Crear chatbot"
                    : (editorName ?? "Editar chatbot")
                  : VIEW_DETAILS[route.view].title}
              </h1>
              <p>
                {editing
                  ? "Configura tu asistente paso a paso y comprueba el resultado."
                  : VIEW_DETAILS[route.view].description}
              </p>
            </div>
            {!editing ? (
              <p className="workspace-motto">
                Datos que
                <br />
                <span>conversan</span>
              </p>
            ) : null}
          </header>
          {children}
          {!editing ? <WorkspaceBrandBanner /> : null}
        </main>
      </div>
    </div>
  );
}
