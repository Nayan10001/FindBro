import TagList from './TagList';
import './ProfileCard.css';

function ProfileCard({ profile, animationDelay }) {
  // Calculate a more meaningful match percentage
  const calculateMatchPercentage = (profile) => {
    let score = 0;
    let maxScore = 0;
    
    // Skills relevance (40% weight)
    const skillsWeight = 0.4;
    if (profile.skills && profile.skills.length > 0) {
      score += Math.min(profile.skills.length / 10, 1) * skillsWeight * 100;
    }
    maxScore += skillsWeight * 100;
    
    // Experience relevance (30% weight)
    const experienceWeight = 0.3;
    if (profile.experience !== undefined) {
      // Normalize experience (0-15 years scale)
      const normalizedExp = Math.min(profile.experience / 15, 1);
      score += normalizedExp * experienceWeight * 100;
    }
    maxScore += experienceWeight * 100;
    
    // Role match (20% weight)
    const roleWeight = 0.2;
    if (profile.roles && profile.roles.length > 0) {
      score += Math.min(profile.roles.length / 5, 1) * roleWeight * 100;
    }
    maxScore += roleWeight * 100;
    
    // Profile completeness (10% weight)
    const completenessWeight = 0.1;
    let completenessScore = 0;
    if (profile.name) completenessScore += 0.2;
    if (profile.handle) completenessScore += 0.2;
    if (profile.skills && profile.skills.length > 0) completenessScore += 0.2;
    if (profile.roles && profile.roles.length > 0) completenessScore += 0.2;
    if (profile.interests && profile.interests.length > 0) completenessScore += 0.2;
    
    score += completenessScore * completenessWeight * 100;
    maxScore += completenessWeight * 100;
    
    // Use original score if available and higher
    const originalScore = (profile.score || 0) * 100;
    const calculatedScore = Math.round((score / maxScore) * 100);
    
    return Math.max(originalScore, calculatedScore, 65); // Minimum 65% for better UX
  };

  const matchPercentage = calculateMatchPercentage(profile);
  const experienceText = profile.experience === undefined 
    ? 'N/A' 
    : `${profile.experience} ${profile.experience === 1 ? 'year' : 'years'}`;

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
        <div className="profile-score">{matchPercentage}% Match</div>
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