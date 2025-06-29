import './SearchTypeIndicator.css';

function SearchTypeIndicator({ detectedType, onTypeChange, isVisible }) {
  if (!isVisible) return null;

  const getTypeInfo = (type) => {
    switch (type) {
      case 'developers':
        return { icon: <i className="fas fa-code"></i>, label: 'Searching for Developers' };
      case 'projects':
        return { icon: <i className="fas fa-rocket"></i>, label: 'Searching for Projects' };
      case 'startups':
        return { icon: <i className="fas fa-building"></i>, label: 'Searching for Startups' };
      default:
        return { icon: <i className="fas fa-search"></i>, label: 'Searching' };
    }
  };

  const typeInfo = getTypeInfo(detectedType);

  return (
    <div className={`search-type-indicator ${detectedType}`}>
      <span className="search-type-icon">{typeInfo.icon}</span>
      <span className="search-type-text">{typeInfo.label}</span>
      <span className="search-type-change">Not what you're looking for?</span>
      
      <div className="search-type-buttons">
        <button 
          className={`search-type-button ${detectedType === 'developers' ? 'active' : ''}`}
          onClick={() => onTypeChange('developers')}
        >
          <i className="fas fa-code"></i> Developers
        </button>
        <button 
          className={`search-type-button ${detectedType === 'projects' ? 'active' : ''}`}
          onClick={() => onTypeChange('projects')}
        >
          <i className="fas fa-rocket"></i> Projects
        </button>
        <button 
          className={`search-type-button ${detectedType === 'startups' ? 'active' : ''}`}
          onClick={() => onTypeChange('startups')}
        >
          <i className="fas fa-building"></i> Startups
        </button>
      </div>
    </div>
  );
}

export default SearchTypeIndicator;