import TagList from './TagList';
import './ProfileCard.css';

function ProfileCard({ profile, animationDelay }) {
  const scorePercent = Math.round((profile.score || 0) * 100);
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
        <div className="profile-score">{scorePercent}% Match</div>
      </div>
      
      <div className="profile-body">
        <div className="profile-experience">
          ⏱️ <span>Experience: {experienceText}</span>
        </div>
        <div className="profile-timezone">
          🌍 <span>Timezone: {profile.timezone || 'N/A'}</span>
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