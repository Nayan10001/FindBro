import './SearchInput.css';

function SearchInput({ value, onChange, onKeyPress, isSearching, onSearch }) {
  return (
    <div className="search-input-wrapper">
      <div className="search-input-container">
        <textarea
          id="search-input"
          className="search-input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyPress={onKeyPress}
          placeholder="People working on biotech in the Bay Area"
          rows={1}
        />
        <button 
          className="search-button" 
          onClick={onSearch}
          disabled={isSearching}
          title="Search developers"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M5 12h14M12 5l7 7-7 7"/>
          </svg>
        </button>
      </div>
      {isSearching && (
        <div className="typing-indicator">
          <span>Searching</span>
          <div className="typing-dots">
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
            <div className="typing-dot"></div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SearchInput;