import './SuggestionChips.css';

function SuggestionChips({ onChipClick }) {
  const suggestions = [
    { 
      label: 'Full-Stack Engineers', 
      query: 'Full-stack developers with React and Node.js experience',
      icon: <i className="fas fa-layer-group"></i>
    },
    { 
      label: 'AI/ML Projects', 
      query: 'Machine learning projects looking for contributors',
      icon: <i className="fas fa-robot"></i>
    },
    { 
      label: 'Fintech Startups', 
      query: 'Fintech startups in seed stage',
      icon: <i className="fas fa-chart-line"></i>
    }
  ];

  return (
    <div className="suggestion-chips">
      {suggestions.map((suggestion, index) => (
        <button
          key={index}
          className="suggestion-chip"
          onClick={() => onChipClick(suggestion.query)}
        >
          <span className="chip-icon">{suggestion.icon}</span>
          {suggestion.label}
        </button>
      ))}
    </div>
  );
}

export default SuggestionChips;