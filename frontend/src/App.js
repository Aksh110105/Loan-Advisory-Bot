import React from "react";
import Chatbot from "./components/Chatbot";

function App() {
  return (
    <div style={{ fontFamily: "sans-serif", background: "#f9fafb", minHeight: "100vh", paddingBottom: 40 }}>
      {/* Banner */}
      <div
        style={{
          background: "#10b981", // Green to indicate financial support
          color: "#fff",
          padding: 16,
          textAlign: "center",
          fontWeight: "bold",
          borderRadius: 8,
          margin: "16px auto",
          maxWidth: 800,
          boxShadow: "0 2px 6px rgba(0,0,0,0.1)",
        }}
      >
        💸 Your AI-powered Personal Loan Advisor — Ask your questions now!
      </div>

      {/* Hero Section */}
      <section style={{ textAlign: "center", padding: "48px 16px" }}>
        <h1 style={{ fontSize: 36, fontWeight: "bold", marginBottom: 24 }}>
          Welcome to Your Loan Advisory Chatbot
        </h1>
        <img
          src="/robot.gif"
          alt="Loan Assistant Bot"
          style={{ width: 160, height: 160, objectFit: "contain", margin: "0 auto" }}
        />
        <p style={{ marginTop: 16, color: "#4b5563", fontSize: 18 }}>
          I’ll help you explore the best loan options based on your needs, income, location, and goals.
        </p>
      </section>

      {/* Features Section */}
      <section
        style={{
          background: "#fff",
          padding: 40,
          margin: "24px auto",
          maxWidth: 900,
          borderRadius: 12,
          boxShadow: "0 1px 4px rgba(0,0,0,0.05)"
        }}
      >
        <h2 style={{ fontSize: 24, fontWeight: 600, textAlign: "center", marginBottom: 16 }}>
          What I Can Help With
        </h2>
        <ul style={{ paddingLeft: 20, color: "#374151", lineHeight: "1.8em" }}>
          <li>Suggest personal, home, or education loan options</li>
          <li>Compare interest rates from different lenders</li>
          <li>Guide you based on your income, city, and timeline</li>
          <li>Answer EMI, documentation, or eligibility-related questions</li>
        </ul>
      </section>

      {/* Use Cases Section */}
      <section
        style={{
          background: "#f3f4f6",
          padding: 40,
          margin: "24px auto",
          maxWidth: 900,
          borderRadius: 12
        }}
      >
        <h2 style={{ fontSize: 24, fontWeight: 600, textAlign: "center", marginBottom: 16 }}>
          Use Cases
        </h2>
        <ul style={{ paddingLeft: 20, color: "#374151", lineHeight: "1.8em" }}>
          <li>You're exploring loan options for a new house or car</li>
          <li>You want to know if you're eligible for a personal loan</li>
          <li>You’re confused about interest rates, banks, or documentation</li>
          <li>You need help planning your repayment or EMI strategy</li>
        </ul>
      </section>

      {/* Chatbot Section */}
      <section style={{ padding: "48px 16px" }}>
        <h2 style={{ textAlign: "center", fontSize: 28, fontWeight: "bold", marginBottom: 24 }}>
          Talk to Your Loan Advisor Bot
        </h2>
        <Chatbot />
      </section>
    </div>
  );
}

export default App;
