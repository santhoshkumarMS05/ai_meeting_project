import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./History.css";
import EmailSend from "./EmailSend";
import ViewRecipients from "./ViewRecipients";
import Toast from "./Toast";
import Header from "./Header";
import Footer from "./Footer";

const History = ({ onLogout }) => {
  const [user, setUser] = useState(null);
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteTargetId, setDeleteTargetId] = useState(null);
  const [downloading, setDownloading] = useState(null);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [selectedMeeting, setSelectedMeeting] = useState(null);
  const [emailsSent, setEmailsSent] = useState({});
  const [showRecipientsModal, setShowRecipientsModal] = useState(false);
  const [selectedMeetingForRecipients, setSelectedMeetingForRecipients] =
    useState(null);
  const [deleting, setDeleting] = useState(null);
  const [toast, setToast] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [isSearchActive, setIsSearchActive] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const MEETINGS_PER_PAGE = 9;
  const navigate = useNavigate();

  useEffect(() => {
    const userData = localStorage.getItem("user");
    if (userData) {
      const parsedUser = JSON.parse(userData);
      setUser(parsedUser);
      fetchMeetingHistory(parsedUser.email);
    }
  }, []);

  const fetchMeetingHistory = async (email) => {
    setLoading(true);
    try {
      const userEmail = email || user?.email || "default@example.com";
      console.log("🔍 Fetching history for email:", userEmail);
      console.log("🔍 URL:", `http://127.0.0.1:5000/history?user_email=${encodeURIComponent(userEmail)}`);
      const response = await fetch(
        `http://127.0.0.1:5000/history?user_email=${encodeURIComponent(userEmail)}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        },
      );

      if (response.ok) {
        const data = await response.json();
        setMeetings(data.meetings || []);
        setIsSearchActive(false);
        setSearchQuery("");
        setCurrentPage(1);
      } else {
        setError("Failed to load meeting history");
        showToast("Failed to load meetings", "error");
      }
    } catch (err) {
      console.error("❌ Full error:", err);
      console.error("❌ Error message:", err.message);
      setError("Network error. Please try again.");
      showToast("Network error", "error");
    }
    finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();

    if (searchQuery.trim().length < 2) {
      showToast("Search query must be at least 2 characters", "warning");
      return;
    }

    setSearching(true);
    try {
      const response = await fetch(
        `http://127.0.0.1:5000/history/search?q=${encodeURIComponent(searchQuery)}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        },
      );

      if (response.ok) {
        const data = await response.json();
        setMeetings(data.meetings || []);
        setIsSearchActive(true);
        setCurrentPage(1);
        showToast(`Found ${data.count} meeting(s)`, "info");
      } else {
        showToast("Search failed", "error");
      }
    } catch (err) {
      showToast("Network error while searching", "error");
    } finally {
      setSearching(false);
    }
  };

  const handleClearSearch = () => {
    setSearchQuery("");
    setIsSearchActive(false);
    setCurrentPage(1);
    fetchMeetingHistory(user?.email);
  };

  const showToast = (message, type = "success") => {
    setToast({ message, type });
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const handleViewTranscript = (meetingId) => {
    navigate(`/transcript/${meetingId}`);
  };

  const handleDownloadPDF = async (meeting) => {
    if (!meeting.pdf_filename) {
      showToast("PDF not available for this meeting", "warning");
      return;
    }

    setDownloading(meeting.id);
    try {
      const response = await fetch(
        `http://127.0.0.1:5000/download-pdf?meeting_id=${meeting.id}&download=true`,
      );

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download =
          meeting.pdf_filename || `meeting_${meeting.id}_summary.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        showToast("PDF downloaded successfully", "success");
      } else {
        showToast("Failed to download PDF", "error");
      }
    } catch (err) {
      showToast("Network error while downloading", "error");
    } finally {
      setDownloading(null);
    }
  };

  const handleEmailClick = (meeting) => {
    setSelectedMeeting(meeting);
    setShowEmailModal(true);
  };

  const handleEmailSuccess = () => {
    if (selectedMeeting) {
      setEmailsSent({
        ...emailsSent,
        [selectedMeeting.id]: true,
      });
    }
    showToast("Email sent successfully!", "success");
    fetchMeetingHistory(user?.email);
  };

  const handleViewRecipients = (meeting) => {
    setSelectedMeetingForRecipients(meeting);
    setShowRecipientsModal(true);
  };

  const handleDeleteClick = (meetingId) => {
    setDeleteTargetId(meetingId);
    setShowDeleteModal(true);
  };

  const confirmDelete = async () => {
    setDeleting(deleteTargetId);
    try {
      const response = await fetch(
        `http://127.0.0.1:5000/history/${deleteTargetId}`,
        {
          method: "DELETE",
        },
      );

      if (response.ok) {
        fetchMeetingHistory(user?.email);
        setShowDeleteModal(false);
        setDeleteTargetId(null);
        showToast("Meeting deleted successfully", "success");
      } else {
        showToast("Failed to delete meeting", "error");
      }
    } catch (err) {
      showToast("Network error while deleting", "error");
    } finally {
      setDeleting(null);
    }
  };

  const cancelDelete = () => {
    setShowDeleteModal(false);
    setDeleteTargetId(null);
  };

  // Pagination logic
  const indexOfLastMeeting = currentPage * MEETINGS_PER_PAGE;
  const indexOfFirstMeeting = indexOfLastMeeting - MEETINGS_PER_PAGE;
  const currentMeetings = meetings.slice(
    indexOfFirstMeeting,
    indexOfLastMeeting,
  );
  const totalPages = Math.ceil(meetings.length / MEETINGS_PER_PAGE);

  return (
    <div className="dashboard-container">
      {/* Toast Notifications */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Email Send Modal */}
      {showEmailModal && selectedMeeting && (
        <EmailSend
          meeting={selectedMeeting}
          onClose={() => setShowEmailModal(false)}
          onSuccess={handleEmailSuccess}
        />
      )}

      {/* View Recipients Modal */}
      {showRecipientsModal && selectedMeetingForRecipients && (
        <ViewRecipients
          meeting={selectedMeetingForRecipients}
          onClose={() => setShowRecipientsModal(false)}
        />
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="modal-overlay">
          <div className="success-modal error-modal">
            <h2 className="error-title">Delete Meeting? 🗑️</h2>
            <p className="error-message">
              Are you sure you want to delete this meeting? This action cannot
              be undone.
            </p>
            <div className="modal-buttons">
              <button
                onClick={confirmDelete}
                className="delete-confirm-btn"
                disabled={deleting}
              >
                {deleting ? "⏳ Deleting..." : "Yes, Delete"}
              </button>
              <button
                onClick={cancelDelete}
                className="close-modal-btn"
                disabled={deleting}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header Component */}
      <Header
        user={user}
        onLogout={onLogout}
        onNavigateToDashboard={() => navigate("/dashboard")}
      />

      <main className="main-content">
        {/* Welcome Card */}
        <div className="welcome-card">
          <h2 className="welcome-title">Meeting History 📚</h2>
          <p className="welcome-text">
            View and manage all your past meeting transcripts and summaries
          </p>
        </div>

        {/* History Content */}
        <div className="upload-card">
          {/* Search Bar */}
          <form onSubmit={handleSearch} className="search-form">
            <div className="search-input-wrapper">
              <input
                type="text"
                placeholder="🔍 Search meetings by title..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
              />
              <button type="submit" className="search-btn" disabled={searching}>
                {searching ? "⏳ Searching..." : "🔍 Search"}
              </button>
              {isSearchActive && (
                <button
                  type="button"
                  onClick={handleClearSearch}
                  className="clear-search-btn"
                >
                  Clear
                </button>
              )}
            </div>
          </form>

          {loading ? (
            <div className="loading-state">
              <div className="spinner-large"></div>
              <p>Loading meeting history...</p>
            </div>
          ) : error ? (
            <div className="error-state">
              <p className="error-text">❌ {error}</p>
              <button onClick={() => fetchMeetingHistory(user?.email)} className="retry-btn">
                🔄 Retry
              </button>
            </div>
          ) : meetings.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📭</div>
              <h3 className="empty-title">
                {isSearchActive ? "No meetings found" : "No meetings yet"}
              </h3>
              <p className="empty-text">
                {isSearchActive
                  ? `No meetings matching "${searchQuery}"`
                  : "Your meeting history will appear here after you process transcripts"}
              </p>
              <button
                onClick={
                  isSearchActive
                    ? handleClearSearch
                    : () => navigate("/dashboard")
                }
                className="go-dashboard-btn"
              >
                {isSearchActive
                  ? "← Back to all meetings"
                  : "🚀 Go to Dashboard"}
              </button>
            </div>
          ) : (
            <>
              <div className="meetings-grid">
                {currentMeetings.map((meeting) => (
                  <div key={meeting.id} className="meeting-card">
                    <div className="meeting-card-header">
                      <h3 className="meeting-title">
                        {meeting.title || "Untitled Meeting"}
                      </h3>
                      <span
                        className={`meeting-status ${meeting.status?.toLowerCase()}`}
                      >
                        {meeting.status === "Processing"
                          ? "⏳ Processing..."
                          : meeting.status || "Processed"}
                      </span>
                    </div>

                    <div className="meeting-card-body">
                      <div className="meeting-info">
                        <span className="info-label">📅 Date:</span>
                        <span className="info-value">
                          {formatDate(meeting.created_at)}
                        </span>
                      </div>

                      {meeting.recipients && meeting.recipients.length > 0 && (
                        <div className="meeting-info">
                          <span className="info-label">📧 Recipients:</span>
                          <span className="info-value">
                            {Array.isArray(meeting.recipients)
                              ? meeting.recipients.length
                              : 0}{" "}
                            people
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="meeting-card-actions">
                      <button
                        className="action-btn view-btn"
                        title="View Transcript"
                        onClick={() => handleViewTranscript(meeting.id)}
                      >
                        👁️ View
                      </button>
                      <button
                        className="action-btn download-btn"
                        title="Download PDF"
                        onClick={() => handleDownloadPDF(meeting)}
                        disabled={
                          downloading === meeting.id || !meeting.pdf_filename
                        }
                      >
                        {downloading === meeting.id ? "⏳ ..." : "📥 PDF"}
                      </button>
                      <button
                        className="action-btn recipients-btn"
                        title="View Recipients"
                        onClick={() => handleViewRecipients(meeting)}
                        disabled={
                          !meeting.recipients ||
                          (Array.isArray(meeting.recipients)
                            ? meeting.recipients.length === 0
                            : true)
                        }
                      >
                        👥 Recipients
                      </button>
                      <button
                        className="action-btn resend-btn"
                        title={
                          emailsSent[meeting.id] ? "Resend Email" : "Send Email"
                        }
                        onClick={() => handleEmailClick(meeting)}
                        disabled={!meeting.pdf_filename}
                      >
                        📤 {emailsSent[meeting.id] ? "Resend" : "Send"}
                      </button>
                      <button
                        className="action-btn delete-btn"
                        title="Delete Meeting"
                        onClick={() => handleDeleteClick(meeting.id)}
                        disabled={deleting === meeting.id}
                      >
                        {deleting === meeting.id ? "⏳" : "🗑️"} Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="pagination">
                  <button
                    onClick={() =>
                      setCurrentPage((prev) => Math.max(1, prev - 1))
                    }
                    disabled={currentPage === 1}
                    className="pagination-btn"
                  >
                    ← Previous
                  </button>

                  {Array.from({ length: totalPages }, (_, i) => i + 1).map(
                    (page) => (
                      <button
                        key={page}
                        onClick={() => setCurrentPage(page)}
                        className={`pagination-btn ${currentPage === page ? "active" : ""}`}
                      >
                        {page}
                      </button>
                    ),
                  )}

                  <button
                    onClick={() =>
                      setCurrentPage((prev) => Math.min(totalPages, prev + 1))
                    }
                    disabled={currentPage === totalPages}
                    className="pagination-btn"
                  >
                    Next →
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default History;