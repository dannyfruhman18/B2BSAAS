/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_DASHBOARD_SECRET: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
