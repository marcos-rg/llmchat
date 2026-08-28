/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Absolute origin + `/api` prefix of the backend, e.g. `http://localhost:8000/api`.
   *  Inlined at build time by Vite, so changing it needs a rebuild, not a restart. */
  readonly VITE_API_BASE_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
