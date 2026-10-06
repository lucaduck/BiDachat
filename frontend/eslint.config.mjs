import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
import nextTypeScript from "eslint-config-next/typescript";

const config = [
  { ignores: [".next/**", "node_modules/**", "public/**"] },
  ...nextCoreWebVitals,
  ...nextTypeScript,
];
export default config;
