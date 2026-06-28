import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import "./Transcript.css";
import Header from "./Header";
import Footer from "./Footer";

const Transcript = ({ onLogout }) => {
  const { meetingId } = useParams();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [meeting, setMeeting] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [downloading, setDownloading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [editedTranscript, setEditedTranscript] = useState("");
  const [editedSummary, setEditedSummary] = useState("");
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [toast, setToast] = useState(null);
  const [notes, setNotes] = useState("");
  const [savingNotes, setSavingNotes] = useState(false);

  // Add to useEffect to fetch notes:
  const fetchNotes = async () => {
    try {
      const response = await fetch(
        `http://localhost:5000/history/${meetingId}/notes`,
      );
      const data = await response.json();
      if (data.success) {
        setNotes(data.note || "");
      }
    } catch (error) {
      console.error("Error fetching notes:", error);
    }
  };

  const saveNotes = async () => {
    setSavingNotes(true);
    try {
      await fetch(`http://localhost:5000/history/${meetingId}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ note: notes }),
      });
    } catch (error) {
      console.error("Error saving notes:", error);
    } finally {
      setSavingNotes(false);
    }
  };


  useEffect(() => {
    const userData = localStorage.getItem("user");
    if (userData) {
      setUser(JSON.parse(userData));
    }
    fetchMeetingDetails();
    fetchNotes();
  }, [meetingId]);

  const showToast = (message, type = "success") => {
    setToast({ message, type });
  };

  const fetchMeetingDetails = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://127.0.0.1:5000/history/${meetingId}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        },
      );

      if (response.ok) {
        const data = await response.json();
        setMeeting(data.meeting);
        setEditedTranscript(data.meeting.transcript || "");
        setEditedSummary(data.meeting.summary || "");
      } else {
        setError("Failed to load meeting details");
      }
    } catch (err) {
      setError("Network error. Please try again.");
      console.error("Error fetching meeting:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setSaveSuccess(false);

    try {
      const response = await fetch(
        `http://127.0.0.1:5000/history/${meetingId}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            transcript: editedTranscript,
            summary: editedSummary,
            status: "Edited",
          }),
        },
      );

      if (response.ok) {
        setSaveSuccess(true);
        setIsEditing(false);
        await fetchMeetingDetails();

        setTimeout(() => setSaveSuccess(false), 3000);
      } else {
        setError("Failed to save changes");
      }
    } catch (err) {
      setError("Network error. Please try again.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!meeting || !meeting.pdf_path) {
      alert("PDF not available for this meeting");
      return;
    }

    setDownloading(true);
    try {
      const response = await fetch(
        `http://127.0.0.1:5000/download-pdf?meeting_id=${meetingId}&download=true`,
      );

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = meeting.pdf_filename || `meeting_${meetingId}_summary.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        alert("Failed to download PDF");
      }
    } catch (err) {
      alert("Network error while downloading PDF");
      console.error("Download error:", err);
    } finally {
      setDownloading(false);
    }
  };

  const handleViewPDF = async () => {
    if (!meeting || !meeting.pdf_path) {
      alert("PDF not available for this meeting");
      return;
    }

    try {
      const url = `http://127.0.0.1:5000/download-pdf?meeting_id=${meetingId}`;
      window.open(url, "_blank");
    } catch (err) {
      alert("Failed to open PDF");
      console.error("View PDF error:", err);
    }
  };

  const parseTaskAssignments = (taskData) => {
    console.log("📋 Parsing task assignments:", taskData);

    if (!taskData) {
      console.log("❌ No task data provided");
      return [];
    }

    if (Array.isArray(taskData)) {
      console.log("✅ Task data is already an array");
      return taskData;
    }

    if (typeof taskData === "string") {
      // Try JSON parse first
      try {
        const parsed = JSON.parse(taskData);
        if (Array.isArray(parsed)) {
          console.log("✅ Parsed as JSON array");
          return parsed;
        }
      } catch (e) {
        console.log("📝 Not JSON, parsing as markdown table");
      }

      // Parse markdown table
      const lines = taskData.split("\n");
      const tasks = [];

      for (const line of lines) {
        const trimmedLine = line.trim();

        // Skip empty lines, header separators, and header row
        if (
          !trimmedLine ||
          trimmedLine.includes("---") ||
          trimmedLine.toLowerCase().includes("assigned to") ||
          (trimmedLine.toLowerCase().includes("task") &&
            trimmedLine.toLowerCase().includes("deadline"))
        ) {
          continue;
        }

        if (trimmedLine.includes("|")) {
          const cells = trimmedLine
            .split("|")
            .map((cell) => cell.trim())
            .filter((cell) => cell);

          console.log("🔍 Parsed cells:", cells);

          if (cells.length >= 3) {
            tasks.push({
              assignedTo: cells[0],
              task: cells[1],
              deadline: cells[2],
            });
          }
        }
      }

      console.log("✅ Parsed tasks:", tasks);
      return tasks;
    }

    console.log("❌ Unknown task data type");
    return [];
  };

  const parseDependencies = (depData) => {
    console.log("🔗 Parsing dependencies:", depData);

    if (!depData) {
      console.log("❌ No dependency data provided");
      return [];
    }

    if (Array.isArray(depData)) {
      console.log("✅ Dependency data is already an array");
      return depData;
    }

    if (typeof depData === "string") {
      // Try JSON parse first
      try {
        const parsed = JSON.parse(depData);
        if (Array.isArray(parsed)) {
          console.log("✅ Parsed as JSON array");
          return parsed;
        }
      } catch (e) {
        console.log("📝 Not JSON, parsing as markdown table");
      }

      // Parse markdown table
      const lines = depData.split("\n");
      const dependencies = [];

      for (const line of lines) {
        const trimmedLine = line.trim();

        // Skip empty lines, header separators, and header row
        if (
          !trimmedLine ||
          trimmedLine.includes("---") ||
          trimmedLine.toLowerCase().includes("person") ||
          trimmedLine.toLowerCase().includes("dependent")
        ) {
          continue;
        }

        if (trimmedLine.includes("|")) {
          const cells = trimmedLine
            .split("|")
            .map((cell) => cell.trim())
            .filter((cell) => cell);

          console.log("🔍 Parsed cells:", cells);

          if (cells.length >= 5) {
            dependencies.push({
              person: cells[0],
              dependentTask: cells[1],
              dependsOn: cells[2],
              requiredTask: cells[3],
              reason: cells[4],
            });
          }
        }
      }

      console.log("✅ Parsed dependencies:", dependencies);
      return dependencies;
    }

    console.log("❌ Unknown dependency data type");
    return [];
  };

  const parseKeyDecisions = (keyDecisionsData) => {
    console.log("🔑 Parsing key decisions:", keyDecisionsData);

    if (!keyDecisionsData) {
      console.log("❌ No key decisions data provided");
      return [];
    }

    if (Array.isArray(keyDecisionsData)) {
      console.log("✅ Key decisions data is already an array");
      return keyDecisionsData;
    }

    if (typeof keyDecisionsData === "string") {
      // Check if it says "No key decisions"
      if (keyDecisionsData.toLowerCase().includes("no key decisions")) {
        return [];
      }

      // Try JSON parse first
      try {
        const parsed = JSON.parse(keyDecisionsData);
        if (Array.isArray(parsed)) {
          console.log("✅ Parsed as JSON array");
          return parsed;
        }
      } catch (e) {
        console.log("📝 Not JSON, parsing as markdown table");
      }

      // Parse markdown table
      const lines = keyDecisionsData.split("\n");
      const decisions = [];

      for (const line of lines) {
        const trimmedLine = line.trim();

        if (
          !trimmedLine ||
          trimmedLine.includes("---") ||
          (trimmedLine.toLowerCase().includes("decision") &&
            trimmedLine.toLowerCase().includes("made by"))
        ) {
          continue;
        }

        if (trimmedLine.includes("|")) {
          const cells = trimmedLine
            .split("|")
            .map((cell) => cell.trim())
            .filter((cell) => cell);

          if (cells.length >= 2) {
            decisions.push({
              decision: cells[0],
              madeBy: cells[1],
              impact: cells[2] || "Not specified",
            });
          }
        }
      }

      console.log("✅ Parsed key decisions:", decisions);
      return decisions;
    }

    return [];
  };

  const parseNextSteps = (nextStepsData) => {
    console.log("📍 Parsing next steps:", nextStepsData);

    if (!nextStepsData) {
      console.log("❌ No next steps data provided");
      return [];
    }

    if (Array.isArray(nextStepsData)) {
      console.log("✅ Next steps data is already an array");
      return nextStepsData;
    }

    if (typeof nextStepsData === "string") {
      // Check if it says "No next steps"
      if (nextStepsData.toLowerCase().includes("no next steps")) {
        return [];
      }

      // Try JSON parse first
      try {
        const parsed = JSON.parse(nextStepsData);
        if (Array.isArray(parsed)) {
          console.log("✅ Parsed as JSON array");
          return parsed;
        }
      } catch (e) {
        console.log("📝 Not JSON, parsing as markdown table");
      }

      // Parse markdown table
      const lines = nextStepsData.split("\n");
      const steps = [];

      for (const line of lines) {
        const trimmedLine = line.trim();

        if (
          !trimmedLine ||
          trimmedLine.includes("---") ||
          (trimmedLine.toLowerCase().includes("action") &&
            trimmedLine.toLowerCase().includes("owner"))
        ) {
          continue;
        }

        if (trimmedLine.includes("|")) {
          const cells = trimmedLine
            .split("|")
            .map((cell) => cell.trim())
            .filter((cell) => cell);

          if (cells.length >= 2) {
            steps.push({
              action: cells[0],
              owner: cells[1],
              timeline: cells[2] || "Not specified",
            });
          }
        }
      }

      console.log("✅ Parsed next steps:", steps);
      return steps;
    }

    return [];
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  if (loading) {
    return (
      <div className="dashboard-container">
        <Header
          user={user}
          onLogout={onLogout}
          onNavigateToDashboard={() => navigate("/dashboard")}
        />
        <main className="main-content">
          <div className="loading-state">
            <div className="spinner-large"></div>
            <p>Loading meeting details...</p>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  if (error || !meeting) {
    return (
      <div className="dashboard-container">
        <Header
          user={user}
          onLogout={onLogout}
          onNavigateToDashboard={() => navigate("/dashboard")}
        />
        <main className="main-content">
          <div className="error-state">
            <p className="error-text">❌ {error || "Meeting not found"}</p>
            <button onClick={() => navigate("/history")} className="retry-btn">
              ← Back to History
            </button>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  const tasks = parseTaskAssignments(meeting.task_assignments);
  const dependencies = parseDependencies(meeting.dependencies);
  const keyDecisions = parseKeyDecisions(meeting.key_decisions);
  const nextSteps = parseNextSteps(meeting.next_steps);

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
      <Header
        user={user}
        onLogout={onLogout}
        onNavigateToDashboard={() => navigate("/dashboard")}
      />

      <main className="main-content">
        {/* Meeting Header */}
        <div className="transcript-header">
          <button onClick={() => navigate("/history")} className="back-btn">
            ← Back to History
          </button>
          <h1 className="meeting-main-title">
            {meeting.meeting_title || meeting.title || "Meeting Details"}
          </h1>
          <p className="meeting-date">📅 {formatDate(meeting.created_at)}</p>

          <div className="pdf-actions">
            {!isEditing && (
              <>
                <button
                  onClick={handleViewPDF}
                  className="view-pdf-btn"
                  disabled={!meeting.pdf_path}
                >
                  👁️ View PDF
                </button>
                <button
                  onClick={handleDownloadPDF}
                  className="download-pdf-btn"
                  disabled={downloading || !meeting.pdf_path}
                >
                  {downloading ? "⏳ Downloading..." : "📥 Download PDF"}
                </button>
                <button
                  onClick={() => setIsEditing(true)}
                  className="edit-button"
                >
                  ✏️ Edit Transcript
                </button>
              </>
            )}
            {isEditing && (
              <>
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="save-button"
                >
                  {isSaving ? "💾 Saving..." : "💾 Save Changes"}
                </button>
                <button
                  onClick={() => {
                    setIsEditing(false);
                    setEditedTranscript(meeting.transcript);
                    setEditedSummary(meeting.summary);
                  }}
                  disabled={isSaving}
                  className="cancel-button"
                >
                  ❌ Cancel
                </button>
              </>
            )}
          </div>
        </div>

        {/* Success Message */}
        {saveSuccess && (
          <div className="success-banner">✅ Changes saved successfully!</div>
        )}

        {/* Meeting Summary */}
        <div className="detail-section">
          <h2 className="section-title">📋 Meeting Overview</h2>
          {isEditing ? (
            <textarea
              value={editedSummary}
              onChange={(e) => setEditedSummary(e.target.value)}
              className="edit-textarea summary-textarea"
              placeholder="Edit summary..."
            />
          ) : (
            <div className="summary-content">
              {meeting.summary ? (
                meeting.summary.split("\n\n").map(
                  (paragraph, index) =>
                    paragraph.trim() && (
                      <p key={index} className="summary-paragraph">
                        {paragraph}
                      </p>
                    ),
                )
              ) : (
                <p className="no-data-message">No summary available</p>
              )}
            </div>
          )}
        </div>

        {/* Notes Section */}
        <div className="notes-section">
          <h2>📝 Meeting Notes</h2>
          <textarea
            className="notes-textarea"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add your notes here... (saved automatically)"
          />
          <button
            className="save-notes-btn"
            onClick={saveNotes}
            disabled={savingNotes}
          >
            {savingNotes ? "💾 Saving..." : "💾 Save Notes"}
          </button>
        </div>

        {/* Task Assignments */}
        <div className="detail-section">
          <h2 className="section-title">✅ Task Assignments</h2>
          {tasks.length > 0 ? (
            <div className="table-container">
              <table className="data-table task-table">
                <thead>
                  <tr>
                    <th>Assigned To</th>
                    <th>Task</th>
                    <th>Deadline</th>
                  </tr>
                </thead>
                <tbody>
                  {tasks.map((task, index) => (
                    <tr key={index}>
                      <td className="person-cell">{task.assignedTo}</td>
                      <td className="task-cell">{task.task}</td>
                      <td className="deadline-cell">{task.deadline}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="no-data-message">
              No task assignments found for this meeting.
            </p>
          )}
        </div>

        {/* Dependencies */}
        <div className="detail-section">
          <h2 className="section-title">🔗 Task Dependencies</h2>
          {dependencies.length > 0 ? (
            <div className="table-container">
              <table className="data-table dependency-table">
                <thead>
                  <tr>
                    <th>Person</th>
                    <th>Dependent Task</th>
                    <th>Depends On</th>
                    <th>Required Task</th>
                    <th>Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {dependencies.map((dep, index) => (
                    <tr key={index}>
                      <td className="person-cell">{dep.person}</td>
                      <td className="task-cell">{dep.dependentTask}</td>
                      <td className="person-cell">{dep.dependsOn}</td>
                      <td className="task-cell">{dep.requiredTask}</td>
                      <td className="reason-cell">{dep.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="no-data-message">
              No task dependencies identified for this meeting.
            </p>
          )}
        </div>

        {/* Key Decisions */}
        <div className="detail-section">
          <h2 className="section-title">🔑 Key Decisions</h2>
          {keyDecisions.length > 0 ? (
            <div className="table-container">
              <table className="data-table decisions-table">
                <thead>
                  <tr>
                    <th>Decision</th>
                    <th>Made By</th>
                    <th>Impact</th>
                  </tr>
                </thead>
                <tbody>
                  {keyDecisions.map((decision, index) => (
                    <tr key={index}>
                      <td className="task-cell">{decision.decision}</td>
                      <td className="person-cell">{decision.madeBy}</td>
                      <td className="reason-cell">{decision.impact}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="no-data-message">
              No key decisions were made in this meeting.
            </p>
          )}
        </div>

        {/* Next Steps */}
        <div className="detail-section">
          <h2 className="section-title">📍 Next Steps</h2>
          {nextSteps.length > 0 ? (
            <div className="table-container">
              <table className="data-table nextsteps-table">
                <thead>
                  <tr>
                    <th>Action</th>
                    <th>Owner</th>
                    <th>Timeline</th>
                  </tr>
                </thead>
                <tbody>
                  {nextSteps.map((step, index) => (
                    <tr key={index}>
                      <td className="task-cell">{step.action}</td>
                      <td className="person-cell">{step.owner}</td>
                      <td className="deadline-cell">{step.timeline}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="no-data-message">
              No next steps were identified in this meeting.
            </p>
          )}
        </div>

        {/* Transcript */}
        <div className="detail-section">
          <h2 className="section-title">📝 Full Transcript</h2>
          {isEditing ? (
            <textarea
              value={editedTranscript}
              onChange={(e) => setEditedTranscript(e.target.value)}
              className="edit-textarea transcript-textarea"
              placeholder="Edit transcript..."
            />
          ) : (
            <div className="transcript-content">
              {meeting.transcript ? (
                <pre className="transcript-text">{meeting.transcript}</pre>
              ) : (
                <p className="no-data-message">No transcript available</p>
              )}
            </div>
          )}
        </div>

        {/* Recipients Section */}
        {meeting.recipients && meeting.recipients.length > 0 && (
          <div className="detail-section">
            <h2 className="section-title">👥 Email Recipients</h2>
            <div className="recipients-list">
              {meeting.recipients.map((recipient, index) => (
                <div key={index} className="recipient-item">
                  <span className="recipient-name">{recipient.name}</span>
                  <span className="recipient-email">{recipient.email}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
};

export default Transcript;
