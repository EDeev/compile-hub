import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import { resolve } from "path"

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 3000,
    // API в разработке: compilehub-api на :8000 (WebSocket — тоже через прокси)
    proxy: {
      "/api": { target: "http://localhost:8000", ws: true }
    }
  },
  build: {
    // крупные библиотеки — отдельными файлами: кэшируются между обновлениями сайта
    rollupOptions: {
      output: {
        manualChunks: {
          react: [
            "react",
            "react/jsx-runtime",
            "react-dom",
            "react-dom/client",
            "react-router-dom"
          ],
          xterm: ["@xterm/xterm", "@xterm/addon-fit"]
        }
      }
    }
  },
  resolve: {
    alias: {
      "@": resolve(__dirname, "./src"),
      "@components": resolve(__dirname, "./src/components"),
      "@assets": resolve(__dirname, "./src/assets"),
      "@styles": resolve(__dirname, "./src/styles")
    }
  }
})
