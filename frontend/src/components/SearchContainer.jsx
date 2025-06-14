import { useState } from 'react';
import SearchInput from './SearchInput';
import SuggestionChips from './SuggestionChips';
import './SearchContainer.css';

function SearchContainer({ onSearch }) {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) {
      // Add shake animation for empty search
      const input = document.getElementById('search-input');
      input.classList.add('input-error-shake');
      setTimeout(() => {
        input.classList.remove('input-error-shake');
      }, 500);
      return;
    }

    setIsSearching(true);
    await onSearch(query);
    setIsSearching(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  const fillSearchInput = (text) => {
    setQuery(text);
  };

  return (
    <div className="search-container">
      <div className="search-prompt">
        <h2>Who can I help you find?</h2>
      </div>
      
      <div className="search-wrapper">
        <SearchInput
          value={query}
          onChange={setQuery}
          onKeyPress={handleKeyPress}
          isSearching={isSearching}
          onSearch={handleSearch}
        />
        
        <SuggestionChips onChipClick={fillSearchInput} />
      </div>
    </div>
  );
}

export default SearchContainer;