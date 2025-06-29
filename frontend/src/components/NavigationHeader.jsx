import { useNavigate, useLocation } from 'react-router-dom';
import './NavigationHeader.css';

function NavigationHeader() {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Search', icon: '🔍' },
    { path: '/connect', label: 'Connect', icon: '🤝' },
    { path: '/projects', label: 'Projects', icon: '🚀' },
    { path: '/startups', label: 'Startups', icon: '🏢' }
  ];

  return (
    <nav className="navigation-header">
      <div className="nav-container">
        <div className="nav-logo" onClick={() => navigate('/')}>
          <span className="logo-text">FindBro</span>
        </div>
        
        <div className="nav-links">
          {navItems.map((item) => (
            <button
              key={item.path}
              className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
              onClick={() => navigate(item.path)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </button>
          ))}
        </div>
      </div>
    </nav>
  );
}

export default NavigationHeader;