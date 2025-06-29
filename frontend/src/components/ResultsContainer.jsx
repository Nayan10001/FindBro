import ProfileCard from './ProfileCard';
import LoadingSpinner from './LoadingSpinner';
import './ResultsContainer.css';

function ResultsContainer({ results, isLoading, showNoResults }) {
  // Only show the results container if there's something to display
  const shouldShowContainer = isLoading || results.length > 0 || showNoResults;
  
  if (!shouldShowContainer) {
    return null;
  }

  return (
    <div className="results-container">
      {/* Only show header when there are actual results */}
      {results.length > 0 && (
        <div className="results-header">
          <h2>Developer Matches</h2>
          <div className="results-meta"></div>
        </div>
      )}
      
      {isLoading && <LoadingSpinner />}
      
      {results.length > 0 && (
        <div className="results-list">
          {results.map((profile, index) => (
            <ProfileCard 
              key={index} 
              profile={profile} 
              animationDelay={`${index * 0.1}s`}
            />
          ))}
        </div>
      )}
      
      {showNoResults && !isLoading && (
        <div className="no-results">
          No developers found matching your criteria. Try adjusting your search terms or requirements.
        </div>
      )}
    </div>
  );
}

export default ResultsContainer;