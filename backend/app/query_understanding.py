import re
import spacy
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Load spaCy model (you'll need: python -m spacy download en_core_web_sm)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Warning: spaCy model not found. Install with: python -m spacy download en_core_web_sm")
    nlp = None

class QueryType(Enum):
    SKILL_BASED = "skill_based"
    ROLE_BASED = "role_based"
    COMPANY_BASED = "company_based"
    EXPERIENCE_BASED = "experience_based"
    LOCATION_BASED = "location_based"
    EDUCATION_BASED = "education_based"
    HYBRID = "hybrid"

@dataclass
class ParsedQuery:
    """Structured representation of a parsed query"""
    original_query: str
    query_type: QueryType
    skills: List[str]
    roles: List[str]
    companies: List[str]
    experience_requirements: Dict[str, int]  # min_years, max_years, exact_years
    education_requirements: List[str]
    location_requirements: List[str]
    seniority_level: Optional[str]
    must_have_skills: List[str]
    nice_to_have_skills: List[str]
    confidence_score: float

class QueryUnderstanding:
    def __init__(self):
        self.skill_patterns = self._load_skill_patterns()
        self.role_patterns = self._load_role_patterns()
        self.company_patterns = self._load_company_patterns()
        self.experience_patterns = self._load_experience_patterns()
        self.education_patterns = self._load_education_patterns()
        self.seniority_patterns = self._load_seniority_patterns()
        
    def _load_skill_patterns(self) -> Dict[str, List[str]]:
        """Define skill patterns and their variations"""
        return {
            # Programming Languages
            'python': ['python', 'py', 'python3', 'python developer'],
            'javascript': ['javascript', 'js', 'node.js', 'nodejs', 'node js'],
            'java': ['java', 'java developer', 'java programming'],
            'typescript': ['typescript', 'ts'],
            'go': ['go', 'golang', 'go language'],
            'rust': ['rust', 'rust lang'],
            'c++': ['c++', 'cpp', 'c plus plus'],
            'c#': ['c#', 'csharp', 'c sharp'],
            'php': ['php', 'php developer'],
            'ruby': ['ruby', 'ruby on rails', 'rails'],
            'swift': ['swift', 'ios swift'],
            'kotlin': ['kotlin', 'android kotlin'],
            
            # Frontend Technologies
            'react': ['react', 'reactjs', 'react.js', 'react js'],
            'vue': ['vue', 'vuejs', 'vue.js', 'vue js'],
            'angular': ['angular', 'angularjs', 'angular.js'],
            'svelte': ['svelte', 'sveltejs'],
            'html': ['html', 'html5'],
            'css': ['css', 'css3', 'styling'],
            'sass': ['sass', 'scss'],
            'tailwind': ['tailwind', 'tailwindcss', 'tailwind css'],
            
            # Backend/Databases
            'django': ['django', 'django rest framework', 'drf'],
            'flask': ['flask', 'flask api'],
            'fastapi': ['fastapi', 'fast api'],
            'express': ['express', 'expressjs', 'express.js'],
            'spring': ['spring', 'spring boot', 'spring framework'],
            'postgresql': ['postgresql', 'postgres', 'psql'],
            'mongodb': ['mongodb', 'mongo', 'mongo db'],
            'mysql': ['mysql', 'my sql'],
            'redis': ['redis', 'redis cache'],
            
            # Cloud/DevOps
            'aws': ['aws', 'amazon web services', 'amazon aws'],
            'azure': ['azure', 'microsoft azure', 'azure cloud'],
            'gcp': ['gcp', 'google cloud', 'google cloud platform'],
            'docker': ['docker', 'containerization', 'containers'],
            'kubernetes': ['kubernetes', 'k8s', 'k8'],
            'terraform': ['terraform', 'infrastructure as code'],
            'jenkins': ['jenkins', 'ci/cd', 'continuous integration'],
            
            # Data/ML
            'machine_learning': ['machine learning', 'ml', 'artificial intelligence', 'ai'],
            'deep_learning': ['deep learning', 'neural networks', 'dl'],
            'data_science': ['data science', 'data scientist', 'data analysis'],
            'pandas': ['pandas', 'data manipulation'],
            'numpy': ['numpy', 'numerical computing'],
            'tensorflow': ['tensorflow', 'tf'],
            'pytorch': ['pytorch', 'torch'],
            'scikit_learn': ['scikit-learn', 'sklearn', 'scikit learn'],
        }
    
    def _load_role_patterns(self) -> Dict[str, List[str]]:
        """Define role patterns and their variations"""
        return {
            'software_engineer': ['software engineer', 'software developer', 'developer', 'engineer', 'swe'],
            'frontend_developer': ['frontend developer', 'front-end developer', 'frontend engineer', 'fe developer', 'ui developer'],
            'backend_developer': ['backend developer', 'back-end developer', 'backend engineer', 'be developer', 'server developer'],
            'fullstack_developer': ['fullstack developer', 'full-stack developer', 'full stack developer', 'fullstack engineer'],
            'devops_engineer': ['devops engineer', 'devops', 'sre', 'site reliability engineer', 'infrastructure engineer'],
            'data_scientist': ['data scientist', 'data analyst', 'ml engineer', 'machine learning engineer'],
            'product_manager': ['product manager', 'pm', 'product owner', 'po'],
            'tech_lead': ['tech lead', 'technical lead', 'lead developer', 'engineering lead'],
            'architect': ['architect', 'solution architect', 'software architect', 'system architect'],
            'mobile_developer': ['mobile developer', 'android developer', 'ios developer', 'mobile engineer'],
            'qa_engineer': ['qa engineer', 'quality assurance', 'test engineer', 'sdet'],
        }
    
    def _load_company_patterns(self) -> Dict[str, List[str]]:
        """Define company patterns and their variations"""
        return {
            'google': ['google', 'alphabet'],
            'meta': ['meta', 'facebook', 'fb'],
            'amazon': ['amazon', 'aws', 'amazon web services'],
            'microsoft': ['microsoft', 'msft'],
            'apple': ['apple', 'cupertino'],
            'netflix': ['netflix', 'nflx'],
            'tesla': ['tesla'],
            'uber': ['uber', 'uber technologies'],
            'airbnb': ['airbnb', 'air bnb'],
            'spotify': ['spotify'],
            'stripe': ['stripe', 'stripe inc'],
            'salesforce': ['salesforce', 'sfdc'],
            'oracle': ['oracle', 'oracle corporation'],
            'ibm': ['ibm', 'international business machines'],
            'cisco': ['cisco', 'cisco systems'],
            'adobe': ['adobe', 'adobe systems'],
            'nvidia': ['nvidia', 'nvidia corporation'],
            'intel': ['intel', 'intel corporation'],
            'flipkart': ['flipkart', 'flipkart india'],
            'zomato': ['zomato'],
            'swiggy': ['swiggy'],
            'paytm': ['paytm', 'one97'],
            'razorpay': ['razorpay'],
            'byju': ['byju', 'byjus', "byju's"],
            'ola': ['ola', 'ola cabs'],
            'cred': ['cred'],
            'zerodha': ['zerodha'],
        }
    
    def _load_experience_patterns(self) -> List[Tuple[str, str]]:
        """Define experience patterns with their types"""
        return [
            # Exact years
            (r'(\d+)\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)', 'exact'),
            (r'(\d+)\s*(?:year|yr)\s*(?:experienced|exp)', 'exact'),
            
            # Minimum years
            (r'(\d+)\+\s*(?:years?|yrs?)', 'min'),
            (r'(?:minimum|min|at least)\s*(\d+)\s*(?:years?|yrs?)', 'min'),
            (r'(\d+)\s*(?:years?|yrs?)\s*(?:or more|plus|minimum)', 'min'),
            
            # Range
            (r'(\d+)-(\d+)\s*(?:years?|yrs?)', 'range'),
            (r'(\d+)\s*to\s*(\d+)\s*(?:years?|yrs?)', 'range'),
            (r'between\s*(\d+)\s*(?:and|to)\s*(\d+)\s*(?:years?|yrs?)', 'range'),
            
            # Seniority levels
            (r'(?:junior|jr|entry|fresh|fresher|new grad)', 'junior'),
            (r'(?:senior|sr|experienced)', 'senior'),
            (r'(?:lead|principal|staff|architect)', 'lead'),
            (r'(?:mid|intermediate|mid-level)', 'mid'),
        ]
    
    def _load_education_patterns(self) -> Dict[str, List[str]]:
        """Define education patterns"""
        return {
            'iit': ['iit', 'indian institute of technology', 'iit bombay', 'iit delhi', 'iit madras', 'iit kanpur', 'iit kharagpur'],
            'iisc': ['iisc', 'indian institute of science', 'iisc bangalore'],
            'nit': ['nit', 'national institute of technology'],
            'bits': ['bits', 'bits pilani', 'birla institute'],
            'iiit': ['iiit', 'international institute of information technology'],
            'stanford': ['stanford', 'stanford university'],
            'mit': ['mit', 'massachusetts institute of technology'],
            'harvard': ['harvard', 'harvard university'],
            'berkeley': ['berkeley', 'uc berkeley', 'university of california berkeley'],
            'carnegie_mellon': ['carnegie mellon', 'cmu'],
            'caltech': ['caltech', 'california institute of technology'],
        }
    
    def _load_seniority_patterns(self) -> Dict[str, List[str]]:
        """Define seniority level patterns"""
        return {
            'junior': ['junior', 'jr', 'entry', 'fresh', 'fresher', 'new grad', 'graduate', 'trainee'],
            'mid': ['mid', 'intermediate', 'mid-level', 'associate'],
            'senior': ['senior', 'sr', 'experienced'],
            'lead': ['lead', 'principal', 'staff', 'architect', 'director'],
        }
    
    def parse_query(self, query: str) -> ParsedQuery:
        """Main method to parse a query into structured components"""
        query_lower = query.lower().strip()
        
        # Initialize result structure
        result = ParsedQuery(
            original_query=query,
            query_type=QueryType.HYBRID,
            skills=[],
            roles=[],
            companies=[],
            experience_requirements={},
            education_requirements=[],
            location_requirements=[],
            seniority_level=None,
            must_have_skills=[],
            nice_to_have_skills=[],
            confidence_score=0.0
        )
        
        # Extract different components
        result.skills = self._extract_skills(query_lower)
        result.roles = self._extract_roles(query_lower)
        result.companies = self._extract_companies(query_lower)
        result.experience_requirements = self._extract_experience(query_lower)
        result.education_requirements = self._extract_education(query_lower)
        result.seniority_level = self._extract_seniority(query_lower)
        
        # Determine query type based on dominant components
        result.query_type = self._determine_query_type(result)
        
        # Separate must-have vs nice-to-have (using NLP if available)
        result.must_have_skills, result.nice_to_have_skills = self._categorize_skills(query, result.skills)
        
        # Calculate confidence score
        result.confidence_score = self._calculate_confidence(result)
        
        return result
    
    def _extract_skills(self, query: str) -> List[str]:
        """Extract skills from query"""
        found_skills = []
        
        for canonical_skill, variations in self.skill_patterns.items():
            for variation in variations:
                if variation in query:
                    found_skills.append(canonical_skill)
                    break
        
        return list(set(found_skills))  # Remove duplicates
    
    def _extract_roles(self, query: str) -> List[str]:
        """Extract roles from query"""
        found_roles = []
        
        for canonical_role, variations in self.role_patterns.items():
            for variation in variations:
                if variation in query:
                    found_roles.append(canonical_role)
                    break
        
        return list(set(found_roles))
    
    def _extract_companies(self, query: str) -> List[str]:
        """Extract companies from query"""
        found_companies = []
        
        for canonical_company, variations in self.company_patterns.items():
            for variation in variations:
                if variation in query:
                    found_companies.append(canonical_company)
                    break
        
        return list(set(found_companies))
    
    def _extract_experience(self, query: str) -> Dict[str, int]:
        """Extract experience requirements from query"""
        experience_req = {}
        
        for pattern, exp_type in self.experience_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            
            if matches:
                if exp_type == 'exact':
                    experience_req['exact_years'] = int(matches[0])
                elif exp_type == 'min':
                    experience_req['min_years'] = int(matches[0])
                elif exp_type == 'range':
                    if isinstance(matches[0], tuple):
                        experience_req['min_years'] = int(matches[0][0])
                        experience_req['max_years'] = int(matches[0][1])
                    else:
                        experience_req['min_years'] = int(matches[0])
                        experience_req['max_years'] = int(matches[1])
                elif exp_type in ['junior', 'mid', 'senior', 'lead']:
                    experience_req['seniority_level'] = exp_type
                
                break  # Take first match
        
        return experience_req
    
    def _extract_education(self, query: str) -> List[str]:
        """Extract education requirements from query"""
        found_education = []
        
        for canonical_edu, variations in self.education_patterns.items():
            for variation in variations:
                if variation in query:
                    found_education.append(canonical_edu)
                    break
        
        return list(set(found_education))
    
    def _extract_seniority(self, query: str) -> Optional[str]:
        """Extract seniority level from query"""
        for seniority, variations in self.seniority_patterns.items():
            for variation in variations:
                if variation in query:
                    return seniority
        return None
    
    def _determine_query_type(self, result: ParsedQuery) -> QueryType:
        """Determine the primary query type based on extracted components"""
        component_counts = {
            'skills': len(result.skills),
            'roles': len(result.roles),
            'companies': len(result.companies),
            'experience': len(result.experience_requirements),
            'education': len(result.education_requirements),
        }
        
        # Simple heuristic to determine primary type
        if component_counts['companies'] > 0 and component_counts['roles'] > 0:
            return QueryType.HYBRID
        elif component_counts['companies'] > 0:
            return QueryType.COMPANY_BASED
        elif component_counts['roles'] > 0:
            return QueryType.ROLE_BASED
        elif component_counts['skills'] > 0:
            return QueryType.SKILL_BASED
        elif component_counts['experience'] > 0:
            return QueryType.EXPERIENCE_BASED
        elif component_counts['education'] > 0:
            return QueryType.EDUCATION_BASED
        else:
            return QueryType.HYBRID
    
    def _categorize_skills(self, query: str, skills: List[str]) -> Tuple[List[str], List[str]]:
        """Categorize skills into must-have vs nice-to-have using NLP"""
        if not nlp or not skills:
            return skills, []  # All skills as must-have if no NLP
        
        # Use NLP to analyze the query structure
        doc = nlp(query)
        
        # Simple heuristic: skills mentioned with strong verbs are must-have
        strong_indicators = ['need', 'require', 'must', 'essential', 'critical']
        weak_indicators = ['prefer', 'nice', 'bonus', 'plus', 'good to have']
        
        query_lower = query.lower()
        
        if any(indicator in query_lower for indicator in strong_indicators):
            return skills, []  # All must-have
        elif any(indicator in query_lower for indicator in weak_indicators):
            # More sophisticated logic could be added here
            return skills[:len(skills)//2], skills[len(skills)//2:]
        else:
            return skills, []  # Default to must-have
    
    def _calculate_confidence(self, result: ParsedQuery) -> float:
        """Calculate confidence score for the parsed query"""
        total_components = (
            len(result.skills) +
            len(result.roles) +
            len(result.companies) +
            len(result.experience_requirements) +
            len(result.education_requirements) +
            (1 if result.seniority_level else 0)
        )
        
        # Base confidence on number of recognized components
        if total_components == 0:
            return 0.0
        elif total_components <= 2:
            return 0.6
        elif total_components <= 4:
            return 0.8
        else:
            return 0.95
    
    def generate_search_filters(self, parsed_query: ParsedQuery) -> Dict[str, any]:
        """Convert parsed query into search filters for your existing system"""
        filters = {}
        
        # Experience filters
        if 'min_years' in parsed_query.experience_requirements:
            filters['min_experience'] = parsed_query.experience_requirements['min_years']
        if 'max_years' in parsed_query.experience_requirements:
            filters['max_experience'] = parsed_query.experience_requirements['max_years']
        if 'exact_years' in parsed_query.experience_requirements:
            filters['min_experience'] = parsed_query.experience_requirements['exact_years'] - 1
            filters['max_experience'] = parsed_query.experience_requirements['exact_years'] + 1
        
        # Skill filters
        if parsed_query.must_have_skills:
            filters['required_skills'] = parsed_query.must_have_skills
        
        # Company filters
        if parsed_query.companies:
            tier1_companies = ['google', 'meta', 'amazon', 'apple', 'microsoft', 'netflix']
            if any(company in tier1_companies for company in parsed_query.companies):
                filters['tier1_company_only'] = True
        
        # Education filters
        if parsed_query.education_requirements:
            tier1_edu = ['iit', 'iisc', 'stanford', 'mit', 'harvard']
            if any(edu in tier1_edu for edu in parsed_query.education_requirements):
                filters['education_tier'] = 1
        
        return filters
    
    def generate_enhanced_query(self, parsed_query: ParsedQuery) -> str:
        """Generate an enhanced query string for semantic search"""
        components = []
        
        # Add roles with higher weight
        if parsed_query.roles:
            role_text = ' '.join(parsed_query.roles).replace('_', ' ')
            components.append(f"{role_text} {role_text}")  # Duplicate for weight
        
        # Add skills
        if parsed_query.skills:
            skill_text = ' '.join(parsed_query.skills).replace('_', ' ')
            components.append(skill_text)
        
        # Add companies
        if parsed_query.companies:
            company_text = ' '.join(parsed_query.companies).replace('_', ' ')
            components.append(company_text)
        
        # Add seniority context
        if parsed_query.seniority_level:
            components.append(parsed_query.seniority_level)
        
        # Add experience context
        if parsed_query.experience_requirements:
            if 'exact_years' in parsed_query.experience_requirements:
                components.append(f"{parsed_query.experience_requirements['exact_years']} years experience")
            elif 'min_years' in parsed_query.experience_requirements:
                components.append(f"{parsed_query.experience_requirements['min_years']}+ years experience")
        
        # Add education context
        if parsed_query.education_requirements:
            edu_text = ' '.join(parsed_query.education_requirements).replace('_', ' ')
            components.append(edu_text)
        
        return ' '.join(components) if components else parsed_query.original_query


# Example usage and testing
if __name__ == "__main__":
    qu = QueryUnderstanding()
    
    # Test queries
    test_queries = [
        "Senior Python developer from Google with 5+ years experience",
        "React frontend engineer at Meta",
        "Machine learning engineer from IIT Bombay",
        "DevOps engineer with AWS and Docker experience",
        "Junior fullstack developer with Python Django",
        "Data scientist with 3-5 years experience",
        "Technical lead with React and Node.js",
        "iOS developer from Apple or Google",
        "Senior backend engineer with microservices experience",
        "ML engineer with TensorFlow and PyTorch from Stanford"
    ]
    
    print("Testing Query Understanding:")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nOriginal Query: '{query}'")
        parsed = qu.parse_query(query)
        
        print(f"Query Type: {parsed.query_type.value}")
        print(f"Skills: {parsed.skills}")
        print(f"Roles: {parsed.roles}")
        print(f"Companies: {parsed.companies}")
        print(f"Experience: {parsed.experience_requirements}")
        print(f"Education: {parsed.education_requirements}")
        print(f"Seniority: {parsed.seniority_level}")
        print(f"Confidence: {parsed.confidence_score:.2f}")
        
        # Show generated filters and enhanced query
        filters = qu.generate_search_filters(parsed)
        enhanced_query = qu.generate_enhanced_query(parsed)
        
        print(f"Generated Filters: {filters}")
        print(f"Enhanced Query: '{enhanced_query}'")
        print("-" * 40)