import TagList from './TagList';
import './ProjectCard.css';

function ProjectCard({ project, animationDelay }) {
  const scorePercent = Math.round((project.score || 0) * 100);
  
  const formatStatus = (status) => {
    return status.replace(/_/g, ' ');
  };

  const getStatusIcon = (status) => {
    const icons = {
      'seeking_contributors': '👥',
      'active_development': '🚀',
      'mvp_complete': '✅',
      'beta_testing': '🧪',
      'prototype': '🔬',
      'seeking_funding': '💰'
    };
    return icons[status] || '📋';
  };

  return (
    <div 
      className="project-card fade-in" 
      style={{ animationDelay }}
    >
      <div className="project-header">
        <div className="project-title-section">
          <h3 className="project-title">{project.title || 'Untitled Project'}</h3>
          <div className="project-owner">
            <div className="project-owner-avatar">
              {project.owner?.avatar || project.owner?.name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <span>by {project.owner?.name || 'Unknown'}</span>
            {project.owner?.handle && (
              <span className="project-owner-handle">@{project.owner.handle}</span>
            )}
          </div>
        </div>
        <div className="project-score">{scorePercent}% Match</div>
      </div>
      
      <div className="project-description">
        {project.description || 'No description available.'}
      </div>

      <div className="project-meta">
        <div className="project-meta-item">
          <span className="project-meta-icon">📊</span>
          <div className={`project-status ${project.status}`}>
            {getStatusIcon(project.status)}
            {formatStatus(project.status || 'unknown')}
          </div>
        </div>
        
        <div className="project-meta-item">
          <span className="project-meta-icon">📁</span>
          <span>{project.project_type || 'N/A'}</span>
        </div>
        
        <div className="project-meta-item">
          <span className="project-meta-icon">🏷️</span>
          <span>{project.category || 'Other'}</span>
        </div>
        
        <div className="project-meta-item">
          <span className="project-meta-icon">⏰</span>
          <span>{project.timeline || 'N/A'}</span>
        </div>
        
        <div className="project-meta-item">
          <span className="project-meta-icon">💼</span>
          <span>{project.commitment || 'N/A'}</span>
        </div>
        
        <div className="project-meta-item">
          <span className="project-meta-icon">📈</span>
          <span>{project.experience_level || 'Any'} Level</span>
        </div>
      </div>
      
      <div className="project-body">
        <div>
          <div className="project-section-title">Tech Stack</div>
          <TagList 
            items={project.tech_stack} 
            tagClass="tech" 
            emptyText="No tech stack specified" 
          />
        </div>
        
        <div>
          <div className="project-section-title">Looking For</div>
          <TagList 
            items={project.looking_for} 
            tagClass="role" 
            emptyText="No specific roles mentioned" 
          />
        </div>
        
        <div>
          <div className="project-section-title">Tags</div>
          <TagList 
            items={project.tags} 
            tagClass="interest" 
            emptyText="No tags specified" 
          />
        </div>
      </div>

      {(project.github_url || project.demo_url) && (
        <div className="project-links">
          {project.github_url && (
            <a 
              href={project.github_url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="project-link"
            >
              <span>📂</span>
              GitHub
            </a>
          )}
          {project.demo_url && (
            <a 
              href={project.demo_url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="project-link"
            >
              <span>🌐</span>
              Live Demo
            </a>
          )}
        </div>
      )}

      <div className="project-team-info">
        <div className="project-team-stat">
          <span>👥</span>
          <span>{project.current_contributors || 0}/{project.team_size || 0} Contributors</span>
        </div>
        {project.created_at && (
          <div className="project-team-stat">
            <span>📅</span>
            <span>Created {new Date(project.created_at).toLocaleDateString()}</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default ProjectCard;