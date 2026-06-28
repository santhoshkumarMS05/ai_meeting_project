import React, { useState } from 'react';
import './EmailSend.css';

const EmailSend = ({ meeting, onClose, onSuccess }) => {
  const [recipients, setRecipients] = useState(
    meeting.recipients && meeting.recipients.length > 0 
      ? meeting.recipients 
      : [{ name: '', email: '' }]
  );
  const [sending, setSending] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [emailError, setEmailError] = useState(null);

  const handleAddRecipient = () => {
    setRecipients([...recipients, { name: '', email: '' }]);
    setEmailError(null);
  };

  const handleRemoveRecipient = (index) => {
    setRecipients(recipients.filter((_, i) => i !== index));
    setEmailError(null);
  };

  const handleRecipientChange = (index, field, value) => {
    const newRecipients = [...recipients];
    newRecipients[index][field] = value;
    setRecipients(newRecipients);
    setEmailError(null);
  };

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validateRecipients = () => {
    const validRecipients = recipients.filter(r => r.name.trim() && r.email.trim());
    
    if (validRecipients.length === 0) {
      setEmailError('Please add at least one recipient with name and email');
      return false;
    }

    // Check each email for valid format
    for (let i = 0; i < validRecipients.length; i++) {
      const recipient = validRecipients[i];
      if (!validateEmail(recipient.email)) {
        setEmailError(`Invalid email format: ${recipient.email}`);
        return false;
      }
    }

    return validRecipients;
  };

  const handleSendEmail = async () => {
    const validRecipients = validateRecipients();
    if (!validRecipients) return;

    setSending(true);
    try {
      const response = await fetch(`http://127.0.0.1:5000/history/${meeting.id}/resend`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          recipients: validRecipients
        })
      });

      if (response.ok) {
        const data = await response.json();
        setSuccessMessage(`Email sent to ${validRecipients.length} recipient(s)`);
        setShowSuccess(true);
        
        setTimeout(() => {
          onSuccess();
          onClose();
        }, 3500);
      } else {
        setEmailError('Failed to send email. Please try again.');
      }
    } catch (err) {
      setEmailError('Network error while sending email');
      console.error('Send error:', err);
    } finally {
      setSending(false);
    }
  };

  return (
    <>
      {/* Success Animation */}
      {showSuccess && (
        <div className="success-overlay">
          <div className="success-popup-container">
            <div className="success-checkmark-wrapper">
              <svg className="success-checkmark-svg" viewBox="0 0 52 52">
                <circle className="checkmark-circle-svg" cx="26" cy="26" r="25" />
                <path className="checkmark-path-svg" d="M14.1 27.2l7.1 7.2 16.7-16.8" />
              </svg>
            </div>
            <h2 className="success-title">Email Sent!</h2>
            <p className="success-message">{successMessage}</p>
          </div>
        </div>
      )}

      {/* Email Send Modal */}
      <div className="modal-overlay-email">
        <div className="email-modal">
          <div className="email-modal-header">
            <h2 className="email-modal-title">📧 Send Meeting Summary</h2>
            <p className="email-modal-subtitle">Send meeting summary to recipients</p>
          </div>

          <div className="email-modal-body">
            {/* Error Message */}
            {emailError && (
              <div className="email-error-alert">
                <span className="error-icon">❌</span>
                <span className="error-text">{emailError}</span>
              </div>
            )}

            <div className="meeting-info-section">
              <h3 className="section-title">Meeting Details</h3>
              <div className="meeting-info-box">
                <p><strong>Title:</strong> {meeting.title || 'Untitled Meeting'}</p>
                <p><strong>PDF:</strong> {meeting.pdf_filename || 'Not available'}</p>
              </div>
            </div>

            <div className="recipients-section">
              <h3 className="section-title">Recipients</h3>
              <p className="section-description">Add people to send this meeting summary to:</p>

              <div className="recipients-list">
                {recipients.map((recipient, index) => (
                  <div key={index} className="recipient-input-group">
                    <div className="recipient-inputs">
                      <input
                        type="text"
                        placeholder="Recipient Name"
                        value={recipient.name}
                        onChange={(e) => handleRecipientChange(index, 'name', e.target.value)}
                        className="recipient-input"
                      />
                      <input
                        type="email"
                        placeholder="Email Address (e.g., john@example.com)"
                        value={recipient.email}
                        onChange={(e) => handleRecipientChange(index, 'email', e.target.value)}
                        className={`recipient-input ${
                          recipient.email && !validateEmail(recipient.email) ? 'invalid-email' : ''
                        }`}
                      />
                      {recipient.email && !validateEmail(recipient.email) && (
                        <span className="email-validation-hint">❌ Invalid email format</span>
                      )}
                    </div>
                    {recipients.length > 1 && (
                      <button
                        onClick={() => handleRemoveRecipient(index)}
                        className="remove-recipient-btn"
                        title="Remove recipient"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                ))}
              </div>

              <button onClick={handleAddRecipient} className="add-recipient-btn">
                + Add More Recipients
              </button>
            </div>
          </div>

          <div className="email-modal-footer">
            <button onClick={onClose} className="cancel-btn" disabled={sending}>
              Cancel
            </button>
            <button 
              onClick={handleSendEmail} 
              className="send-btn"
              disabled={sending}
            >
              {sending ? '⏳ Sending...' : '📤 Send Email'}
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default EmailSend;