import json
import os
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
import hashlib
import re
from typing import List, Dict, Any, Optional
from collections import Counter
import numpy as np

# --- ADDITION: Import from your query_understanding.py file ---
from query_understanding import QueryUnderstanding, ParsedQuery


# Load SentenceTransformer model once
model = SentenceTransformer('all-MiniLM-L6-v2')
# Get the actual embedding size from the model
EMBEDDING_SIZE = model.get_sentence_embedding_dimension()

QDRANT_HOST = "http://localhost:6333"
COLLECTION_NAME = "user_profiles"

# Fix the path to make it work regardless of where the script is run from
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_FILE = os.path.join(PROJECT_ROOT, "backend", "data", "profiles.json")

client = QdrantClient(url=QDRANT_HOST)

# --- ADDITION: Initialize the query understanding module ---
query_understander = QueryUnderstanding()


def generate_hash(text: str) -> int:
    """Generate a unique hash for each profile - fixed to avoid collisions"""
    # Use SHA256 for better distribution and avoid collisions
    return int(hashlib.sha256(text.encode('utf-8')).hexdigest(), 16) % (10 ** 15)


def normalize_text(text: str) -> str:
    """Normalize text for keyword matching"""
    return re.sub(r'[^\w\s]', '', text.lower().strip())


def extract_keywords(text: str) -> List[str]:
    """Extract keywords from text, removing common stop words"""
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 
        'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'looking', 'need', 'want', 'seeking', 'experience', 'years', 'from'
    }
    
    normalized = normalize_text(text)
    words = normalized.split()
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    return keywords


def calculate_reputation_score(profile_data: Dict, query: str = "") -> float:
    """Calculates a score based on the reputation of companies and institutes."""
    score = 0.0
    
    # Enhanced tiered companies
    t1_companies = {
        'google', 'meta', 'facebook', 'amazon', 'apple', 'netflix', 'microsoft',
        'openai', 'anthropic', 'deepmind'
    }
    t2_companies = {
        'salesforce', 'oracle', 'ibm', 'cisco', 'adobe', 'sap', 'nvidia', 'intel',
        'twitter', 'linkedin', 'spotify', 'airbnb', 'tesla', 'spacex'
    }
    t3_companies = {
        'stripe', 'paypal', 'square', 'razorpay', 'paytm', 'zomato', 'swiggy', 
        'uber', 'ola', 'cred', 'zerodha', 'flipkart', 'myntra', 'byju', 'unacademy'
    }

    # Enhanced tiered institutes with more comprehensive coverage
    t1_institutes = {
        'iit bombay', 'iit madras', 'iit delhi', 'iit kanpur', 'iit kharagpur', 
        'iisc bangalore', 'iisc', 'stanford', 'mit', 'harvard', 'berkeley',
        'carnegie mellon', 'caltech'
    }
    t2_institutes = {
        'iit', 'nit', 'bits', 'iiit', 'dtu', 'nsit', 'vit', 'manipal',
        'delhi technological university', 'international institute of information technology'
    }

    # Extract company and institute names from profile
    work_history = profile_data.get('work_history', [])
    education = profile_data.get('education', {})
    
    # Get all companies from work history
    company_names = set()
    for item in work_history:
        company = normalize_text(item.get('company', ''))
        if company:
            company_names.add(company)
    
    institute_name = normalize_text(education.get('institution', '') + ' ' + education.get('degree', ''))
    
    # Calculate company reputation score
    company_score = 0.0
    for company in company_names:
        if any(t1_comp in company for t1_comp in t1_companies):
            company_score = max(company_score, 0.4)
        elif any(t2_comp in company for t2_comp in t2_companies):
            company_score = max(company_score, 0.25)
        elif any(t3_comp in company for t3_comp in t3_companies):
            company_score = max(company_score, 0.15)
    
    score += company_score
        
    # Calculate institute reputation score
    institute_score = 0.0
    if any(t1_inst in institute_name for t1_inst in t1_institutes):
        institute_score = 0.4
    elif any(t2_inst in institute_name for t2_inst in t2_institutes):
        institute_score = 0.25
    
    score += institute_score

    # Bonus score for query-specific matches
    query_keywords = set(extract_keywords(query))
    if query_keywords:
        # Company match bonus
        if query_keywords.intersection(company_names):
            score += 0.3
        # Institute match bonus
        if any(keyword in institute_name for keyword in query_keywords):
            score += 0.3
        
    return min(score, 1.0)


def calculate_keyword_score(query_keywords: List[str], profile_text: str, profile_data: Dict) -> float:
    """Enhanced keyword matching score between query and profile"""
    if not query_keywords:
        return 0.0
    
    profile_keywords = extract_keywords(profile_text)
    
    # Extract keywords from all structured fields with appropriate weights
    structured_fields = {
        'skill_tags': 3.0,  # Skills are most important
        'preferred_roles': 2.5,  # Roles are very important
        'project_interests': 1.5,  # Interests are moderately important
        'availability_timezone': 1.0,
        'name': 1.0,
    }
    
    weighted_keywords = []
    
    # Add weighted keywords from structured fields
    for field, weight in structured_fields.items():
        if field in profile_data and profile_data[field]:
            if isinstance(profile_data[field], list):
                field_keywords = []
                for item in profile_data[field]:
                    field_keywords.extend(extract_keywords(str(item)))
            else:
                field_keywords = extract_keywords(str(profile_data[field]))
            
            # Add each keyword multiple times based on weight
            for keyword in field_keywords:
                weighted_keywords.extend([keyword] * int(weight))
    
    # Add work history keywords with medium weight
    for work_item in profile_data.get('work_history', []):
        company_keywords = extract_keywords(work_item.get('company', ''))
        role_keywords = extract_keywords(work_item.get('role', ''))
        for keyword in company_keywords + role_keywords:
            weighted_keywords.extend([keyword] * 2)
    
    # Add education keywords with medium weight
    education = profile_data.get('education', {})
    institution_keywords = extract_keywords(education.get('institution', ''))
    degree_keywords = extract_keywords(education.get('degree', ''))
    for keyword in institution_keywords + degree_keywords:
        weighted_keywords.extend([keyword] * 2)
    
    # Combine with profile keywords
    all_profile_keywords = profile_keywords + weighted_keywords
    
    if not all_profile_keywords:
        return 0.0
    
    # Calculate weighted overlap score
    query_set = set(query_keywords)
    profile_counter = Counter(all_profile_keywords)
    
    # Calculate match score with frequency weighting
    match_score = 0.0
    total_query_weight = len(query_keywords)
    
    for query_keyword in query_keywords:
        if query_keyword in profile_counter:
            # Weight by frequency in profile (capped at 5 for diminishing returns)
            frequency_weight = min(profile_counter[query_keyword], 5)
            match_score += frequency_weight / 5.0  # Normalize to [0,1]
    
    # Normalize by query length
    if total_query_weight > 0:
        match_score = match_score / total_query_weight
    
    # Add exact skill/role match bonus
    exact_matches = 0
    skill_tags = [normalize_text(skill) for skill in profile_data.get('skill_tags', [])]
    roles = [normalize_text(role) for role in profile_data.get('preferred_roles', [])]
    
    for keyword in query_keywords:
        if keyword in skill_tags:
            exact_matches += 2  # Higher weight for skill matches
        elif keyword in roles:
            exact_matches += 1.5  # High weight for role matches
    
    exact_match_bonus = min(exact_matches * 0.15, 0.6)  # Cap bonus at 0.6
    
    return min(match_score + exact_match_bonus, 1.0)


def calculate_experience_score(query: str, years_experience: int) -> float:
    """Enhanced experience relevance score based on query context"""
    query_lower = query.lower()
    
    # More comprehensive experience level detection
    if any(term in query_lower for term in ['senior', 'lead', 'principal', 'staff', 'architect']):
        target_years = 6
    elif any(term in query_lower for term in ['junior', 'entry', 'fresh', 'new grad', 'intern']):
        target_years = 1
    elif any(term in query_lower for term in ['mid', 'intermediate', 'experienced']):
        target_years = 3
    else:
        # Look for specific year mentions with more patterns
        year_patterns = [
            r'(\d+)\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)',
            r'(\d+)\+\s*(?:years?|yrs?)',
            r'(\d+)-(\d+)\s*(?:years?|yrs?)'
        ]
        
        for pattern in year_patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                if isinstance(matches[0], tuple) and len(matches[0]) == 2:
                    # Range like "3-5 years"
                    target_years = (int(matches[0][0]) + int(matches[0][1])) / 2
                else:
                    target_years = int(matches[0])
                break
        else:
            return 0.5  # Neutral score if no experience context
    
    # Enhanced scoring with smoother curve
    diff = abs(years_experience - target_years)
    if diff == 0:
        return 1.0
    elif diff <= 1:
        return 0.9
    elif diff <= 2:
        return 0.75
    elif diff <= 3:
        return 0.6
    elif diff <= 5:
        return 0.4
    else:
        return 0.2


def calculate_role_alignment_score(query: str, profile_data: Dict) -> float:
    """Calculate how well the profile's preferred roles align with the query"""
    query_keywords = set(extract_keywords(query))
    preferred_roles = profile_data.get('preferred_roles', [])
    
    if not preferred_roles or not query_keywords:
        return 0.0
    
    role_keywords = set()
    for role in preferred_roles:
        role_keywords.update(extract_keywords(role))
    
    # Direct role keyword matches
    direct_matches = len(query_keywords.intersection(role_keywords))
    
    # Semantic role matching (common role synonyms)
    role_synonyms = {
        'developer': ['engineer', 'programmer', 'coder', 'dev'],
        'engineer': ['developer', 'programmer', 'dev'],
        'frontend': ['front-end', 'ui', 'client-side'],
        'backend': ['back-end', 'server-side', 'api'],
        'fullstack': ['full-stack', 'full stack'],
        'devops': ['sre', 'infrastructure', 'deployment'],
        'data': ['analytics', 'scientist', 'analyst'],
        'ml': ['machine learning', 'ai', 'artificial intelligence'],
        'mobile': ['android', 'ios', 'react native', 'flutter']
    }
    
    semantic_matches = 0
    for query_word in query_keywords:
        for role_word in role_keywords:
            # Check if they are synonyms
            for key, synonyms in role_synonyms.items():
                if ((query_word == key and role_word in synonyms) or 
                    (role_word == key and query_word in synonyms)):
                    semantic_matches += 0.5
    
    total_matches = direct_matches + semantic_matches
    max_possible_matches = min(len(query_keywords), len(role_keywords))
    
    if max_possible_matches == 0:
        return 0.0
    
    return min(total_matches / max_possible_matches, 1.0)


def ensure_collection_exists(collection_name: str, embedding_size: int):
    """Create collection with proper error handling"""
    try:
        if client.collection_exists(collection_name):
            collection_info = client.get_collection(collection_name)
            if collection_info.config.params.vectors.size != embedding_size:
                print(f"Collection exists but with wrong vector size. Recreating...")
                client.delete_collection(collection_name)
            else:
                print(f"Collection '{collection_name}' already exists with correct configuration")
                return
        
        print(f"Creating collection '{collection_name}' with vector size {embedding_size}")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=embedding_size, 
                distance=models.Distance.COSINE
            )
        )
        print(f"Collection '{collection_name}' created successfully")
        
    except Exception as e:
        print(f"Error managing collection: {str(e)}")
        raise


def get_json_file_hash() -> str:
    """Get hash of the JSON file to detect changes"""
    try:
        with open(DATA_FILE, 'rb') as f:
            content = f.read()
            return hashlib.sha256(content).hexdigest()
    except Exception as e:
        print(f"Error reading JSON file for hash: {str(e)}")
        return ""


def get_stored_file_hash(collection_name: str) -> str:
    """Get the stored file hash from collection metadata"""
    try:
        scroll_result = client.scroll(
            collection_name=collection_name,
            limit=1,
            with_payload=True,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="is_metadata",
                        match=models.MatchValue(value=True)
                    )
                ]
            )
        )
        if scroll_result[0]:
            return scroll_result[0][0].payload.get("file_hash", "")
        return ""
    except Exception:
        return ""


def store_file_hash(collection_name: str, file_hash: str):
    """Store the current file hash as metadata in the collection"""
    try:
        metadata_id = generate_hash("__metadata__")
        client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=metadata_id,
                    vector=[0.0] * EMBEDDING_SIZE,
                    payload={
                        "is_metadata": True,
                        "file_hash": file_hash,
                        "last_updated": str(os.path.getmtime(DATA_FILE))
                    }
                )
            ]
        )
    except Exception as e:
        print(f"Error storing file hash: {str(e)}")


def is_collection_populated(collection_name: str) -> bool:
    """Check if collection has any non-metadata points"""
    try:
        info = client.get_collection(collection_name)
        total_points = info.points_count
        metadata_count = 0
        try:
            scroll_result = client.scroll(
                collection_name=collection_name,
                limit=1,
                with_payload=True,
                scroll_filter=models.Filter(
                    must=[models.FieldCondition(key="is_metadata", match=models.MatchValue(value=True))]
                )
            )
            metadata_count = len(scroll_result[0])
        except Exception:
            pass
        return (total_points - metadata_count) > 0
    except Exception as e:
        print(f"Error checking collection population: {str(e)}")
        return False


def needs_database_update() -> bool:
    """Check if database needs to be updated based on file changes"""
    try:
        if not client.collection_exists(COLLECTION_NAME):
            print("Collection doesn't exist - needs creation")
            return True
        
        if not is_collection_populated(COLLECTION_NAME):
            print("Collection is empty - needs population")
            return True
        
        current_hash = get_json_file_hash()
        stored_hash = get_stored_file_hash(COLLECTION_NAME)
        
        if current_hash != stored_hash:
            print(f"File has changed - needs update")
            return True
        
        print("Database is up to date")
        return False
        
    except Exception as e:
        print(f"Error checking if database needs update: {str(e)}")
        return True


def create_enhanced_profile_text(profile: Dict) -> str:
    """Create enhanced profile text for better semantic search"""
    name = profile.get('name', '')
    handle = profile.get('handle', '')
    skills = profile.get('skill_tags', [])
    experience = profile.get('years_of_experience', 0)
    roles = profile.get('preferred_roles', [])
    interests = profile.get('project_interests', [])
    timezone = profile.get('availability_timezone', '')
    work_history = profile.get('work_history', [])
    education = profile.get('education', {})

    # Create detailed work history text
    work_history_text = ""
    if work_history:
        work_entries = []
        for item in work_history:
            company = item.get('company', '')
            role = item.get('role', '')
            duration = item.get('duration_years', 0)
            if company and role:
                work_entries.append(f"{role} at {company} for {duration} years")
        work_history_text = "; ".join(work_entries)

    # Create education text
    education_text = ""
    if education:
        institution = education.get('institution', '')
        degree = education.get('degree', '')
        if institution and degree:
            education_text = f"{degree} from {institution}"
        elif institution:
            education_text = f"studied at {institution}"
        elif degree:
            education_text = f"holds {degree}"

    # Create comprehensive profile text for semantic search
    profile_parts = [
        f"Name: {name}",
        f"Handle: {handle}",
        f"Skills: {', '.join(skills)}" if skills else "",
        f"Experience: {experience} years",
        f"Preferred Roles: {', '.join(roles)}" if roles else "",
        f"Project Interests: {', '.join(interests)}" if interests else "",
        f"Timezone: {timezone}" if timezone else "",
        f"Work History: {work_history_text}" if work_history_text else "",
        f"Education: {education_text}" if education_text else ""
    ]
    
    # Filter out empty parts
    profile_parts = [part for part in profile_parts if part and not part.endswith(": ")]
    
    return "\n".join(profile_parts)


def load_and_index_profiles(force_reload: bool = False):
    """Load profiles with enhanced processing and validation"""
    
    if not force_reload and not needs_database_update():
        print("Database is already up to date. Skipping reload.")
        return
    
    try:
        print(f"Attempting to load data from: {DATA_FILE}")
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Successfully loaded {len(data)} profiles from JSON file")
        
        if not isinstance(data, list):
            raise ValueError("JSON data should be a list of profiles")
        if len(data) == 0:
            raise ValueError("No profiles found in JSON file")
            
    except Exception as e:
        print(f"Error loading or parsing data: {e}")
        raise

    ensure_collection_exists(COLLECTION_NAME, EMBEDDING_SIZE)
    
    profile_texts = []
    profile_ids = []
    payloads = []
    
    for i, profile in enumerate(data):
        try:
            # Validate required fields
            required_fields = ['name', 'handle', 'skill_tags', 'years_of_experience']
            for field in required_fields:
                if field not in profile:
                    print(f"Warning: Profile {i} missing required field '{field}', skipping")
                    continue
            
            # Create enhanced profile text
            profile_text = create_enhanced_profile_text(profile)
            
            # Create unique identifier
            unique_text = f"{profile_text}__{i}"
            profile_id = generate_hash(unique_text)
            
            profile_texts.append(profile_text)
            profile_ids.append(profile_id)
            
            # Create comprehensive payload
            payload = {
                **profile,  # Include all original data
                "profile_text": profile_text,
                "original_index": i,
                "is_metadata": False,
                # Add computed fields for faster filtering
                "total_work_experience": sum(
                    item.get('duration_years', 0) 
                    for item in profile.get('work_history', [])
                ),
                "has_tier1_company": any(
                    company.lower() in ['google', 'meta', 'facebook', 'amazon', 'apple', 'netflix', 'microsoft']
                    for item in profile.get('work_history', [])
                    for company in [item.get('company', '')]
                ),
                "education_tier": _calculate_education_tier(profile.get('education', {}))
            }
            
            payloads.append(payload)
            
        except Exception as e:
            print(f"Error processing profile {i}: {e}")
            continue

    if not profile_texts:
        raise ValueError("No profiles could be processed successfully")

    try:
        print("Generating embeddings...")
        embeddings = model.encode(profile_texts, show_progress_bar=True)
        
        print("Clearing and recreating collection...")
        if client.collection_exists(COLLECTION_NAME):
            client.delete_collection(COLLECTION_NAME)
        ensure_collection_exists(COLLECTION_NAME, EMBEDDING_SIZE)
        
        print("Inserting profiles into vector database...")
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=models.Batch(
                ids=profile_ids, 
                vectors=[emb.tolist() for emb in embeddings], 
                payloads=payloads
            ),
            wait=True
        )

        current_hash = get_json_file_hash()
        store_file_hash(COLLECTION_NAME, current_hash)
        
        final_count = client.get_collection(COLLECTION_NAME).points_count
        print(f"Successfully inserted {final_count} total points into vector database")
        
    except Exception as e:
        print(f"Error during embedding or database insertion: {e}")
        raise


def _calculate_education_tier(education: Dict) -> int:
    """Helper function to calculate education tier"""
    institution = education.get('institution', '').lower()
    
    if any(tier1 in institution for tier1 in ['iit', 'iisc', 'stanford', 'mit', 'harvard']):
        return 1
    elif any(tier2 in institution for tier2 in ['nit', 'bits', 'iiit', 'dtu']):
        return 2
    else:
        return 3


def verify_database_integrity():
    """Enhanced database integrity verification"""
    try:
        collection_info = client.get_collection(COLLECTION_NAME)
        total_points = collection_info.points_count
        
        metadata_count = 0
        try:
            scroll_result = client.scroll(
                collection_name=COLLECTION_NAME, limit=1, with_payload=True,
                scroll_filter=models.Filter(
                    must=[models.FieldCondition(key="is_metadata", match=models.MatchValue(value=True))]
                )
            )
            metadata_count = len(scroll_result[0])
        except Exception:
            pass
        
        profile_count = total_points - metadata_count
        
        print(f"\nDatabase Verification:")
        print(f"Collection: {COLLECTION_NAME}")
        print(f"Profile points: {profile_count}")
        
        # Sample a few profiles to verify structure
        sample_results = client.scroll(
            collection_name=COLLECTION_NAME, limit=3, with_payload=True, with_vectors=False,
            scroll_filter=models.Filter(
                must=[models.FieldCondition(key="is_metadata", match=models.MatchValue(value=False))]
            )
        )
        
        if sample_results[0]:
            print("Sample profile verification:")
            for i, point in enumerate(sample_results[0][:2]):
                payload = point.payload
                print(f"  Profile {i+1}: {payload.get('name', 'Unknown')} - Fields OK")
                
                # Check for required fields
                required_fields = ['work_history', 'education', 'skill_tags', 'preferred_roles']
                missing_fields = [field for field in required_fields if field not in payload]
                if missing_fields:
                    print(f"    WARNING: Missing fields: {missing_fields}")
        
        return True
        
    except Exception as e:
        print(f"Error verifying database: {e}")
        return False


def semantic_search(query: str, top_k: int = 20) -> list:
    """Enhanced semantic vector search with better filtering"""
    try:
        query_embedding = model.encode(query).tolist()
        search_result = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=top_k,
            with_payload=True,
            query_filter=models.Filter(
                must=[models.FieldCondition(key="is_metadata", match=models.MatchValue(value=False))]
            )
        )
        return [{"profile": hit.payload, "semantic_score": hit.score, "id": hit.id} for hit in search_result]
    except Exception as e:
        print(f"Error during semantic search: {e}")
        return []


def hybrid_search(
    query: str, 
    top_k: int = 5,
    semantic_weight: float = 0.4,
    keyword_weight: float = 0.25,
    experience_weight: float = 0.1,
    reputation_weight: float = 0.15,
    role_alignment_weight: float = 0.1,
    min_semantic_score: float = 0.05
) -> List[Dict[str, Any]]:
    """Enhanced hybrid search with role alignment scoring"""
    
    # Get more candidates for better filtering
    semantic_results = semantic_search(query, top_k=min(100, top_k * 10))
    semantic_results = [r for r in semantic_results if r['semantic_score'] >= min_semantic_score]
    
    if not semantic_results:
        return []
    
    query_keywords = extract_keywords(query)
    hybrid_results = []
    
    for result in semantic_results:
        profile = result['profile']
        
        # Calculate all scoring components
        keyword_score = calculate_keyword_score(query_keywords, profile.get('profile_text', ''), profile)
        experience_score = calculate_experience_score(query, profile.get('years_of_experience', 0))
        reputation_score = calculate_reputation_score(profile, query)
        role_alignment_score = calculate_role_alignment_score(query, profile)
        
        # Calculate weighted hybrid score
        hybrid_score = (
            semantic_weight * result['semantic_score'] +
            keyword_weight * keyword_score +
            experience_weight * experience_score +
            reputation_weight * reputation_score +
            role_alignment_weight * role_alignment_score
        )
        
        hybrid_results.append({
            "profile": profile,
            "semantic_score": result['semantic_score'],
            "keyword_score": keyword_score,
            "experience_score": experience_score,
            "reputation_score": reputation_score,
            "role_alignment_score": role_alignment_score,
            "hybrid_score": hybrid_score,
            "id": result['id']
        })
    
    # Sort by hybrid score and return top results
    hybrid_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
    return hybrid_results[:top_k]


def search_profiles(
    query: str,
    top_k: int = 5,
    search_type: str = "hybrid",
    **kwargs
) -> List[Dict[str, Any]]:
    """Main search function that supports both semantic and hybrid search"""
    if search_type == "semantic":
        return semantic_search(query, top_k)
    elif search_type == "hybrid":
        return hybrid_search(query, top_k, **kwargs)
    else:
        raise ValueError("search_type must be 'semantic' or 'hybrid'")


def print_search_results(results: List[Dict[str, Any]], query: str, search_type: str = "hybrid"):
    """Enhanced results printing with more details"""
    print(f"\n{search_type.capitalize()} search results for: '{query}'")
    print("=" * 60)
    
    if not results:
        print("No results found.")
        return
    
    for i, result in enumerate(results, 1):
        profile = result["profile"]
        print(f"\n{i}. {profile['name']} (@{profile['handle']})")
        
        if search_type == "hybrid":
            print(f"   📊 Hybrid Score: {result['hybrid_score']:.4f}")
            scores_breakdown = (
                f"   └─ Semantic: {result['semantic_score']:.3f} | "
                f"Keyword: {result['keyword_score']:.3f} | "
                f"Experience: {result['experience_score']:.3f} | "
                f"Reputation: {result.get('reputation_score', 0.0):.3f} | "
                f"Role Align: {result.get('role_alignment_score', 0.0):.3f}"
            )
            print(scores_breakdown)
        else:
            print(f"   📊 Semantic Score: {result['semantic_score']:.4f}")
            
        print(f"   🛠️  Skills: {', '.join(profile.get('skill_tags', []))}")
        print(f"   📅 Experience: {profile.get('years_of_experience', 0)} years")
        print(f"   🎯 Preferred Roles: {', '.join(profile.get('preferred_roles', []))}")
        
        # Enhanced work history display
        work_history = profile.get('work_history', [])
        if work_history:
            latest_job = work_history[0]  # Assuming most recent is first
            print(f"   💼 Latest Role: {latest_job.get('role', 'N/A')} at {latest_job.get('company', 'N/A')} ({latest_job.get('duration_years', 0)} years)")
        
        # Enhanced education display
        education = profile.get('education', {})
        if education:
            institution = education.get('institution', 'N/A')
            degree = education.get('degree', 'N/A')
            print(f"   🎓 Education: {degree} from {institution}")
        
        # Additional useful info
        if profile.get('project_interests'):
            print(f"   🚀 Interests: {', '.join(profile.get('project_interests', []))}")
        
        if profile.get('availability_timezone'):
            print(f"   🌍 Timezone: {profile.get('availability_timezone')}")


def advanced_search(
    query: str,
    filters: Dict[str, Any] = None,
    top_k: int = 5,
    search_type: str = "hybrid"
) -> List[Dict[str, Any]]:
    """Advanced search with filtering capabilities"""
    
    if filters is None:
        filters = {}
    
    # Build Qdrant filter conditions
    filter_conditions = [
        models.FieldCondition(key="is_metadata", match=models.MatchValue(value=False))
    ]
    
    # Experience range filter
    if 'min_experience' in filters:
        filter_conditions.append(
            models.FieldCondition(
                key="years_of_experience",
                range=models.Range(gte=filters['min_experience'])
            )
        )
    
    if 'max_experience' in filters:
        filter_conditions.append(
            models.FieldCondition(
                key="years_of_experience",
                range=models.Range(lte=filters['max_experience'])
            )
        )
    
    # Skills filter
    if 'required_skills' in filters:
        for skill in filters['required_skills']:
            filter_conditions.append(
                models.FieldCondition(
                    key="skill_tags",
                    match=models.MatchAny(any=[skill])
                )
            )
    
    # Timezone filter
    if 'timezone' in filters:
        filter_conditions.append(
            models.FieldCondition(
                key="availability_timezone",
                match=models.MatchValue(value=filters['timezone'])
            )
        )
    
    # Tier 1 company filter
    if filters.get('tier1_company_only', False):
        filter_conditions.append(
            models.FieldCondition(
                key="has_tier1_company",
                match=models.MatchValue(value=True)
            )
        )
    
    # Education tier filter
    if 'education_tier' in filters:
        filter_conditions.append(
            models.FieldCondition(
                key="education_tier",
                match=models.MatchValue(value=filters['education_tier'])
            )
        )
    
    # Perform filtered search
    try:
        query_embedding = model.encode(query).tolist()
        search_result = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=top_k * 3,  # Get more results for post-processing
            with_payload=True,
            query_filter=models.Filter(must=filter_conditions)
        )
        
        results = [{"profile": hit.payload, "semantic_score": hit.score, "id": hit.id} for hit in search_result]
        
        if search_type == "hybrid":
            # Apply hybrid scoring to filtered results
            query_keywords = extract_keywords(query)
            hybrid_results = []
            
            for result in results:
                profile = result['profile']
                
                keyword_score = calculate_keyword_score(query_keywords, profile.get('profile_text', ''), profile)
                experience_score = calculate_experience_score(query, profile.get('years_of_experience', 0))
                reputation_score = calculate_reputation_score(profile, query)
                role_alignment_score = calculate_role_alignment_score(query, profile)
                
                hybrid_score = (
                    0.4 * result['semantic_score'] +
                    0.25 * keyword_score +
                    0.1 * experience_score +
                    0.15 * reputation_score +
                    0.1 * role_alignment_score
                )
                
                hybrid_results.append({
                    "profile": profile,
                    "semantic_score": result['semantic_score'],
                    "keyword_score": keyword_score,
                    "experience_score": experience_score,
                    "reputation_score": reputation_score,
                    "role_alignment_score": role_alignment_score,
                    "hybrid_score": hybrid_score,
                    "id": result['id']
                })
            
            hybrid_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
            return hybrid_results[:top_k]
        
        return results[:top_k]
        
    except Exception as e:
        print(f"Error during advanced search: {e}")
        return []


def get_profile_statistics():
    """Get statistics about the profiles in the database"""
    try:
        # Get all profiles
        scroll_result = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=1000,  # Adjust based on your data size
            with_payload=True,
            scroll_filter=models.Filter(
                must=[models.FieldCondition(key="is_metadata", match=models.MatchValue(value=False))]
            )
        )
        
        profiles = [point.payload for point in scroll_result[0]]
        
        if not profiles:
            return {"error": "No profiles found"}
        
        # Calculate statistics
        total_profiles = len(profiles)
        
        # Experience distribution
        experience_values = [p.get('years_of_experience', 0) for p in profiles]
        avg_experience = sum(experience_values) / len(experience_values) if experience_values else 0
        
        # Skill distribution
        all_skills = []
        for p in profiles:
            all_skills.extend(p.get('skill_tags', []))
        skill_counts = Counter(all_skills)
        
        # Role distribution
        all_roles = []
        for p in profiles:
            all_roles.extend(p.get('preferred_roles', []))
        role_counts = Counter(all_roles)
        
        # Company distribution
        all_companies = []
        for p in profiles:
            for work_item in p.get('work_history', []):
                if work_item.get('company'):
                    all_companies.append(work_item['company'])
        company_counts = Counter(all_companies)
        
        return {
            "total_profiles": total_profiles,
            "average_experience": round(avg_experience, 1),
            "experience_range": {
                "min": min(experience_values) if experience_values else 0,
                "max": max(experience_values) if experience_values else 0
            },
            "top_skills": dict(skill_counts.most_common(10)),
            "top_roles": dict(role_counts.most_common(10)),
            "top_companies": dict(company_counts.most_common(10)),
            "unique_skills": len(skill_counts),
            "unique_roles": len(role_counts),
            "unique_companies": len(company_counts)
        }
        
    except Exception as e:
        print(f"Error getting profile statistics: {e}")
        return {"error": str(e)}

# --- START OF ADDED CODE ---

def intelligent_search(
    query: str,
    top_k: int = 5,
    use_query_understanding: bool = True,
    debug: bool = False
) -> List[Dict[str, Any]]:
    """
    Enhanced search function that uses query understanding
    """
    if use_query_understanding:
        # Parse the query
        parsed_query = query_understander.parse_query(query)
        
        if debug:
            print(f"Parsed Query: {parsed_query}")
        
        # Generate enhanced query for semantic search
        enhanced_query = query_understander.generate_enhanced_query(parsed_query)
        
        # Generate filters for advanced search
        filters = query_understander.generate_search_filters(parsed_query)
        
        if debug:
            print(f"Enhanced Query: '{enhanced_query}'")
            print(f"Generated Filters: {filters}")
        
        # Use advanced search with filters if we have them
        if filters:
            results = advanced_search(
                enhanced_query, 
                filters=filters, 
                top_k=top_k,
                search_type="hybrid"
            )
        else:
            # Use regular hybrid search with enhanced query
            results = hybrid_search(enhanced_query, top_k=top_k)
        
        # Add query understanding metadata to results
        for result in results:
            result['parsed_query'] = parsed_query
            result['enhanced_query'] = enhanced_query
            result['applied_filters'] = filters
        
        return results
    else:
        # Fall back to original hybrid search
        return hybrid_search(query, top_k=top_k)

def enhanced_print_results(results: List[Dict[str, Any]], original_query: str):
    """Enhanced results printing with query understanding info"""
    print(f"\nIntelligent search results for: '{original_query}'")
    print("=" * 60)
    
    if not results:
        print("No results found.")
        return
    
    # Show query understanding if available
    if results and 'parsed_query' in results[0]:
        parsed = results[0]['parsed_query']
        print(f"🧠 Query Understanding:")
        print(f"   Type: {parsed.query_type.value}")
        print(f"   Confidence: {parsed.confidence_score:.2f}")
        if parsed.skills:
            print(f"   Skills: {', '.join(parsed.skills)}")
        if parsed.roles:
            print(f"   Roles: {', '.join(parsed.roles)}")
        if parsed.companies:
            print(f"   Companies: {', '.join(parsed.companies)}")
        if parsed.experience_requirements:
            print(f"   Experience: {parsed.experience_requirements}")
        
        if 'applied_filters' in results[0] and results[0]['applied_filters']:
            print(f"   Applied Filters: {results[0]['applied_filters']}")
        print()
    
    # Show results
    for i, result in enumerate(results, 1):
        profile = result["profile"]
        print(f"{i}. {profile['name']} (@{profile['handle']})")
        
        if 'hybrid_score' in result:
            print(f"   📊 Hybrid Score: {result['hybrid_score']:.4f}")
            # Show breakdown if available
            if all(key in result for key in ['semantic_score', 'keyword_score', 'experience_score']):
                scores_breakdown = (
                    f"   └─ Semantic: {result['semantic_score']:.3f} | "
                    f"Keyword: {result['keyword_score']:.3f} | "
                    f"Experience: {result['experience_score']:.3f}"
                )
                if 'reputation_score' in result:
                    scores_breakdown += f" | Reputation: {result['reputation_score']:.3f}"
                if 'role_alignment_score' in result:
                    scores_breakdown += f" | Role: {result['role_alignment_score']:.3f}"
                print(scores_breakdown)
        
        print(f"   🛠️  Skills: {', '.join(profile.get('skill_tags', []))}")
        print(f"   📅 Experience: {profile.get('years_of_experience', 0)} years")
        print(f"   🎯 Roles: {', '.join(profile.get('preferred_roles', []))}")
        
        # Show work history
        work_history = profile.get('work_history', [])
        if work_history:
            latest_job = work_history[0]
            print(f"   💼 Latest: {latest_job.get('role', 'N/A')} at {latest_job.get('company', 'N/A')}")
        
        # Show education
        education = profile.get('education', {})
        if education.get('institution'):
            print(f"   🎓 Education: {education.get('degree', '')} from {education.get('institution', '')}")
        
        print()

# --- END OF ADDED CODE ---


if __name__ == "__main__":
    try:
        print("Starting profile indexing process...")
        load_and_index_profiles(force_reload=True)
        verify_database_integrity()
        print("\nDatabase is ready for use!")
        
        # --- NEW MAIN BLOCK TO TEST INTELLIGENT SEARCH ---
        
        print("\n" + "="*70)
        print("Testing Enhanced Search with Query Understanding:")
        print("=" * 70)
        
        test_queries = [
            "Senior Python developer from Google with 5+ years experience",
            "React frontend engineer",
            "Machine learning engineer from IIT",
            "DevOps engineer with AWS experience",
            "Junior developer with Django",
        ]
        
        for query in test_queries:
            print(f"\n{'='*70}")
            results = intelligent_search(query, top_k=3, debug=True)
            enhanced_print_results(results, query)
            
            # Compare with original search
            print(f"\n--- Comparison with Original Hybrid Search ---")
            original_results = hybrid_search(query, top_k=3)
            print(f"Original search found {len(original_results)} results")
            if original_results:
                print(f"Top result: {original_results[0]['profile']['name']} (score: {original_results[0]['hybrid_score']:.4f})")
            else:
                print("No results found.")
        
    except Exception as e:
        print(f"Error during execution: {e}")
        import traceback
        traceback.print_exc()

else:
    try:
        if needs_database_update():
            print("Database is out of date or not found. Indexing profiles...")
            load_and_index_profiles()
        else:
            print("Profile database is up to date.")
    except Exception as e:
        print(f"Warning: Error checking or setting up collection: {e}")