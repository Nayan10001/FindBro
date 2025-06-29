import json
import os
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
import hashlib
import re
from typing import List, Dict, Any, Optional
from collections import Counter
import numpy as np

# Load SentenceTransformer model once
model = SentenceTransformer('all-MiniLM-L6-v2')
EMBEDDING_SIZE = model.get_sentence_embedding_dimension()

QDRANT_HOST = "http://localhost:6333"
STARTUPS_COLLECTION_NAME = "startups"

# Fix the path to make it work regardless of where the script is run from
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STARTUPS_DATA_FILE = os.path.join(PROJECT_ROOT, "backend", "data", "startups.json")

client = QdrantClient(url=QDRANT_HOST)


def generate_hash(text: str) -> int:
    """Generate a unique hash for each startup"""
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
        'startup', 'company', 'business', 'platform', 'solution', 'service',
        'mobile', 'app', 'apps', 'application', 'applications', 'game', 'games'
    }
    
    normalized = normalize_text(text)
    words = normalized.split()
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    return keywords


def extract_industry_from_description(description: str, alt_text: str = "") -> List[str]:
    """Extract industry/category information from description and alt text"""
    combined_text = f"{description} {alt_text}".lower()
    
    # Industry keyword mapping
    industry_keywords = {
        'gaming': ['game', 'games', 'gaming', 'mobile games', 'social games'],
        'mobile': ['mobile', 'app', 'apps', 'application', 'applications'],
        'social': ['social', 'viral', 'community', 'networking'],
        'entertainment': ['entertainment', 'fun', 'leisure', 'outrageous'],
        'software': ['software', 'technology', 'tech', 'development'],
        'media': ['media', 'content', 'digital'],
        'saas': ['saas', 'software as a service', 'platform'],
        'fintech': ['fintech', 'financial', 'banking', 'payment'],
        'healthcare': ['healthcare', 'health', 'medical', 'fitness'],
        'ecommerce': ['ecommerce', 'e-commerce', 'marketplace', 'retail', 'shopping'],
        'edtech': ['education', 'learning', 'training', 'teaching'],
        'ai': ['ai', 'artificial intelligence', 'machine learning', 'ml'],
        'blockchain': ['blockchain', 'crypto', 'cryptocurrency', 'bitcoin']
    }
    
    detected_industries = []
    for industry, keywords in industry_keywords.items():
        if any(keyword in combined_text for keyword in keywords):
            detected_industries.append(industry)
    
    return detected_industries if detected_industries else ['technology']


def extract_technologies_from_description(description: str, alt_text: str = "") -> List[str]:
    """Extract technology stack information from description and alt text"""
    combined_text = f"{description} {alt_text}".lower()
    
    tech_keywords = {
        'mobile': ['mobile', 'ios', 'android', 'app', 'smartphone'],
        'web': ['web', 'website', 'browser', 'html', 'css', 'javascript'],
        'social': ['social', 'social media', 'networking'],
        'gaming': ['gaming', 'game engine', 'unity', 'unreal'],
        'ai': ['ai', 'artificial intelligence', 'machine learning', 'ml', 'neural'],
        'cloud': ['cloud', 'aws', 'azure', 'google cloud'],
        'database': ['database', 'sql', 'nosql', 'mongodb'],
        'api': ['api', 'rest', 'graphql'],
        'blockchain': ['blockchain', 'smart contract', 'ethereum']
    }
    
    detected_technologies = []
    for tech, keywords in tech_keywords.items():
        if any(keyword in combined_text for keyword in keywords):
            detected_technologies.append(tech)
    
    return detected_technologies if detected_technologies else ['software']


def determine_stage_from_description(description: str) -> str:
    """Determine startup stage from description"""
    description_lower = description.lower()
    
    if any(word in description_lower for word in ['idea', 'concept', 'planning', 'prototype']):
        return 'idea'
    elif any(word in description_lower for word in ['mvp', 'beta', 'testing', 'development']):
        return 'mvp'
    elif any(word in description_lower for word in ['launch', 'launched', 'first', 'initial']):
        return 'seed'
    elif any(word in description_lower for word in ['growing', 'expansion', 'scale', 'users']):
        return 'series_a'
    elif any(word in description_lower for word in ['established', 'proven', 'successful']):
        return 'series_b'
    else:
        return 'unknown'


def calculate_startup_keyword_score(query_keywords: List[str], startup_text: str, startup_data: Dict) -> float:
    """Calculate keyword matching score between query and startup"""
    startup_keywords = extract_keywords(startup_text)
    
    # Also extract keywords from structured fields
    industries = startup_data.get('industries', [])
    technologies = startup_data.get('technologies', [])
    
    structured_text = " ".join([
        " ".join(industries) if isinstance(industries, list) else str(industries),
        " ".join(technologies) if isinstance(technologies, list) else str(technologies),
        startup_data.get('stage', ''),
        startup_data.get('city', ''),
        startup_data.get('alt', '')
    ])
    startup_keywords.extend(extract_keywords(structured_text))
    
    if not query_keywords or not startup_keywords:
        return 0.0
    
    # Calculate overlap score
    query_set = set(query_keywords)
    startup_set = set(startup_keywords)
    
    intersection = query_set.intersection(startup_set)
    union = query_set.union(startup_set)
    
    # Jaccard similarity with boost for exact matches
    jaccard_score = len(intersection) / len(union) if union else 0
    
    # Boost score for exact industry/technology matches
    exact_matches = 0
    industry_terms = [normalize_text(term) for term in industries if term]
    tech_terms = [normalize_text(tech) for tech in technologies if tech]
    
    for keyword in query_keywords:
        if keyword in industry_terms or keyword in tech_terms:
            exact_matches += 1
    
    exact_match_boost = exact_matches * 0.3
    
    return min(jaccard_score + exact_match_boost, 1.0)


def calculate_startup_stage_score(query: str, stage: str, funding_amount: Optional[float] = None) -> float:
    """Calculate startup stage/maturity relevance score based on query context"""
    query_lower = query.lower()
    stage_lower = stage.lower() if stage else ''
    
    # Map query intentions to preferred startup stages
    if any(word in query_lower for word in ['early', 'seed', 'mvp', 'prototype', 'new']):
        if stage_lower in ['seed', 'pre-seed', 'mvp', 'prototype', 'idea']:
            return 1.0
        elif stage_lower in ['series_a', 'early_stage']:
            return 0.8
        else:
            return 0.5
    elif any(word in query_lower for word in ['growth', 'scale', 'established', 'mature']):
        if stage_lower in ['series_b', 'series_c', 'growth', 'scale_up', 'established']:
            return 1.0
        elif stage_lower in ['series_a']:
            return 0.8
        else:
            return 0.6
    elif any(word in query_lower for word in ['funded', 'investment', 'venture']):
        if funding_amount and funding_amount > 0:
            return 1.0
        elif stage_lower in ['series_a', 'series_b', 'series_c', 'funded']:
            return 0.9
        else:
            return 0.4
    else:
        return 0.7  # Neutral score


def calculate_startup_market_score(query: str, startup_data: Dict) -> float:
    """Calculate market relevance score based on location and target demographics"""
    query_lower = query.lower()
    score = 0.0
    factors = 0
    
    # Location relevance
    city = startup_data.get('city', '').lower()
    if city:
        factors += 1
        if any(loc in query_lower for loc in ['global', 'international', 'worldwide']):
            if any(term in city for term in ['new york', 'san francisco', 'london', 'tel aviv']):
                score += 1.0
            else:
                score += 0.7
        elif any(region in city for region in query_lower.split()):
            score += 1.0
        else:
            score += 0.5
    
    # Target demographic relevance (extracted from alt text)
    alt_text = startup_data.get('alt', '').lower()
    if alt_text:
        factors += 1
        if any(demo in query_lower for demo in ['young', 'adult', 'teen', 'millennial']):
            if any(demo in alt_text for demo in ['young', 'adult', 'teen']):
                score += 1.0
            else:
                score += 0.6
        else:
            score += 0.5
    
    return score / factors if factors > 0 else 0.7


def ensure_startups_collection_exists(collection_name: str, embedding_size: int):
    """Create startups collection with proper error handling"""
    try:
        if client.collection_exists(collection_name):
            collection_info = client.get_collection(collection_name)
            if collection_info.config.params.vectors.size != embedding_size:
                print(f"Startups collection exists but with wrong vector size. Recreating...")
                client.delete_collection(collection_name)
            else:
                print(f"Startups collection '{collection_name}' already exists with correct configuration")
                return
        
        print(f"Creating startups collection '{collection_name}' with vector size {embedding_size}")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=embedding_size, 
                distance=models.Distance.COSINE
            )
        )
        print(f"Startups collection '{collection_name}' created successfully")
        
    except Exception as e:
        print(f"Error managing startups collection: {str(e)}")
        raise


def get_startups_file_hash() -> str:
    """Get hash of the startups JSON file to detect changes"""
    try:
        with open(STARTUPS_DATA_FILE, 'rb') as f:
            content = f.read()
            return hashlib.sha256(content).hexdigest()
    except Exception as e:
        print(f"Error reading startups JSON file for hash: {str(e)}")
        return ""


def get_stored_startups_file_hash(collection_name: str) -> str:
    """Get the stored startups file hash from collection metadata"""
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


def store_startups_file_hash(collection_name: str, file_hash: str):
    """Store the current startups file hash as metadata in the collection"""
    try:
        metadata_id = generate_hash("__startups_metadata__")
        client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=metadata_id,
                    vector=[0.0] * EMBEDDING_SIZE,
                    payload={
                        "is_metadata": True,
                        "file_hash": file_hash,
                        "last_updated": str(os.path.getmtime(STARTUPS_DATA_FILE))
                    }
                )
            ]
        )
    except Exception as e:
        print(f"Error storing startups file hash: {str(e)}")


def is_startups_collection_populated(collection_name: str) -> bool:
    """Check if startups collection has any non-metadata points"""
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
        
        actual_startups = total_points - metadata_count
        return actual_startups > 0
    except Exception as e:
        print(f"Error checking startups collection population: {str(e)}")
        return False


def needs_startups_database_update() -> bool:
    """Check if startups database needs to be updated based on file changes"""
    try:
        if not client.collection_exists(STARTUPS_COLLECTION_NAME):
            print("Startups collection doesn't exist - needs creation")
            return True
        
        if not is_startups_collection_populated(STARTUPS_COLLECTION_NAME):
            print("Startups collection is empty - needs population")
            return True
        
        current_hash = get_startups_file_hash()
        stored_hash = get_stored_startups_file_hash(STARTUPS_COLLECTION_NAME)
        
        if current_hash != stored_hash:
            print(f"Startups file has changed - needs update")
            return True
        
        print("Startups database is up to date")
        return False
        
    except Exception as e:
        print(f"Error checking if startups database needs update: {str(e)}")
        return True


def load_and_index_startups(force_reload: bool = False):
    """Load startups with better error handling and validation"""
    
    if not force_reload and not needs_startups_database_update():
        print("Startups database is already up to date. Skipping reload.")
        return
    
    try:
        print(f"Attempting to load startups data from: {STARTUPS_DATA_FILE}")
        with open(STARTUPS_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Successfully loaded {len(data)} startups from JSON file")
        
        if not isinstance(data, list):
            raise ValueError("Startups JSON data should be a list of startups")
            
        if len(data) == 0:
            raise ValueError("No startups found in JSON file")
            
    except FileNotFoundError:
        print(f"Error: Startups file not found at {STARTUPS_DATA_FILE}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error parsing startups JSON file: {str(e)}")
        raise
    except Exception as e:
        print(f"Unexpected error loading startups data: {str(e)}")
        raise

    # Ensure collection exists before processing
    ensure_startups_collection_exists(STARTUPS_COLLECTION_NAME, EMBEDDING_SIZE)
    
    startup_texts = []
    startup_ids = []
    payloads = []
    successful_startups = 0
    failed_startups = 0

    for i, startup in enumerate(data):
        try:
            # Handle the new data structure
            name = startup.get('name', f'Startup_{i}') or f'Startup_{i}'
            description = startup.get('description', '') or ''
            alt = startup.get('alt', '') or ''
            link = startup.get('link', '') or ''
            city = startup.get('city', '') or ''
            images = startup.get('images', '') or ''

            # Extract derived fields from description and alt text
            industries = extract_industry_from_description(description, alt)
            technologies = extract_technologies_from_description(description, alt)
            stage = determine_stage_from_description(description)

            # Create comprehensive startup text for embedding
            startup_text = (
                f"Name: {name}\n"
                f"Description: {description}\n"
                f"Alt Text: {alt}\n"
                f"Industries: {', '.join(industries)}\n"
                f"Technologies: {', '.join(technologies)}\n"
                f"Stage: {stage}\n"
                f"City: {city}\n"
                f"Link: {link}"
            )

            # Create a unique identifier
            unique_text = f"{startup_text}__{i}"
            startup_id = generate_hash(unique_text)
            
            # Check for duplicate IDs
            while startup_id in startup_ids:
                unique_text = f"{startup_text}__{i}_{len(startup_ids)}"
                startup_id = generate_hash(unique_text)
            
            startup_texts.append(startup_text)
            startup_ids.append(startup_id)
            
            # Create enhanced payload with derived fields
            enhanced_payload = {
                **startup,  # Include all original startup data
                "startup_text": startup_text,
                "original_index": i,
                "is_metadata": False,
                "industries": industries,
                "technologies": technologies,
                "stage": stage,
                # Add convenience fields for search
                "search_text": f"{name} {description} {alt} {' '.join(industries)} {' '.join(technologies)} {city}".lower()
            }
            
            payloads.append(enhanced_payload)
            successful_startups += 1
            
        except Exception as e:
            print(f"Error processing startup {i}: {str(e)}")
            print(f"Startup data: {startup}")
            failed_startups += 1
            continue

    print(f"Processed {successful_startups} startups successfully, {failed_startups} failed")
    
    if successful_startups == 0:
        raise ValueError("No startups could be processed successfully")

    try:
        # Generate embeddings
        print("Generating startup embeddings...")
        embeddings = model.encode(startup_texts)
        embeddings = [emb.tolist() for emb in embeddings]
        print(f"Generated {len(embeddings)} startup embeddings")
        
        # Clear existing data and insert new data
        print("Clearing existing startups collection data...")
        if client.collection_exists(STARTUPS_COLLECTION_NAME):
            client.delete_collection(STARTUPS_COLLECTION_NAME)
        ensure_startups_collection_exists(STARTUPS_COLLECTION_NAME, EMBEDDING_SIZE)
        
        # Insert data
        print("Inserting startups into vector database...")
        client.upsert(
            collection_name=STARTUPS_COLLECTION_NAME,
            points=models.Batch(
                ids=startup_ids, 
                vectors=embeddings, 
                payloads=payloads
            ),
            wait=True
        )

        # Store the file hash
        current_hash = get_startups_file_hash()
        store_startups_file_hash(STARTUPS_COLLECTION_NAME, current_hash)
        
        # Verify insertion
        final_count = client.get_collection(STARTUPS_COLLECTION_NAME).points_count
        print(f"Successfully inserted {final_count} total points into startups database")
        
    except Exception as e:
        print(f"Error during startup embedding generation or database insertion: {str(e)}")
        raise


def semantic_search_startups(query: str, top_k: int = 20) -> list:
    """Pure semantic vector search for startups"""
    try:
        query_embedding = model.encode(query).tolist()

        search_result = client.search(
            collection_name=STARTUPS_COLLECTION_NAME,
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
                "startup": hit.payload,
                "semantic_score": hit.score,
                "id": hit.id
            })
        return results
        
    except Exception as e:
        print(f"Error during startup semantic search: {str(e)}")
        return []


def hybrid_search_startups(
    query: str, 
    top_k: int = 5,
    semantic_weight: float = 0.6,
    keyword_weight: float = 0.2,
    stage_weight: float = 0.1,
    market_weight: float = 0.1,
    min_semantic_score: float = 0.1
) -> List[Dict[str, Any]]:
    """Hybrid search for startups combining semantic similarity, keyword matching, stage relevance, and market fit"""
    
    # Get semantic search results
    semantic_results = semantic_search_startups(query, top_k=min(50, top_k * 4))
    
    # Filter out results below minimum semantic threshold
    semantic_results = [r for r in semantic_results if r['semantic_score'] >= min_semantic_score]
    
    if not semantic_results:
        return []
    
    # Extract query keywords
    query_keywords = extract_keywords(query)
    
    # Calculate hybrid scores
    hybrid_results = []
    
    for result in semantic_results:
        startup = result['startup']
        semantic_score = result['semantic_score']
        
        # Calculate keyword matching score
        keyword_score = calculate_startup_keyword_score(
            query_keywords, 
            startup.get('startup_text', ''), 
            startup
        )
        
        # Calculate stage relevance score
        stage_score = calculate_startup_stage_score(
            query, 
            startup.get('stage', ''),
            None  # No funding amount in current data structure
        )
        
        # Calculate market relevance score
        market_score = calculate_startup_market_score(query, startup)
        
        # Calculate weighted hybrid score
        hybrid_score = (
            semantic_weight * semantic_score +
            keyword_weight * keyword_score +
            stage_weight * stage_score +
            market_weight * market_score
        )
        
        hybrid_results.append({
            "startup": startup,
            "semantic_score": semantic_score,
            "keyword_score": keyword_score,
            "stage_score": stage_score,
            "market_score": market_score,
            "hybrid_score": hybrid_score,
            "id": result['id']
        })
    
    # Sort by hybrid score and return top results
    hybrid_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
    return hybrid_results[:top_k]


def search_startups(
    query: str,
    top_k: int = 5,
    search_type: str = "hybrid",
    **kwargs
) -> List[Dict[str, Any]]:
    """Main startup search function that supports both semantic and hybrid search"""
    if search_type == "semantic":
        return semantic_search_startups(query, top_k)
    elif search_type == "hybrid":
        return hybrid_search_startups(query, top_k, **kwargs)
    else:
        raise ValueError("search_type must be 'semantic' or 'hybrid'")


def verify_startups_database_integrity():
    """Verify that all startups were inserted correctly"""
    try:
        collection_info = client.get_collection(STARTUPS_COLLECTION_NAME)
        total_points = collection_info.points_count
        
        # Count metadata points
        metadata_count = 0
        try:
            scroll_result = client.scroll(
                collection_name=STARTUPS_COLLECTION_NAME,
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
        
        startup_count = total_points - metadata_count
        
        print(f"\nStartups Database Verification:")
        print(f"Collection: {STARTUPS_COLLECTION_NAME}")
        print(f"Total points: {total_points}")
        print(f"Startup points: {startup_count}")
        print(f"Metadata points: {metadata_count}")
        
        # Sample a few startups
        sample_results = client.scroll(
            collection_name=STARTUPS_COLLECTION_NAME,
            limit=3,
            with_payload=True,
            with_vectors=False,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="is_metadata",
                        match=models.MatchValue(value=False)
                    )
                ]
            )
        )
        
        print(f"\nSample startups:")
        for i, point in enumerate(sample_results[0], 1):
            payload = point.payload
            print(f"{i}. {payload.get('name', 'N/A')}")
            print(f"   Industries: {', '.join(payload.get('industries', []))}")
            print(f"   Stage: {payload.get('stage', 'N/A')}")
            print(f"   City: {payload.get('city', 'N/A')}")
            print(f"   Technologies: {', '.join(payload.get('technologies', []))}")
        
        return True
        
    except Exception as e:
        print(f"Error verifying startups database: {str(e)}")
        return False


# Initialize startups database when module is imported
try:
    if not client.collection_exists(STARTUPS_COLLECTION_NAME):
        print(f"Startups collection '{STARTUPS_COLLECTION_NAME}' does not exist. Creating and loading data...")
        load_and_index_startups()
    elif needs_startups_database_update():
        print(f"Startups database is out of date. Updating with latest startups...")
        load_and_index_startups()
    else:
        collection_info = client.get_collection(STARTUPS_COLLECTION_NAME)
        total_points = collection_info.points_count
        print(f"Using existing startups collection '{STARTUPS_COLLECTION_NAME}' with {total_points} startups")
except Exception as e:
    print(f"Warning: Error checking or setting up startups collection: {str(e)}")
    print("Startup search functionality may not work properly.")


if __name__ == "__main__":
    try:
        print("Starting startups indexing process...")
        load_and_index_startups(force_reload=True)
        verify_startups_database_integrity()
        print(f"\nStartups collection '{STARTUPS_COLLECTION_NAME}' is ready!")
        
        # Test search functionality
        print("\n" + "="*50)
        print("Testing startup search functionality...")
        
        test_queries = [
            "mobile gaming startups",
            "social games young adults",
            "viral mobile apps",
            "Tel Aviv startups",
            "entertainment mobile apps"
        ]
        
        for query in test_queries:
            print(f"\nTesting query: '{query}'")
            results = search_startups(query, top_k=3, search_type="hybrid")
            print(f"Found {len(results)} results")
            
            for i, result in enumerate(results, 1):
                startup = result['startup']
                print(f"  {i}. {startup.get('name', 'N/A')} - Score: {result['hybrid_score']:.3f}")
                print(f"     Industries: {', '.join(startup.get('industries', []))}")
                print(f"     Stage: {startup.get('stage', 'N/A')}")
                print(f"     City: {startup.get('city', 'N/A')}")
        
    except Exception as e:
        print(f"Error during execution: {str(e)}")
        import traceback
        traceback.print_exc()