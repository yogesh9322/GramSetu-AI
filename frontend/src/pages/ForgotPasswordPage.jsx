import React, { useState } from "react"
import { API } from "../config"

export default function ForgotPasswordPage({ setPage }) {
  const [email, setEmail] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState(false)
  const [successMsg, setSuccessMsg] = useState("")
  const [devResetUrl, setDevResetUrl] = useState("")

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError("")
    
    const trimmedEmail = email.trim().toLowerCase()
    if (!trimmedEmail) {
      setError("Please enter your email address.")
      return
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(trimmedEmail)) {
      setError("Please enter a valid email address (e.g. name@example.com).")
      return
    }

    setLoading(true)
    try {
      const res = await fetch(`${API}/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: trimmedEmail })
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || "Failed to process request. Please try again.")
      }
      setSuccess(true)
      setSuccessMsg(data.message || "If an account exists with this email, a password reset link has been sent to your inbox.")
      if (data.dev_reset_url) {
        setDevResetUrl(data.dev_reset_url)
      }
    } catch (err) {
      if (err.name === "TypeError" || err.message === "Failed to fetch") {
        setError(
          window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
            ? "Backend server is not running! Please start the backend server using: uvicorn main:app --reload"
            : "Backend server is waking up. Render free instances take ~30 seconds to wake up from sleep — please wait a moment and try again."
        )
      } else {
        setError(err.message)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-split-layout" style={{ minHeight: "100vh", background: "#070a08", display: "flex", fontFamily: "'Plus Jakarta Sans', sans-serif" }}>
      {/* Left Spotlight Panel */}
      <div className="auth-left-panel" style={{
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
            🔒
          </div>

          <span className="badge badge-emerald" style={{ marginBottom: 16 }}>ACCOUNT RECOVERY</span>

          <h1 style={{ fontFamily: "Playfair Display", fontSize: 40, fontWeight: 900, color: "#fff", lineHeight: 1.2, marginBottom: 16 }}>
            Recover Your <br /><span className="shimmer-text">GramSetu AI</span> Account
          </h1>

          <p style={{ fontSize: 16, color: "rgba(255,255,255,0.65)", lineHeight: 1.7, marginBottom: 40 }}>
            Don't worry — it happens! Enter your registered email address and we'll send you a secure link to create a new password.
          </p>

          {/* Quick Security Checklist */}
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {[
              "⏱️ Secure one-time reset link valid for 20 minutes",
              "🔐 Cryptographically hashed tokens for total privacy",
              "🌾 Immediate access restored to all 63+ schemes",
              "🛡️ Zero password stored in plain-text ever"
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

      {/* Right Form Panel */}
      <div className="auth-right-panel" style={{
        width: 520, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center",
        padding: "50px 48px", background: "rgba(14, 22, 16, 0.95)", borderLeft: "1px solid rgba(255,255,255,0.08)"
      }}>
        <div style={{ width: "100%", maxWidth: 380 }}>
          {/* Back to Sign In Link */}
          <button
            onClick={() => setPage("login")}
            style={{
              background: "none", border: "none", color: "rgba(255,255,255,0.45)", cursor: "pointer",
              fontSize: 14, fontWeight: 600, marginBottom: 28, display: "flex", alignItems: "center", gap: 6,
              transition: "color 0.2s"
            }}
            onMouseEnter={e => e.target.style.color = "#4caf50"}
            onMouseLeave={e => e.target.style.color = "rgba(255,255,255,0.45)"}
          >
            ← Return to Sign In
          </button>

          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
            <span style={{ fontSize: 28 }}>🌾</span>
            <span style={{ fontSize: 18, fontWeight: 800, color: "#fff", fontFamily: "Playfair Display" }}>GramSetu AI</span>
          </div>

          <h2 style={{ fontSize: 28, fontWeight: 800, color: "#fff", marginBottom: 8 }}>Forgot Your Password?</h2>
          <p style={{ fontSize: 14, color: "rgba(255,255,255,0.5)", marginBottom: 28, lineHeight: 1.5 }}>
            Enter your registered email address. We'll send you a link to reset your password.
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

          {success ? (
            devResetUrl ? (
              <div style={{
                background: "rgba(255, 193, 7, 0.08)", border: "1px solid rgba(255, 193, 7, 0.35)",
                borderRadius: 16, padding: "24px 20px", textAlign: "center",
                boxShadow: "0 10px 30px rgba(0,0,0,0.3)"
              }}>
                <div style={{
                  width: 56, height: 56, borderRadius: "50%", background: "rgba(255, 193, 7, 0.18)",
                  display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px",
                  fontSize: 26, color: "#ffc107"
                }}>
                  🔑
                </div>
                <h3 style={{ fontSize: 18, fontWeight: 800, color: "#fff", marginBottom: 10 }}>Password Reset Ready!</h3>
                <p style={{ fontSize: 13, color: "rgba(255,255,255,0.75)", lineHeight: 1.6, marginBottom: 16 }}>
                  {successMsg}
                </p>
                <div style={{
                  background: "rgba(0,0,0,0.45)", border: "1px dashed rgba(255, 193, 7, 0.4)",
                  borderRadius: 10, padding: "10px 12px", fontSize: 12, color: "#ffc107",
                  wordBreak: "break-all", marginBottom: 18, userSelect: "all", fontFamily: "monospace"
                }}>
                  {devResetUrl}
                </div>
                <a
                  href={devResetUrl}
                  style={{
                    display: "block", width: "100%", padding: "14px", borderRadius: 12,
                    fontSize: 15, fontWeight: 800, background: "linear-gradient(135deg, #f59e0b, #d97706)",
                    color: "#000", textAlign: "center", textDecoration: "none",
                    boxShadow: "0 4px 15px rgba(245, 158, 11, 0.35)", marginBottom: 12
                  }}
                >
                  👉 Click Here to Reset Your Password Now
                </a>
                <button
                  type="button"
                  onClick={() => setPage("login")}
                  style={{ background: "none", border: "none", color: "rgba(255,255,255,0.5)", fontSize: 13, cursor: "pointer", marginTop: 6 }}
                >
                  Return to Sign In
                </button>
              </div>
            ) : (
              <div style={{
                background: "rgba(76,175,80,0.1)", border: "1px solid rgba(76,175,80,0.35)",
                borderRadius: 16, padding: "24px 20px", textAlign: "center",
                boxShadow: "0 10px 30px rgba(0,0,0,0.3)"
              }}>
                <div style={{
                  width: 56, height: 56, borderRadius: "50%", background: "rgba(76,175,80,0.2)",
                  display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px",
                  fontSize: 26, color: "#4caf50"
                }}>
                  ✉️
                </div>
                <h3 style={{ fontSize: 18, fontWeight: 800, color: "#fff", marginBottom: 10 }}>Check Your Inbox</h3>
                <p style={{ fontSize: 14, color: "rgba(255,255,255,0.75)", lineHeight: 1.6, marginBottom: 20 }}>
                  {successMsg}
                </p>
                <div style={{ background: "rgba(255,255,255,0.04)", borderRadius: 10, padding: "10px 14px", fontSize: 12, color: "rgba(255,255,255,0.5)", marginBottom: 20 }}>
                  ⏱️ The reset link expires in <strong>20 minutes</strong>. Don't see it? Check your Spam or Promotions folder.
                </div>
                <button
                  onClick={() => setPage("login")}
                  className="btn-primary"
                  style={{ width: "100%", padding: "12px", borderRadius: 10, fontSize: 14, fontWeight: 700 }}
                >
                  Back to Sign In
                </button>
              </div>
            )
          ) : (
            <form onSubmit={handleSubmit}>
              <div style={{ marginBottom: 24 }}>
                <label style={{ fontSize: 12, fontWeight: 700, color: "rgba(255,255,255,0.7)", textTransform: "uppercase", letterSpacing: 0.8, display: "block", marginBottom: 8 }}>
                  Registered Email Address
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  autoFocus
                  style={{
                    width: "100%", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.12)",
                    borderRadius: 12, padding: "14px 16px", color: "#fff", fontSize: 15, outline: "none",
                    transition: "all 0.2s"
                  }}
                  onFocus={e => e.target.style.borderColor = "rgba(76,175,80,0.6)"}
                  onBlur={e => e.target.style.borderColor = "rgba(255,255,255,0.12)"}
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-primary"
                style={{ width: "100%", padding: 15, borderRadius: 12, fontSize: 16, fontWeight: 700 }}
              >
                {loading ? "Sending Reset Link..." : "Send Reset Link ✉️"}
              </button>

              <div style={{ marginTop: 24, textAlign: "center" }}>
                <span style={{ fontSize: 13, color: "rgba(255,255,255,0.45)" }}>Remember your password? </span>
                <button
                  type="button"
                  onClick={() => setPage("login")}
                  style={{ background: "none", border: "none", color: "#4caf50", fontSize: 13, fontWeight: 700, cursor: "pointer", padding: 0 }}
                >
                  Sign In
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
