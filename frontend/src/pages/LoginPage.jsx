import React, { useState, useContext } from "react"
import { AuthContext } from "../context/AuthContext"

const API = "http://127.0.0.1:8000"

export default function LoginPage({ setPage }) {
  const { login } = useContext(AuthContext)
  const [form, setForm] = useState({ email: "", password: "" })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [showPass, setShowPass] = useState(false)

  const handle = async (e) => {
    e.preventDefault()
    setLoading(true); setError("")
    try {
      const res = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form)
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || "Login failed")
      login(data.user, data.token)
    } catch (err) {
      if (err.name === "TypeError" || err.message === "Failed to fetch") {
        setError("Backend server is not running! Please start the backend server using: uvicorn main:app --reload")
      } else {
        setError(err.message)
      }
    } finally {
      setLoading(false)
    }
  }

  const fillDemo = () => {
    setForm({ email: "demo@gramsetu.ai", password: "demo123" })
  }

  return (
    <div style={{ minHeight: "100vh", background: "#070a08", display: "flex", fontFamily: "'Plus Jakarta Sans', sans-serif" }}>
      {/* Left Spotlight Panel */}
      <div style={{
        flex: 1.2,
        background: "linear-gradient(135deg, #09140b 0%, #142817 50%, #09140b 100%)",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        padding: "60px 80px",
        position: "relative",
        overflow: "hidden"
      }}>
        <div style={{ position: "absolute", top: -100, left: -100, width: 400, height: 400, background: "radial-gradient(circle, rgba(76,175,80,0.2) 0%, transparent 70%)", borderRadius: "50%" }} />

        <div style={{ maxWidth: 440, position: "relative", zIndex: 2 }}>
          <div style={{
            width: 72, height: 72, background: "linear-gradient(135deg,#1b5e20,#4caf50)",
            borderRadius: 20, display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 34, marginBottom: 28, boxShadow: "0 10px 30px rgba(76,175,80,0.35)"
          }}>
            🌾
          </div>

          <span className="badge badge-emerald" style={{ marginBottom: 16 }}>AUTHENTICATION WORKSPACE</span>

          <h1 style={{ fontFamily: "Playfair Display", fontSize: 40, fontWeight: 900, color: "#fff", lineHeight: 1.2, marginBottom: 16 }}>
            Welcome Back to <br /><span className="shimmer-text">GramSetu AI</span>
          </h1>

          <p style={{ fontSize: 16, color: "rgba(255,255,255,0.65)", lineHeight: 1.7, marginBottom: 40 }}>
            Access personalized government scheme advisories, saved chat logs, and voice assistance across Hindi, Marathi, and English.
          </p>

          {/* Quick Feature Checklist */}
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {[
              "🎤 Voice input in native regional dialects",
              "🤖 Groq Llama 3.3 70B RAG AI Pipeline",
              "📋 63 Central & State Government Schemes",
              "🔒 100% Free & Open Access Forever"
            ].map((feature, idx) => (
              <div key={idx} style={{
                display: "flex", alignItems: "center", gap: 12,
                background: "rgba(255,255,255,0.04)", border: "1px solid rgba(76,175,80,0.2)",
                borderRadius: 12, padding: "12px 16px", color: "rgba(255,255,255,0.85)", fontSize: 14, fontWeight: 500
              }}>
                {feature}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Login Form */}
      <div style={{
        width: 520, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center",
        padding: "50px 48px", background: "rgba(14, 22, 16, 0.95)", borderLeft: "1px solid rgba(255,255,255,0.08)"
      }}>
        <div style={{ width: "100%", maxWidth: 380 }}>
          {/* Back Link */}
          <button
            onClick={() => setPage("home")}
            style={{
              background: "none", border: "none", color: "rgba(255,255,255,0.45)", cursor: "pointer",
              fontSize: 14, fontWeight: 600, marginBottom: 36, display: "flex", alignItems: "center", gap: 6
            }}
          >
            ← Return to Homepage
          </button>

          <h2 style={{ fontSize: 32, fontWeight: 800, color: "#fff", marginBottom: 8 }}>Sign In</h2>
          <p style={{ fontSize: 14, color: "rgba(255,255,255,0.5)", marginBottom: 32 }}>
            Enter your credentials to manage your account
          </p>

          {error && (
            <div style={{
              background: "rgba(239,83,80,0.12)", border: "1px solid rgba(239,83,80,0.35)",
              borderRadius: 12, padding: "12px 16px", marginBottom: 24, fontSize: 14, color: "#ef5350",
              display: "flex", alignItems: "center", gap: 10
            }}>
              ⚠️ {error}
            </div>
          )}

          <form onSubmit={handle}>
            <div style={{ marginBottom: 20 }}>
              <label style={{ fontSize: 12, fontWeight: 700, color: "rgba(255,255,255,0.7)", textTransform: "uppercase", letterSpacing: 0.8, display: "block", marginBottom: 8 }}>
                Email Address
              </label>
              <input
                type="email"
                required
                value={form.email}
                onChange={e => setForm(p => ({ ...p, email: e.target.value }))}
                placeholder="name@example.com"
                style={{
                  width: "100%", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.12)",
                  borderRadius: 12, padding: "14px 16px", color: "#fff", fontSize: 15, outline: "none",
                  transition: "all 0.2s"
                }}
              />
            </div>

            <div style={{ marginBottom: 28 }}>
              <label style={{ fontSize: 12, fontWeight: 700, color: "rgba(255,255,255,0.7)", textTransform: "uppercase", letterSpacing: 0.8, display: "block", marginBottom: 8 }}>
                Password
              </label>
              <div style={{ position: "relative" }}>
                <input
                  type={showPass ? "text" : "password"}
                  required
                  value={form.password}
                  onChange={e => setForm(p => ({ ...p, password: e.target.value }))}
                  placeholder="Enter your password"
                  style={{
                    width: "100%", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.12)",
                    borderRadius: 12, padding: "14px 46px 14px 16px", color: "#fff", fontSize: 15, outline: "none",
                    transition: "all 0.2s"
                  }}
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  style={{ position: "absolute", right: 14, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", fontSize: 16, color: "rgba(255,255,255,0.4)" }}
                >
                  {showPass ? "🙈" : "👁️"}
                </button>
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn-primary" style={{ width: "100%", padding: 15, borderRadius: 12, fontSize: 16 }}>
              {loading ? "Signing in..." : "Sign In to GramSetu AI →"}
            </button>
          </form>

          {/* Quick Demo Fill Card */}
          <div style={{ marginTop: 24, background: "rgba(76,175,80,0.08)", border: "1px solid rgba(76,175,80,0.25)", borderRadius: 14, padding: "14px 18px", textAlign: "center" }}>
            <div style={{ fontSize: 12, color: "rgba(255,255,255,0.6)", marginBottom: 8 }}>Want to test without registering?</div>
            <button
              onClick={fillDemo}
              style={{
                background: "rgba(76,175,80,0.2)", border: "1px solid rgba(76,175,80,0.4)", color: "#4caf50",
                padding: "8px 16px", borderRadius: 8, fontSize: 13, fontWeight: 700, cursor: "pointer", width: "100%"
              }}
            >
              ⚡ Click to Fill Demo Credentials
            </button>
          </div>

          <div style={{ textAlign: "center", marginTop: 28, fontSize: 14, color: "rgba(255,255,255,0.5)" }}>
            Don't have an account?{" "}
            <button onClick={() => setPage("register")} style={{ background: "none", border: "none", color: "#4caf50", fontWeight: 700, cursor: "pointer", padding: 0 }}>
              Create Account Free →
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
