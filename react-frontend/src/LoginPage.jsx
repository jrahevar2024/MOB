import { useState } from 'react';
import { Lock, User, Eye, EyeOff, Bot } from 'lucide-react';
import './LoginPage.css';

function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSignUp, setIsSignUp] = useState(false);
  const [userRole, setUserRole] = useState('user'); // 'user' or 'admin'

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    // Simple validation
    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password');
      setIsLoading(false);
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      setIsLoading(false);
      return;
    }

    // Simulate API call
    setTimeout(() => {
      // For demo purposes, accept any username/password
      // In production, you'd validate against your backend
      const user = {
        username: username,
        email: `${username}@example.com`,
        role: userRole, // 'user' or 'admin'
        loginTime: new Date().toISOString()
      };
      
      // Store user in localStorage
      localStorage.setItem('user', JSON.stringify(user));
      localStorage.setItem('authToken', 'demo-token-' + Date.now());
      
      setIsLoading(false);
      onLogin(user);
    }, 1000);
  };

  const handleDemoLogin = (role = 'admin') => {
    const demoUser = role === 'admin' ? 'admin' : 'demo';
    setUsername(demoUser);
    setPassword('demo123');
    setTimeout(() => {
      const user = {
        username: demoUser,
        email: `${demoUser}@motherofbots.com`,
        role: role,
        loginTime: new Date().toISOString()
      };
      localStorage.setItem('user', JSON.stringify(user));
      localStorage.setItem('authToken', 'demo-token-' + Date.now());
      onLogin(user);
    }, 500);
  };

  return (
    <div className="login-container">
      <div className="login-background">
        <div className="gradient-orb orb-1"></div>
        <div className="gradient-orb orb-2"></div>
        <div className="gradient-orb orb-3"></div>
      </div>

      <div className="login-card">
        <div className="login-header">
          <div className="logo-container">
            <Bot size={48} className="logo-icon" />
          </div>
          <h1 className="login-title">Mother of Bots</h1>
          <p className="login-subtitle">
            {isSignUp ? 'Create your account' : 'Welcome back! Please login to continue'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="username" className="form-label">
              <User size={18} />
              Username
            </label>
            <input
              id="username"
              type="text"
              className="form-input"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={isLoading}
              autoComplete="username"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password" className="form-label">
              <Lock size={18} />
              Password
            </label>
            <div className="password-input-wrapper">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                className="form-input"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
                autoComplete="current-password"
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="role" className="form-label">
              <User size={18} />
              User Role
            </label>
            <select
              id="role"
              className="form-input role-select"
              value={userRole}
              onChange={(e) => setUserRole(e.target.value)}
              disabled={isLoading}
            >
              <option value="user">Normal User</option>
              <option value="admin">Administrator</option>
            </select>
          </div>

          {!isSignUp && (
            <div className="form-footer">
              <label className="remember-me">
                <input type="checkbox" />
                <span>Remember me</span>
              </label>
              <a href="#" className="forgot-password">
                Forgot password?
              </a>
            </div>
          )}

          <button
            type="submit"
            className="login-button"
            disabled={isLoading}
          >
            {isLoading ? (
              <span className="loading-spinner">
                <div className="spinner"></div>
                {isSignUp ? 'Creating account...' : 'Logging in...'}
              </span>
            ) : (
              isSignUp ? 'Sign Up' : 'Login'
            )}
          </button>

          <div className="demo-buttons-group">
            <button
              type="button"
              className="demo-button"
              onClick={() => handleDemoLogin('user')}
              disabled={isLoading}
            >
              <User size={18} />
              Demo User
            </button>
            <button
              type="button"
              className="demo-button admin"
              onClick={() => handleDemoLogin('admin')}
              disabled={isLoading}
            >
              <Bot size={18} />
              Demo Admin
            </button>
          </div>
        </form>

        <div className="login-divider">
          <span>or</span>
        </div>

        <div className="signup-prompt">
          {isSignUp ? (
            <>
              Already have an account?{' '}
              <button
                className="toggle-mode-btn"
                onClick={() => {
                  setIsSignUp(false);
                  setError('');
                }}
              >
                Login here
              </button>
            </>
          ) : (
            <>
              Don't have an account?{' '}
              <button
                className="toggle-mode-btn"
                onClick={() => {
                  setIsSignUp(true);
                  setError('');
                }}
              >
                Sign up here
              </button>
            </>
          )}
        </div>

        <div className="login-footer">
          <p>Powered by Google Vertex AI & Gemini 🦜️</p>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;

