import TagList from './TagList';
import './StartupCard.css';

function StartupCard({ startup, animationDelay }) {
  const scorePercent = Math.round((startup.score || 0) * 100);
  
  const formatStage = (stage) => {
    if (!stage) return 'unknown';
    return stage.replace(/_/g, ' ');
  };

  const getStageIcon = (stage) => {
    const icons = {
      'seed': '🌱',
      'series_a': '🚀',
      'series_b': '📈',
      'mvp': '🔧',
      'idea': '💡',
      'unknown': '❓'
    };
    return icons[stage] || '🏢';
  };

  // Debug log to see what data we're receiving
  console.log('StartupCard received:', startup);

  return (
    <div 
      className="startup-card fade-in" 
      style={{ animationDelay }}
    >
      <div className="startup-header">
        <div className="startup-title-section">
          <h3 className="startup-name">{startup.name || 'Unnamed Startup'}</h3>
          {startup.city && (
            <div className="startup-location">
              <span>📍</span>
              <span>{startup.city}</span>
            </div>
          )}
        </div>
        <div className="startup-score">{scorePercent}% Match</div>
      </div>
      
      <div className="startup-description">
        {startup.description || 'No description available.'}
      </div>

      {startup.alt && (
        <div className="startup-alt-text">
          "{startup.alt}"
        </div>
      )}

      <div className="startup-meta">
        <div className="startup-meta-item">
          <span className="startup-meta-icon">🏗️</span>
          <div className={`startup-stage ${startup.stage || 'unknown'}`}>
            {getStageIcon(startup.stage)}
            {formatStage(startup.stage || 'unknown')}
          </div>
        </div>
      </div>
      
      <div className="startup-body">
        <div>
          <div className="startup-section-title">Industries</div>
          <TagList 
            items={startup.industries || []} 
            tagClass="interest" 
            emptyText="No industries specified" 
          />
        </div>
        
        <div>
          <div className="startup-section-title">Technologies</div>
          <TagList 
            items={startup.technologies || []} 
            tagClass="tech" 
            emptyText="No technologies specified" 
          />
        </div>
      </div>

      {startup.link && (
        <a 
          href={startup.link} 
          target="_blank" 
          rel="noopener noreferrer"
          className="startup-link"
        >
          <span>🌐</span>
          Visit Website
        </a>
      )}

      {startup.images && (
        <div className="startup-images">
          <strong>Images:</strong> {startup.images}
        </div>
      )}
    </div>
  );
}

export default StartupCard;