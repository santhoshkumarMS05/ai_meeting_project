import React, { useState, useEffect } from "react";
import "./Dashboard.css";
import Header from "./Header";
import Footer from "./Footer";
import { useNavigate } from "react-router-dom";

const Dashboard = ({ onLogout }) => {
  const [user, setUser] = useState(null);
  const [meetingLink, setMeetingLink] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [showErrorModal, setShowErrorModal] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [analytics, setAnalytics] = useState(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const userData = localStorage.getItem("user");
    if (userData) {
      setUser(JSON.parse(userData));
    }
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await fetch("http://localhost:5000/analytics");
      const data = await response.json();
      if (data.success) {
        setAnalytics(data);
      }
    } catch (error) {
      console.error("Error fetching analytics:", error);
    } finally {
      setAnalyticsLoading(false);
    }
  };


  const handleJoinMeeting = async () => {
    if (!meetingLink.trim()) {
      setErrorMessage("Please enter a meeting link");
      setShowErrorModal(true);
      return;
    }

    setLoading(true);
    setStatus("Joining meeting...");
    console.log("🔍 FRONTEND user_email:", user?.email || "default@example.com");

    try {
      const response = await fetch("http://127.0.0.1:5000/join-meeting", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          meeting_link: meetingLink,
          user_email: user?.email || "default@example.com", // ← ADD THIS LINE
        }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setStatus("✅ Agent is joining the meeting");
        setShowSuccessModal(true);
        setLoading(false);
        setTimeout(() => {
          setMeetingLink("");
          setStatus("");
        }, 2000);
      } else {
        setErrorMessage(data.error || "Failed to join meeting");
        setShowErrorModal(true);
        setStatus("❌ Failed to join meeting");
        setLoading(false);
      }
    } catch (error) {
      setErrorMessage("Network error. Please check if the server is running.");
      setShowErrorModal(true);
      setStatus("❌ Connection error");
      setLoading(false);
    }
  };

  const closeSuccessModal = () => {
    setShowSuccessModal(false);
    setStatus("");
  };

  const closeErrorModal = () => {
    setShowErrorModal(false);
    setErrorMessage("");
  };

  return (
    <div className="dashboard-container">
      {/* Success Modal */}
      {showSuccessModal && (
        <div className="modal-overlay">
          <div className="success-modal">
            <div className="success-animation">
              <svg
                className="checkmark"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 52 52"
              >
                <circle
                  className="checkmark-circle"
                  cx="26"
                  cy="26"
                  r="25"
                  fill="none"
                />
                <path
                  className="checkmark-check"
                  fill="none"
                  d="M14.1 27.2l7.1 7.2 16.7-16.8"
                />
              </svg>
            </div>
            <h2 className="success-title">Success! 🎉</h2>
            <p className="success-message">
              AI Agent is joining the meeting! A new browser window has opened.
              Close the browser to leave the meeting.
            </p>
            <div className="modal-buttons">
              <button onClick={closeSuccessModal} className="close-modal-btn">
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Error Modal */}
      {showErrorModal && (
        <div className="modal-overlay">
          <div className="success-modal error-modal">
            <div className="error-animation">
              <svg
                className="error-mark"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 52 52"
              >
                <circle
                  className="error-circle"
                  cx="26"
                  cy="26"
                  r="25"
                  fill="none"
                />
                <path
                  className="error-cross"
                  fill="none"
                  d="M16 16 l20 20 M36 16 l-20 20"
                />
              </svg>
            </div>
            <h2 className="error-title">Oops! ❌</h2>
            <p className="error-message">{errorMessage}</p>
            <div className="modal-buttons">
              <button onClick={closeErrorModal} className="close-modal-btn">
                Try Again
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header Component */}

      <Header
        user={user}
        onLogout={onLogout}
        onNavigateToHistory={() => navigate("/history")}
      />

      {/* Main Content */}
      <main className="main-content">
        {/* Welcome Card */}
        <div className="welcome-card">
          <h2 className="welcome-title">Welcome back, {user?.username}! 👋</h2>
          <p className="welcome-text">
            Paste your meeting link below and let our AI agent join and
            transcribe automatically
          </p>
        </div>

        {/* Meeting Join Card */}
        <div className="upload-card">
          <div className="upload-form">
            {/* Meeting Link Input */}
            <div className="form-section">
              <label className="section-label">
                🔗 Meeting Link <span className="required">*</span>
              </label>
              <div className="meeting-link-area">
                <input
                  type="text"
                  placeholder="Paste your Google Meet, Zoom, or Teams link here..."
                  value={meetingLink}
                  onChange={(e) => setMeetingLink(e.target.value)}
                  className="meeting-link-input"
                  disabled={loading}
                />
                <div className="input-hint">
                  <span>
                    💡 Tip: Make sure the meeting link is valid and accessible
                  </span>
                </div>
              </div>
            </div>

            {/* Status Message */}
            {status && (
              <div
                className={`status-section ${status.includes("✅") ? "status-success" : status.includes("❌") ? "status-error" : "status-loading"}`}
              >
                <p className="status-message">{status}</p>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="button"
              onClick={handleJoinMeeting}
              disabled={loading}
              className="submit-btn"
            >
              {loading ? (
                <span className="submit-loading">
                  <svg
                    className="submit-spinner"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="spinner-circle"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="spinner-path"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    ></path>
                  </svg>
                  <span>Joining Meeting...</span>
                </span>
              ) : (
                "🚀 Join Meeting with AI Agent"
              )}
            </button>

            {/* Info Card */}
            <div className="info-card">
              <h3 className="info-title">ℹ️ How it works:</h3>
              <ul className="info-list">
                <li>Paste your meeting link above</li>
                <li>Click "Join Meeting with AI Agent"</li>
                <li>Our AI agent will join and transcribe the meeting</li>
                <li>You'll receive a summary and action items via email</li>
              </ul>
            </div>
          </div>
        </div>
      </main>

            {/* Analytics Section */}
      {analyticsLoading ? (
        <div className="analytics-loading">Loading analytics...</div>
      ) : analytics && (
        <div className="analytics-grid main-content">
          {/* Stats Cards */}
          <div className="analytics-section">
            <h3 className="analytics-title">📊 Analytics Overview</h3>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon">📈</div>
                <h4>Total Meetings</h4>
                <p className="stat-value">{analytics.stats.total_meetings}</p>
              </div>
              <div className="stat-card">
                <div className="stat-icon">⏱️</div>
                <h4>Avg Duration</h4>
                <p className="stat-value">{analytics.stats.avg_duration.toFixed(1)} min</p>
              </div>
            </div>
          </div>

          {/* Word Cloud */}
          {analytics.top_words && analytics.top_words.length > 0 && (
            <div className="analytics-section">
              <h3 className="analytics-title">🔤 Most Discussed Topics</h3>
              <div className="word-cloud">
                {analytics.top_words.map((item, i) => (
                  <span
                    key={i}
                    className="word-tag"
                    style={{
                      fontSize: `${12 + (item.count * 1.5)}px`,
                    }}
                  >
                    {item.word}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Recent Meetings */}
          {analytics.recent_meetings && analytics.recent_meetings.length > 0 && (
            <div className="analytics-section">
              <h3 className="analytics-title">📅 Recent Meetings</h3>
              <div className="recent-meetings-list">
                {analytics.recent_meetings.map((m) => (
                  <div
                    key={m.id}
                    className="recent-meeting-item"
                    onClick={() => navigate(`/transcript/${m.id}`)}
                  >
                    <div className="recent-meeting-info">
                      <h4>{m.title}</h4>
                      <p>{new Date(m.created_at).toLocaleDateString()}</p>
                    </div>
                    <span className="arrow">→</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <Footer />
    </div>
  );
};

export default Dashboard;
