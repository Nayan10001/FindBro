import { useState } from 'react';
import Header from './components/Header';
import SearchContainer from './components/SearchContainer';
import ResultsContainer from './components/ResultsContainer';
import BackgroundAnimation from './components/BackgroundAnimation';
import './App.css';

function App() {
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showNoResults, setShowNoResults] = useState(false);

  const handleSearch = async (query) => {
    if (!query.trim()) return;

    setIsLoading(true);
    setSearchResults([]);
    setShowNoResults(false);

    try {
      // Simulate API call - replace with actual API endpoint
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

  return (
    <div className="app">
      <BackgroundAnimation />
      <div className="container">
        <Header />
        <SearchContainer onSearch={handleSearch} />
        <ResultsContainer 
          results={searchResults}
          isLoading={isLoading}
          showNoResults={showNoResults}
        />
      </div>
    </div>
  );
}

export default App;