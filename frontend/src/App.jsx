import { useState, useEffect } from "react"
import HomePage from "./pages/HomePage"
import LoginPage from "./pages/LoginPage"
import RegisterPage from "./pages/RegisterPage"
import ChatbotPage from "./pages/ChatbotPage"
import ForgotPasswordPage from "./pages/ForgotPasswordPage"
import ResetPasswordPage from "./pages/ResetPasswordPage"
import { AuthContext } from "./context/AuthContext"

export default function App() {
  const [page, setPage] = useState("home")
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem("token") || null)

  useEffect(() => {
    // Check URL path and query parameters for deep linking
    const path = window.location.pathname.toLowerCase().replace(/\/$/, "")
    const params = new URLSearchParams(window.location.search)

    if (path === "/reset-password" || params.has("token")) {
      setPage("reset-password")
    } else if (path === "/forgot-password") {
      setPage("forgot-password")
    } else if (path === "/login") {
      setPage("login")
    } else if (path === "/register") {
      setPage("register")
    }
  }, [])

  useEffect(() => {
    if (token) {
      const saved = localStorage.getItem("user")
      if (saved) setUser(JSON.parse(saved))
    }
  }, [token])

  const login = (userData, authToken) => {
    setUser(userData)
    setToken(authToken)
    localStorage.setItem("token", authToken)
    localStorage.setItem("user", JSON.stringify(userData))
    setPage("chatbot")
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem("token")
    localStorage.removeItem("user")
    setPage("home")
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      {page === "home" && <HomePage setPage={setPage} />}
      {page === "login" && <LoginPage setPage={setPage} />}
      {page === "register" && <RegisterPage setPage={setPage} />}
      {page === "chatbot" && <ChatbotPage setPage={setPage} />}
      {page === "forgot-password" && <ForgotPasswordPage setPage={setPage} />}
      {page === "reset-password" && <ResetPasswordPage setPage={setPage} />}
    </AuthContext.Provider>
  )
}
