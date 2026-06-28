import React from 'react';
import './Header.css';
import logo from '../../assets/meetscribe.png';

const Header = ({ user, onLogout, onNavigateToDashboard, onNavigateToHistory }) => {
  return (
    <header className="dashboard-header">
      <div className="header-content">
        <div className="header-inner">
          <div className="header-logo">
            <div className="logo-container">
              <img src={logo} alt="MeetScribe Logo" className="logo-image" />
            </div>
            <div className="brand-info">
              <h1 className="header-title">MeetScribe</h1>
              <p className="header-subtitle">AI-Powered Meeting Intelligence</p>
            </div>
          </div>
          
          <div className="header-actions">
            {/* Navigation Buttons */}
            <div className="nav-buttons">
              {onNavigateToDashboard && (
                <button onClick={onNavigateToDashboard} className="nav-btn dashboard-btn" title="Go to Dashboard">
                  <svg className="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="3" width="7" height="7"></rect>
                    <rect x="14" y="3" width="7" height="7"></rect>
                    <rect x="14" y="14" width="7" height="7"></rect>
                    <rect x="3" y="14" width="7" height="7"></rect>
                  </svg>
                  <span>Dashboard</span>
                </button>
              )}
              
              {onNavigateToHistory && (
                <button onClick={onNavigateToHistory} className="nav-btn history-btn" title="View History">
                  <svg className="nav-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                  <span>History</span>
                </button>
              )}
            </div>

            {/* User Info */}
            <div className="user-info">
              <div className="user-avatar">
                {user?.username?.charAt(0).toUpperCase()}
              </div>
              <div className="user-details">
                <p className="user-name">{user?.username}</p>
                <p className="user-email">{user?.email}</p>
              </div>
            </div>

            {/* Logout Button */}
            <button onClick={onLogout} className="logout-button">
              <svg className="logout-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                <polyline points="16 17 21 12 16 7"></polyline>
                <line x1="21" y1="12" x2="9" y2="12"></line>
              </svg>
              <span>Logout</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;