import React from "react"
import { CAT_COLORS } from "../data/schemesData"

export default function SchemeModal({ scheme, onClose, onAskAI }) {
  if (!scheme) return null

  const categoryColor = CAT_COLORS[scheme.category] || "#4caf50"

  return (
    <div style={{
      position: "fixed",
      inset: 0,
      zIndex: 1000,
      background: "rgba(0, 0, 0, 0.75)",
      backdropFilter: "blur(8px)",
      display: "flex",
      alignItems: "center",
      justify: "center",
      padding: "20px"
    }} onClick={onClose}>
      <div style={{
        background: "rgba(18, 26, 20, 0.95)",
        border: "1px solid rgba(76, 175, 80, 0.3)",
        borderRadius: 24,
        maxWidth: 560,
        width: "100%",
        maxHeight: "90vh",
        overflowY: "auto",
        boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.8), 0 0 30px rgba(76, 175, 80, 0.15)",
        padding: "28px",
        position: "relative",
        animation: "mi 0.3s cubic-bezier(0.16, 1, 0.3, 1)"
      }} onClick={e => e.stopPropagation()}>
        {/* Close Button */}
        <button onClick={onClose} style={{
          position: "absolute",
          top: 20,
          right: 20,
          background: "rgba(255, 255, 255, 0.08)",
          border: "1px solid rgba(255, 255, 255, 0.12)",
          color: "rgba(255, 255, 255, 0.6)",
          width: 34,
          height: 34,
          borderRadius: "50%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 16,
          cursor: "pointer",
          transition: "all 0.2s"
        }}>
          ✕
        </button>

        {/* Header Header */}
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 20 }}>
          <div style={{
            width: 56,
            height: 56,
            background: `${categoryColor}22`,
            border: `1px solid ${categoryColor}44`,
            borderRadius: 16,
            display: "flex",
            alignItems: "center",
            justify: "center",
            fontSize: 28,
            flexShrink: 0
          }}>
            {scheme.icon}
          </div>
          <div>
            <span style={{
              background: `${categoryColor}25`,
              color: categoryColor,
              border: `1px solid ${categoryColor}40`,
              fontSize: 11,
              fontWeight: 700,
              padding: "3px 10px",
              borderRadius: 20,
              textTransform: "uppercase",
              letterSpacing: 0.5
            }}>
              {scheme.category}
            </span>
            <h2 style={{ fontSize: 22, fontWeight: 800, color: "#fff", marginTop: 6, lineHeight: 1.3 }}>
              {scheme.name}
            </h2>
          </div>
        </div>

        {/* Benefit Box */}
        <div style={{
          background: "linear-gradient(135deg, rgba(76, 175, 80, 0.12) 0%, rgba(46, 125, 50, 0.05) 100%)",
          border: "1px solid rgba(76, 175, 80, 0.25)",
          borderRadius: 14,
          padding: "16px 20px",
          marginBottom: 24,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between"
        }}>
          <div>
            <div style={{ fontSize: 11, textTransform: "uppercase", color: "rgba(255, 255, 255, 0.5)", fontWeight: 600, letterSpacing: 0.5 }}>
              Key Benefit
            </div>
            <div style={{ fontSize: 18, fontWeight: 800, color: "#4caf50", marginTop: 2 }}>
              💰 {scheme.benefit}
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 11, textTransform: "uppercase", color: "rgba(255, 255, 255, 0.5)", fontWeight: 600, letterSpacing: 0.5 }}>
              Toll-Free Helpline
            </div>
            <div style={{ fontSize: 15, fontWeight: 700, color: "#fff", marginTop: 2 }}>
              📞 {scheme.helpline}
            </div>
          </div>
        </div>

        {/* Description */}
        <div style={{ marginBottom: 24 }}>
          <h4 style={{ fontSize: 13, textTransform: "uppercase", letterSpacing: 0.8, color: "rgba(255, 255, 255, 0.4)", marginBottom: 8, fontWeight: 700 }}>
            Overview
          </h4>
          <p style={{ fontSize: 14, color: "rgba(255, 255, 255, 0.8)", lineHeight: 1.6 }}>
            {scheme.desc}
          </p>
        </div>

        {/* Checklist */}
        <div style={{ marginBottom: 28, background: "rgba(255, 255, 255, 0.03)", border: "1px solid rgba(255, 255, 255, 0.06)", borderRadius: 14, padding: "16px" }}>
          <h4 style={{ fontSize: 13, textTransform: "uppercase", letterSpacing: 0.8, color: "rgba(255, 255, 255, 0.4)", marginBottom: 12, fontWeight: 700 }}>
            General Requirements
          </h4>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            {["Valid Aadhaar Card", "Active Bank Account", "Domicile Certificate", "Category / Land Record"].map((item, idx) => (
              <div key={idx} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "rgba(255, 255, 255, 0.75)" }}>
                <span style={{ color: "#4caf50", fontWeight: "bold" }}>✓</span> {item}
              </div>
            ))}
          </div>
        </div>

        {/* CTA Buttons */}
        <div style={{ display: "flex", gap: 12 }}>
          <button onClick={() => { onClose(); onAskAI(scheme.question) }} style={{
            flex: 1,
            background: "linear-gradient(135deg, #2e7d32 0%, #4caf50 100%)",
            border: "none",
            color: "#fff",
            padding: "14px",
            borderRadius: 12,
            fontSize: 15,
            fontWeight: 700,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 8,
            boxShadow: "0 4px 20px rgba(76, 175, 80, 0.4)",
            transition: "all 0.2s"
          }}>
            🤖 Ask AI About {scheme.name.split(" ")[0]} →
          </button>
        </div>
      </div>
    </div>
  )
}
