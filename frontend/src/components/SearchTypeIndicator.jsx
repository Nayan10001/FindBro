import './SearchTypeIndicator.css';

function SearchTypeIndicator({ detectedType, onTypeChange, isVisible }) {
  if (!isVisible) return null;

  const getTypeInfo = (type) => {
    switch (type) {
      case 'developers':
        return { icon: '👨‍💻', label: 'Searching for Developers' };
      case 'projects':
        return { icon: '🚀', label: 'Searching for Projects' };
      case 'startups':
        return { icon: '🏢', label: 'Searching for Startups' };
      default:
        return { icon: '🔍', label: 'Searching' };
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
          👨‍💻 Developers
        </button>
        <button 
          className={`search-type-button ${detectedType === 'projects' ? 'active' : ''}`}
          onClick={() => onTypeChange('projects')}
        >
          🚀 Projects
        </button>
        <button 
          className={`search-type-button ${detectedType === 'startups' ? 'active' : ''}`}
          onClick={() => onTypeChange('startups')}
        >
          🏢 Startups
        </button>
      </div>
    </div>
  );
}

export default SearchTypeIndicator;