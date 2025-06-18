import TagList from './TagList';
import './ProfileCard.css';

function ProfileCard({ profile, animationDelay }) {
  // Calculate criteria matches based on profile data
  const calculateCriteriaMatches = (profile) => {
    const criteria = [];
    let totalScore = 0;
    let maxScore = 0;

    // Check for AI/ML skills
    const aiSkills = ['machine learning', 'ai', 'artificial intelligence', 'tensorflow', 'pytorch', 'scikit-learn', 'deep learning', 'neural networks'];
    const hasAISkills = profile.skills?.some(skill => 
      aiSkills.some(aiSkill => skill.toLowerCase().includes(aiSkill.toLowerCase()))
    );
    
    if (hasAISkills) {
      criteria.push({
        text: 'Works in AI',
        status: 'yes',
        icon: 'match'
      });
      totalScore += 2;
    } else {
      criteria.push({
        text: 'Works in AI',
        status: 'no',
        icon: 'no-match'
      });
    }
    maxScore += 2;

    // Check for company experience (FANG-like companies)
    const topCompanies = ['google', 'facebook', 'amazon', 'netflix', 'apple', 'microsoft', 'meta', 'tesla', 'uber', 'airbnb'];
    const hasTopCompanyExp = profile.interests?.some(interest => 
      topCompanies.some(company => interest.toLowerCase().includes(company.toLowerCase()))
    ) || profile.roles?.some(role => 
      topCompanies.some(company => role.toLowerCase().includes(company.toLowerCase()))
    );

    if (hasTopCompanyExp) {
      criteria.push({
        text: 'Works at top companies',
        status: 'yes',
        icon: 'match'
      });
      totalScore += 2;
    } else if (profile.experience >= 3) {
      criteria.push({
        text: 'Works at top companies',
        status: 'partial',
        icon: 'partial'
      });
      totalScore += 1;
    } else {
      criteria.push({
        text: 'Works at top companies',
        status: 'no',
        icon: 'no-match'
      });
    }
    maxScore += 2;

    // Check for senior experience
    const isSenior = profile.experience >= 5;
    if (isSenior) {
      criteria.push({
        text: 'Senior level experience',
        status: 'yes',
        icon: 'match'
      });
      totalScore += 1;
    } else if (profile.experience >= 2) {
      criteria.push({
        text: 'Senior level experience',
        status: 'partial',
        icon: 'partial'
      });
      totalScore += 0.5;
    } else {
      criteria.push({
        text: 'Senior level experience',
        status: 'no',
        icon: 'no-match'
      });
    }
    maxScore += 1;

    // Check for full-stack capabilities
    const frontendSkills = ['react', 'vue', 'angular', 'javascript', 'typescript', 'html', 'css'];
    const backendSkills = ['node', 'python', 'java', 'go', 'rust', 'php', 'ruby', 'c#'];
    
    const hasFrontend = profile.skills?.some(skill => 
      frontendSkills.some(fe => skill.toLowerCase().includes(fe.toLowerCase()))
    );
    const hasBackend = profile.skills?.some(skill => 
      backendSkills.some(be => skill.toLowerCase().includes(be.toLowerCase()))
    );

    if (hasFrontend && hasBackend) {
      criteria.push({
        text: 'Full-stack capabilities',
        status: 'yes',
        icon: 'match'
      });
      totalScore += 1;
    } else if (hasFrontend || hasBackend) {
      criteria.push({
        text: 'Full-stack capabilities',
        status: 'partial',
        icon: 'partial'
      });
      totalScore += 0.5;
    } else {
      criteria.push({
        text: 'Full-stack capabilities',
        status: 'no',
        icon: 'no-match'
      });
    }
    maxScore += 1;

    const score = Math.round((totalScore / maxScore) * 10);
    return { criteria, score };
  };

  const { criteria, score } = calculateCriteriaMatches(profile);
  const experienceText = profile.experience === undefined 
    ? 'N/A' 
    : `${profile.experience} ${profile.experience === 1 ? 'year' : 'years'}`;

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
          {profile.name ? profile.name.charAt(0).toUpperCase() : 'N'}
        </div>
        <div className="profile-info">
          <h3 className="profile-name">{profile.name || 'N/A'}</h3>
          <span className="profile-handle">
            {profile.handle ? `@${profile.handle}` : '@ N/A'}
          </span>
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
            🌍 <span>{profile.timezone || 'N/A'}</span>
          </div>
        </div>
        
        <div>
          <div className="profile-section-title">Skills</div>
          <TagList 
            items={profile.skills} 
            tagClass="skill" 
            emptyText="No skills listed" 
          />
        </div>
        
        <div>
          <div className="profile-section-title">Preferred Roles</div>
          <TagList 
            items={profile.roles} 
            tagClass="role" 
            emptyText="No preferred roles listed" 
          />
        </div>
        
        <div>
          <div className="profile-section-title">Project Interests</div>
          <TagList 
            items={profile.interests} 
            tagClass="interest" 
            emptyText="No project interests listed" 
          />
        </div>
      </div>
    </div>
  );
}

export default ProfileCard;