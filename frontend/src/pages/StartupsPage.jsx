import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import NavigationHeader from '../components/NavigationHeader';
import BackgroundAnimation from '../components/BackgroundAnimation';
import SearchContainer from '../components/SearchContainer';
import StartupCard from '../components/StartupCard';
import './StartupsPage.css';

function StartupsPage() {
  const [startups, setStartups] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showNoResults, setShowNoResults] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const location = useLocation();

  // Check if we came from a search query
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const query = searchParams.get('q');
    
    if (query) {
      setSearchQuery(query);
      handleSearch(query);
    }
  }, [location]);

  const handleSearch = async (query) => {
    if (!query.trim()) return;

    console.log('Searching for startups with query:', query);
    setIsLoading(true);
    setStartups([]);
    setShowNoResults(false);
    setSearchQuery(query);

    try {
      // Use the correct API endpoint for startup search
      const response = await fetch(`http://localhost:8000/api/search/startups?query=${encodeURIComponent(query)}&limit=12`);
      
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Unknown server error' }));
        console.error('API Error:', errorData);
        throw new Error(`Server error: ${response.status} ${errorData.message || response.statusText}`);
      }
      
      const data = await response.json();
      console.log('API Response:', data);
      
      if (data.status === 'error') {
        console.error('Search Error:', data.message);
        throw new Error(data.message);
      }
      
      if (data.results && data.results.length === 0) {
        console.log('No results found');
        setShowNoResults(true);
      } else if (data.results) {
        console.log(`Found ${data.results.length} startups`);
        setStartups(data.results);
      } else {
        console.error('Unexpected response format:', data);
        setShowNoResults(true);
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
      <NavigationHeader />
      <BackgroundAnimation />
      
      <div className="startups-container" style={{ paddingTop: '80px' }}>
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
                Found {startups.length} startup{startups.length !== 1 ? 's' : ''} matching "{searchQuery}"
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
            {searchQuery ? (
              <>
                No startups found matching "{searchQuery}". 
                <br />
                Try different keywords like "fintech", "AI startups", "seed stage", or specific industries.
              </>
            ) : (
              'No startups found matching your criteria. Try different keywords or explore various industries and technologies.'
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default StartupsPage;