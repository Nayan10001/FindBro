// src/components/ProfileCard.jsx

import TagList from './TagList';
import './ProfileCard.css';

function ProfileCard({ profile, animationDelay }) {
  // Destructure the new nested objects from the 'profile' prop.
  // Add default empty objects/arrays to prevent errors if a key is missing.
  const {
    basic_info = {},
    skills_and_roles = {},
    interests = {},
    work_history = [],
    education = {},
  } = profile;

  // Now, use these new variables to get the data
  const name = basic_info.name || 'N/A';
  const handle = basic_info.handle ? `@${basic_info.handle}` : 'N/A';
  
  const years_of_experience = skills_and_roles.years_of_experience;
  const skills = skills_and_roles.skill_tags || [];
  const roles = skills_and_roles.preferred_roles || [];
  const timezone = skills_and_roles.availability_timezone || 'N/A';
  
  const project_interests = interests.project_interests || [];

  // This function now uses the corrected variables for your "Criteria Match" logic
  const calculateCriteriaMatches = () => {
    const criteria = [];
    let totalScore = 0;
    let maxScore = 0;

    // Check for AI/ML skills
    const aiSkills = ['machine learning', 'ai', 'artificial intelligence', 'tensorflow', 'pytorch', 'scikit-learn', 'deep learning', 'neural networks'];
    const hasAISkills = skills.some(skill => 
      aiSkills.some(aiSkill => skill.toLowerCase().includes(aiSkill.toLowerCase()))
    );
    
    if (hasAISkills) {
      criteria.push({ text: 'Works in AI', status: 'yes', icon: 'match' });
      totalScore += 2;
    } else {
      criteria.push({ text: 'Works in AI', status: 'no', icon: 'no-match' });
    }
    maxScore += 2;

    // Check for company experience (FANG-like companies)
    const topCompanies = ['google', 'facebook', 'amazon', 'netflix', 'apple', 'microsoft', 'meta', 'tesla', 'uber', 'airbnb'];
    const hasTopCompanyExp = work_history.some(job => 
        topCompanies.some(company => job.company.toLowerCase().includes(company.toLowerCase()))
    ) || project_interests.some(interest => 
      topCompanies.some(company => interest.toLowerCase().includes(company.toLowerCase()))
    ) || roles.some(role => 
      topCompanies.some(company => role.toLowerCase().includes(company.toLowerCase()))
    );

    if (hasTopCompanyExp) {
      criteria.push({ text: 'Works at top companies', status: 'yes', icon: 'match' });
      totalScore += 2;
    } else if (years_of_experience >= 3) {
      criteria.push({ text: 'Works at top companies', status: 'partial', icon: 'partial' });
      totalScore += 1;
    } else {
      criteria.push({ text: 'Works at top companies', status: 'no', icon: 'no-match' });
    }
    maxScore += 2;

    // Check for senior experience
    const isSenior = years_of_experience >= 5;
    if (isSenior) {
      criteria.push({ text: 'Senior level experience', status: 'yes', icon: 'match' });
      totalScore += 1;
    } else if (years_of_experience >= 2) {
      criteria.push({ text: 'Senior level experience', status: 'partial', icon: 'partial' });
      totalScore += 0.5;
    } else {
      criteria.push({ text: 'Senior level experience', status: 'no', icon: 'no-match' });
    }
    maxScore += 1;

    // Check for full-stack capabilities
    const frontendSkills = ['react', 'vue', 'angular', 'javascript', 'typescript', 'html', 'css'];
    const backendSkills = ['node', 'python', 'java', 'go', 'rust', 'php', 'ruby', 'c#'];
    
    const hasFrontend = skills.some(skill => 
      frontendSkills.some(fe => skill.toLowerCase().includes(fe.toLowerCase()))
    );
    const hasBackend = skills.some(skill => 
      backendSkills.some(be => skill.toLowerCase().includes(be.toLowerCase()))
    );

    if (hasFrontend && hasBackend) {
      criteria.push({ text: 'Full-stack capabilities', status: 'yes', icon: 'match' });
      totalScore += 1;
    } else if (hasFrontend || hasBackend) {
      criteria.push({ text: 'Full-stack capabilities', status: 'partial', icon: 'partial' });
      totalScore += 0.5;
    } else {
      criteria.push({ text: 'Full-stack capabilities', status: 'no', icon: 'no-match' });
    }
    maxScore += 1;

    const score = Math.round((totalScore / maxScore) * 10);
    return { criteria, score };
  };

  const { criteria, score } = calculateCriteriaMatches();
  const experienceText = years_of_experience === undefined 
    ? 'N/A' 
    : `${years_of_experience} ${years_of_experience === 1 ? 'year' : 'years'}`;

  const getStatusIcon = (iconType) => {
    switch (iconType) {
      case 'match': return '✓';
      case 'partial': return '~';
      case 'no-match': return '×';
      default: return '•';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'yes': return 'Yes';
      case 'partial': return 'Partial';
      case 'no': return 'No';
      default: return 'Unknown';
    }
  };

  return (
    <div 
      className="profile-card fade-in" 
      style={{ animationDelay }}
    >
      <div className="profile-header">
        <div className="profile-avatar">
          {name ? name.charAt(0).toUpperCase() : 'N'}
        </div>
        <div className="profile-info">
          <h3 className="profile-name">{name}</h3>
          <span className="profile-handle">{handle}</span>
        </div>
        <div className="criteria-match">
          <div className="criteria-header">
            <span className="criteria-title">Criteria Match</span>
            <span className="criteria-score">Score: {score}</span>
          </div>
          <div className="criteria-list">
            {criteria.map((criterion, index) => (
              <div key={index} className="criteria-item">
                <div className={`criteria-icon ${criterion.icon}`}>
                  {getStatusIcon(criterion.icon)}
                </div>
                <span className="criteria-text">{criterion.text}</span>
                <span className={`criteria-status ${criterion.status}`}>
                  {getStatusText(criterion.status)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      <div className="profile-body">
        <div className="profile-meta-row">
          <div className="profile-experience">
            ⏱️ <span>{experienceText}</span>
          </div>
          <div className="profile-timezone">
            🌍 <span>{timezone}</span>
          </div>
        </div>
        
        <div>
          <div className="profile-section-title">Skills</div>
          <TagList 
            items={skills} 
            tagClass="skill" 
            emptyText="No skills listed" 
          />
        </div>
        
        <div>
          <div className="profile-section-title">Preferred Roles</div>
          <TagList 
            items={roles} 
            tagClass="role" 
            emptyText="No preferred roles listed" 
          />
        </div>
        
        <div>
          <div className="profile-section-title">Project Interests</div>
          <TagList 
            items={project_interests} 
            tagClass="interest" 
            emptyText="No project interests listed" 
          />
        </div>

        {/* Enhanced Work History and Education sections using the new CSS classes */}
        <div className="details-grid">
          {work_history.length > 0 && (
            <div className="work-history-section">
              <div className="details-box">
                <div className="details-header">Work History</div>
                <ul className="details-list">
                  {work_history.map((job, index) => (
                    <li key={index} className="details-list-item">
                      <div className="item-main">{job.role || 'N/A'}</div>
                      <div className="item-sub">
                        {job.company || 'N/A'} • {job.duration_years || 'N/A'} years
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {education.institution && (
            <div className="education-section">
              <div className="details-box">
                <div className="details-header">Education</div>
                <div className="details-list">
                  <div className="details-list-item">
                    <div className="item-main">{education.degree || 'Degree not specified'}</div>
                    <div className="item-sub">{education.institution}</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
        
      </div>
    </div>
  );
}

export default ProfileCard;