from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import sys
import pathlib
from typing import Optional, List, Dict, Any
import asyncio
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the app directory to the path so we can import the search modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the enhanced search functionality
from search import search_profiles, verify_database_integrity
from project_search import search_projects, verify_projects_database_integrity

app = FastAPI(
    title="FindBro API", 
    description="AI-Powered Developer Search Platform",
    version="1.0.0"
)

# Configure CORS with more specific settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:5173", 
        "http://127.0.0.1:3000", 
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Define paths
current_dir = pathlib.Path(__file__).parent.absolute()
project_root = current_dir.parent
frontend_build_dir = project_root / "frontend" / "dist"

logger.info(f"Project root: {project_root}")
logger.info(f"Frontend build directory: {frontend_build_dir}")

def format_search_results(results: List[Dict[str, Any]], search_type: str = "hybrid") -> List[Dict[str, Any]]:
    """Format search results for API response"""
    formatted_results = []
    
    for item in results:
        profile = item["profile"]
        
        # Handle different score types based on search method
        if search_type == "hybrid":
            score = item.get("hybrid_score", 0.0)
            score_details = {
                "hybrid_score": item.get("hybrid_score", 0.0),
                "semantic_score": item.get("semantic_score", 0.0),
                "keyword_score": item.get("keyword_score", 0.0),
                "experience_score": item.get("experience_score", 0.0)
            }
        else:  # semantic search
            score = item.get("semantic_score", 0.0)
            score_details = {
                "semantic_score": score
            }
        
        formatted_results.append({
            "name": profile.get("name", "N/A"),
            "handle": profile.get("handle", "N/A"),
            "skills": profile.get("skill_tags", []),
            "experience": profile.get("years_of_experience", 0),
            "roles": profile.get("preferred_roles", []),
            "timezone": profile.get("availability_timezone", "N/A"),
            "interests": profile.get("project_interests", []),
            "score": round(score, 4),
            "score_details": score_details,
            "id": item.get("id")
        })
    
    return formatted_results

def format_project_search_results(results: List[Dict[str, Any]], search_type: str = "hybrid") -> List[Dict[str, Any]]:
    """Format project search results for API response"""
    formatted_results = []
    
    for item in results:
        project = item["project"]
        
        # Handle different score types based on search method
        if search_type == "hybrid":
            score = item.get("hybrid_score", 0.0)
            score_details = {
                "hybrid_score": item.get("hybrid_score", 0.0),
                "semantic_score": item.get("semantic_score", 0.0),
                "keyword_score": item.get("keyword_score", 0.0),
                "status_score": item.get("status_score", 0.0)
            }
        else:  # semantic search
            score = item.get("semantic_score", 0.0)
            score_details = {
                "semantic_score": score
            }
        
        formatted_results.append({
            "id": project.get("id"),
            "title": project.get("title", "N/A"),
            "description": project.get("description", ""),
            "owner": project.get("owner", {}),
            "status": project.get("status", "unknown"),
            "tech_stack": project.get("tech_stack", []),
            "looking_for": project.get("looking_for", []),
            "project_type": project.get("project_type", ""),
            "category": project.get("category", ""),
            "timeline": project.get("timeline", ""),
            "commitment": project.get("commitment", ""),
            "experience_level": project.get("experience_level", ""),
            "tags": project.get("tags", []),
            "github_url": project.get("github_url"),
            "demo_url": project.get("demo_url"),
            "team_size": project.get("team_size", 0),
            "current_contributors": project.get("current_contributors", 0),
            "created_at": project.get("created_at", ""),
            "score": round(score, 4),
            "score_details": score_details
        })
    
    return formatted_results

@app.get("/api/search")
async def search_profiles_endpoint(
    query: str = Query(..., description="Search query to find matching developer profiles"),
    limit: int = Query(5, description="Maximum number of results to return", ge=1, le=20),
    search_type: str = Query("hybrid", description="Search type: 'semantic' or 'hybrid'"),
    semantic_weight: float = Query(0.6, description="Weight for semantic similarity in hybrid search", ge=0.0, le=1.0),
    keyword_weight: float = Query(0.3, description="Weight for keyword matching in hybrid search", ge=0.0, le=1.0),
    experience_weight: float = Query(0.1, description="Weight for experience relevance in hybrid search", ge=0.0, le=1.0)
):
    """
    Search for developer profiles based on the query string.
    
    Supports both semantic and hybrid search methods:
    - semantic: Uses only vector similarity
    - hybrid: Combines semantic similarity, keyword matching, and experience relevance
    """
    start_time = time.time()
    
    try:
        # Validate query
        if not query or query.strip() == "":
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Validate search type
        if search_type not in ["semantic", "hybrid"]:
            raise HTTPException(status_code=400, detail="search_type must be 'semantic' or 'hybrid'")
        
        # Validate weights sum to approximately 1.0 for hybrid search
        if search_type == "hybrid":
            total_weight = semantic_weight + keyword_weight + experience_weight
            if abs(total_weight - 1.0) > 0.1:  # Allow small tolerance
                raise HTTPException(
                    status_code=400, 
                    detail=f"Weights should sum to 1.0, got {total_weight}"
                )
        
        logger.info(f"Search request: query='{query}', type={search_type}, limit={limit}")
        
        # Perform the search using the enhanced search function
        if search_type == "hybrid":
            results = await search_profiles(
                query=query,
                top_k=limit,
                search_type="hybrid",
                semantic_weight=semantic_weight,
                keyword_weight=keyword_weight,
                experience_weight=experience_weight
            )
        else:
            results = await search_profiles(
                query=query,
                top_k=limit,
                search_type="semantic"
            )
        
        # Format the results for the API response
        formatted_results = format_search_results(results, search_type)
        
        processing_time = time.time() - start_time
        logger.info(f"Search completed in {processing_time:.2f}s")
        
        response = {
            "status": "success",
            "query": query.strip(),
            "search_type": search_type,
            "result_count": len(formatted_results),
            "processing_time": round(processing_time, 3),
            "results": formatted_results
        }
        
        # Add search parameters for hybrid search
        if search_type == "hybrid":
            response["search_parameters"] = {
                "semantic_weight": semantic_weight,
                "keyword_weight": keyword_weight,
                "experience_weight": experience_weight
            }
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error in search after {processing_time:.2f}s: {str(e)}")
        
        # Return error response instead of raising exception
        return {
            "status": "error",
            "message": f"Search failed: {str(e)}",
            "query": query if 'query' in locals() else None,
            "result_count": 0,
            "processing_time": round(processing_time, 3),
            "results": []
        }

@app.get("/api/search/projects")
async def search_projects_endpoint(
    query: str = Query(..., description="Search query to find matching projects"),
    limit: int = Query(8, description="Maximum number of results to return", ge=1, le=20),
    search_type: str = Query("hybrid", description="Search type: 'semantic' or 'hybrid'"),
    semantic_weight: float = Query(0.7, description="Weight for semantic similarity in hybrid search", ge=0.0, le=1.0),
    keyword_weight: float = Query(0.2, description="Weight for keyword matching in hybrid search", ge=0.0, le=1.0),
    status_weight: float = Query(0.1, description="Weight for status relevance in hybrid search", ge=0.0, le=1.0)
):
    """
    Search for projects based on the query string.
    
    Supports both semantic and hybrid search methods:
    - semantic: Uses only vector similarity
    - hybrid: Combines semantic similarity, keyword matching, and status relevance
    """
    start_time = time.time()
    
    try:
        # Validate query
        if not query or query.strip() == "":
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Validate search type
        if search_type not in ["semantic", "hybrid"]:
            raise HTTPException(status_code=400, detail="search_type must be 'semantic' or 'hybrid'")
        
        # Validate weights sum to approximately 1.0 for hybrid search
        if search_type == "hybrid":
            total_weight = semantic_weight + keyword_weight + status_weight
            if abs(total_weight - 1.0) > 0.1:  # Allow small tolerance
                raise HTTPException(
                    status_code=400, 
                    detail=f"Weights should sum to 1.0, got {total_weight}"
                )
        
        logger.info(f"Project search request: query='{query}', type={search_type}, limit={limit}")
        
        # Perform the project search
        if search_type == "hybrid":
            results = await search_projects(
                query=query,
                top_k=limit,
                search_type="hybrid",
                semantic_weight=semantic_weight,
                keyword_weight=keyword_weight,
                status_weight=status_weight
            )
        else:
            results = await search_projects(
                query=query,
                top_k=limit,
                search_type="semantic"
            )
        
        # Format the results for the API response
        formatted_results = format_project_search_results(results, search_type)
        
        processing_time = time.time() - start_time
        logger.info(f"Project search completed in {processing_time:.2f}s")
        
        response = {
            "status": "success",
            "query": query.strip(),
            "search_type": search_type,
            "result_count": len(formatted_results),
            "processing_time": round(processing_time, 3),
            "results": formatted_results
        }
        
        # Add search parameters for hybrid search
        if search_type == "hybrid":
            response["search_parameters"] = {
                "semantic_weight": semantic_weight,
                "keyword_weight": keyword_weight,
                "status_weight": status_weight
            }
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error in project search after {processing_time:.2f}s: {str(e)}")
        
        # Return error response instead of raising exception
        return {
            "status": "error",
            "message": f"Project search failed: {str(e)}",
            "query": query if 'query' in locals() else None,
            "result_count": 0,
            "processing_time": round(processing_time, 3),
            "results": []
        }

@app.get("/api/stats")
async def get_database_stats():
    """Get database statistics and verify integrity."""
    try:
        # Check both profiles and projects databases
        profiles_healthy = verify_database_integrity()
        projects_healthy = verify_projects_database_integrity()
        
        return {
            "status": "success",
            "profiles_database_healthy": profiles_healthy,
            "projects_database_healthy": projects_healthy,
            "overall_healthy": profiles_healthy and projects_healthy,
            "message": "Database statistics retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to get database stats: {str(e)}",
            "profiles_database_healthy": False,
            "projects_database_healthy": False,
            "overall_healthy": False
        }

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    try:
        # Test database connectivity by checking if we can get stats
        profiles_healthy = verify_database_integrity()
        projects_healthy = verify_projects_database_integrity()
        
        return {
            "status": "healthy",
            "profiles_database": "connected" if profiles_healthy else "disconnected",
            "projects_database": "connected" if projects_healthy else "disconnected",
            "api": "operational",
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "degraded",
            "profiles_database": "error",
            "projects_database": "error",
            "api": "operational",
            "error": str(e),
            "timestamp": time.time()
        }

# Serve React app static files (only if built)
if frontend_build_dir.exists():
    app.mount("/static", StaticFiles(directory=frontend_build_dir / "assets"), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        """Serve React app for all non-API routes"""
        # Don't serve React app for API routes
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        
        # Serve index.html for all other routes (React Router will handle routing)
        return FileResponse(frontend_build_dir / "index.html")
    
    @app.get("/")
    async def read_root():
        """Serve the main React app"""
        return FileResponse(frontend_build_dir / "index.html")
else:
    @app.get("/")
    async def read_root():
        """Development message when React app is not built"""
        return {
            "message": "FindBro API is running",
            "status": "Backend ready",
            "note": "React frontend not built. Run 'npm run build' in the frontend directory to serve the full application.",
            "api_docs": "http://localhost:8000/docs"
        }

# Add startup event to verify database
@app.on_event("startup")
async def startup_event():
    """Verify database connection on startup."""
    try:
        logger.info("Verifying database connections...")
        profiles_healthy = verify_database_integrity()
        projects_healthy = verify_projects_database_integrity()
        
        if profiles_healthy:
            logger.info("✅ Profiles database connection verified successfully")
        else:
            logger.warning("⚠️ Profiles database connection issues detected")
            
        if projects_healthy:
            logger.info("✅ Projects database connection verified successfully")
        else:
            logger.warning("⚠️ Projects database connection issues detected")
            
    except Exception as e:
        logger.error(f"❌ Database verification failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting FindBro API server...")
    logger.info(f"Frontend build directory: {frontend_build_dir}")
    
    # Check if frontend is built
    if frontend_build_dir.exists():
        logger.info(f"✅ Frontend build found. Full-stack app will be served.")
    else:
        logger.warning(f"⚠️ Frontend not built. Only API will be available.")
        logger.info(f"To build frontend: cd frontend && npm run build")
    
    logger.info("\nAvailable endpoints:")
    logger.info("- GET  /api/search (hybrid/semantic search for profiles)")
    logger.info("- GET  /api/search/projects (hybrid/semantic search for projects)")
    logger.info("- GET  /api/stats (database statistics)")
    logger.info("- GET  /health (health check)")
    logger.info("- GET  /docs (API documentation)")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        workers=1,  # Single worker for development
        access_log=True,
        log_level="info"
    )