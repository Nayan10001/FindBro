import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import SearchContainer from '../components/SearchContainer';
import ResultsContainer from '../components/ResultsContainer';
import BackgroundAnimation from '../components/BackgroundAnimation';
import SearchTypeIndicator from '../components/SearchTypeIndicator';
import { detectSearchType } from '../utils/searchDetection';

function HomePage() {
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showNoResults, setShowNoResults] = useState(false);
  const [detectedSearchType, setDetectedSearchType] = useState('developers');
  const [showTypeIndicator, setShowTypeIndicator] = useState(false);
  const [currentQuery, setCurrentQuery] = useState('');
  const navigate = useNavigate();

  const handleSearch = async (query, forceType = null) => {
    if (!query.trim()) return;

    // Detect search type or use forced type
    const searchType = forceType || detectSearchType(query);
    setDetectedSearchType(searchType);
    setCurrentQuery(query);
    setShowTypeIndicator(true);

    // Auto-redirect to appropriate page based on search type
    if (searchType === 'projects') {
      navigate(`/projects?q=${encodeURIComponent(query)}`);
      return;
    } else if (searchType === 'startups') {
      navigate(`/startups?q=${encodeURIComponent(query)}`);
      return;
    }

    // Search for developer profiles (default or explicit)
    setIsLoading(true);
    setSearchResults([]);
    setShowNoResults(false);

    try {
      const response = await fetch(`http://localhost:8000/api/search?query=${encodeURIComponent(query)}`);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Unknown server error' }));
        throw new Error(`Server error: ${response.status} ${errorData.message || response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.status === 'error') {
        throw new Error(data.message);
      }
      
      if (data.results.length === 0) {
        setShowNoResults(true);
      } else {
        setSearchResults(data.results);
      }
      
    } catch (error) {
      console.error('Error fetching search results:', error);
      setShowNoResults(true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTypeChange = (newType) => {
    setDetectedSearchType(newType);
    
    if (currentQuery) {
      if (newType === 'projects') {
        navigate(`/projects?q=${encodeURIComponent(currentQuery)}`);
      } else if (newType === 'startups') {
        navigate(`/startups?q=${encodeURIComponent(currentQuery)}`);
      } else {
        // Re-search for developers
        handleSearch(currentQuery, 'developers');
      }
    }
  };

  return (
    <div className="app">
      <BackgroundAnimation />
      <div className="container">
        <Header />
        <SearchContainer onSearch={handleSearch} />
        <SearchTypeIndicator 
          detectedType={detectedSearchType}
          onTypeChange={handleTypeChange}
          isVisible={showTypeIndicator}
        />
        <ResultsContainer 
          results={searchResults}
          isLoading={isLoading}
          showNoResults={showNoResults}
        />
      </div>
    </div>
  );
}

export default HomePage;