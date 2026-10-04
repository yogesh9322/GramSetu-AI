import { useState, useEffect } from "react"
import HomePage from "./pages/HomePage"
import LoginPage from "./pages/LoginPage"
import RegisterPage from "./pages/RegisterPage"
import ChatbotPage from "./pages/ChatbotPage"
import { AuthContext } from "./context/AuthContext"

export default function App() {
  const [page, setPage] = useState("home")
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem("token") || null)

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
    </AuthContext.Provider>
  )
}
