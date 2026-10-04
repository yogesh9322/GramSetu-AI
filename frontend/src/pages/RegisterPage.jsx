import React, { useState, useContext } from "react"
import { AuthContext } from "../context/AuthContext"

const API = "http://127.0.0.1:8000"

export default function RegisterPage({ setPage }) {
  const { login } = useContext(AuthContext)
  const [form, setForm] = useState({ name: "", email: "", password: "", confirm: "", language: "hindi", state: "Maharashtra" })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [step, setStep] = useState(1)

  const STATES = ["Maharashtra", "Uttar Pradesh", "Bihar", "Madhya Pradesh", "Rajasthan", "Gujarat", "Punjab", "Haryana", "Karnataka", "Tamil Nadu", "Other"]

  const nextStep = () => {
    if (!form.name.trim()) return setError("Please enter your full name")
    if (!form.email.trim()) return setError("Please enter your email address")
    if (!form.email.includes("@")) return setError("Please enter a valid email address")
    setError(""); setStep(2)
  }

  const handle = async (e) => {
    e.preventDefault()
    if (form.password.length < 6) return setError("Password must be at least 6 characters")
    if (form.password !== form.confirm) return setError("Passwords do not match")
    setLoading(true); setError("")
    try {
      const res = await fetch(`${API}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: form.name, email: form.email, password: form.password, language: form.language, state: form.state })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || "Registration failed")
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

  return (
    <div style={{ minHeight: "100vh", background: "#070a08", display: "flex", fontFamily: "'Plus Jakarta Sans', sans-serif" }}>
      {/* Left Panel */}
      <div style={{
        flex: 1.2, background: "linear-gradient(135deg,#09140b 0%,#142817 50%,#09140b 100%)",
        display: "flex", flexDirection: "column", justifyContent: "center", padding: "60px 80px", position: "relative"
      }}>
        <div style={{ maxWidth: 440, position: "relative", zIndex: 2 }}>
          <div style={{ fontSize: 60, marginBottom: 20 }}>🌾</div>
          <span className="badge badge-emerald" style={{ marginBottom: 16 }}>CREATE FREE ACCOUNT</span>

          <h1 style={{ fontFamily: "Playfair Display", fontSize: 40, fontWeight: 900, color: "#fff", lineHeight: 1.2, marginBottom: 16 }}>
            Join GramSetu AI <br /><span className="shimmer-text">Village Network</span>
          </h1>

          <p style={{ fontSize: 16, color: "rgba(255,255,255,0.65)", lineHeight: 1.7, marginBottom: 36 }}>
            Get instant answers on 63+ government schemes in Hindi, Marathi & English — zero fee, forever.
          </p>

          {/* Stepper Progress */}
          <div style={{ display: "flex", gap: 16, marginBottom: 36 }}>
            {[{ n: 1, title: "Personal Info" }, { n: 2, title: "Password & Security" }].map(s => (
              <div key={s.n} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{
                  width: 32, height: 32, borderRadius: "50%",
                  background: step >= s.n ? "linear-gradient(135deg,#2e7d32,#4caf50)" : "rgba(255,255,255,0.08)",
                  color: step >= s.n ? "#fff" : "rgba(255,255,255,0.4)",
                  display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 800
                }}>
                  {step > s.n ? "✓" : s.n}
                </div>
                <span style={{ fontSize: 13, fontWeight: 700, color: step >= s.n ? "#fff" : "rgba(255,255,255,0.4)" }}>
                  {s.title}
                </span>
              </div>
            ))}
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {["Instant voice input in native regional dialects", "Auto-saved query history & bookmarks", "Direct helpline numbers & portal links", "100% Free - No credit card required"].map((b, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 14, color: "rgba(255,255,255,0.8)" }}>
                <span style={{ color: "#4caf50", fontWeight: "bold" }}>✓</span> {b}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Form Panel */}
      <div style={{
        width: 520, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center",
        padding: "50px 48px", background: "rgba(14, 22, 16, 0.95)", borderLeft: "1px solid rgba(255,255,255,0.08)"
      }}>
        <div style={{ width: "100%", maxWidth: 380 }}>
          <button onClick={() => setPage("home")} style={{ background: "none", border: "none", color: "rgba(255,255,255,0.45)", cursor: "pointer", fontSize: 14, fontWeight: 600, marginBottom: 32 }}>
            ← Return to Homepage
          </button>

          <h2 style={{ fontSize: 30, fontWeight: 800, color: "#fff", marginBottom: 6 }}>Create Free Account</h2>
          <p style={{ fontSize: 14, color: "rgba(255,255,255,0.5)", marginBottom: 28 }}>
            Step {step} of 2 — {step === 1 ? "Enter basic details" : "Set security password"}
          </p>

          {error && (
            <div style={{ background: "rgba(239,83,80,0.12)", border: "1px solid rgba(239,83,80,0.35)", borderRadius: 12, padding: "12px 16px", marginBottom: 20, fontSize: 14, color: "#ef5350" }}>
              ⚠️ {error}
            </div>
          )}

          {step === 1 ? (
            <div>
              <div style={{ marginBottom: 18 }}>
                <label style={{ fontSize: 12, fontWeight: 700, color: "rgba(255,255,255,0.7)", textTransform: "uppercase", letterSpacing: 0.8, display: "block", marginBottom: 8 }}>
                  Full Name
                </label>
                <input
                  value={form.name}
                  onChange={e => setForm(p => ({ ...p, name: e.target.value }))}
                  placeholder="e.g. Rajesh Kumar"
                  style={{ width: "100%", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 12, padding: "14px 16px", color: "#fff", fontSize: 15, outline: "none" }}
                />
              </div>

              <div style={{ marginBottom: 18 }}>
                <label style={{ fontSize: 12, fontWeight: 700, color: "rgba(255,255,255,0.7)", textTransform: "uppercase", letterSpacing: 0.8, display: "block", marginBottom: 8 }}>
                  Email Address
                </label>
                <input
                  type="email"
                  value={form.email}
                  onChange={e => setForm(p => ({ ...p, email: e.target.value }))}
                  placeholder="name@example.com"
                  style={{ width: "100%", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 12, padding: "14px 16px", color: "#fff", fontSize: 15, outline: "none" }}
                />
              </div>

              <div style={{ marginBottom: 18 }}>
                <label style={{ fontSize: 12, fontWeight: 700, color: "rgba(255,255,255,0.7)", textTransform: "uppercase", letterSpacing: 0.8, display: "block", marginBottom: 8 }}>
                  State / Region
                </label>
                <select
                  value={form.state}
                  onChange={e => setForm(p => ({ ...p, state: e.target.value }))}
                  style={{ width: "100%", background: "#121d15", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 12, padding: "14px 16px", color: "#fff", fontSize: 15, outline: "none" }}
                >
                  {STATES.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>

              <div style={{ marginBottom: 28 }}>
                <label style={{ fontSize: 12, fontWeight: 700, color: "rgba(255,255,255,0.7)", textTransform: "uppercase", letterSpacing: 0.8, display: "block", marginBottom: 10 }}>
                  Preferred Language
                </label>
                <div style={{ display: "flex", gap: 8 }}>
                  {[
                    { v: "marathi", l: "मराठी", icon: "🟠" },
                    { v: "hindi", l: "हिंदी", icon: "🇮🇳" },
                    { v: "english", l: "English", icon: "🔵" }
                  ].map(l => (
                    <button
                      key={l.v}
                      type="button"
                      onClick={() => setForm(p => ({ ...p, language: l.v }))}
                      style={{
                        flex: 1, padding: "12px 8px", borderRadius: 10,
                        border: `1px solid ${form.language === l.v ? "rgba(76,175,80,0.6)" : "rgba(255,255,255,0.1)"}`,
                        background: form.language === l.v ? "rgba(76,175,80,0.15)" : "rgba(255,255,255,0.03)",
                        color: form.language === l.v ? "#4caf50" : "rgba(255,255,255,0.6)",
                        fontSize: 13, fontWeight: 700, cursor: "pointer", transition: "all 0.2s"
                      }}
                    >
                      {l.icon} {l.l}
                    </button>
                  ))}
                </div>
              </div>

              <button className="btn-primary" onClick={nextStep} style={{ width: "100%", padding: 15, borderRadius: 12, fontSize: 16 }}>
                Continue to Password →
              </button>
            </div>
          ) : (
            <form onSubmit={handle}>
              <div style={{ marginBottom: 18 }}>
                <label style={{ fontSize: 12, fontWeight: 700, color: "rgba(255,255,255,0.7)", textTransform: "uppercase", letterSpacing: 0.8, display: "block", marginBottom: 8 }}>
                  Password
                </label>
                <input
                  type="password"
                  value={form.password}
                  onChange={e => setForm(p => ({ ...p, password: e.target.value }))}
                  placeholder="Min. 6 characters"
                  style={{ width: "100%", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 12, padding: "14px 16px", color: "#fff", fontSize: 15, outline: "none" }}
                />
              </div>

              <div style={{ marginBottom: 28 }}>
                <label style={{ fontSize: 12, fontWeight: 700, color: "rgba(255,255,255,0.7)", textTransform: "uppercase", letterSpacing: 0.8, display: "block", marginBottom: 8 }}>
                  Confirm Password
                </label>
                <input
                  type="password"
                  value={form.confirm}
                  onChange={e => setForm(p => ({ ...p, confirm: e.target.value }))}
                  placeholder="Re-enter password"
                  style={{ width: "100%", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 12, padding: "14px 16px", color: "#fff", fontSize: 15, outline: "none" }}
                />
                {form.confirm && form.password === form.confirm && form.password.length >= 6 && (
                  <div style={{ fontSize: 12, color: "#4caf50", marginTop: 8, fontWeight: 600 }}>✅ Passwords match!</div>
                )}
              </div>

              <div style={{ display: "flex", gap: 12 }}>
                <button type="button" onClick={() => setStep(1)} className="btn-outline" style={{ flex: 1, padding: 14, borderRadius: 12 }}>
                  ← Back
                </button>
                <button type="submit" disabled={loading} className="btn-primary" style={{ flex: 2, padding: 14, borderRadius: 12 }}>
                  {loading ? "Registering..." : "Complete Setup 🚀"}
                </button>
              </div>
            </form>
          )}

          <div style={{ textAlign: "center", marginTop: 28, fontSize: 14, color: "rgba(255,255,255,0.5)" }}>
            Already have an account?{" "}
            <button onClick={() => setPage("login")} style={{ background: "none", border: "none", color: "#4caf50", fontWeight: 700, cursor: "pointer", padding: 0 }}>
              Sign In →
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
