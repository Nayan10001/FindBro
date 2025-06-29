import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import BackgroundAnimation from '../components/BackgroundAnimation';
import './ConnectionHomePage.css';

function ConnectionHomePage() {
  const [selectedCategory, setSelectedCategory] = useState(null);
  const navigate = useNavigate();

  const categories = [
    {
      id: 'cofounders',
      title: '👥 Find Your Next Co-Founder',
      description: 'Connect with potential co-founders who share your vision and complement your skills',
      searchQuery: 'co-founder material with startup experience and shared vision'
    },
    {
      id: 'alumni',
      title: '🎓 Find Alumni from Your College',
      description: 'Reconnect with fellow alumni who are building amazing things',
      searchQuery: 'alumni from my college working on innovative projects'
    },
    {
      id: 'collaborators',
      title: '🧠 Find Collaborators, Not Followers',
      description: 'Find people who challenge your ideas and push you to grow',
      searchQuery: 'experienced developers who love to collaborate and innovate'
    },
    {
      id: 'idea-buddy',
      title: '💡 Find Your Next Big Idea Buddy',
      description: 'Connect with creative minds who love brainstorming and turning ideas into reality',
      searchQuery: 'creative developers interested in brainstorming and building new ideas'
    },
    {
      id: 'mentor',
      title: '🧑‍🏫 Find a Mentor Who Actually Cares',
      description: 'Find experienced professionals willing to guide your journey',
      searchQuery: 'senior developers interested in mentoring and knowledge sharing'
    },
    {
      id: 'local-builders',
      title: '👨‍💻 Find Builders from Your City',
      description: 'Connect with local developers and entrepreneurs in your area',
      searchQuery: 'developers and builders in my city for local collaboration'
    },
    {
      id: 'like-minded',
      title: '💬 Find People Who Think and Code Like You',
      description: 'Discover developers with similar coding philosophies and approaches',
      searchQuery: 'developers with similar coding style and technical philosophy'
    },
    {
      id: 'dream-team',
      title: '🧩 Find Your Dream Dev Team',
      description: 'Assemble a team of skilled developers for your next big project',
      searchQuery: 'skilled developers looking to join exciting team projects'
    },
    {
      id: 'product-geeks',
      title: '💼 Find Product Geeks for Your Vision',
      description: 'Connect with product-minded people who understand user experience',
      searchQuery: 'product-minded developers with UX and user-focused experience'
    },
    {
      id: 'hackathon-team',
      title: '⚡ Find Teammates for Hackathons or Side Projects',
      description: 'Find energetic developers ready for hackathons and weekend projects',
      searchQuery: 'developers interested in hackathons and side projects'
    },
    {
      id: 'problem-solvers',
      title: '🛠 Find Problem Solvers, Not Just Coders',
      description: 'Connect with developers who think beyond code and solve real problems',
      searchQuery: 'problem-solving developers who think beyond just coding'
    },
    {
      id: 'open-source',
      title: '🌍 Find Open Source Contributors Who Align With You',
      description: 'Discover contributors who share your open source values and interests',
      searchQuery: 'open source contributors with shared values and interests'
    }
  ];

  const handleCategoryClick = (category) => {
    setSelectedCategory(category.id);
    // Navigate to search page with the category's search query
    navigate(`/?q=${encodeURIComponent(category.searchQuery)}`);
  };

  const handleGetStarted = () => {
    navigate('/');
  };

  return (
    <div className="connection-homepage">
      <BackgroundAnimation />
      
      <div className="connection-container">
        {/* Hero Section */}
        <section className="hero-section">
          <div className="hero-content">
            <h1 className="hero-title">
              Connect with People Who <span className="highlight">Matter</span>
            </h1>
            <p className="hero-subtitle">
              FindBro helps you connect with people who matter—whether you're building a startup, 
              joining a hackathon, looking for a mentor, or searching for someone who truly shares your vision.
            </p>
            <p className="hero-philosophy">
              We believe in connecting <strong>humans, not just profiles</strong>—based on shared intent, 
              values, experience, and the will to build something meaningful.
            </p>
            <button className="cta-button" onClick={handleGetStarted}>
              Start Connecting
            </button>
          </div>
        </section>

        {/* Categories Section */}
        <section className="categories-section">
          <div className="section-header">
            <h2 className="section-title">💬 What You Can Do on FindBro</h2>
            <p className="section-subtitle">Choose your journey and find the right people for it</p>
          </div>

          <div className="categories-grid">
            {categories.map((category) => (
              <div
                key={category.id}
                className={`category-card ${selectedCategory === category.id ? 'selected' : ''}`}
                onClick={() => handleCategoryClick(category)}
              >
                <h3 className="category-title">{category.title}</h3>
                <p className="category-description">{category.description}</p>
                <div className="category-arrow">→</div>
              </div>
            ))}
          </div>
        </section>

        {/* How It Works Section */}
        <section className="how-it-works-section">
          <div className="section-header">
            <h2 className="section-title">⚙ How It Works</h2>
          </div>

          <div className="steps-grid">
            <div className="step-card">
              <div className="step-icon">🎯</div>
              <h3 className="step-title">Intent-Aware Profiles</h3>
              <p className="step-description">
                Users express their goals, skills, institutions, values, and collaboration styles—not just resume data.
              </p>
            </div>

            <div className="step-card">
              <div className="step-icon">🧠</div>
              <h3 className="step-title">Smart Matching Engine</h3>
              <p className="step-description">
                Our hybrid search system uses AI to understand not just what you're looking for, but who you're aligned with.
              </p>
            </div>

            <div className="step-card">
              <div className="step-icon">🔍</div>
              <h3 className="step-title">Search by What Matters</h3>
              <p className="step-description">
                From "co-founder material" to "mentorship style", you get results based on purpose and compatibility.
              </p>
            </div>

            <div className="step-card">
              <div className="step-icon">🤖</div>
              <h3 className="step-title">AgentBro (Coming Soon)</h3>
              <p className="step-description">
                A personalized AI agent that finds matches, filters noise, and reaches out for you—like having your own talent scout.
              </p>
            </div>
          </div>
        </section>

        {/* Why Different Section */}
        <section className="why-different-section">
          <div className="section-header">
            <h2 className="section-title">✅ Why FindBro is Different</h2>
          </div>

          <div className="differences-grid">
            <div className="difference-item">
              <div className="difference-icon">🎯</div>
              <span>Built for real collaboration, not just networking</span>
            </div>
            <div className="difference-item">
              <div className="difference-icon">🧑‍🤝‍🧑</div>
              <span>Focused on intent, alignment, and shared vision</span>
            </div>
            <div className="difference-item">
              <div className="difference-icon">🔍</div>
              <span>Intelligent discovery based on skills, values, goals, and availability</span>
            </div>
            <div className="difference-item">
              <div className="difference-icon">💬</div>
              <span>Meaningful conversations, not cold outreach</span>
            </div>
          </div>
        </section>

        {/* Designed For Section */}
        <section className="designed-for-section">
          <div className="section-header">
            <h2 className="section-title">✨ Designed For</h2>
          </div>

          <div className="audience-grid">
            <div className="audience-item">🌱 Aspiring founders</div>
            <div className="audience-item">🎓 Students, alumni, and college builders</div>
            <div className="audience-item">🤝 Mentors & community contributors</div>
            <div className="audience-item">💻 Side project explorers</div>
            <div className="audience-item">🔍 People who just want to find their tribe</div>
          </div>
        </section>

        {/* Get Started Section */}
        <section className="get-started-section">
          <div className="section-header">
            <h2 className="section-title">👣 Get Started</h2>
          </div>

          <div className="get-started-steps">
            <div className="get-started-step">
              <div className="step-number">1</div>
              <span>✅ Sign up and create your profile</span>
            </div>
            <div className="get-started-step">
              <div className="step-number">2</div>
              <span>🔎 Browse intent-based categories</span>
            </div>
            <div className="get-started-step">
              <div className="step-number">3</div>
              <span>💬 Reach out, team up, and build together</span>
            </div>
          </div>

          <button className="cta-button secondary" onClick={handleGetStarted}>
            Start Your Journey
          </button>
        </section>
      </div>
    </div>
  );
}

export default ConnectionHomePage;