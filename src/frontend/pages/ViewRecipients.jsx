import React, { useState, useEffect } from 'react';
import './ViewRecipients.css';

const ViewRecipients = ({ meeting, onClose }) => {
  const [recipients, setRecipients] = useState([]);
  const [sentRecipients, setSentRecipients] = useState([]);
  const [unsent, setUnsent] = useState([]);

  useEffect(() => {
    // Parse recipients data
    console.log("📧 Meeting data:", meeting);
    console.log("📧 Recipients raw:", meeting.recipients);

    let recipientsList = [];

    if (meeting.recipients) {
      if (typeof meeting.recipients === 'string') {
        try {
          recipientsList = JSON.parse(meeting.recipients);
        } catch (e) {
          console.error("Error parsing recipients:", e);
          recipientsList = [];
        }
      } else if (Array.isArray(meeting.recipients)) {
        recipientsList = meeting.recipients;
      }
    }

    console.log("📧 Parsed recipients:", recipientsList);

    setRecipients(recipientsList);

    // Separate sent and unsent
    const sent = recipientsList.filter(r => r.email_sent === true || r.email_sent === 'true' || r.email_sent === 1);
    const pending = recipientsList.filter(r => !r.email_sent || r.email_sent === false || r.email_sent === 'false' || r.email_sent === 0);

    setSentRecipients(sent);
    setUnsent(pending);
  }, [meeting]);

  return (
    <div className="modal-overlay-recipients">
      <div className="recipients-modal">
        <div className="recipients-modal-header">
          <h2 className="recipients-modal-title">📧 Email Recipients</h2>
          <p className="recipients-modal-subtitle">{meeting.title || meeting.meeting_title || 'Meeting'}</p>
        </div>

        <div className="recipients-modal-body">
          {recipients.length === 0 ? (
            <div className="no-recipients">
              <p className="no-recipients-icon">📭</p>
              <p className="no-recipients-text">No recipients for this meeting</p>
            </div>
          ) : (
            <>
              {sentRecipients.length > 0 && (
                <div className="recipients-section">
                  <h3 className="recipients-section-title">✅ Email Sent ({sentRecipients.length})</h3>
                  <div className="recipients-list">
                    {sentRecipients.map((recipient, index) => (
                      <div key={`sent-${index}`} className="recipient-item sent">
                        <div className="recipient-avatar">
                          {recipient.name ? recipient.name.charAt(0).toUpperCase() : 'U'}
                        </div>
                        <div className="recipient-info">
                          <p className="recipient-name">{recipient.name || 'Unknown'}</p>
                          <p className="recipient-email">{recipient.email || 'No email'}</p>
                        </div>
                        <div className="recipient-status sent-status">
                          <span className="status-icon">✓</span>
                          <span className="status-text">Sent</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {unsent.length > 0 && (
                <div className="recipients-section">
                  <h3 className="recipients-section-title">⏳ Pending ({unsent.length})</h3>
                  <div className="recipients-list">
                    {unsent.map((recipient, index) => (
                      <div key={`pending-${index}`} className="recipient-item pending">
                        <div className="recipient-avatar pending-avatar">
                          {recipient.name ? recipient.name.charAt(0).toUpperCase() : 'U'}
                        </div>
                        <div className="recipient-info">
                          <p className="recipient-name">{recipient.name || 'Unknown'}</p>
                          <p className="recipient-email">{recipient.email || 'No email'}</p>
                        </div>
                        <div className="recipient-status pending-status">
                          <span className="status-icon">⏳</span>
                          <span className="status-text">Pending</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        <div className="recipients-modal-footer">
          <button onClick={onClose} className="close-recipients-btn">
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default ViewRecipients;