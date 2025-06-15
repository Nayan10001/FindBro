import json
import os
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
import hashlib
import re
from typing import List, Dict, Any, Optional
from collections import Counter
import numpy as np
import asyncio
from functools import lru_cache
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load SentenceTransformer model once and cache it
@lru_cache(maxsize=1)
def get_model():
    """Load and cache the sentence transformer model"""
    logger.info("Loading SentenceTransformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("Model loaded successfully")
    return model

model = get_model()
EMBEDDING_SIZE = model.get_sentence_embedding_dimension()

QDRANT_HOST = "http://localhost:6333"
COLLECTION_NAME = "user_profiles"

# Fix the path to make it work regardless of where the script is run from
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_FILE = os.path.join(PROJECT_ROOT, "backend", "data", "profiles.json")

# Initialize client with connection pooling
client = QdrantClient(
    url=QDRANT_HOST,
    timeout=30,
    prefer_grpc=False  # Use HTTP for better compatibility
)

# Cache for frequently accessed data
@lru_cache(maxsize=100)
def cached_extract_keywords(text: str) -> tuple:
    """Cached version of extract_keywords"""
    return tuple(extract_keywords_internal(text))

def extract_keywords_internal(text: str) -> List[str]:
    """Extract keywords from text, removing common stop words"""
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 
        'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'looking', 'need', 'want', 'seeking', 'experience', 'years'
    }
    
    normalized = normalize_text(text)
    words = normalized.split()
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    return keywords

def extract_keywords(text: str) -> List[str]:
    """Extract keywords with caching"""
    return list(cached_extract_keywords(text))

def generate_hash(text: str) -> int:
    """Generate a unique hash for each profile - fixed to avoid collisions"""
    return int(hashlib.sha256(text.encode('utf-8')).hexdigest(), 16) % (10 ** 15)

def normalize_text(text: str) -> str:
    """Normalize text for keyword matching"""
    return re.sub(r'[^\w\s]', '', text.lower().strip())

def calculate_keyword_score(query_keywords: List[str], profile_text: str, profile_data: Dict) -> float:
    """Calculate keyword matching score between query and profile"""
    profile_keywords = extract_keywords(profile_text)
    
    # Also extract keywords from structured fields for better matching
    structured_text = " ".join([
        " ".join(profile_data.get('skill_tags', [])),
        " ".join(profile_data.get('preferred_roles', [])),
        " ".join(profile_data.get('project_interests', [])),
        profile_data.get('availability_timezone', ''),
        profile_data.get('name', '')
    ])
    profile_keywords.extend(extract_keywords(structured_text))
    
    if not query_keywords or not profile_keywords:
        return 0.0
    
    # Calculate overlap score
    query_set = set(query_keywords)
    profile_set = set(profile_keywords)
    
    intersection = query_set.intersection(profile_set)
    union = query_set.union(profile_set)
    
    # Jaccard similarity with boost for exact matches
    jaccard_score = len(intersection) / len(union) if union else 0
    
    # Boost score for exact skill/role matches
    exact_matches = 0
    skill_tags = [normalize_text(skill) for skill in profile_data.get('skill_tags', [])]
    roles = [normalize_text(role) for role in profile_data.get('preferred_roles', [])]
    
    for keyword in query_keywords:
        if keyword in skill_tags or keyword in roles:
            exact_matches += 1
    
    exact_match_boost = exact_matches * 0.2
    
    return min(jaccard_score + exact_match_boost, 1.0)

def calculate_experience_score(query: str, years_experience: int) -> float:
    """Calculate experience relevance score based on query context"""
    query_lower = query.lower()
    
    # Extract experience requirements from query
    if 'senior' in query_lower or 'lead' in query_lower:
        target_years = 5
    elif 'junior' in query_lower or 'entry' in query_lower:
        target_years = 1
    elif 'mid' in query_lower or 'intermediate' in query_lower:
        target_years = 3
    else:
        # Look for specific year mentions
        year_matches = re.findall(r'(\d+)\s*(?:year|yr)', query_lower)
        if year_matches:
            target_years = int(year_matches[0])
        else:
            return 0.5  # Neutral score if no experience context
    
    # Calculate score based on how close the experience is to target
    diff = abs(years_experience - target_years)
    if diff == 0:
        return 1.0
    elif diff <= 2:
        return 0.8
    elif diff <= 5:
        return 0.6
    else:
        return 0.3

def ensure_collection_exists(collection_name: str, embedding_size: int):
    """Create collection with proper error handling"""
    try:
        # Check if collection exists and get its info
        if client.collection_exists(collection_name):
            collection_info = client.get_collection(collection_name)
            # Check if the vector size matches
            if collection_info.config.params.vectors.size != embedding_size:
                logger.warning(f"Collection exists but with wrong vector size. Recreating...")
                client.delete_collection(collection_name)
            else:
                logger.info(f"Collection '{collection_name}' already exists with correct configuration")
                return
        
        # Create collection with the correct embedding size
        logger.info(f"Creating collection '{collection_name}' with vector size {embedding_size}")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=embedding_size, 
                distance=models.Distance.COSINE
            )
        )
        logger.info(f"Collection '{collection_name}' created successfully")
        
    except Exception as e:
        logger.error(f"Error managing collection: {str(e)}")
        raise

def get_json_file_hash() -> str:
    """Get hash of the JSON file to detect changes"""
    try:
        with open(DATA_FILE, 'rb') as f:
            content = f.read()
            return hashlib.sha256(content).hexdigest()
    except Exception as e:
        logger.error(f"Error reading JSON file for hash: {str(e)}")
        return ""

def get_stored_file_hash(collection_name: str) -> str:
    """Get the stored file hash from collection metadata"""
    try:
        # Try to get a point that contains the file hash in metadata
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
        
        if scroll_result[0]:  # If metadata point exists
            return scroll_result[0][0].payload.get("file_hash", "")
        return ""
    except Exception:
        return ""

def store_file_hash(collection_name: str, file_hash: str):
    """Store the current file hash as metadata in the collection"""
    try:
        # Create a special metadata point
        metadata_id = generate_hash("__metadata__")
        client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=metadata_id,
                    vector=[0.0] * EMBEDDING_SIZE,  # Dummy vector
                    payload={
                        "is_metadata": True,
                        "file_hash": file_hash,
                        "last_updated": str(os.path.getmtime(DATA_FILE))
                    }
                )
            ]
        )
    except Exception as e:
        logger.error(f"Error storing file hash: {str(e)}")

def is_collection_populated(collection_name: str) -> bool:
    """Check if collection has any non-metadata points"""
    try:
        info = client.get_collection(collection_name)
        total_points = info.points_count
        
        # Check for metadata points
        metadata_count = 0
        try:
            scroll_result = client.scroll(
                collection_name=collection_name,
                limit=10,
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
            metadata_count = len(scroll_result[0])
        except Exception:
            pass
        
        actual_profiles = total_points - metadata_count
        return actual_profiles > 0
    except Exception as e:
        logger.error(f"Error checking collection population: {str(e)}")
        return False

def needs_database_update() -> bool:
    """Check if database needs to be updated based on file changes"""
    try:
        if not client.collection_exists(COLLECTION_NAME):
            logger.info("Collection doesn't exist - needs creation")
            return True
        
        if not is_collection_populated(COLLECTION_NAME):
            logger.info("Collection is empty - needs population")
            return True
        
        current_hash = get_json_file_hash()
        stored_hash = get_stored_file_hash(COLLECTION_NAME)
        
        if current_hash != stored_hash:
            logger.info(f"File has changed - needs update")
            return True
        
        logger.info("Database is up to date")
        return False
        
    except Exception as e:
        logger.error(f"Error checking if database needs update: {str(e)}")
        return True  # Default to updating if we can't determine

def load_and_index_profiles(force_reload: bool = False):
    """Load profiles with better error handling and validation"""
    
    # Check if update is needed (unless forced)
    if not force_reload and not needs_database_update():
        logger.info("Database is already up to date. Skipping reload.")
        return
    
    try:
        logger.info(f"Attempting to load data from: {DATA_FILE}")
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Successfully loaded {len(data)} profiles from JSON file")
        
        # Validate data structure
        if not isinstance(data, list):
            raise ValueError("JSON data should be a list of profiles")
            
        if len(data) == 0:
            raise ValueError("No profiles found in JSON file")
            
    except FileNotFoundError:
        logger.error(f"Error: File not found at {DATA_FILE}")
        # Alternative locations to check
        possible_locations = [
            os.path.join(os.path.dirname(__file__), "..", "data", "profiles.json"),
            os.path.join(os.path.dirname(__file__), "data", "profiles.json"),
            os.path.join(PROJECT_ROOT, "data", "profiles.json"),
            "profiles.json"  # Current directory
        ]
        
        for location in possible_locations:
            try:
                logger.info(f"Trying alternative location: {location}")
                with open(location, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"Successfully loaded {len(data)} profiles from {location}")
                break
            except FileNotFoundError:
                continue
        else:
            raise FileNotFoundError(f"Could not find profiles.json in any expected location")
    
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON file: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading data: {str(e)}")
        raise

    # Ensure collection exists before processing
    ensure_collection_exists(COLLECTION_NAME, EMBEDDING_SIZE)
    
    profile_texts = []
    profile_ids = []
    payloads = []
    successful_profiles = 0
    failed_profiles = 0

    for i, profile in enumerate(data):
        try:
            # Handle missing or None values gracefully
            name = profile.get('name', f'User_{i}') or f'User_{i}'
            handle = profile.get('handle', f'user_{i}') or f'user_{i}'
            skills = profile.get('skill_tags', []) or []
            experience = profile.get('years_of_experience', 0) or 0
            roles = profile.get('preferred_roles', []) or []
            timezone = profile.get('availability_timezone', 'Unknown') or 'Unknown'
            interests = profile.get('project_interests', []) or []

            # Ensure all fields are proper types
            if not isinstance(skills, list):
                skills = []
            if not isinstance(roles, list):
                roles = []
            if not isinstance(interests, list):
                interests = []
            if not isinstance(experience, (int, float)):
                experience = 0

            profile_text = (
                f"Name: {name}\nHandle: {handle}\nSkills: {', '.join(skills)}\n"
                f"Experience: {experience} years\nPreferred Roles: {', '.join(roles)}\n"
                f"Timezone: {timezone}\nProject Interests: {', '.join(interests)}"
            )

            # Create a unique identifier including index to avoid collisions
            unique_text = f"{profile_text}__{i}"
            profile_id = generate_hash(unique_text)
            
            # Check for duplicate IDs
            while profile_id in profile_ids:
                unique_text = f"{profile_text}__{i}_{len(profile_ids)}"
                profile_id = generate_hash(unique_text)
            
            profile_texts.append(profile_text)
            profile_ids.append(profile_id)
            payloads.append({
                "name": name,
                "handle": handle,
                "skill_tags": skills,
                "years_of_experience": int(experience),
                "preferred_roles": roles,
                "availability_timezone": timezone,
                "project_interests": interests,
                "profile_text": profile_text,
                "original_index": i,  # Track original position
                "is_metadata": False  # Mark as regular profile (not metadata)
            })
            successful_profiles += 1
            
        except Exception as e:
            logger.error(f"Error processing profile {i}: {str(e)}")
            failed_profiles += 1
            continue

    logger.info(f"Processed {successful_profiles} profiles successfully, {failed_profiles} failed")
    
    if successful_profiles == 0:
        raise ValueError("No profiles could be processed successfully")

    try:
        # Generate embeddings in batches to handle memory better
        logger.info("Generating embeddings...")
        batch_size = 32  # Smaller batch size for better memory management
        embeddings = []
        
        for i in range(0, len(profile_texts), batch_size):
            batch_texts = profile_texts[i:i + batch_size]
            batch_embeddings = model.encode(batch_texts, show_progress_bar=False)
            embeddings.extend([emb.tolist() for emb in batch_embeddings])
            logger.info(f"Generated embeddings for batch {i//batch_size + 1}/{(len(profile_texts) + batch_size - 1)//batch_size}")

        logger.info(f"Generated {len(embeddings)} embeddings")
        
        # Clear existing data and insert new data
        logger.info("Clearing existing collection data...")
        if client.collection_exists(COLLECTION_NAME):
            client.delete_collection(COLLECTION_NAME)
        ensure_collection_exists(COLLECTION_NAME, EMBEDDING_SIZE)
        
        # Insert data in batches
        logger.info("Inserting profiles into vector database...")
        batch_size = 50  # Qdrant batch size
        
        for i in range(0, len(profile_ids), batch_size):
            batch_ids = profile_ids[i:i + batch_size]
            batch_vectors = embeddings[i:i + batch_size]
            batch_payloads = payloads[i:i + batch_size]
            
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=models.Batch(
                    ids=batch_ids, 
                    vectors=batch_vectors, 
                    payloads=batch_payloads
                ),
                wait=True
            )
            logger.info(f"Inserted batch {i//batch_size + 1}/{(len(profile_ids) + batch_size - 1)//batch_size}")

        # Store the file hash for future change detection
        current_hash = get_json_file_hash()
        store_file_hash(COLLECTION_NAME, current_hash)
        
        # Verify insertion
        final_count = client.get_collection(COLLECTION_NAME).points_count
        logger.info(f"Successfully inserted {final_count} total points (including metadata) into vector database")
        
    except Exception as e:
        logger.error(f"Error during embedding generation or database insertion: {str(e)}")
        raise

def verify_database_integrity():
    """Verify that all profiles were inserted correctly"""
    try:
        collection_info = client.get_collection(COLLECTION_NAME)
        total_points = collection_info.points_count
        
        # Count metadata points
        metadata_count = 0
        try:
            scroll_result = client.scroll(
                collection_name=COLLECTION_NAME,
                limit=10,
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
            metadata_count = len(scroll_result[0])
        except Exception:
            pass
        
        profile_count = total_points - metadata_count
        
        logger.info(f"Database Verification:")
        logger.info(f"Collection: {COLLECTION_NAME}")
        logger.info(f"Total points: {total_points}")
        logger.info(f"Profile points: {profile_count}")
        logger.info(f"Metadata points: {metadata_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error verifying database: {str(e)}")
        return False

async def semantic_search(query: str, top_k: int = 20) -> list:
    """
    Async semantic vector search - used as part of hybrid search
    """
    try:
        # Use cached model for faster inference
        query_embedding = model.encode([query], show_progress_bar=False)[0].tolist()

        search_result = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=top_k,
            with_payload=True,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="is_metadata",
                        match=models.MatchValue(value=False)
                    )
                ]
            )
        )

        results = []
        for hit in search_result:
            results.append({
                "profile": hit.payload,
                "semantic_score": hit.score,
                "id": hit.id
            })
        return results
        
    except Exception as e:
        logger.error(f"Error during semantic search: {str(e)}")
        return []

async def hybrid_search(
    query: str, 
    top_k: int = 5,
    semantic_weight: float = 0.6,
    keyword_weight: float = 0.3,
    experience_weight: float = 0.1,
    min_semantic_score: float = 0.1
) -> List[Dict[str, Any]]:
    """
    Async hybrid search combining semantic similarity, keyword matching, and experience relevance.
    """
    # Get semantic search results (more candidates for better hybrid scoring)
    semantic_results = await semantic_search(query, top_k=min(50, top_k * 4))
    
    # Filter out results below minimum semantic threshold
    semantic_results = [r for r in semantic_results if r['semantic_score'] >= min_semantic_score]
    
    if not semantic_results:
        return []
    
    # Extract query keywords for keyword matching
    query_keywords = extract_keywords(query)
    
    # Calculate hybrid scores
    hybrid_results = []
    
    for result in semantic_results:
        profile = result['profile']
        semantic_score = result['semantic_score']
        
        # Calculate keyword matching score
        keyword_score = calculate_keyword_score(
            query_keywords, 
            profile.get('profile_text', ''), 
            profile
        )
        
        # Calculate experience relevance score
        experience_score = calculate_experience_score(
            query, 
            profile.get('years_of_experience', 0)
        )
        
        # Calculate weighted hybrid score
        hybrid_score = (
            semantic_weight * semantic_score +
            keyword_weight * keyword_score +
            experience_weight * experience_score
        )
        
        hybrid_results.append({
            "profile": profile,
            "semantic_score": semantic_score,
            "keyword_score": keyword_score,
            "experience_score": experience_score,
            "hybrid_score": hybrid_score,
            "id": result['id']
        })
    
    # Sort by hybrid score and return top results
    hybrid_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
    return hybrid_results[:top_k]

async def search_profiles(
    query: str,
    top_k: int = 5,
    search_type: str = "hybrid",
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Main async search function that supports both semantic and hybrid search
    """
    if search_type == "semantic":
        return await semantic_search(query, top_k)
    elif search_type == "hybrid":
        return await hybrid_search(query, top_k, **kwargs)
    else:
        raise ValueError("search_type must be 'semantic' or 'hybrid'")

def print_search_results(results: List[Dict[str, Any]], query: str, search_type: str = "hybrid"):
    """Helper function to print search results in a readable format"""
    logger.info(f"{search_type.capitalize()} search results for: '{query}'")
    
    if not results:
        logger.info("No results found.")
        return
    
    for i, result in enumerate(results, 1):
        profile = result["profile"]
        logger.info(f"{i}. {profile['name']} (@{profile['handle']})")
        
        if search_type == "hybrid":
            logger.info(f"   Hybrid Score: {result['hybrid_score']:.4f}")
        else:
            logger.info(f"   Semantic Score: {result['semantic_score']:.4f}")

# Initialize database when module is imported
try:
    if not client.collection_exists(COLLECTION_NAME):
        logger.info(f"Collection '{COLLECTION_NAME}' does not exist. Creating and loading data...")
        load_and_index_profiles()
    elif needs_database_update():
        logger.info(f"Database is out of date. Updating with latest profiles...")
        load_and_index_profiles()
    else:
        collection_info = client.get_collection(COLLECTION_NAME)
        total_points = collection_info.points_count
        logger.info(f"Using existing collection '{COLLECTION_NAME}' with {total_points} profiles (database up to date)")
except Exception as e:
    logger.error(f"Warning: Error checking or setting up collection: {str(e)}")
    logger.error("Search functionality may not work properly. Check your Qdrant server connection.")

if __name__ == "__main__":
    # This code only runs when the script is executed directly
    try:
        logger.info("Starting profile indexing process...")
        load_and_index_profiles(force_reload=True)  # Force reload for testing
        
        # Verify the database
        verify_database_integrity()
        
        logger.info(f"Collection '{COLLECTION_NAME}' is now set up with embedding size {EMBEDDING_SIZE}")
        logger.info("Database is ready for use with your frontend!")
        
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        import traceback
        traceback.print_exc()