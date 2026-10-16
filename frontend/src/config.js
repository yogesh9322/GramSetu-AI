// Centralized API configuration with automatic production fallback
export const API = import.meta.env.VITE_API_URL || (
  typeof window !== "undefined" && (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
    ? "http://127.0.0.1:8000"
    : "https://gramsetu-ai-backend.onrender.com"
)
