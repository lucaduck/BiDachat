import Image from "next/image";

export function CircuitLogo({
  size = 46,
  priority = false,
}: Readonly<{ size?: number; priority?: boolean }>) {
  return (
    <span className="circuit-logo" aria-hidden="true">
      <Image
        className="circuit-logo-light"
        src="/brand/logo-bc-circuit-light.png"
        alt=""
        width={size}
        height={size}
        priority={priority}
      />
      <Image
        className="circuit-logo-dark"
        src="/brand/logo-bc-circuit.png"
        alt=""
        width={size}
        height={size}
        priority={priority}
      />
    </span>
  );
}
