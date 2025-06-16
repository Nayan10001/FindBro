/**
 * Intelligent search detection utility
 * Analyzes search queries to determine the most appropriate search type
 */

// Keywords that indicate searching for developers/people
const DEVELOPER_KEYWORDS = [
  // Role-based keywords
  'developer', 'developers', 'engineer', 'engineers', 'programmer', 'programmers',
  'coder', 'coders', 'architect', 'architects', 'designer', 'designers',
  'frontend', 'backend', 'fullstack', 'full-stack', 'devops', 'sre',
  'mobile developer', 'web developer', 'software engineer', 'data scientist',
  'machine learning engineer', 'ai engineer', 'security engineer',
  
  // Experience-based keywords
  'senior', 'junior', 'lead', 'principal', 'staff', 'expert', 'experienced',
  'beginner', 'entry level', 'mid-level', 'intermediate', 'advanced',
  
  // Skill-based keywords
  'react', 'vue', 'angular', 'node', 'python', 'java', 'javascript', 'typescript',
  'golang', 'rust', 'swift', 'kotlin', 'php', 'ruby', 'c++', 'c#',
  'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
  
  // People-related keywords
  'people', 'person', 'team member', 'teammate', 'colleague', 'professional',
  'talent', 'candidate', 'hire', 'hiring', 'recruit', 'recruiting',
  'freelancer', 'contractor', 'consultant', 'mentor', 'mentee',
  
  // Location-based (when looking for people)
  'in san francisco', 'in new york', 'in london', 'in berlin', 'in toronto',
  'remote developer', 'remote engineer', 'remote worker',
  
  // Collaboration keywords
  'looking for', 'need', 'want', 'seeking', 'find me', 'help me find'
];

// Keywords that indicate searching for projects
const PROJECT_KEYWORDS = [
  // Project-specific terms
  'project', 'projects', 'open source', 'opensource', 'github', 'repository',
  'repo', 'codebase', 'application', 'app', 'platform', 'tool', 'library',
  'framework', 'api', 'service', 'website', 'web app', 'mobile app',
  
  // Project actions
  'contribute', 'contributing', 'contribution', 'collaborate', 'collaboration',
  'join project', 'help with', 'work on', 'build', 'building', 'create',
  'develop', 'developing', 'code', 'coding', 'programming',
  
  // Project status
  'mvp', 'prototype', 'beta', 'alpha', 'production', 'live', 'deployed',
  'in development', 'under development', 'seeking contributors',
  'looking for help', 'need help', 'volunteers needed',
  
  // Project types
  'web project', 'mobile project', 'ai project', 'ml project', 'blockchain project',
  'game', 'gaming project', 'saas', 'fintech project', 'healthtech',
  'edtech', 'social impact', 'non-profit project',
  
  // Technology projects
  'react project', 'vue project', 'angular project', 'node project',
  'python project', 'java project', 'javascript project'
];

// Keywords that indicate searching for startups
const STARTUP_KEYWORDS = [
  // Startup-specific terms
  'startup', 'startups', 'company', 'companies', 'business', 'businesses',
  'venture', 'ventures', 'firm', 'organization', 'enterprise',
  
  // Startup stages
  'seed stage', 'series a', 'series b', 'series c', 'pre-seed', 'early stage',
  'growth stage', 'scale-up', 'unicorn', 'decacorn',
  
  // Startup roles
  'founder', 'co-founder', 'ceo', 'cto', 'cfo', 'vp', 'head of',
  'chief', 'director', 'manager', 'lead', 'executive',
  
  // Startup activities
  'funding', 'investment', 'investor', 'vc', 'venture capital',
  'angel investor', 'accelerator', 'incubator', 'pitch', 'demo day',
  
  // Industry terms
  'fintech', 'healthtech', 'edtech', 'proptech', 'insurtech', 'regtech',
  'biotech', 'cleantech', 'agtech', 'foodtech', 'retailtech',
  'saas', 'b2b', 'b2c', 'marketplace', 'platform',
  
  // Startup characteristics
  'innovative', 'disruptive', 'emerging', 'cutting-edge', 'next-gen',
  'stealth mode', 'stealth startup', 'well-funded', 'bootstrapped',
  
  // Location-based startup searches
  'silicon valley startup', 'bay area startup', 'nyc startup', 'london startup',
  'berlin startup', 'tel aviv startup', 'bangalore startup'
];

/**
 * Analyzes a search query and determines the most appropriate search type
 * @param {string} query - The search query to analyze
 * @returns {string} - 'developers', 'projects', 'startups', or 'developers' (default)
 */
export function detectSearchType(query) {
  if (!query || typeof query !== 'string') {
    return 'developers';
  }

  const normalizedQuery = query.toLowerCase().trim();
  
  // Count matches for each category
  const developerMatches = DEVELOPER_KEYWORDS.filter(keyword => 
    normalizedQuery.includes(keyword.toLowerCase())
  ).length;
  
  const projectMatches = PROJECT_KEYWORDS.filter(keyword => 
    normalizedQuery.includes(keyword.toLowerCase())
  ).length;
  
  const startupMatches = STARTUP_KEYWORDS.filter(keyword => 
    normalizedQuery.includes(keyword.toLowerCase())
  ).length;

  // Weight the matches (some keywords are stronger indicators)
  let developerScore = developerMatches;
  let projectScore = projectMatches;
  let startupScore = startupMatches;

  // Boost scores for strong indicators
  if (normalizedQuery.includes('project') || normalizedQuery.includes('contribute')) {
    projectScore += 2;
  }
  
  if (normalizedQuery.includes('startup') || normalizedQuery.includes('company')) {
    startupScore += 2;
  }
  
  if (normalizedQuery.includes('developer') || normalizedQuery.includes('engineer')) {
    developerScore += 2;
  }

  // Special patterns that strongly indicate specific search types
  if (/\b(join|contribute to|help with|work on)\s+(project|repo|repository)\b/i.test(normalizedQuery)) {
    return 'projects';
  }
  
  if (/\b(startup|company)\s+(in|at|from)\b/i.test(normalizedQuery)) {
    return 'startups';
  }
  
  if (/\b(hire|find|looking for|need)\s+(developer|engineer|programmer)\b/i.test(normalizedQuery)) {
    return 'developers';
  }

  // Determine the winner
  const maxScore = Math.max(developerScore, projectScore, startupScore);
  
  if (maxScore === 0) {
    // No clear indicators, default to developers
    return 'developers';
  }
  
  if (startupScore === maxScore && startupScore > 0) {
    return 'startups';
  }
  
  if (projectScore === maxScore && projectScore > 0) {
    return 'projects';
  }
  
  // Default to developers (including ties)
  return 'developers';
}

/**
 * Gets suggestions for improving search queries based on detected type
 * @param {string} query - The original query
 * @param {string} detectedType - The detected search type
 * @returns {string[]} - Array of suggested improvements
 */
export function getSearchSuggestions(query, detectedType) {
  const suggestions = [];
  
  switch (detectedType) {
    case 'developers':
      suggestions.push(
        'Try adding experience level: "senior React developer"',
        'Specify location: "Python developers in San Francisco"',
        'Include skills: "full-stack developer with Node.js experience"'
      );
      break;
      
    case 'projects':
      suggestions.push(
        'Specify project type: "open source React projects"',
        'Add technology: "machine learning projects using Python"',
        'Include status: "projects seeking contributors"'
      );
      break;
      
    case 'startups':
      suggestions.push(
        'Add industry: "fintech startups"',
        'Specify stage: "seed stage AI startups"',
        'Include location: "startups in Silicon Valley"'
      );
      break;
  }
  
  return suggestions;
}

/**
 * Formats the query for better search results based on detected type
 * @param {string} query - The original query
 * @param {string} detectedType - The detected search type
 * @returns {string} - Optimized query
 */
export function optimizeQuery(query, detectedType) {
  // This could be expanded to automatically enhance queries
  // For now, just return the original query
  return query.trim();
}