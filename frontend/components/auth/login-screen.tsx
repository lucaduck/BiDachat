"use client";
import "./login.css";

import { useEffect, useState, type FormEvent } from "react";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Icon } from "@/components/ui/icon";
import { InputField } from "@/components/ui/field";
import { Alert } from "@/components/ui/status";
import { ApiError } from "@/services/api-client";

import { useSession } from "./session-provider";

export function LoginScreen() {
  const { login, sessionExpired } = useSession();
  const [theme, setTheme] = useState<"light" | "dark">(() =>
    typeof window !== "undefined" && localStorage.getItem("bidachat-theme") === "dark"
      ? "dark"
      : "light",
  );
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("bidachat-theme", theme);
  }, [theme]);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);
  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login({ email, password });
    } catch (requestError) {
      setError(
        requestError instanceof ApiError && requestError.status === 429
          ? "Demasiados intentos de inicio de sesión. Espera unos minutos antes de volver a intentar."
          : "No se pudo iniciar sesión. Verifica tus credenciales e inténtalo nuevamente.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }
  return (
    <main className="login-page">
      <header className="login-brand">
        <span>BI-DATA · Asistentes de análisis</span>
        <Button
          variant="secondary"
          className="login-theme-toggle"
          onClick={() => setTheme((value) => (value === "light" ? "dark" : "light"))}
          aria-label={
            theme === "light" ? "Cambiar a modo oscuro" : "Cambiar a modo claro"
          }
        >
          <Icon name={theme === "light" ? "moon" : "sun"} />
          {theme === "light" ? "Modo oscuro" : "Modo claro"}
        </Button>
      </header>
      <div className="login-content">
        <section className="login-card" aria-labelledby="login-title">
          <div className="login-identity">
            <Image
              className="login-logo"
              src={
                theme === "dark"
                  ? "/brand/login-logo-dark.png"
                  : "/brand/logo-bidachat-light.png"
              }
              alt="BIDACHAT · Gestor de chatbots · Plataforma inteligente"
              width={theme === "dark" ? 1536 : 1254}
              height={theme === "dark" ? 1024 : 1254}
              sizes="(max-width: 760px) 280px, (max-width: 1100px) 45vw, 480px"
              priority
            />
          </div>
          <div className="login-form-panel">
            <h1 id="login-title">Iniciar sesión</h1>
            <p>Gestiona los asistentes vinculados a los cuadros de mando de BI-DATA.</p>
            {sessionExpired ? (
              <Alert tone="warning">
                Tu sesión terminó. Inicia sesión para continuar donde estabas.
              </Alert>
            ) : null}
            <form className="form-stack" onSubmit={handleSubmit}>
              {error ? <Alert tone="error">{error}</Alert> : null}
              <div className="login-email-field">
                <InputField
                  id="email"
                  label="Correo institucional"
                  type="email"
                  autoComplete="email"
                  placeholder="Tu correo de acceso"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                  disabled={isSubmitting}
                />
                <Icon name="mail" />
              </div>
              <div className="password-field">
                <InputField
                  id="password"
                  label="Contraseña"
                  type={isPasswordVisible ? "text" : "password"}
                  autoComplete="current-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                  disabled={isSubmitting}
                />
                <button
                  className="password-toggle"
                  type="button"
                  aria-label={
                    isPasswordVisible ? "Ocultar contraseña" : "Mostrar contraseña"
                  }
                  aria-pressed={isPasswordVisible}
                  onClick={() => setIsPasswordVisible((value) => !value)}
                >
                  <Icon name="eye" />
                </button>
              </div>
              <Button
                className="button-full login-submit"
                type="submit"
                isLoading={isSubmitting}
              >
                {isSubmitting ? "Validando acceso…" : "Iniciar sesión"}
              </Button>
            </form>
            <div className="login-access-note">
              <Icon name="shield" />
              <span>Acceso exclusivo para investigadores autorizados</span>
            </div>
          </div>
        </section>
        <p className="login-description">
          BIDACHAT conecta tus fuentes de conocimiento con los cuadros de mando de
          BI-DATA.
        </p>
      </div>
      <footer className="login-footer">
        BI-DATA · Aplicación de gestión de chatbots
      </footer>
    </main>
  );
}
