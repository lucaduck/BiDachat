import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "danger" | "quiet";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  isLoading?: boolean;
  variant?: ButtonVariant;
};

export function Button({
  children,
  className = "",
  isLoading = false,
  variant = "primary",
  ...props
}: Readonly<ButtonProps>) {
  return (
    <button
      {...props}
      className={`button button-${variant} ${className}`.trim()}
      aria-busy={isLoading || undefined}
      disabled={props.disabled || isLoading}
    >
      {isLoading ? <span className="spinner" aria-hidden="true" /> : null}
      <span>{children}</span>
    </button>
  );
}
