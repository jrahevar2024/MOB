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

    // Static credentials validation
    const validCredentials = {
      'admin@motherofbots.com': { password: 'admin@123', role: 'admin' },
      'user@motherofbots.com': { password: 'user@123', role: 'user' }
    };

    const credentials = validCredentials[username.trim().toLowerCase()];
    
    if (!credentials || credentials.password !== password) {
      setError('Invalid username or password');
      setIsLoading(false);
      return;
    }

    // Simulate API call
    setTimeout(() => {
      const user = {
        username: username.trim().toLowerCase().split('@')[0],
        email: username.trim().toLowerCase(),
        role: credentials.role,
        loginTime: new Date().toISOString()
      };
      
      // Store user in localStorage
      localStorage.setItem('user', JSON.stringify(user));
      localStorage.setItem('authToken', 'auth-token-' + Date.now());
      
      setIsLoading(false);
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
              Email
            </label>
            <input
              id="username"
              type="email"
              className="form-input"
              placeholder="admin@motherofbots.com or user@motherofbots.com"
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
                Logging in...
              </span>
            ) : (
              'Login'
            )}
          </button>
        </form>

        <div className="login-credentials-info">
          <p><strong>Admin:</strong> admin@motherofbots.com / admin@123</p>
          <p><strong>User:</strong> user@motherofbots.com / user@123</p>
        </div>

        <div className="login-footer">
          <p>Powered by Google Vertex AI & Gemini 🦜️</p>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;

