import React, { useState, useEffect, useRef } from "react"
import { ALL_SCHEMES, CAT_COLORS } from "../data/schemesData"
import SchemeModal from "../components/SchemeModal"

const STATS = [
  { num: "63+", label: "Govt Schemes Covered", icon: "📋" },
  { num: "3", label: "Languages (Hindi, Marathi, English)", icon: "🌐" },
  { num: "800M+", label: "Rural Indian Citizens", icon: "🇮🇳" },
  { num: "100%", label: "Free Forever & Open", icon: "💚" },
]

const FEATURES = [
  { icon: "🎤", title: "Voice Input & Audio Response", desc: "Speak naturally in Hindi, Marathi, or English and hear instant audio answers tailored for rural users." },
  { icon: "🤖", title: "Llama 3.3 70B RAG Engine", desc: "Powered by Groq high-speed AI with RAG pipeline for 100% grounded, accurate government policy answers." },
  { icon: "🌐", title: "Automatic Language Detection", desc: "No manual settings needed — GramSetu AI auto-detects your native language automatically." },
  { icon: "📋", title: "63+ Scheme Knowledgebase", desc: "Exhaustive coverage of central & state agriculture, health, housing, financial & pension schemes." },
  { icon: "⚡", title: "Step-by-Step Application Guide", desc: "Get clear document checklists, official portal links, and toll-free helpline numbers." },
  { icon: "🔒", title: "Secure & Account Saving", desc: "Personal account login with saved search history, preference settings, and total privacy." },
]

const FAQS = [
  { q: "GramSetu AI (ग्रामसेतू) क्या है?", a: "GramSetu AI एक AI संचालित डिजिटल सहायक है जो ग्रामीण नागरिकों को 63+ सरकारी योजनाओं (जैसे PM Kisan, Ayushman Bharat, PM Awas) की जानकारी हिंदी, मराठी और अंग्रेजी में देता है।" },
  { q: "क्या यह सेवा मुफ्त है?", a: "हाँ! GramSetu AI 100% मुफ्त है और इसे ग्रामीण भारत के सशक्तिकरण के लिए बनाया गया है।" },
  { q: "क्या मैं बोलकर (Voice) सवाल पूछ सकता हूँ?", a: "बिल्कुल! आप माइक आइकन पर क्लिक करके हिंदी या मराठी में बोल सकते हैं और AI आपको उत्तर बोलकर भी सुनाएगा।" },
  { q: "कौन-कौन सी भाषाएं supported हैं?", a: "हिंदी (Hindi), मराठी (Marathi), और अंग्रेजी (English) — AI अपने आप आपकी भाषा पहचान लेता है।" }
]

export default function HomePage({ setPage }) {
  const [scrollY, setScrollY] = useState(0)
  const [typedText, setTypedText] = useState("")
  const [search, setSearch] = useState("")
  const [activeCategory, setActiveCategory] = useState("all")
  const [selectedScheme, setSelectedScheme] = useState(null)
  const [activeFaq, setActiveFaq] = useState(null)
  const [activeDemoScheme, setActiveDemoScheme] = useState(0)

  const phrases = [
    "PM Kisan yojana ke liye kaun eligible hai?",
    "आयुष्मान भारत कार्ड कैसे बनाएं?",
    "मनरेगा जॉब कार्ड कसे मिळवायचे?",
    "PM Ujjwala yojana free LPG cylinder eligibility?",
    "Sukanya Samridhi account mein kitna interest milta hai?"
  ]
  const phraseRef = useRef(0)
  const charRef = useRef(0)
  const deletingRef = useRef(false)

  useEffect(() => {
    const onScroll = () => setScrollY(window.scrollY)
    window.addEventListener("scroll", onScroll)
    return () => window.removeEventListener("scroll", onScroll)
  }, [])

  useEffect(() => {
    const timer = setInterval(() => {
      const phrase = phrases[phraseRef.current]
      if (!deletingRef.current) {
        if (charRef.current < phrase.length) {
          setTypedText(phrase.slice(0, charRef.current + 1))
          charRef.current++
        } else {
          setTimeout(() => { deletingRef.current = true }, 1800)
        }
      } else {
        if (charRef.current > 0) {
          setTypedText(phrase.slice(0, charRef.current - 1))
          charRef.current--
        } else {
          deletingRef.current = false
          phraseRef.current = (phraseRef.current + 1) % phrases.length
        }
      }
    }, 55)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveDemoScheme(prev => (prev + 1) % ALL_SCHEMES.length)
    }, 2500)
    return () => clearInterval(interval)
  }, [])

  const categories = ["all", ...Object.keys(CAT_COLORS)]

  const filteredSchemes = ALL_SCHEMES.filter(s => {
    const matchesSearch = !search ||
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.benefit.toLowerCase().includes(search.toLowerCase()) ||
      s.category.toLowerCase().includes(search.toLowerCase())
    const matchesCategory = activeCategory === "all" || s.category === activeCategory
    return matchesSearch && matchesCategory
  })

  return (
    <div style={{ background: "#070a08", color: "#fff", minHeight: "100vh", overflowX: "hidden" }}>
      {/* NAVBAR */}
      <nav style={{
        position: "fixed", top: 0, left: 0, right: 0, zIndex: 100,
        background: scrollY > 30 ? "rgba(7, 10, 8, 0.92)" : "transparent",
        backdropFilter: scrollY > 30 ? "blur(20px)" : "none",
        borderBottom: scrollY > 30 ? "1px solid rgba(76, 175, 80, 0.2)" : "1px solid transparent",
        transition: "all 0.3s ease", padding: "0 6%"
      }}>
        <div style={{ maxWidth: 1240, margin: "0 auto", display: "flex", alignItems: "center", justifyContent: "space-between", height: 74 }}>
          {/* Logo */}
          <div style={{ display: "flex", alignItems: "center", gap: 12, cursor: "pointer" }} onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}>
            <div style={{
              width: 42, height: 42, background: "linear-gradient(135deg, #1b5e20 0%, #4caf50 100%)",
              borderRadius: 12, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22,
              boxShadow: "0 4px 18px rgba(76, 175, 80, 0.4)"
            }}>
              🌾
            </div>
            <div>
              <div style={{ fontFamily: "Playfair Display", fontSize: 22, fontWeight: 800, color: "#fff", letterSpacing: -0.5 }}>
                GramSetu <span style={{ color: "#4caf50" }}>AI</span>
              </div>
              <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", textTransform: "uppercase", letterSpacing: 1, fontWeight: 600 }}>
                Village AI Bridge
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <div style={{ display: "flex", alignItems: "center", gap: 32 }}>
            {[
              { label: "Overview", id: "hero" },
              { label: "Key Features", id: "features" },
              { label: "63 Schemes", id: "schemes" },
              { label: "FAQ", id: "faq" }
            ].map(item => (
              <span
                key={item.label}
                onClick={() => {
                  if (item.id === "hero") window.scrollTo({ top: 0, behavior: "smooth" })
                  else document.getElementById(item.id)?.scrollIntoView({ behavior: "smooth" })
                }}
                style={{ fontSize: 14, fontWeight: 600, color: "rgba(255,255,255,0.7)", cursor: "pointer", transition: "color 0.2s" }}
                onMouseEnter={e => e.target.style.color = "#4caf50"}
                onMouseLeave={e => e.target.style.color = "rgba(255,255,255,0.7)"}
              >
                {item.label}
              </span>
            ))}
          </div>

          {/* Action Buttons */}
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <button
              onClick={() => setPage("login")}
              style={{
                background: "rgba(255,255,255,0.05)",
                border: "1px solid rgba(255,255,255,0.15)",
                color: "#fff", padding: "9px 20px", borderRadius: 10,
                fontSize: 14, fontWeight: 600, cursor: "pointer", transition: "all 0.2s"
              }}
              onMouseEnter={e => { e.target.style.background = "rgba(76,175,80,0.15)"; e.target.style.borderColor = "rgba(76,175,80,0.5)" }}
              onMouseLeave={e => { e.target.style.background = "rgba(255,255,255,0.05)"; e.target.style.borderColor = "rgba(255,255,255,0.15)" }}
            >
              Log In
            </button>
            <button
              onClick={() => setPage("register")}
              className="btn-primary"
              style={{ padding: "9px 22px", borderRadius: 10, fontSize: 14 }}
            >
              Get Started Free ✨
            </button>
          </div>
        </div>
      </nav>

      {/* HERO SECTION */}
      <section id="hero" style={{ minHeight: "100vh", display: "flex", alignItems: "center", position: "relative", padding: "120px 6% 60px" }}>
        {/* Background Radial Lights */}
        <div style={{ position: "absolute", top: "10%", left: "50%", transform: "translateX(-50%)", width: 800, height: 500, background: "radial-gradient(ellipse 60% 50% at 50% 0%, rgba(76,175,80,0.22) 0%, transparent 70%)", pointerEvents: "none" }} />
        <div style={{ position: "absolute", bottom: "10%", right: "5%", width: 400, height: 400, background: "radial-gradient(circle, rgba(139,195,74,0.08) 0%, transparent 70%)", pointerEvents: "none" }} />

        <div style={{ maxWidth: 1240, margin: "0 auto", width: "100%", display: "grid", gridTemplateColumns: "1.1fr 0.9fr", gap: 60, alignItems: "center" }}>
          {/* Left Column */}
          <div>
            <div style={{ display: "inline-flex", alignItems: "center", gap: 10, background: "rgba(76, 175, 80, 0.12)", border: "1px solid rgba(76, 175, 80, 0.3)", borderRadius: 100, padding: "7px 18px", marginBottom: 28 }}>
              <span style={{ width: 8, height: 8, background: "#4caf50", borderRadius: "50%", boxShadow: "0 0 10px #4caf50" }} />
              <span style={{ fontSize: 13, color: "#4caf50", fontWeight: 700, letterSpacing: 0.5 }}>
                🌾 MULTILINGUAL AI FOR RURAL INDIA
              </span>
            </div>

            <h1 style={{ fontFamily: "Playfair Display", fontSize: "clamp(42px, 5.2vw, 66px)", fontWeight: 900, lineHeight: 1.12, marginBottom: 24 }}>
              Connecting Villages <br />
              <span className="shimmer-text">To 63+ Government</span> <br />
              Schemes & Benefits
            </h1>

            <p style={{ fontSize: 18, color: "rgba(255,255,255,0.7)", lineHeight: 1.7, marginBottom: 36, maxWidth: 540 }}>
              Discover eligibility, required documents, and step-by-step guidance in <strong style={{ color: "#fff" }}>Hindi, Marathi, and English</strong> using voice or text AI assistant.
            </p>

            {/* Interactive Prompt Simulated Bar */}
            <div style={{ background: "rgba(22, 33, 25, 0.7)", border: "1px solid rgba(76, 175, 80, 0.3)", borderRadius: 16, padding: "16px 20px", marginBottom: 36, display: "flex", alignItems: "center", gap: 14, boxShadow: "0 8px 30px rgba(0,0,0,0.3)" }}>
              <span style={{ fontSize: 20 }}>🎤</span>
              <div style={{ fontSize: 15, color: "rgba(255,255,255,0.85)", fontFamily: "'Tiro Devanagari Hindi', 'Plus Jakarta Sans', sans-serif", flex: 1, minHeight: 24 }}>
                {typedText}<span style={{ borderRight: "2px solid #4caf50" }}>&nbsp;</span>
              </div>
              <span style={{ background: "rgba(76,175,80,0.2)", color: "#4caf50", padding: "4px 10px", borderRadius: 8, fontSize: 12, fontWeight: 700 }}>
                Live Demo
              </span>
            </div>

            {/* CTA Buttons */}
            <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
              <button onClick={() => setPage("register")} className="btn-primary" style={{ padding: "16px 36px", fontSize: 16, borderRadius: 14 }}>
                Launch Free Assistant 🚀
              </button>
              <button onClick={() => setPage("login")} className="btn-outline" style={{ padding: "16px 28px", fontSize: 16, borderRadius: 14 }}>
                Demo Credentials →
              </button>
            </div>
          </div>

          {/* Right Column - Interactive Chat Simulation */}
          <div style={{ position: "relative" }}>
            <div className="glass-card animate-float" style={{ padding: 24, borderRadius: 24, border: "1px solid rgba(76, 175, 80, 0.3)", boxShadow: "0 20px 50px rgba(0,0,0,0.5), 0 0 30px rgba(76,175,80,0.15)" }}>
              {/* Header */}
              <div style={{ background: "linear-gradient(135deg,#1b5e20,#2e7d32)", padding: "16px 20px", borderRadius: 16, display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <div style={{ width: 40, height: 40, background: "rgba(255,255,255,0.2)", borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20 }}>🌾</div>
                  <div>
                    <div style={{ fontSize: 15, fontWeight: 800, color: "#fff" }}>GramSetu AI Assistant</div>
                    <div style={{ fontSize: 11, color: "rgba(255,255,255,0.75)", display: "flex", alignItems: "center", gap: 6 }}>
                      <span style={{ width: 6, height: 6, background: "#4caf50", borderRadius: "50%" }} />
                      Groq Llama 3.3 70B RAG Active
                    </div>
                  </div>
                </div>
                <span className="badge badge-emerald">Live</span>
              </div>

              {/* Chat Messages */}
              <div style={{ display: "flex", flexDirection: "column", gap: 14, marginBottom: 20 }}>
                <div style={{ alignSelf: "flex-end", background: "linear-gradient(135deg, #2e7d32, #4caf50)", padding: "12px 16px", borderRadius: "16px 16px 4px 16px", maxWidth: "85%", fontSize: 13, color: "#fff", fontWeight: 500 }}>
                  PM Kisan scheme ke liye पात्रता (eligibility) kya hai? 🌾
                </div>

                <div style={{ alignSelf: "flex-start", background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)", padding: "14px 16px", borderRadius: "16px 16px 16px 4px", maxWidth: "90%", fontSize: 13, color: "rgba(255,255,255,0.9)", lineHeight: 1.6 }}>
                  <strong style={{ color: "#4caf50" }}>PM-KISAN (पीएम किसान) पात्रता:</strong><br />
                  ✅ Small & Marginal farmer families with cultivable land<br />
                  💰 Financial Benefit: ₹6,000 / year in 3 installments<br />
                  📑 Documents: Aadhaar card, Bank Account, Land ownership<br />
                  📞 Helpline: 155261 / 1800115526
                </div>

                {/* Rotating Scheme Spotlight */}
                <div style={{ background: "rgba(76, 175, 80, 0.1)", border: "1px solid rgba(76, 175, 80, 0.3)", borderRadius: 14, padding: "12px 16px", display: "flex", alignItems: "center", gap: 12 }}>
                  <span style={{ fontSize: 26 }}>{ALL_SCHEMES[activeDemoScheme].icon}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: "#fff" }}>{ALL_SCHEMES[activeDemoScheme].name}</div>
                    <div style={{ fontSize: 12, color: "#4caf50", fontWeight: 600 }}>💰 {ALL_SCHEMES[activeDemoScheme].benefit}</div>
                  </div>
                  <span style={{ fontSize: 11, background: `${CAT_COLORS[ALL_SCHEMES[activeDemoScheme].category]}33`, color: CAT_COLORS[ALL_SCHEMES[activeDemoScheme].category] || "#4caf50", padding: "3px 8px", borderRadius: 6, fontWeight: 700 }}>
                    {ALL_SCHEMES[activeDemoScheme].category}
                  </span>
                </div>
              </div>

              {/* Input Simulated */}
              <div style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 12, padding: "10px 14px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span style={{ fontSize: 13, color: "rgba(255,255,255,0.4)" }}>Ask anything in Hindi, Marathi, or English...</span>
                <div style={{ width: 32, height: 32, background: "linear-gradient(135deg,#2e7d32,#4caf50)", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14 }}>🎤</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* INFINITE MARQUEE TICKER */}
      <div style={{ borderTop: "1px solid rgba(76,175,80,0.15)", borderBottom: "1px solid rgba(76,175,80,0.15)", background: "rgba(76,175,80,0.03)", padding: "18px 0", overflow: "hidden" }}>
        <div className="marquee-container">
          <div className="marquee-content">
            {ALL_SCHEMES.slice(0, 30).map((s, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(76,175,80,0.2)", borderRadius: 100, padding: "8px 20px", whiteSpace: "nowrap", flexShrink: 0 }}>
                <span>{s.icon}</span>
                <span style={{ fontSize: 13, fontWeight: 700, color: "#fff" }}>{s.name}</span>
                <span style={{ fontSize: 12, color: "#4caf50", fontWeight: 600 }}>• {s.benefit}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* STATS SECTION */}
      <section style={{ padding: "90px 6%" }}>
        <div style={{ maxWidth: 1240, margin: "0 auto", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 24 }}>
          {STATS.map((s, i) => (
            <div key={i} className="glass-card" style={{ padding: "36px 28px", textAlign: "center" }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>{s.icon}</div>
              <div style={{ fontFamily: "Playfair Display", fontSize: 46, fontWeight: 900, color: "#4caf50", marginBottom: 6 }}>{s.num}</div>
              <div style={{ fontSize: 14, color: "rgba(255,255,255,0.6)", fontWeight: 600 }}>{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* FEATURES SECTION */}
      <section id="features" style={{ padding: "90px 6%", background: "rgba(255,255,255,0.01)", borderTop: "1px solid rgba(255,255,255,0.05)" }}>
        <div style={{ maxWidth: 1240, margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: 60 }}>
            <span className="badge badge-emerald" style={{ marginBottom: 12 }}>REVOLUTIONIZING RURAL AID</span>
            <h2 style={{ fontFamily: "Playfair Display", fontSize: "clamp(32px, 4vw, 48px)", fontWeight: 900, marginTop: 8 }}>
              Built Exclusively for <span className="shimmer-text">Rural Citizens</span>
            </h2>
            <p style={{ fontSize: 16, color: "rgba(255,255,255,0.55)", maxWidth: 540, margin: "14px auto 0" }}>
              Designed to eliminate complex portals, language barriers, and middleman exploitation.
            </p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 24 }}>
            {FEATURES.map((f, i) => (
              <div key={i} className="glass-card" style={{ padding: "32px 28px" }}>
                <div style={{ width: 52, height: 52, background: "rgba(76, 175, 80, 0.12)", border: "1px solid rgba(76, 175, 80, 0.25)", borderRadius: 14, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 26, marginBottom: 20 }}>
                  {f.icon}
                </div>
                <h3 style={{ fontSize: 19, fontWeight: 800, color: "#fff", marginBottom: 10 }}>{f.title}</h3>
                <p style={{ fontSize: 14, color: "rgba(255,255,255,0.6)", lineHeight: 1.65 }}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SCHEMES EXPLORER GRID */}
      <section id="schemes" style={{ padding: "90px 6%" }}>
        <div style={{ maxWidth: 1240, margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: 40 }}>
            <span className="badge badge-emerald" style={{ marginBottom: 12 }}>KNOWLEDGE BASE</span>
            <h2 style={{ fontFamily: "Playfair Display", fontSize: "clamp(32px, 4vw, 48px)", fontWeight: 900 }}>
              Explore <span className="shimmer-text">63+ Schemes</span>
            </h2>
            <p style={{ fontSize: 16, color: "rgba(255,255,255,0.55)", marginTop: 10 }}>
              Click on any scheme card below to inspect benefits, eligibility & helpline numbers!
            </p>
          </div>

          {/* Search Bar & Categories */}
          <div style={{ marginBottom: 32 }}>
            <div style={{ position: "relative", maxWidth: 600, margin: "0 auto 24px" }}>
              <input
                type="text"
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="🔍 Search schemes by name, benefit, or category..."
                style={{
                  width: "100%", background: "rgba(22, 33, 25, 0.7)", border: "1px solid rgba(76, 175, 80, 0.3)",
                  borderRadius: 14, padding: "14px 20px", color: "#fff", fontSize: 15, outline: "none"
                }}
              />
            </div>

            {/* Category Pills */}
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "center" }}>
              {categories.map(cat => (
                <button
                  key={cat}
                  onClick={() => setActiveCategory(cat)}
                  style={{
                    padding: "8px 16px", borderRadius: 100, border: `1px solid ${activeCategory === cat ? (CAT_COLORS[cat] || "#4caf50") : "rgba(255,255,255,0.1)"}`,
                    background: activeCategory === cat ? `${CAT_COLORS[cat] || "#2e7d32"}33` : "rgba(255,255,255,0.03)",
                    color: activeCategory === cat ? (CAT_COLORS[cat] || "#4caf50") : "rgba(255,255,255,0.6)",
                    fontSize: 13, fontWeight: 700, cursor: "pointer", transition: "all 0.2s"
                  }}
                >
                  {cat === "all" ? "🌐 All Schemes (63)" : cat}
                </button>
              ))}
            </div>
          </div>

          {/* Schemes Grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(270px, 1fr))", gap: 20 }}>
            {filteredSchemes.map(s => (
              <div
                key={s.id}
                className="glass-card"
                onClick={() => setSelectedScheme(s)}
                style={{ padding: 20, cursor: "pointer", position: "relative", display: "flex", flexDirection: "column", justifyContent: "space-between" }}
              >
                <div>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
                    <span style={{ fontSize: 32 }}>{s.icon}</span>
                    <span style={{
                      fontSize: 10, fontWeight: 800, background: `${CAT_COLORS[s.category] || "#2e7d32"}25`,
                      color: CAT_COLORS[s.category] || "#4caf50", border: `1px solid ${CAT_COLORS[s.category] || "#4caf50"}40`,
                      padding: "3px 8px", borderRadius: 6, textTransform: "uppercase"
                    }}>
                      {s.category}
                    </span>
                  </div>
                  <h4 style={{ fontSize: 16, fontWeight: 800, color: "#fff", marginBottom: 6, lineHeight: 1.3 }}>
                    {s.name}
                  </h4>
                  <div style={{ fontSize: 13, color: "#4caf50", fontWeight: 700, marginBottom: 10 }}>
                    💰 {s.benefit}
                  </div>
                </div>

                <div style={{ borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: 10, display: "flex", alignItems: "center", justifyContent: "space-between", fontSize: 12, color: "rgba(255,255,255,0.4)" }}>
                  <span>📞 {s.helpline}</span>
                  <span style={{ color: "#4caf50", fontWeight: 700 }}>Details →</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ SECTION */}
      <section id="faq" style={{ padding: "90px 6%", background: "rgba(255,255,255,0.01)", borderTop: "1px solid rgba(255,255,255,0.05)" }}>
        <div style={{ maxWidth: 840, margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: 50 }}>
            <span className="badge badge-emerald" style={{ marginBottom: 12 }}>FREQUENTLY ASKED</span>
            <h2 style={{ fontFamily: "Playfair Display", fontSize: "clamp(30px, 4vw, 42px)", fontWeight: 900 }}>
              Got Questions?
            </h2>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {FAQS.map((faq, i) => (
              <div
                key={i}
                className="glass-card"
                onClick={() => setActiveFaq(activeFaq === i ? null : i)}
                style={{ padding: 22, cursor: "pointer" }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <h3 style={{ fontSize: 16, fontWeight: 700, color: "#fff" }}>{faq.q}</h3>
                  <span style={{ fontSize: 18, color: "#4caf50" }}>{activeFaq === i ? "−" : "+"}</span>
                </div>
                {activeFaq === i && (
                  <p style={{ marginTop: 14, fontSize: 14, color: "rgba(255,255,255,0.7)", lineHeight: 1.6, borderTop: "1px solid rgba(255,255,255,0.08)", paddingTop: 12 }}>
                    {faq.a}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer style={{ borderTop: "1px solid rgba(255,255,255,0.08)", padding: "50px 6%", textAlign: "center", background: "#050806" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10, marginBottom: 16 }}>
          <div style={{ width: 36, height: 36, background: "linear-gradient(135deg,#1b5e20,#4caf50)", borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>🌾</div>
          <span style={{ fontFamily: "Playfair Display", fontSize: 20, fontWeight: 800 }}>GramSetu AI</span>
        </div>
        <p style={{ fontSize: 13, color: "rgba(255,255,255,0.4)" }}>
          Bridging Villages to Government Schemes • Powered by FastAPI & Vite React • 100% Free
        </p>
      </footer>

      {/* Scheme Detail Modal */}
      {selectedScheme && (
        <SchemeModal
          scheme={selectedScheme}
          onClose={() => setSelectedScheme(null)}
          onAskAI={() => setPage("register")}
        />
      )}
    </div>
  )
}
