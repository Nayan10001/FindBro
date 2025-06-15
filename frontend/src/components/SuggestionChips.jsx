import './SuggestionChips.css';

function SuggestionChips({ onChipClick }) {
  const suggestions = [
    { label: 'Full-Stack Engineer', query: 'Developers with full-stack experience' },
    { label: 'Open Source Projects', query: 'Open source projects looking for contributors' },
    { label: 'AI/ML Projects', query: 'Machine learning and AI projects' }
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