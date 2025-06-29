import { useNavigate, useLocation } from 'react-router-dom';
import './NavigationHeader.css';

function NavigationHeader() {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Search', icon: <i className="fas fa-search"></i> },
    { path: '/connect', label: 'Connect', icon: <i className="fas fa-handshake"></i> },
    { path: '/projects', label: 'Projects', icon: <i className="fas fa-rocket"></i> },
    { path: '/startups', label: 'Startups', icon: <i className="fas fa-building"></i> }
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