import type {
  InputHTMLAttributes,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from "react";

type FieldBaseProps = { error?: string; hint?: string; label: string };
type InputProps = FieldBaseProps & InputHTMLAttributes<HTMLInputElement>;
type SelectProps = FieldBaseProps & SelectHTMLAttributes<HTMLSelectElement>;
type TextareaProps = FieldBaseProps & TextareaHTMLAttributes<HTMLTextAreaElement>;

function FieldMessage({
  error,
  hint,
  id,
}: Pick<FieldBaseProps, "error" | "hint"> & { id?: string }) {
  if (error)
    return (
      <p id={id} className="field-error" role="alert">
        {error}
      </p>
    );
  return hint ? (
    <p id={id} className="field-hint">
      {hint}
    </p>
  ) : null;
}
export function InputField({ error, hint, id, label, ...props }: Readonly<InputProps>) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input
        {...props}
        aria-invalid={Boolean(error)}
        aria-describedby={error || hint ? `${id}-message` : props["aria-describedby"]}
        className="input"
        id={id}
      />
      <FieldMessage id={`${id}-message`} error={error} hint={hint} />
    </div>
  );
}
export function SelectField({
  children,
  error,
  hint,
  id,
  label,
  ...props
}: Readonly<SelectProps>) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <select
        {...props}
        aria-invalid={Boolean(error)}
        aria-describedby={error || hint ? `${id}-message` : props["aria-describedby"]}
        className="input"
        id={id}
      >
        {children}
      </select>
      <FieldMessage id={`${id}-message`} error={error} hint={hint} />
    </div>
  );
}
export function TextareaField({
  error,
  hint,
  id,
  label,
  ...props
}: Readonly<TextareaProps>) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <textarea
        {...props}
        aria-invalid={Boolean(error)}
        aria-describedby={error || hint ? `${id}-message` : props["aria-describedby"]}
        className="input textarea"
        id={id}
      />
      <FieldMessage id={`${id}-message`} error={error} hint={hint} />
    </div>
  );
}
