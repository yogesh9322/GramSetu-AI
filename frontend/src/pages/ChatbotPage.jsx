import React, { useState, useRef, useEffect, useContext } from "react"
import { AuthContext } from "../context/AuthContext"
import { ALL_SCHEMES, CAT_COLORS } from "../data/schemesData"
import SchemeModal from "../components/SchemeModal"
import axios from "axios"

const API = "http://127.0.0.1:8000"

function FormattedAnswer({ text, lang = "hindi" }) {
  const [copied, setCopied] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [audioLoading, setAudioLoading] = useState(false)
  const audioRef = useRef(null)
  const utteranceRef = useRef(null)
  const isStoppingRef = useRef(false)

  useEffect(() => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.getVoices()
    }
  }, [])

  const copyToClipboard = () => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const cleanForTTS = (str, language = "hindi") => {
    if (!str) return ""
    let t = str

    // 1. Ranges 2-3 -> 2 से 3 (Hindi) / 2 ते 3 (Marathi) / 2 to 3 (English)
    const langLower = language ? language.toLowerCase() : "hindi"
    t = t.replace(/(\d+)\s*[-–—]\s*(\d+)/g, (match, p1, p2) => {
      if (langLower === "marathi") return `${p1} ते ${p2}`
      if (langLower === "hindi") return `${p1} से ${p2}`
      return `${p1} to ${p2}`
    })

    // 2. Numbered points 1. 2. 3.
    const hiOrdinals = { 1: "पहला", 2: "दूसरा", 3: "तीसरा", 4: "चौथा", 5: "पांचवां", 6: "छठा", 7: "सातवां", 8: "आठवां", 9: "नौवां", 10: "दसवां" }
    const mrOrdinals = { 1: "पहिला मुद्दा", 2: "दूसरा मुद्दा", 3: "तिसरा मुद्दा", 4: "चौथा मुद्दा", 5: "पांचवा मुद्दा", 6: "सहावा मुद्दा", 7: "सातवा मुद्दा", 8: "आठवा मुद्दा", 9: "नववा मुद्दा", 10: "दहावा मुद्दा" }
    const enOrdinals = { 1: "First", 2: "Second", 3: "Third", 4: "Fourth", 5: "Fifth", 6: "Sixth", 7: "Seventh", 8: "Eighth", 9: "Ninth", 10: "Tenth" }

    t = t.replace(/^\s*(\d+)\.\s+/gm, (match, num) => {
      const n = parseInt(num, 10)
      if (langLower === "marathi") return `${mrOrdinals[n] || `मुद्दा ${n}`}, `
      if (langLower === "hindi") return `${hiOrdinals[n] || `पॉइंट ${n}`}, `
      return `${enOrdinals[n] || `Point ${n}`}, `
    })

    // 3. Clean Markdown tables (| col1 | col2 |)
    t = t.replace(/\|[^\n]+\|/g, (match) => {
      return match.replace(/[\|\-\:\=]+/g, " ").trim() + ", "
    })

    // 4. Clean Markdown links, headers, formatting
    t = t.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    t = t.replace(/http[s]?:\/\/\S+/g, "")
    t = t.replace(/#+\s*/g, "")
    t = t.replace(/[*_~`]/g, "")
    t = t.replace(/^\s*[\-\*•]+\s*/gm, ", ")

    // 5. Replace line breaks with a soft comma pause so it takes a small natural line-end breath
    t = t.replace(/\n+/g, ", ")

    // 6. Clean duplicate punctuation and extra spaces
    t = t.replace(/\s*,\s*,+/g, ", ")
    t = t.replace(/\s+/g, " ")

    return t.trim()
  }

  const getSmoothChunks = (cleanText) => {
    const parts = cleanText.split(/([.!?।\n]+)/)
    const chunks = []
    let current = ""

    for (let i = 0; i < parts.length; i += 2) {
      const textPart = parts[i]?.trim()
      const punct = parts[i + 1] || ". "
      if (!textPart) continue

      const sentence = textPart + (punct.includes("\n") ? ". " : punct + " ")

      if ((current + sentence).length > 220 && current.length > 0) {
        chunks.push(current.trim())
        current = sentence
      } else {
        current += sentence
      }
    }

    if (current.trim()) {
      chunks.push(current.trim())
    }

    return chunks.length > 0 ? chunks : [cleanText]
  }

  const stopVoice = () => {
    isStoppingRef.current = true

    if (utteranceRef.current) {
      utteranceRef.current.onstart = null
      utteranceRef.current.onend = null
      utteranceRef.current.onerror = null
      utteranceRef.current = null
    }

    if (audioRef.current) {
      try {
        audioRef.current.onplay = null
        audioRef.current.onended = null
        audioRef.current.onerror = null
        audioRef.current.pause()
        audioRef.current.currentTime = 0
        audioRef.current.removeAttribute('src')
        audioRef.current.load()
      } catch {}
      audioRef.current = null
    }

    if ('speechSynthesis' in window) {
      try { window.speechSynthesis.cancel() } catch {}
    }

    setSpeaking(false)
    setAudioLoading(false)
  }

  const speakText = () => {
    if (speaking || audioLoading) {
      stopVoice()
      return
    }

    stopVoice()
    isStoppingRef.current = false

    const cleanText = cleanForTTS(text, lang)
    if (!cleanText) return

    // 1. Primary Engine: Smooth Paragraph Speech Engine (Instant 0ms start, human cadence, zero awkward pauses!)
    if ('speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel()
        if (window.speechSynthesis.paused) {
          window.speechSynthesis.resume()
        }

        const chunks = getSmoothChunks(cleanText)
        let index = 0

        const speakNextChunk = () => {
          if (isStoppingRef.current || index >= chunks.length) {
            setSpeaking(false)
            setAudioLoading(false)
            return
          }

          const currentChunk = chunks[index]
          const utterance = new SpeechSynthesisUtterance(currentChunk)
          utteranceRef.current = utterance

          const voices = window.speechSynthesis.getVoices()
          let selectedVoice = null

          if (lang === "marathi" || lang === "hindi") {
            selectedVoice = voices.find(v => v.lang.includes("hi") || v.lang.includes("mr") || v.name.toLowerCase().includes("hindi") || v.name.toLowerCase().includes("india"))
          } else {
            selectedVoice = voices.find(v => v.lang.includes("en-IN") || v.lang.includes("en"))
          }

          if (selectedVoice) {
            utterance.voice = selectedVoice
          }

          if (lang === "marathi") utterance.lang = "mr-IN"
          else if (lang === "hindi") utterance.lang = "hi-IN"
          else utterance.lang = "en-IN"

          utterance.rate = 1.05 // Crisp, natural responsive speaking rate

          utterance.onstart = () => {
            if (isStoppingRef.current) return
            setSpeaking(true)
            setAudioLoading(false)
          }

          utterance.onend = () => {
            if (isStoppingRef.current) return
            index++
            if (index < chunks.length) {
              speakNextChunk()
            } else {
              setSpeaking(false)
              setAudioLoading(false)
            }
          }

          utterance.onerror = (e) => {
            if (isStoppingRef.current || e.error === "canceled" || e.error === "interrupted") {
              setSpeaking(false)
              setAudioLoading(false)
              return
            }
            index++
            if (index < chunks.length) {
              speakNextChunk()
            } else {
              playServerTTS(cleanText)
            }
          }

          window.speechSynthesis.speak(utterance)
        }

        setAudioLoading(true)
        speakNextChunk()
        return
      } catch (e) {
        console.warn("Browser SpeechSynthesis error, falling back to server audio", e)
      }
    }

    // 2. Fallback Engine: Server gTTS Streaming Audio
    playServerTTS(cleanText)
  }

  const playServerTTS = (cleanText) => {
    if (isStoppingRef.current) return
    setAudioLoading(true)
    try {
      const audioUrl = `${API}/tts?text=${encodeURIComponent(cleanText.slice(0, 500))}&language=${encodeURIComponent(lang)}`
      const audio = new Audio(audioUrl)
      audioRef.current = audio

      audio.onplay = () => {
        if (isStoppingRef.current) return
        setAudioLoading(false)
        setSpeaking(true)
      }

      audio.onended = () => {
        if (isStoppingRef.current) return
        setSpeaking(false)
        setAudioLoading(false)
      }

      audio.onerror = () => {
        if (isStoppingRef.current) return
        stopVoice()
      }

      audio.play().catch(() => {
        if (isStoppingRef.current) return
        stopVoice()
      })
    } catch {
      stopVoice()
    }
  }

  return (
    <div style={{ lineHeight: 1.75, fontSize: 14, fontFamily: "'Tiro Devanagari Hindi','Plus Jakarta Sans',sans-serif" }}>
      {/* Dedicated Card Header Bar (No overlapping) */}
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        paddingBottom: 8,
        marginBottom: 12,
        borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
        gap: 10,
        flexWrap: "wrap"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, fontWeight: 700, color: "#81c784", letterSpacing: "0.5px" }}>
          <span>🌾</span>
          <span>GRAMSETU ADVISORY</span>
        </div>

        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <button
            onClick={speakText}
            disabled={audioLoading}
            title="Read answer aloud"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 5,
              background: speaking ? "rgba(239,83,80,0.22)" : audioLoading ? "rgba(255,235,59,0.22)" : "rgba(76,175,80,0.15)",
              border: `1px solid ${speaking ? "#ef5350" : audioLoading ? "#fbc02d" : "rgba(76,175,80,0.4)"}`,
              color: speaking ? "#ef5350" : audioLoading ? "#fbc02d" : "#a5d6a7",
              borderRadius: 6,
              padding: "4px 10px",
              fontSize: 11,
              fontWeight: 700,
              cursor: "pointer",
              transition: "all 0.2s"
            }}
          >
            {audioLoading ? "⏳ Loading Voice..." : speaking ? "⏹️ Stop Voice" : "🔊 Listen"}
          </button>
          <button
            onClick={copyToClipboard}
            title="Copy answer"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 5,
              background: "rgba(255,255,255,0.06)",
              border: "1px solid rgba(255,255,255,0.12)",
              color: copied ? "#81c784" : "rgba(255,255,255,0.6)",
              borderRadius: 6,
              padding: "4px 10px",
              fontSize: 11,
              fontWeight: 600,
              cursor: "pointer",
              transition: "all 0.2s"
            }}
          >
            {copied ? "✓ Copied" : "📋 Copy"}
          </button>
        </div>
      </div>

      {text.split("\n").filter(l => l.trim()).map((line, i) => {
        const trimmed = line.trim()
        const bold = line.replace(/\*\*(.*?)\*\*/g, "<strong style='color:#4caf50; font-weight:700;'>$1</strong>")

        // Heading lines (#, ##, ###)
        if (/^#{1,4}\s+/.test(trimmed)) {
          const heading = bold.replace(/^#{1,4}\s+/, "")
          return (
            <div key={i} style={{
              fontSize: 15,
              fontWeight: 800,
              color: "#81c784",
              margin: "12px 0 6px 0",
              display: "flex",
              alignItems: "center",
              gap: 6
            }} dangerouslySetInnerHTML={{ __html: heading }} />
          )
        }

        // Table lines (| col1 | col2 |)
        if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
          const cells = trimmed.split("|").slice(1, -1).map(c => c.trim())
          if (cells.every(c => /^[-:\s]+$/.test(c))) {
            return null // divider row
          }
          return (
            <div key={i} style={{
              display: "grid",
              gridTemplateColumns: cells.length === 2 ? "1fr 2fr" : `repeat(${cells.length}, 1fr)`,
              gap: 10,
              padding: "7px 12px",
              margin: "4px 0",
              background: "rgba(255,255,255,0.03)",
              borderRadius: 8,
              border: "1px solid rgba(255,255,255,0.06)",
              fontSize: 13
            }}>
              {cells.map((cell, cIdx) => (
                <div
                  key={cIdx}
                  style={{ fontWeight: cIdx === 0 ? 700 : 400, color: cIdx === 0 ? "#81c784" : "#e2e8f0" }}
                  dangerouslySetInnerHTML={{ __html: cell.replace(/\*\*(.*?)\*\*/g, "<strong style='color:#4caf50;'>$1</strong>") }}
                />
              ))}
            </div>
          )
        }
        
        // Numbered list
        if (/^\d+[\.\)]\s*/.test(trimmed)) {
          return (
            <div key={i} style={{ padding: "8px 14px", margin: "5px 0", borderRadius: 10, background: "rgba(76,175,80,0.08)", borderLeft: "3px solid #4caf50", color: "#e2e8f0" }}
              dangerouslySetInnerHTML={{ __html: bold }}
            />
          )
        }

        // Bullet list
        if (/^[\*\-•]/.test(trimmed)) {
          return (
            <div key={i} style={{ padding: "6px 14px", margin: "4px 0", borderRadius: 8, background: "rgba(255,255,255,0.03)", borderLeft: "3px solid rgba(76,175,80,0.4)", color: "rgba(255,255,255,0.88)" }}
              dangerouslySetInnerHTML={{ __html: "• " + bold.replace(/^[\*\-•]\s*/, "") }}
            />
          )
        }

        return (
          <p key={i} style={{ margin: "0 0 8px 0", color: "rgba(255,255,255,0.9)" }} dangerouslySetInnerHTML={{ __html: bold }} />
        )
      })}
    </div>
  )
}

export default function ChatbotPage({ setPage }) {
  const { user, logout } = useContext(AuthContext)
  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: `नमस्ते ${user?.name || ""}! 👋 मैं GramSetu AI हूँ।\nबाईं तरफ 63 सरकारी योजनाओं की सूची है — किसी भी योजना पर क्लिक करें या अपना सवाल पूछें।\nHindi, Marathi या English — अपनी भाषा में बात करें!`,
      lang: user?.language || "hindi"
    }
  ])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [lang, setLang] = useState(user?.language || "hindi")
  const [activeTab, setActiveTab] = useState("schemes")
  const [search, setSearch] = useState("")
  const [category, setCategory] = useState("all")
  const [isRecording, setIsRecording] = useState(false)
  const [audioUrl, setAudioUrl] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [selectedScheme, setSelectedScheme] = useState(null)
  const [modalScheme, setModalScheme] = useState(null)

  const messagesEndRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const audioRef = useRef(null)
  const recognitionRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, loading])

  const categories = ["all", ...Object.keys(CAT_COLORS)]

  const filteredSchemes = ALL_SCHEMES.filter(s => {
    const ms = !search ||
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.category.toLowerCase().includes(search.toLowerCase()) ||
      s.benefit.toLowerCase().includes(search.toLowerCase())
    return ms && (category === "all" || s.category === category)
  })

  const ask = async (q = input) => {
    if (!q.trim()) return
    setMessages(p => [...p, { role: "user", text: q }])
    setInput("")
    setLoading(true)
    setActiveTab("chat")
    try {
      const res = await axios.post(
        `${API}/ask`,
        { question: q, language: lang },
        { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } }
      )
      setMessages(p => [...p, { role: "bot", text: res.data.answer, lang: res.data.language }])
    } catch {
      setMessages(p => [
        ...p,
        { role: "bot", text: "❌ Backend service unreachable. Please ensure the Python FastAPI backend (uvicorn) is running!", lang }
      ])
    } finally {
      setLoading(false)
    }
  }

  const fallbackServerRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaRecorderRef.current = new MediaRecorder(stream)
      audioChunksRef.current = []
      mediaRecorderRef.current.ondataavailable = e => audioChunksRef.current.push(e.data)
      mediaRecorderRef.current.onstop = async () => {
        stream.getTracks().forEach(t => t.stop())
        setLoading(true)
        try {
          const form = new FormData()
          form.append("audio", new Blob(audioChunksRef.current, { type: "audio/wav" }), "rec.wav")
          const res = await axios.post(`${API}/voice-ask`, form, {
            headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
            responseType: "blob"
          })

          const decodeHeader = (b64) => {
            try {
              return atob(b64) ? new TextDecoder().decode(new Uint8Array(atob(b64).split('').map(c => c.charCodeAt(0)))) : b64
            } catch {
              return b64
            }
          }
          const q = decodeHeader(res.headers["x-question"]) || "Voice Question"
          const ans = decodeHeader(res.headers["x-answer"]) || ""
          setMessages(p => [
            ...p,
            { role: "user", text: `🎤 "${q}"` },
            { role: "bot", text: ans, lang: res.headers["x-language"] || lang }
          ])
          setAudioUrl(URL.createObjectURL(res.data))
        } catch {
          setMessages(p => [...p, { role: "bot", text: "❌ Voice processing failed. Please type your query.", lang }])
        } finally {
          setLoading(false)
        }
      }
      mediaRecorderRef.current.start()
      setIsRecording(true)
    } catch {
      alert("Microphone access denied or unsupported in this browser environment!")
    }
  }

  const startRecording = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition()
        recognition.continuous = false
        recognition.interimResults = false
        recognition.lang = lang === "marathi" ? "mr-IN" : lang === "hindi" ? "hi-IN" : "en-IN"

        recognition.onstart = () => setIsRecording(true)
        recognition.onresult = (e) => {
          const transcript = e.results[0]?.[0]?.transcript
          if (transcript) {
            setInput(transcript)
            ask(transcript)
          }
        }
        recognition.onerror = () => {
          setIsRecording(false)
          fallbackServerRecording()
        }
        recognition.onend = () => setIsRecording(false)
        recognitionRef.current = recognition
        recognition.start()
        return
      } catch {
        // Fall back below
      }
    }
    fallbackServerRecording()
  }

  const stopRecording = () => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop() } catch {}
      recognitionRef.current = null
    }
    if (mediaRecorderRef.current && isRecording) {
      try { mediaRecorderRef.current.stop() } catch {}
    }
    setIsRecording(false)
  }

  const LANG_LABELS = { marathi: "मराठी", hindi: "हिंदी", english: "English" }

  return (
    <div style={{ height: "100vh", background: "#070a08", display: "flex", fontFamily: "'Plus Jakarta Sans', sans-serif", overflow: "hidden" }}>
      {/* SIDEBAR WORKSPACE */}
      <div style={{
        width: sidebarOpen ? 330 : 0, minWidth: sidebarOpen ? 330 : 0,
        background: "rgba(12, 18, 14, 0.95)", borderRight: "1px solid rgba(255,255,255,0.08)",
        display: "flex", flexDirection: "column", overflow: "hidden", transition: "all 0.3s cubic-bezier(0.16,1,0.3,1)", flexShrink: 0
      }}>
        {/* Sidebar Header */}
        <div style={{ padding: "18px 16px 14px", borderBottom: "1px solid rgba(255,255,255,0.08)", flexShrink: 0 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer" }} onClick={() => setPage("home")}>
              <div style={{ width: 36, height: 36, background: "linear-gradient(135deg,#1b5e20,#4caf50)", borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>🌾</div>
              <div>
                <div style={{ fontSize: 15, fontWeight: 800, color: "#fff", fontFamily: "Playfair Display" }}>GramSetu AI</div>
                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)" }}>63 Scheme Knowledgebase</div>
              </div>
            </div>
            <button onClick={() => setPage("home")} title="Return Home" style={{ background: "none", border: "none", color: "rgba(255,255,255,0.4)", cursor: "pointer", fontSize: 13 }}>🏠</button>
          </div>

          {/* Navigation Tabs */}
          <div style={{ display: "flex", background: "rgba(255,255,255,0.05)", borderRadius: 10, padding: 3, gap: 4 }}>
            {[{ id: "schemes", label: "📋 63 Schemes" }, { id: "chat", label: "💬 Quick Ask" }].map(t => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                style={{
                  flex: 1, padding: "8px 6px", borderRadius: 8, border: "none", cursor: "pointer",
                  fontSize: 12, fontWeight: 700,
                  background: activeTab === t.id ? "linear-gradient(135deg,#2e7d32,#4caf50)" : "transparent",
                  color: activeTab === t.id ? "#fff" : "rgba(255,255,255,0.45)",
                  transition: "all 0.2s"
                }}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* SCHEMES TAB */}
        {activeTab === "schemes" && (
          <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
            <div style={{ padding: "12px 14px 8px", flexShrink: 0 }}>
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder={`Search ${ALL_SCHEMES.length} schemes...`}
                style={{
                  width: "100%", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)",
                  borderRadius: 10, padding: "8px 12px", color: "#fff", fontSize: 12, outline: "none", marginBottom: 8
                }}
              />

              {/* Category Pills */}
              <div style={{ display: "flex", gap: 4, flexWrap: "wrap", maxHeight: 68, overflowY: "auto" }}>
                {categories.map(c => (
                  <button
                    key={c}
                    onClick={() => setCategory(c)}
                    style={{
                      padding: "3px 8px", borderRadius: 12,
                      border: `1px solid ${category === c ? (CAT_COLORS[c] || "#4caf50") : "rgba(255,255,255,0.08)"}`,
                      background: category === c ? `${CAT_COLORS[c] || "#2e7d32"}33` : "transparent",
                      color: category === c ? (CAT_COLORS[c] || "#4caf50") : "rgba(255,255,255,0.4)",
                      cursor: "pointer", fontSize: 10, fontWeight: 700, transition: "all 0.15s"
                    }}
                  >
                    {c === "all" ? "All" : c}
                  </button>
                ))}
              </div>
            </div>

            {/* Scheme Item List */}
            <div style={{ flex: 1, overflowY: "auto", padding: "0 10px 14px" }}>
              {filteredSchemes.length === 0 ? (
                <div style={{ textAlign: "center", padding: 24, color: "rgba(255,255,255,0.3)", fontSize: 12 }}>
                  No schemes match filter
                </div>
              ) : filteredSchemes.map(s => (
                <div
                  key={s.id}
                  className="glass-card"
                  onClick={() => { setSelectedScheme(s); ask(s.question) }}
                  style={{
                    padding: "10px 12px", marginBottom: 6, cursor: "pointer",
                    border: selectedScheme?.id === s.id ? "1px solid rgba(76,175,80,0.6)" : "1px solid rgba(255,255,255,0.06)",
                    background: selectedScheme?.id === s.id ? "rgba(76,175,80,0.12)" : "rgba(255,255,255,0.02)",
                    display: "flex", gap: 10, alignItems: "center"
                  }}
                >
                  <span style={{ fontSize: 20, flexShrink: 0 }}>{s.icon}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: "#fff", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                      {s.name}
                    </div>
                    <div style={{ display: "flex", gap: 6, marginTop: 2, alignItems: "center" }}>
                      <span style={{ fontSize: 10, color: "#4caf50", fontWeight: 700 }}>💰 {s.benefit}</span>
                      <span style={{ fontSize: 9, background: `${CAT_COLORS[s.category] || "#2e7d32"}22`, color: CAT_COLORS[s.category] || "#4caf50", padding: "1px 5px", borderRadius: 4, fontWeight: 700 }}>
                        {s.category}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); setModalScheme(s) }}
                    title="Info Modal"
                    style={{ background: "rgba(255,255,255,0.08)", border: "none", color: "rgba(255,255,255,0.5)", borderRadius: 6, padding: "2px 6px", fontSize: 10, cursor: "pointer" }}
                  >
                    ℹ️
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* CHAT TAB (Quick Prompts) */}
        {activeTab === "chat" && (
          <div style={{ flex: 1, padding: "14px", overflowY: "auto", display: "flex", flexDirection: "column", gap: 16 }}>
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, color: "rgba(255,255,255,0.4)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 10 }}>
                Response Language
              </div>
              {[
                { v: "marathi", l: "🟠 मराठी (Marathi)" },
                { v: "hindi", l: "🇮🇳 हिंदी (Hindi)" },
                { v: "english", l: "🔵 English" }
              ].map(l => (
                <button
                  key={l.v}
                  onClick={() => setLang(l.v)}
                  style={{
                    width: "100%", padding: "10px 14px", borderRadius: 10,
                    border: `1px solid ${lang === l.v ? "rgba(76,175,80,0.6)" : "rgba(255,255,255,0.08)"}`,
                    background: lang === l.v ? "rgba(76,175,80,0.15)" : "transparent",
                    color: lang === l.v ? "#4caf50" : "rgba(255,255,255,0.6)",
                    cursor: "pointer", fontSize: 13, fontWeight: 700, textAlign: "left", marginBottom: 6
                  }}
                >
                  {l.l}
                </button>
              ))}
            </div>

            <div>
              <div style={{ fontSize: 11, fontWeight: 700, color: "rgba(255,255,255,0.4)", textTransform: "uppercase", letterSpacing: 1, marginBottom: 10 }}>
                Popular Village Questions
              </div>
              {[
                "PM Kisan ke liye eligible kaun hai?",
                "Ayushman Bharat card kaise banaye?",
                "MGNREGA job card kaise milega?",
                "Free LPG connection Ujjwala scheme?",
                "Sukanya Samridhi account kaise khole?",
                "e-Shram card unorganized workers?"
              ].map((q, i) => (
                <button
                  key={i}
                  onClick={() => ask(q)}
                  style={{
                    width: "100%", padding: "9px 12px", borderRadius: 8,
                    border: "1px solid rgba(255,255,255,0.08)", background: "rgba(255,255,255,0.02)",
                    color: "rgba(255,255,255,0.65)", cursor: "pointer", fontSize: 12, textAlign: "left", marginBottom: 6,
                    lineHeight: 1.4, transition: "all 0.2s"
                  }}
                  onMouseEnter={e => { e.currentTarget.style.background = "rgba(76,175,80,0.1)"; e.currentTarget.style.color = "#fff" }}
                  onMouseLeave={e => { e.currentTarget.style.background = "rgba(255,255,255,0.02)"; e.currentTarget.style.color = "rgba(255,255,255,0.65)" }}
                >
                  💡 {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* User Account Footer */}
        <div style={{ padding: "12px 14px", borderTop: "1px solid rgba(255,255,255,0.08)", display: "flex", alignItems: "center", gap: 10, flexShrink: 0 }}>
          <div style={{ width: 34, height: 34, background: "linear-gradient(135deg,#2e7d32,#4caf50)", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, fontWeight: 800, color: "#fff" }}>
            {(user?.name || "U")[0].toUpperCase()}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#fff", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {user?.name || "Village User"}
            </div>
            <div style={{ fontSize: 10, color: "#4caf50", fontWeight: 600 }}>
              {LANG_LABELS[lang]}
            </div>
          </div>
          <button onClick={logout} style={{ background: "rgba(239,83,80,0.12)", border: "1px solid rgba(239,83,80,0.25)", color: "#ef5350", padding: "5px 10px", borderRadius: 8, cursor: "pointer", fontSize: 11, fontWeight: 700 }}>
            Logout
          </button>
        </div>
      </div>

      {/* MAIN CHAT WORKSPACE */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {/* Header Bar */}
        <div style={{ padding: "14px 24px", borderBottom: "1px solid rgba(255,255,255,0.08)", display: "flex", alignItems: "center", justifyContent: "space-between", flexShrink: 0, background: "rgba(10, 15, 12, 0.8)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              style={{
                background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)",
                color: "rgba(255,255,255,0.7)", width: 36, height: 36, borderRadius: 10, cursor: "pointer",
                fontSize: 16, display: "flex", alignItems: "center", justifyContent: "center"
              }}
            >
              ☰
            </button>
            <div>
              <div style={{ fontSize: 16, fontWeight: 800, color: "#fff" }}>GramSetu AI Advisory Assistant</div>
              <div style={{ fontSize: 11, color: "rgba(255,255,255,0.45)", display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ width: 6, height: 6, background: "#4caf50", borderRadius: "50%", boxShadow: "0 0 8px #4caf50" }} />
                Online • 63 Schemes • {LANG_LABELS[lang]} Mode
                {selectedScheme && <span style={{ color: "#4caf50" }}> • {selectedScheme.icon} {selectedScheme.name}</span>}
              </div>
            </div>
          </div>

          {/* Quick Language Toggle */}
          <div style={{ display: "flex", gap: 6 }}>
            {[
              { v: "marathi", l: "🟠 मराठी" },
              { v: "hindi", l: "🇮🇳 हिंदी" },
              { v: "english", l: "🔵 English" }
            ].map(l => (
              <button
                key={l.v}
                onClick={() => setLang(l.v)}
                style={{
                  padding: "6px 12px", borderRadius: 8,
                  border: `1px solid ${lang === l.v ? "rgba(76,175,80,0.6)" : "rgba(255,255,255,0.08)"}`,
                  background: lang === l.v ? "rgba(76,175,80,0.15)" : "transparent",
                  color: lang === l.v ? "#4caf50" : "rgba(255,255,255,0.4)",
                  cursor: "pointer", fontSize: 12, fontWeight: 700, transition: "all 0.2s"
                }}
              >
                {l.l}
              </button>
            ))}
          </div>
        </div>

        {/* Message Stream */}
        <div style={{ flex: 1, overflowY: "auto", padding: "24px", display: "flex", flexDirection: "column", gap: 16 }}>
          {messages.map((msg, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
                gap: 12,
                alignItems: "flex-start"
              }}
            >
              {msg.role === "bot" && (
                <div style={{
                  width: 38, height: 38, background: "linear-gradient(135deg,#1b5e20,#4caf50)",
                  borderRadius: 12, display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 18, flexShrink: 0, boxShadow: "0 4px 14px rgba(76,175,80,0.3)"
                }}>
                  🌾
                </div>
              )}

              <div style={{
                maxWidth: "78%", padding: msg.role === "user" ? "12px 18px" : "16px 20px",
                borderRadius: msg.role === "user" ? "20px 20px 4px 20px" : "20px 20px 20px 4px",
                background: msg.role === "user" ? "linear-gradient(135deg,#2e7d32,#4caf50)" : "rgba(22, 33, 25, 0.7)",
                border: msg.role === "bot" ? "1px solid rgba(76, 175, 80, 0.25)" : "none",
                color: "#fff", fontSize: 15, lineHeight: 1.6, boxShadow: "0 6px 20px rgba(0,0,0,0.25)"
              }}>
                {msg.role === "bot" ? <FormattedAnswer text={msg.text} lang={msg.lang || lang} /> : msg.text}
              </div>

              {msg.role === "user" && (
                <div style={{
                  width: 38, height: 38, background: "linear-gradient(135deg,#1565C0,#1976D2)",
                  borderRadius: 12, display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 14, flexShrink: 0, fontWeight: 800, color: "#fff"
                }}>
                  {(user?.name || "U")[0].toUpperCase()}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
              <div style={{ width: 38, height: 38, background: "linear-gradient(135deg,#1b5e20,#4caf50)", borderRadius: 12, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>
                🌾
              </div>
              <div style={{ padding: "14px 20px", borderRadius: "20px 20px 20px 4px", background: "rgba(22, 33, 25, 0.7)", border: "1px solid rgba(76, 175, 80, 0.25)", display: "flex", gap: 6 }}>
                <span className="badge badge-emerald">Thinking...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Voice Audio Answer Player */}
        {audioUrl && (
          <div style={{ padding: "10px 24px", borderTop: "1px solid rgba(76,175,80,0.2)", display: "flex", alignItems: "center", gap: 12, background: "rgba(76,175,80,0.08)" }}>
            <span style={{ fontSize: 13, color: "#4caf50", fontWeight: 700 }}>🔊 Voice Output Ready:</span>
            <button onClick={() => audioRef.current?.play()} className="btn-primary" style={{ padding: "6px 14px", fontSize: 12, borderRadius: 8 }}>
              ▶ Play Audio Answer
            </button>
            <button onClick={() => setAudioUrl(null)} style={{ background: "none", border: "none", color: "rgba(255,255,255,0.4)", cursor: "pointer", fontSize: 16 }}>
              ✕
            </button>
            <audio ref={audioRef} src={audioUrl} />
          </div>
        )}

        {/* Input Console */}
        <div style={{ padding: "16px 24px", borderTop: "1px solid rgba(255,255,255,0.08)", background: "rgba(10, 15, 12, 0.95)" }}>
          <div style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
            {/* Record Button */}
            <button
              onClick={isRecording ? stopRecording : startRecording}
              style={{
                width: 48, height: 48, borderRadius: 14,
                border: isRecording ? "none" : "1px solid rgba(76, 175, 80, 0.3)",
                background: isRecording ? "linear-gradient(135deg,#c62828,#ef5350)" : "rgba(76, 175, 80, 0.12)",
                color: "#fff", cursor: "pointer", fontSize: 20, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
                boxShadow: isRecording ? "0 0 20px rgba(239,83,80,0.6)" : "none"
              }}
            >
              {isRecording ? "⏹️" : "🎤"}
            </button>

            {/* Input Box */}
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask() } }}
              placeholder={lang === "marathi" ? "कोणत्याही योजनेबद्दल विचारा... (Enter पाठवा)" : lang === "hindi" ? "किसी भी योजना के बारे में पूछें... (Enter दबाएं)" : "Ask about any government scheme..."}
              rows={1}
              style={{
                flex: 1, background: "rgba(255,255,255,0.06)", border: "1px solid rgba(76, 175, 80, 0.25)",
                borderRadius: 14, padding: "14px 18px", color: "#fff", fontSize: 15,
                fontFamily: "'Tiro Devanagari Hindi','Plus Jakarta Sans',sans-serif", outline: "none", resize: "none", lineHeight: 1.4
              }}
            />

            {/* Send Button */}
            <button
              onClick={() => ask()}
              disabled={loading || !input.trim()}
              className="btn-primary"
              style={{
                width: 48, height: 48, borderRadius: 14, padding: 0, fontSize: 20, flexShrink: 0,
                opacity: loading || !input.trim() ? 0.4 : 1, cursor: loading || !input.trim() ? "not-allowed" : "pointer"
              }}
            >
              {loading ? "⏳" : "↑"}
            </button>
          </div>
          <div style={{ marginTop: 8, fontSize: 11, color: "rgba(255,255,255,0.3)", textAlign: "center" }}>
            Press Enter to send • 🎤 Click microphone for Voice input • Click ℹ️ on any scheme in sidebar for full details
          </div>
        </div>
      </div>

      {/* Scheme Modal Trigger from Sidebar */}
      {modalScheme && (
        <SchemeModal
          scheme={modalScheme}
          onClose={() => setModalScheme(null)}
          onAskAI={(q) => ask(q)}
        />
      )}
    </div>
  )
}