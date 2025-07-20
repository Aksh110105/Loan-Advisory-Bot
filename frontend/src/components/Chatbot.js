import React, { useState, useEffect, useRef } from 'react';
import api from '../services/api';
import { v4 as uuidv4 } from 'uuid';

const Chatbot = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState("chat");
  const [context, setContext] = useState(null);
  const [loading, setLoading] = useState(false);
  const [userId, setUserId] = useState(null);
  const chatEndRef = useRef(null);

  useEffect(() => {
    let userUUID = localStorage.getItem("userUUID");
    if (!userUUID) {
      userUUID = uuidv4();
      localStorage.setItem("userUUID", userUUID);
    }
    setUserId(userUUID);

    const sessionId = getSessionId();

    const loadHistory = async () => {
      try {
        const response = await api.get("/chats/resume", {
          headers: {
            user_uuid: userUUID,
            session_id: sessionId
          }
        });

        const { history, context } = response.data;

        if (history?.length) {
          const restored = history.flatMap(chat => [
            { sender: "user", text: chat.user_message },
            { sender: "bot", text: chat.bot_response }
          ]);

          const lastBot = history[history.length - 1]?.bot_response?.toLowerCase();
          const lastIntent = history[history.length - 1]?.intent;

          if (lastIntent === "farewell" || lastIntent === "exit" || (lastBot && lastBot.includes("goodbye"))) {
            greetUser();
          } else {
            setMessages([{ sender: "bot", text: "🔁 Welcome back!" }, ...restored]);
            setContext(context?.summary || null);
            setMode("rag");
          }
        } else {
          greetUser();
        }
      } catch (err) {
        console.error("Failed to load history:", err);
        greetUser();
      }
    };

    loadHistory();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const getSessionId = () => {
    let sessionId = localStorage.getItem("sessionId");
    if (!sessionId) {
      sessionId = uuidv4();
      localStorage.setItem("sessionId", sessionId);
    }
    return sessionId;
  };

  const greetUser = () => {
    setMessages([
      {
        sender: "bot",
        text:
          "👋 I’m your Loan Advisor Chatbot.\n" +
          "I can help you explore personal, home, education, business, MSME, or vehicle loans based on your income, city, and timeline.\n" +
          "Let's get started — What kind of loan are you looking for?"
      }
    ]);
    setMode("chat");
    setContext(null);
  };

  const resetChat = () => {
    const newSession = uuidv4();
    localStorage.setItem("sessionId", newSession);
    setMessages([]);
    setContext(null);
    setMode("chat");
    greetUser();
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) return;

    setMessages(prev => [...prev, { sender: "user", text: trimmed }]);
    setInput("");
    setLoading(true);

    const sessionId = getSessionId();
    const headers = {
      user_uuid: userId,
      session_id: sessionId
    };

    try {
      let response;
      let botReply = "";

      if (mode === "chat") {
        response = await api.post("/chat", {
          message: trimmed,
          model: "GPT-4"
        }, { headers });

        botReply = response.data.response;
        if (response.data.mode === "rag") setMode("rag");
      } else {
        response = await api.post("/rag-chat", {
          message: trimmed
        }, { headers });

        botReply = response.data?.response || "⚠️ I'm not sure how to help with that.";
      }

      setMessages(prev => [...prev, { sender: "bot", text: botReply }]);

    } catch (err) {
      console.error("❌ Chat error:", err);
      setMessages(prev => [...prev, { sender: "bot", text: "🚫 Sorry, something went wrong." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      width: "100%",
      maxWidth: 600,
      margin: "0 auto",
      background: "#fff",
      borderRadius: 12,
      boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
      padding: 16
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
        <strong>💸 Loan Advisor Chatbot</strong>
        <button
          onClick={resetChat}
          style={{
            fontSize: 12,
            border: "none",
            background: "#eee",
            borderRadius: 4,
            padding: "2px 6px",
            cursor: "pointer"
          }}
        >
          🔄 Refresh Chat
        </button>
      </div>

      <div style={{
        height: 500,
        overflowY: "auto",
        background: "#f8f9fa",
        borderRadius: 8,
        padding: 8,
        marginBottom: 8
      }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{ textAlign: msg.sender === "user" ? "right" : "left", marginBottom: 6 }}>
            <div style={{
              display: "inline-block",
              background: msg.sender === "user" ? "#d1e7dd" : "#e2e3e5",
              padding: "8px 12px",
              borderRadius: 12,
              maxWidth: "80%",
              whiteSpace: "pre-line"
            }}>
              {msg.text}
            </div>
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>

      <form onSubmit={sendMessage} style={{ display: "flex", gap: 6 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          disabled={loading}
          placeholder="Type your message..."
          style={{
            flex: 1,
            padding: 8,
            borderRadius: 8,
            border: "1px solid #ccc"
          }}
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          style={{
            background: "#007bff",
            color: "#fff",
            padding: "8px 14px",
            borderRadius: 8,
            border: "none",
            cursor: loading ? "not-allowed" : "pointer"
          }}
        >
          {loading ? "..." : "Send"}
        </button>
      </form>
    </div>
  );
};

export default Chatbot;
