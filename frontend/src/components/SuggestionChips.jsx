import './SuggestionChips.css';

function SuggestionChips({ onChipClick }) {
  const suggestions = [
    { label: 'Full-Stack Engineers', query: 'Full-stack developers with React and Node.js experience' },
    { label: 'AI/ML Projects', query: 'Machine learning projects looking for contributors' },
    { label: 'Fintech Startups', query: 'Fintech startups in seed stage' }
  ];

  return (
    <div className="suggestion-chips">
      {suggestions.map((suggestion, index) => (
        <button
          key={index}
          className="suggestion-chip"
          onClick={() => onChipClick(suggestion.query)}
        >
          {suggestion.label}
        </button>
      ))}
    </div>
  );
}

export default SuggestionChips;