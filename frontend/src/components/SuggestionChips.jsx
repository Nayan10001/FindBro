import './SuggestionChips.css';

function SuggestionChips({ onChipClick }) {
  const suggestions = [
    { label: 'Full-Stack Engineer', query: 'Developers with full-stack experience' },
    { label: 'Alumni Discovery', query: 'Alumni from top tech companies' },
    { label: 'Deep People Research', query: 'Senior developers with AI/ML expertise' }
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