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
PROJECTS_COLLECTION_NAME = "projects"

# Fix the path to make it work regardless of where the script is run from
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROJECTS_DATA_FILE = os.path.join(PROJECT_ROOT, "backend", "data", "projects.json")

client = QdrantClient(url=QDRANT_HOST)


def generate_hash(text: str) -> int:
    """Generate a unique hash for each project"""
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
        'looking', 'need', 'want', 'seeking', 'project', 'platform', 'app'
    }
    
    normalized = normalize_text(text)
    words = normalized.split()
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    return keywords


def calculate_project_keyword_score(query_keywords: List[str], project_text: str, project_data: Dict) -> float:
    """Calculate keyword matching score between query and project"""
    project_keywords = extract_keywords(project_text)
    
    # Also extract keywords from structured fields
    structured_text = " ".join([
        " ".join(project_data.get('tech_stack', [])),
        " ".join(project_data.get('looking_for', [])),
        " ".join(project_data.get('tags', [])),
        project_data.get('category', ''),
        project_data.get('project_type', ''),
        project_data.get('status', '')
    ])
    project_keywords.extend(extract_keywords(structured_text))
    
    if not query_keywords or not project_keywords:
        return 0.0
    
    # Calculate overlap score
    query_set = set(query_keywords)
    project_set = set(project_keywords)
    
    intersection = query_set.intersection(project_set)
    union = query_set.union(project_set)
    
    # Jaccard similarity with boost for exact matches
    jaccard_score = len(intersection) / len(union) if union else 0
    
    # Boost score for exact tech stack/category matches
    exact_matches = 0
    tech_stack = [normalize_text(tech) for tech in project_data.get('tech_stack', [])]
    categories = [normalize_text(project_data.get('category', ''))]
    
    for keyword in query_keywords:
        if keyword in tech_stack or keyword in categories:
            exact_matches += 1
    
    exact_match_boost = exact_matches * 0.3
    
    return min(jaccard_score + exact_match_boost, 1.0)


def calculate_project_status_score(query: str, status: str) -> float:
    """Calculate project status relevance score based on query context"""
    query_lower = query.lower()
    status_lower = status.lower()
    
    # Map query intentions to preferred project statuses
    if any(word in query_lower for word in ['contribute', 'join', 'help']):
        if status_lower in ['seeking_contributors', 'active_development']:
            return 1.0
        elif status_lower in ['beta_testing', 'prototype']:
            return 0.8
        else:
            return 0.5
    elif any(word in query_lower for word in ['complete', 'finished', 'demo']):
        if status_lower in ['mvp_complete', 'beta_testing']:
            return 1.0
        else:
            return 0.6
    else:
        return 0.7  # Neutral score


def ensure_projects_collection_exists(collection_name: str, embedding_size: int):
    """Create projects collection with proper error handling"""
    try:
        if client.collection_exists(collection_name):
            collection_info = client.get_collection(collection_name)
            if collection_info.config.params.vectors.size != embedding_size:
                print(f"Projects collection exists but with wrong vector size. Recreating...")
                client.delete_collection(collection_name)
            else:
                print(f"Projects collection '{collection_name}' already exists with correct configuration")
                return
        
        print(f"Creating projects collection '{collection_name}' with vector size {embedding_size}")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=embedding_size, 
                distance=models.Distance.COSINE
            )
        )
        print(f"Projects collection '{collection_name}' created successfully")
        
    except Exception as e:
        print(f"Error managing projects collection: {str(e)}")
        raise


def get_projects_file_hash() -> str:
    """Get hash of the projects JSON file to detect changes"""
    try:
        with open(PROJECTS_DATA_FILE, 'rb') as f:
            content = f.read()
            return hashlib.sha256(content).hexdigest()
    except Exception as e:
        print(f"Error reading projects JSON file for hash: {str(e)}")
        return ""


def get_stored_projects_file_hash(collection_name: str) -> str:
    """Get the stored projects file hash from collection metadata"""
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


def store_projects_file_hash(collection_name: str, file_hash: str):
    """Store the current projects file hash as metadata in the collection"""
    try:
        metadata_id = generate_hash("__projects_metadata__")
        client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=metadata_id,
                    vector=[0.0] * EMBEDDING_SIZE,
                    payload={
                        "is_metadata": True,
                        "file_hash": file_hash,
                        "last_updated": str(os.path.getmtime(PROJECTS_DATA_FILE))
                    }
                )
            ]
        )
    except Exception as e:
        print(f"Error storing projects file hash: {str(e)}")


def is_projects_collection_populated(collection_name: str) -> bool:
    """Check if projects collection has any non-metadata points"""
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
        
        actual_projects = total_points - metadata_count
        return actual_projects > 0
    except Exception as e:
        print(f"Error checking projects collection population: {str(e)}")
        return False


def needs_projects_database_update() -> bool:
    """Check if projects database needs to be updated based on file changes"""
    try:
        if not client.collection_exists(PROJECTS_COLLECTION_NAME):
            print("Projects collection doesn't exist - needs creation")
            return True
        
        if not is_projects_collection_populated(PROJECTS_COLLECTION_NAME):
            print("Projects collection is empty - needs population")
            return True
        
        current_hash = get_projects_file_hash()
        stored_hash = get_stored_projects_file_hash(PROJECTS_COLLECTION_NAME)
        
        if current_hash != stored_hash:
            print(f"Projects file has changed - needs update")
            return True
        
        print("Projects database is up to date")
        return False
        
    except Exception as e:
        print(f"Error checking if projects database needs update: {str(e)}")
        return True


def load_and_index_projects(force_reload: bool = False):
    """Load projects with better error handling and validation"""
    
    if not force_reload and not needs_projects_database_update():
        print("Projects database is already up to date. Skipping reload.")
        return
    
    try:
        print(f"Attempting to load projects data from: {PROJECTS_DATA_FILE}")
        with open(PROJECTS_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Successfully loaded {len(data)} projects from JSON file")
        
        if not isinstance(data, list):
            raise ValueError("Projects JSON data should be a list of projects")
            
        if len(data) == 0:
            raise ValueError("No projects found in JSON file")
            
    except FileNotFoundError:
        print(f"Error: Projects file not found at {PROJECTS_DATA_FILE}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error parsing projects JSON file: {str(e)}")
        raise
    except Exception as e:
        print(f"Unexpected error loading projects data: {str(e)}")
        raise

    # Ensure collection exists before processing
    ensure_projects_collection_exists(PROJECTS_COLLECTION_NAME, EMBEDDING_SIZE)
    
    project_texts = []
    project_ids = []
    payloads = []
    successful_projects = 0
    failed_projects = 0

    for i, project in enumerate(data):
        try:
            # Handle missing or None values gracefully
            title = project.get('title', f'Project_{i}') or f'Project_{i}'
            description = project.get('description', '') or ''
            owner = project.get('owner', {}) or {}
            tech_stack = project.get('tech_stack', []) or []
            looking_for = project.get('looking_for', []) or []
            category = project.get('category', 'Other') or 'Other'
            tags = project.get('tags', []) or []

            # Ensure all fields are proper types
            if not isinstance(tech_stack, list):
                tech_stack = []
            if not isinstance(looking_for, list):
                looking_for = []
            if not isinstance(tags, list):
                tags = []

            project_text = (
                f"Title: {title}\nDescription: {description}\n"
                f"Tech Stack: {', '.join(tech_stack)}\nLooking For: {', '.join(looking_for)}\n"
                f"Category: {category}\nTags: {', '.join(tags)}\n"
                f"Owner: {owner.get('name', 'Unknown')}"
            )

            # Create a unique identifier
            unique_text = f"{project_text}__{i}"
            project_id = generate_hash(unique_text)
            
            # Check for duplicate IDs
            while project_id in project_ids:
                unique_text = f"{project_text}__{i}_{len(project_ids)}"
                project_id = generate_hash(unique_text)
            
            project_texts.append(project_text)
            project_ids.append(project_id)
            payloads.append({
                **project,  # Include all original project data
                "project_text": project_text,
                "original_index": i,
                "is_metadata": False
            })
            successful_projects += 1
            
        except Exception as e:
            print(f"Error processing project {i}: {str(e)}")
            print(f"Project data: {project}")
            failed_projects += 1
            continue

    print(f"Processed {successful_projects} projects successfully, {failed_projects} failed")
    
    if successful_projects == 0:
        raise ValueError("No projects could be processed successfully")

    try:
        # Generate embeddings
        print("Generating project embeddings...")
        embeddings = model.encode(project_texts)
        embeddings = [emb.tolist() for emb in embeddings]
        print(f"Generated {len(embeddings)} project embeddings")
        
        # Clear existing data and insert new data
        print("Clearing existing projects collection data...")
        if client.collection_exists(PROJECTS_COLLECTION_NAME):
            client.delete_collection(PROJECTS_COLLECTION_NAME)
        ensure_projects_collection_exists(PROJECTS_COLLECTION_NAME, EMBEDDING_SIZE)
        
        # Insert data
        print("Inserting projects into vector database...")
        client.upsert(
            collection_name=PROJECTS_COLLECTION_NAME,
            points=models.Batch(
                ids=project_ids, 
                vectors=embeddings, 
                payloads=payloads
            ),
            wait=True
        )

        # Store the file hash
        current_hash = get_projects_file_hash()
        store_projects_file_hash(PROJECTS_COLLECTION_NAME, current_hash)
        
        # Verify insertion
        final_count = client.get_collection(PROJECTS_COLLECTION_NAME).points_count
        print(f"Successfully inserted {final_count} total points into projects database")
        
    except Exception as e:
        print(f"Error during project embedding generation or database insertion: {str(e)}")
        raise


def semantic_search_projects(query: str, top_k: int = 20) -> list:
    """Pure semantic vector search for projects"""
    try:
        query_embedding = model.encode(query).tolist()

        search_result = client.search(
            collection_name=PROJECTS_COLLECTION_NAME,
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
                "project": hit.payload,
                "semantic_score": hit.score,
                "id": hit.id
            })
        return results
        
    except Exception as e:
        print(f"Error during project semantic search: {str(e)}")
        return []


def hybrid_search_projects(
    query: str, 
    top_k: int = 5,
    semantic_weight: float = 0.7,
    keyword_weight: float = 0.2,
    status_weight: float = 0.1,
    min_semantic_score: float = 0.1
) -> List[Dict[str, Any]]:
    """Hybrid search for projects combining semantic similarity, keyword matching, and status relevance"""
    
    # Get semantic search results
    semantic_results = semantic_search_projects(query, top_k=min(50, top_k * 4))
    
    # Filter out results below minimum semantic threshold
    semantic_results = [r for r in semantic_results if r['semantic_score'] >= min_semantic_score]
    
    if not semantic_results:
        return []
    
    # Extract query keywords
    query_keywords = extract_keywords(query)
    
    # Calculate hybrid scores
    hybrid_results = []
    
    for result in semantic_results:
        project = result['project']
        semantic_score = result['semantic_score']
        
        # Calculate keyword matching score
        keyword_score = calculate_project_keyword_score(
            query_keywords, 
            project.get('project_text', ''), 
            project
        )
        
        # Calculate status relevance score
        status_score = calculate_project_status_score(
            query, 
            project.get('status', '')
        )
        
        # Calculate weighted hybrid score
        hybrid_score = (
            semantic_weight * semantic_score +
            keyword_weight * keyword_score +
            status_weight * status_score
        )
        
        hybrid_results.append({
            "project": project,
            "semantic_score": semantic_score,
            "keyword_score": keyword_score,
            "status_score": status_score,
            "hybrid_score": hybrid_score,
            "id": result['id']
        })
    
    # Sort by hybrid score and return top results
    hybrid_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
    return hybrid_results[:top_k]


def search_projects(
    query: str,
    top_k: int = 5,
    search_type: str = "hybrid",
    **kwargs
) -> List[Dict[str, Any]]:
    """Main project search function that supports both semantic and hybrid search"""
    if search_type == "semantic":
        return semantic_search_projects(query, top_k)
    elif search_type == "hybrid":
        return hybrid_search_projects(query, top_k, **kwargs)
    else:
        raise ValueError("search_type must be 'semantic' or 'hybrid'")


def verify_projects_database_integrity():
    """Verify that all projects were inserted correctly"""
    try:
        collection_info = client.get_collection(PROJECTS_COLLECTION_NAME)
        total_points = collection_info.points_count
        
        # Count metadata points
        metadata_count = 0
        try:
            scroll_result = client.scroll(
                collection_name=PROJECTS_COLLECTION_NAME,
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
        
        project_count = total_points - metadata_count
        
        print(f"\nProjects Database Verification:")
        print(f"Collection: {PROJECTS_COLLECTION_NAME}")
        print(f"Total points: {total_points}")
        print(f"Project points: {project_count}")
        print(f"Metadata points: {metadata_count}")
        
        # Sample a few projects
        sample_results = client.scroll(
            collection_name=PROJECTS_COLLECTION_NAME,
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
        
        print(f"\nSample projects:")
        for i, point in enumerate(sample_results[0], 1):
            payload = point.payload
            print(f"{i}. {payload.get('title', 'N/A')}")
            print(f"   Owner: {payload.get('owner', {}).get('name', 'N/A')}")
            print(f"   Tech: {', '.join(payload.get('tech_stack', []))}")
            print(f"   Status: {payload.get('status', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"Error verifying projects database: {str(e)}")
        return False


# Initialize projects database when module is imported
try:
    if not client.collection_exists(PROJECTS_COLLECTION_NAME):
        print(f"Projects collection '{PROJECTS_COLLECTION_NAME}' does not exist. Creating and loading data...")
        load_and_index_projects()
    elif needs_projects_database_update():
        print(f"Projects database is out of date. Updating with latest projects...")
        load_and_index_projects()
    else:
        collection_info = client.get_collection(PROJECTS_COLLECTION_NAME)
        total_points = collection_info.points_count
        print(f"Using existing projects collection '{PROJECTS_COLLECTION_NAME}' with {total_points} projects")
except Exception as e:
    print(f"Warning: Error checking or setting up projects collection: {str(e)}")
    print("Project search functionality may not work properly.")


if __name__ == "__main__":
    try:
        print("Starting projects indexing process...")
        load_and_index_projects(force_reload=True)
        verify_projects_database_integrity()
        print(f"\nProjects collection '{PROJECTS_COLLECTION_NAME}' is ready!")
        
    except Exception as e:
        print(f"Error during execution: {str(e)}")
        import traceback
        traceback.print_exc()