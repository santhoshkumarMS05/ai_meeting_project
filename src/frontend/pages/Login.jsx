import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./Login.css";
import logo from "../../assets/meetscribe.png";

const Login = ({ onLoginSuccess }) => {
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);

  // Form states
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);

  // Calculate password strength
  const calculatePasswordStrength = (pwd) => {
    let strength = 0;
    if (pwd.length >= 8) strength++;
    if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) strength++;
    if (/\d/.test(pwd)) strength++;
    if (/[@$!%*?&]/.test(pwd)) strength++;
    return strength;
  };

  const handlePasswordChange = (e) => {
    const pwd = e.target.value;
    setPassword(pwd);
    if (!isLogin) {
      setPasswordStrength(calculatePasswordStrength(pwd));
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await fetch("http://localhost:5000/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();

      if (res.ok) {
        localStorage.setItem("token", data.token);
        localStorage.setItem(
          "user",
          JSON.stringify({ username: data.username, email }),
        );
        onLoginSuccess();
        navigate("/dashboard");
      } else {
        setError(data.error || "Login failed. Please try again.");
      }
    } catch (err) {
      setError("Network error. Please check your connection.");
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      setLoading(false);
      return;
    }

    if (passwordStrength < 2) {
      setError(
        "Password must be at least 8 characters with uppercase, lowercase, and numbers",
      );
      setLoading(false);
      return;
    }

    try {
      const res = await fetch("http://localhost:5000/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, email, password }),
      });
      const data = await res.json();

      if (res.ok) {
        setError("");
        setIsLogin(true);
        // Clear signup fields
        setUsername("");
        setPassword("");
        setConfirmPassword("");
        setPasswordStrength(0);
      } else {
        setError(data.error || "Signup failed. Please try again.");
      }
    } catch (err) {
      setError("Network error. Please check your connection.");
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setError("");
    setUsername("");
    setEmail("");
    setPassword("");
    setConfirmPassword("");
    setPasswordStrength(0);
  };

  const features = [
    {
      icon: "🎥",
      title: "Auto Meeting Join",
      description:
        "AI agent joins Google Meet automatically using the provided meeting link",
    },
    {
      icon: "🎙️",
      title: "Live Audio Capture",
      description:
        "Securely capture system meeting audio while the agent is in the call",
    },
    {
      icon: "🧠",
      title: "Speaker Identification",
      description:
        "Split conversation by speakers using voice-based diarization",
    },
    {
      icon: "📝",
      title: "Accurate Transcripts",
      description:
        "Convert meeting audio into clean, readable transcripts using AI",
    },
    {
      icon: "📋",
      title: "Smart Summaries",
      description:
        "Automatically generate concise summaries from meeting discussions",
    },
    {
      icon: "📑",
      title: "Reports & Sharing",
      description: "Generate professional PDF reports and share them via email",
    },
  ];

  const getPasswordStrengthColor = () => {
    if (passwordStrength === 0) return "weak";
    if (passwordStrength === 1 || passwordStrength === 2) return "medium";
    return "strong";
  };

  return (
    <div className="login-container">
      <div className="login-wrapper">
        {/* Left side - Information Panel */}
        <div className="info-panel">
          <div className="decorative-circle decorative-circle-top"></div>
          <div className="decorative-circle decorative-circle-bottom"></div>

          <div className="info-content">
            {/* Logo and Title */}
            <div className="header-section">
              <div className="logo-wrapper">
                <div className="logo-box">
                  <img
                    src={logo}
                    alt="MeetScribe Logo"
                    className="logo-image"
                  />
                </div>
                <div className="logo-text">
                  <h1 className="app-title">MeetScribe</h1>
                  <p className="app-subtitle">AI Meeting Intelligence</p>
                </div>
              </div>
              <p className="app-description">
                Let an AI agent join your meetings, capture the audio, and
                transform conversations into clean transcripts, summaries, and
                shareable reports automatically.
              </p>
            </div>

            {/* Features Grid */}
            <div className="features-section">
              <h3 className="features-title">Platform Features</h3>
              <div className="features-grid">
                {features.map((feature, index) => (
                  <div key={index} className="feature-card">
                    <div className="feature-content">
                      <span
                        className="feature-icon"
                        role="img"
                        aria-label={feature.title}
                      >
                        {feature.icon}
                      </span>
                      <div className="feature-text">
                        <h4 className="feature-title">{feature.title}</h4>
                        <p className="feature-description">
                          {feature.description}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Right side - Auth Form */}
        <div className="form-panel">
          {/* Mobile Logo */}
          <div className="mobile-logo">
            <div className="mobile-logo-box">
              <span className="logo-icon">🎯</span>
            </div>
          </div>

          <div className="form-header">
            <h2 className="form-title">
              {isLogin ? "Welcome Back" : "Create Account"}
            </h2>
            <p className="form-subtitle">
              {isLogin
                ? "Sign in to access your meeting dashboard"
                : "Sign up to get started with MeetScribe"}
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="error-message" role="alert">
              <div className="error-content">
                <span className="error-icon" aria-hidden="true">
                  ✕
                </span>
                <p className="error-text">{error}</p>
              </div>
            </div>
          )}

          {/* Auth Form */}
          <form
            onSubmit={isLogin ? handleLogin : handleSignup}
            className="login-form"
            noValidate
          >
            {/* Username Input (Signup only) */}
            {!isLogin && (
              <div className="form-group">
                <label htmlFor="username" className="form-label">
                  Username
                </label>
                <div className="input-wrapper">
                  <svg
                    className="input-icon"
                    xmlns="http://www.w3.org/2000/svg"
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                  </svg>
                  <input
                    id="username"
                    type="text"
                    placeholder="Enter your username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="form-input"
                    required
                    aria-label="Username"
                  />
                </div>
              </div>
            )}

            {/* Email Input */}
            <div className="form-group">
              <label htmlFor="email" className="form-label">
                Email Address
              </label>
              <div className="input-wrapper">
                <svg
                  className="input-icon"
                  xmlns="http://www.w3.org/2000/svg"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <rect x="2" y="4" width="20" height="16" rx="2"></rect>
                  <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path>
                </svg>
                <input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="form-input"
                  required
                  aria-label="Email Address"
                />
              </div>
            </div>

            {/* Password Input */}
            <div className="form-group">
              <label htmlFor="password" className="form-label">
                Password
              </label>
              <div className="input-wrapper">
                <svg
                  className="input-icon"
                  xmlns="http://www.w3.org/2000/svg"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <rect
                    x="3"
                    y="11"
                    width="18"
                    height="11"
                    rx="2"
                    ry="2"
                  ></rect>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                </svg>
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder={
                    isLogin ? "Enter your password" : "Create a password"
                  }
                  value={password}
                  onChange={handlePasswordChange}
                  className="form-input password-input"
                  required
                  aria-label="Password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="password-toggle"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-4-11-4s1.6-3.6 4.6-6M9.9 4.24A9.98 9.98 0 0 1 12 4c7 0 11 4 11 4s-1.6 3.6-4.6 6m2.5 5.5m5 5L2 2"></path>
                    </svg>
                  ) : (
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                      <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {/* Password Strength Indicator (Signup only) */}
            {!isLogin && (
              <div className="password-strength">
                <div className="strength-bars">
                  <div
                    className={`strength-bar strength-${getPasswordStrengthColor()}`}
                  ></div>
                  <div
                    className={`strength-bar strength-${getPasswordStrengthColor()}`}
                  ></div>
                  <div
                    className={`strength-bar strength-${getPasswordStrengthColor()}`}
                  ></div>
                  <div
                    className={`strength-bar strength-${getPasswordStrengthColor()}`}
                  ></div>
                </div>
                <span
                  className={`strength-text strength-${getPasswordStrengthColor()}`}
                >
                  {passwordStrength === 0 && "Very Weak"}
                  {passwordStrength === 1 && "Weak"}
                  {passwordStrength === 2 && "Fair"}
                  {passwordStrength === 3 && "Good"}
                  {passwordStrength === 4 && "Strong"}
                </span>
              </div>
            )}

            {/* Confirm Password Input (Signup only) */}
            {!isLogin && (
              <div className="form-group">
                <label htmlFor="confirmPassword" className="form-label">
                  Confirm Password
                </label>
                <div className="input-wrapper">
                  <svg
                    className="input-icon"
                    xmlns="http://www.w3.org/2000/svg"
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <rect
                      x="3"
                      y="11"
                      width="18"
                      height="11"
                      rx="2"
                      ry="2"
                    ></rect>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                  </svg>
                  <input
                    id="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="Confirm your password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="form-input password-input"
                    required
                    aria-label="Confirm Password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="password-toggle"
                    aria-label={
                      showConfirmPassword
                        ? "Hide confirm password"
                        : "Show confirm password"
                    }
                  >
                    {showConfirmPassword ? (
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="18"
                        height="18"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-4-11-4s1.6-3.6 4.6-6M9.9 4.24A9.98 9.98 0 0 1 12 4c7 0 11 4 11 4s-1.6 3.6-4.6 6m2.5 5.5m5 5L2 2"></path>
                      </svg>
                    ) : (
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="18"
                        height="18"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                      >
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                      </svg>
                    )}
                  </button>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="submit-button"
              aria-busy={loading}
            >
              {loading ? (
                <span className="loading-content">
                  <svg
                    className="spinner"
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
                  <span>
                    {isLogin ? "Signing In..." : "Creating Account..."}
                  </span>
                </span>
              ) : (
                <span>{isLogin ? "Sign In" : "Create Account"}</span>
              )}
            </button>

            {/* Divider */}
            <div className="divider">
              <span className="divider-text">or</span>
            </div>

            {/* Toggle Mode Link */}
            <button type="button" onClick={toggleMode} className="toggle-link">
              {isLogin
                ? "Don't have an account? Sign up"
                : "Already have an account? Sign in"}
            </button>
          </form>

          {/* Footer Text */}
          <p className="footer-text">
            Trusted by teams worldwide for intelligent meeting analysis
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
