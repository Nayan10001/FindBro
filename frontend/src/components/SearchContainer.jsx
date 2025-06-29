import { useState, useEffect } from 'react';
import SearchInput from './SearchInput';
import SuggestionChips from './SuggestionChips';
import './SearchContainer.css';

function SearchContainer({ onSearch }) {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [currentText, setCurrentText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isTyping, setIsTyping] = useState(true);

  const phrases = [
    'Find Your Next Co-Founder',
    'Find Your Alumni',
    'Find a Mentor Who Cares',
    'Find a Teammate for Your Hackathon',
    'Find Your Perfect Collaborator',
    'Find Passionate Builders',
    'Find Your Dream Dev Team',
    'Find Open Source Contributors',
    'Find People Who Code Like You',
    'Find Designers Who Get You',
    'Find Startups That Need You',
    'Find Engineers with Shared Vision',
    'Find Your Next Technical Co-Lead',
    'Find College Mates Who Build',
    'Find Innovators Across Campuses',
    'Find Problem-Solvers, Not Just Coders',
    'Find Your Weekend Side-Project Team',
    'Find Your Next Big Idea Buddy',
    'Find Builders from Your City',
    'Find Developers from Your College',
    'Find Product Geeks for Your Vision',
    'Find Tech Leaders from Day One',
    'Find Your Tribe in Tech',
    'Find Collaborators, Not Followers'
  ];

  useEffect(() => {
    const currentPhrase = phrases[currentIndex];
    
    if (isTyping) {
      if (currentText.length < currentPhrase.length) {
        const timeout = setTimeout(() => {
          setCurrentText(currentPhrase.slice(0, currentText.length + 1));
        }, 50 + Math.random() * 50); // Variable typing speed for natural feel
        
        return () => clearTimeout(timeout);
      } else {
        // Finished typing, wait before starting to delete
        const timeout = setTimeout(() => {
          setIsTyping(false);
        }, 2000);
        
        return () => clearTimeout(timeout);
      }
    } else {
      if (currentText.length > 0) {
        const timeout = setTimeout(() => {
          setCurrentText(currentText.slice(0, -1));
        }, 30);
        
        return () => clearTimeout(timeout);
      } else {
        // Finished deleting, move to next phrase
        setCurrentIndex((prevIndex) => (prevIndex + 1) % phrases.length);
        setIsTyping(true);
      }
    }
  }, [currentText, currentIndex, isTyping, phrases]);

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
        <h2 className="typewriter-text">
          {currentText}
          <span className={`cursor ${isTyping ? 'typing' : 'waiting'}`}>|</span>
        </h2>
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