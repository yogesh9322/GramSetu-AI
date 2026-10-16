import React, { useState, useEffect } from "react"
import { API } from "../config"

export default function ResetPasswordPage({ setPage }) {
  const [token, setToken] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState(false)
  const [successMsg, setSuccessMsg] = useState("")

  useEffect(() => {
    // Read token from URL query parameters (?token=XYZ)
    const params = new URLSearchParams(window.location.search)
    const urlToken = params.get("token")
    if (urlToken) {
      setToken(urlToken.trim())
    }
  }, [])

  // Calculate password strength
  const getPasswordStrength = (pass) => {
    if (!pass) return { score: 0, label: "None", color: "#6b7280", width: "0%" }
    let score = 0
    if (pass.length >= 6) score += 1
    if (pass.length >= 8) score += 1
    if (/[A-Z]/.test(pass) && /[a-z]/.test(pass)) score += 1
    if (/\d/.test(pass)) score += 1
    if (/[^A-Za-z0-9]/.test(pass)) score += 1

    if (score <= 1) return { score: 1, label: "Weak", color: "#ef5350", width: "25%" }
    if (score <= 3) return { score: 2, label: "Fair", color: "#fbbf24", width: "65%" }
    return { score: 3, label: "Strong", color: "#4caf50", width: "100%" }
  }

  const strength = getPasswordStrength(password)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError("")

    if (!token) {
      setError("Password reset token is missing. Please click the reset link in your email.")
      return
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters long.")
      return
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match. Please verify and try again.")
      return
    }

    setLoading(true)
    try {
      const res = await fetch(`${API}/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password })
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || "Password reset failed. The link may have expired.")
      }
      setSuccess(true)
      setSuccessMsg(data.message || "Your password has been successfully reset! You can now log in.")
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
            🔑
          </div>

          <span className="badge badge-emerald" style={{ marginBottom: 16 }}>SECURITY CREDENTIALS</span>

          <h1 style={{ fontFamily: "Playfair Display", fontSize: 40, fontWeight: 900, color: "#fff", lineHeight: 1.2, marginBottom: 16 }}>
            Set a New <br /><span className="shimmer-text">Secure Password</span>
          </h1>

          <p style={{ fontSize: 16, color: "rgba(255,255,255,0.65)", lineHeight: 1.7, marginBottom: 40 }}>
            Create a strong password to protect your GramSetu AI advisory account, saved bookmarks, and village queries.
          </p>

          {/* Password Best Practices */}
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {[
              "✓ Minimum 6 characters (8+ recommended)",
              "✓ Use a mix of letters, numbers, and symbols",
              "✓ Avoid using your name or common words",
              "✓ Single-use token will expire immediately after reset"
            ].map((tip, idx) => (
              <div key={idx} style={{
                display: "flex", alignItems: "center", gap: 12,
                background: "rgba(255,255,255,0.04)", border: "1px solid rgba(76,175,80,0.2)",
                borderRadius: 12, padding: "12px 16px", color: "rgba(255,255,255,0.85)", fontSize: 14, fontWeight: 500
              }}>
                {tip}
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

          <h2 style={{ fontSize: 28, fontWeight: 800, color: "#fff", marginBottom: 8 }}>Set New Password</h2>
          <p style={{ fontSize: 14, color: "rgba(255,255,255,0.5)", marginBottom: 28 }}>
            Choose a strong, memorable password for your account.
          </p>

          {/* Missing Token Warning */}
          {!token && !success && (
            <div style={{
              background: "rgba(245,158,11,0.12)", border: "1px solid rgba(245,158,11,0.35)",
              borderRadius: 14, padding: "18px 20px", marginBottom: 24, fontSize: 14, color: "#fbbf24"
            }}>
              <div style={{ fontWeight: 700, marginBottom: 6 }}>⚠️ Missing Password Reset Token</div>
              <div style={{ fontSize: 13, lineHeight: 1.5, color: "rgba(255,255,255,0.7)", marginBottom: 14 }}>
                No reset token found in your URL. Please click the full link provided in your email or request a new reset link.
              </div>
              <button
                onClick={() => setPage("forgot-password")}
                style={{
                  background: "rgba(245,158,11,0.2)", border: "1px solid rgba(245,158,11,0.4)", color: "#fbbf24",
                  padding: "8px 14px", borderRadius: 8, fontSize: 13, fontWeight: 700, cursor: "pointer"
                }}
              >
                Request New Reset Link →
              </button>
            </div>
          )}

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
            <div style={{
              background: "rgba(76,175,80,0.12)", border: "1px solid rgba(76,175,80,0.4)",
              borderRadius: 16, padding: "26px 20px", textAlign: "center",
              boxShadow: "0 10px 30px rgba(0,0,0,0.3)"
            }}>
              <div style={{
                width: 58, height: 58, borderRadius: "50%", background: "rgba(76,175,80,0.2)",
                display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px",
                fontSize: 28, color: "#4caf50"
              }}>
                🎉
              </div>
              <h3 style={{ fontSize: 19, fontWeight: 800, color: "#fff", marginBottom: 10 }}>Password Reset Complete!</h3>
              <p style={{ fontSize: 14, color: "rgba(255,255,255,0.75)", lineHeight: 1.6, marginBottom: 22 }}>
                {successMsg}
              </p>
              <button
                onClick={() => {
                  // Clear query params from URL
                  if (window.history.pushState) {
                    window.history.pushState(null, "", "/login")
                  }
                  setPage("login")
                }}
                className="btn-primary"
                style={{ width: "100%", padding: "14px", borderRadius: 10, fontSize: 15, fontWeight: 700 }}
              >
                Proceed to Sign In →
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              {/* New Password */}
              <div style={{ marginBottom: 18 }}>
                <label style={{ fontSize: 12, fontWeight: 700, color: "rgba(255,255,255,0.7)", textTransform: "uppercase", letterSpacing: 0.8, display: "block", marginBottom: 8 }}>
                  New Password
                </label>
                <div style={{ position: "relative" }}>
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="Enter new password (min. 6 chars)"
                    style={{
                      width: "100%", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.12)",
                      borderRadius: 12, padding: "14px 46px 14px 16px", color: "#fff", fontSize: 15, outline: "none",
                      transition: "all 0.2s"
                    }}
                    onFocus={e => e.target.style.borderColor = "rgba(76,175,80,0.6)"}
                    onBlur={e => e.target.style.borderColor = "rgba(255,255,255,0.12)"}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{ position: "absolute", right: 14, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", fontSize: 16, color: "rgba(255,255,255,0.4)" }}
                  >
                    {showPassword ? "🙈" : "👁️"}
                  </button>
                </div>

                {/* Password Strength Meter */}
                {password.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 4, fontWeight: 600 }}>
                      <span style={{ color: "rgba(255,255,255,0.5)" }}>Strength:</span>
                      <span style={{ color: strength.color }}>{strength.label}</span>
                    </div>
                    <div style={{ width: "100%", height: 4, background: "rgba(255,255,255,0.1)", borderRadius: 100, overflow: "hidden" }}>
                      <div style={{ width: strength.width, height: "100%", background: strength.color, transition: "all 0.3s" }} />
                    </div>
                  </div>
                )}
              </div>

              {/* Confirm Password */}
              <div style={{ marginBottom: 26 }}>
                <label style={{ fontSize: 12, fontWeight: 700, color: "rgba(255,255,255,0.7)", textTransform: "uppercase", letterSpacing: 0.8, display: "block", marginBottom: 8 }}>
                  Confirm New Password
                </label>
                <div style={{ position: "relative" }}>
                  <input
                    type={showConfirm ? "text" : "password"}
                    required
                    value={confirmPassword}
                    onChange={e => setConfirmPassword(e.target.value)}
                    placeholder="Re-enter new password"
                    style={{
                      width: "100%", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.12)",
                      borderRadius: 12, padding: "14px 46px 14px 16px", color: "#fff", fontSize: 15, outline: "none",
                      transition: "all 0.2s"
                    }}
                    onFocus={e => e.target.style.borderColor = "rgba(76,175,80,0.6)"}
                    onBlur={e => e.target.style.borderColor = "rgba(255,255,255,0.12)"}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirm(!showConfirm)}
                    style={{ position: "absolute", right: 14, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", fontSize: 16, color: "rgba(255,255,255,0.4)" }}
                  >
                    {showConfirm ? "🙈" : "👁️"}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading || !token}
                className="btn-primary"
                style={{
                  width: "100%", padding: 15, borderRadius: 12, fontSize: 16, fontWeight: 700,
                  opacity: !token ? 0.5 : 1, cursor: !token ? "not-allowed" : "pointer"
                }}
              >
                {loading ? "Resetting Password..." : "Reset Password 🔒"}
              </button>

              <div style={{ marginTop: 20, textAlign: "center" }}>
                <button
                  type="button"
                  onClick={() => setPage("login")}
                  style={{ background: "none", border: "none", color: "rgba(255,255,255,0.45)", fontSize: 13, fontWeight: 600, cursor: "pointer" }}
                >
                  Cancel & Return to Sign In
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
