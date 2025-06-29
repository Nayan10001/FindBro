import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import BackgroundAnimation from '../components/BackgroundAnimation';
import SearchContainer from '../components/SearchContainer';
import ProjectCard from '../components/ProjectCard';
import './ProjectsPage.css';

function ProjectsPage() {
  const [projects, setProjects] = useState([]);
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
    setProjects([]);
    setShowNoResults(false);

    try {
      const response = await fetch(`http://localhost:8000/api/search/projects?query=${encodeURIComponent(query)}&limit=12`);
      
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
        setProjects(data.results);
      }
      
    } catch (error) {
      console.error('Error fetching project search results:', error);
      setShowNoResults(true);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="projects-page">
      <BackgroundAnimation />
      
      <a href="/" className="back-to-home">
        <span>←</span>
        Back to Home
      </a>
      
      <div className="projects-container">
        <div className="projects-header">
          <h1 className="projects-title">Discover Projects</h1>
          <p className="projects-subtitle">
            Find exciting projects to contribute to and collaborate on
          </p>
        </div>
        
        <div className="projects-search-section">
          <SearchContainer onSearch={handleSearch} />
        </div>
        
        {isLoading && (
          <div className="projects-loading">
            <div className="projects-loading-spinner"></div>
            <span>Discovering amazing projects...</span>
          </div>
        )}
        
        {projects.length > 0 && (
          <div className="projects-results">
            <div className="projects-results-header">
              <h2>Project Matches</h2>
              <div className="projects-results-meta">
                Found {projects.length} project{projects.length !== 1 ? 's' : ''} matching your search
              </div>
            </div>
            
            <div className="projects-grid">
              {projects.map((project, index) => (
                <ProjectCard 
                  key={project.id || index} 
                  project={project} 
                  animationDelay={`${index * 0.1}s`}
                />
              ))}
            </div>
          </div>
        )}
        
        {showNoResults && !isLoading && (
          <div className="projects-no-results">
            No projects found matching your criteria. Try different keywords or explore various technologies and project types.
          </div>
        )}
      </div>
    </div>
  );
}

export default ProjectsPage;