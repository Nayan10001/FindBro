import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import BackgroundAnimation from '../components/BackgroundAnimation';
import SearchContainer from '../components/SearchContainer';
import StartupCard from '../components/StartupCard';
import './StartupsPage.css';

function StartupsPage() {
  const [startups, setStartups] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showNoResults, setShowNoResults] = useState(false);
  const location = useLocation();

  // Check if we came from a search query
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const query = searchParams.get('q');
    
    if (query) {
      handleSearch(query);
    }
  }, [location]);

  const handleSearch = async (query) => {
    if (!query.trim()) return;

    setIsLoading(true);
    setStartups([]);
    setShowNoResults(false);

    try {
      const response = await fetch(`http://localhost:8000/api/search/startups?query=${encodeURIComponent(query)}&limit=12`);
      
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
        setStartups(data.results);
      }
      
    } catch (error) {
      console.error('Error fetching startup search results:', error);
      setShowNoResults(true);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="startups-page">
      <BackgroundAnimation />
      
      <a href="/" className="back-to-home">
        <span>←</span>
        Back to Home
      </a>
      
      <div className="startups-container">
        <div className="startups-header">
          <h1 className="startups-title">Discover Startups</h1>
          <p className="startups-subtitle">
            Find innovative startups and entrepreneurial opportunities
          </p>
        </div>
        
        <div className="startups-search-section">
          <SearchContainer onSearch={handleSearch} />
        </div>
        
        {isLoading && (
          <div className="startups-loading">
            <div className="startups-loading-spinner"></div>
            <span>Discovering innovative startups...</span>
          </div>
        )}
        
        {startups.length > 0 && (
          <div className="startups-results">
            <div className="startups-results-header">
              <h2>Startup Matches</h2>
              <div className="startups-results-meta">
                Found {startups.length} startup{startups.length !== 1 ? 's' : ''} matching your search
              </div>
            </div>
            
            <div className="startups-grid">
              {startups.map((startup, index) => (
                <StartupCard 
                  key={startup.id || index} 
                  startup={startup} 
                  animationDelay={`${index * 0.1}s`}
                />
              ))}
            </div>
          </div>
        )}
        
        {showNoResults && !isLoading && (
          <div className="startups-no-results">
            No startups found matching your criteria. Try different keywords or explore various industries and technologies.
          </div>
        )}
      </div>
    </div>
  );
}

export default StartupsPage;