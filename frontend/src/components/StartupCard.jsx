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
      'seed': <i className="fas fa-seedling"></i>,
      'series_a': <i className="fas fa-rocket"></i>,
      'series_b': <i className="fas fa-chart-line"></i>,
      'mvp': <i className="fas fa-wrench"></i>,
      'idea': <i className="far fa-lightbulb"></i>,
      'unknown': <i className="fas fa-question"></i>
    };
    return icons[stage] || <i className="fas fa-building"></i>;
  };

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
              <i className="fas fa-map-marker-alt"></i>
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
          <span className="startup-meta-icon"><i className="fas fa-hammer"></i></span>
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
          <i className="fas fa-external-link-alt"></i>
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