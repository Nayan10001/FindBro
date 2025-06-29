import './SearchInput.css';

function SearchInput({ value, onChange, onKeyPress, isSearching, onSearch }) {
  return (
    <div className="search-input-wrapper">
      <div className="deepsearch-tag">
        <i className="fas fa-brain deepsearch-tag-icon"></i>
        DeepSearch (Beta)
      </div>
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
          <i className="fas fa-arrow-right"></i>
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