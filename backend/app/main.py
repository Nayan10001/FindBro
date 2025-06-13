from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, HTMLResponse
import os
import sys
import pathlib
from typing import Optional, List, Dict, Any

# Add the app directory to the path so we can import the search module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the enhanced search functionality
from search import search_profiles, semantic_search, hybrid_search, verify_database_integrity

app = FastAPI(title="FindBro API", description="API for searching developer profiles")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define paths
current_dir = pathlib.Path(__file__).parent.absolute()
project_root = current_dir.parent.parent  # This should be D:\FIndBro\Search-Engine
frontend_dir = project_root / "frontend"

print(f"Project root: {project_root}")
print(f"Frontend directory: {frontend_dir}")

# Mount static files
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

# Templates for serving HTML with context
templates = Jinja2Templates(directory=str(frontend_dir))

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the frontend HTML with proper template context."""
    print(f"Serving index.html from {frontend_dir}")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/app.js")
async def get_js():
    """Serve the JavaScript file."""
    js_path = frontend_dir / "app.js"
    print(f"Serving app.js from {js_path}")
    return FileResponse(js_path)

@app.get("/style.css")
async def get_css():
    """Serve the CSS file."""
    css_path = frontend_dir / "style.css" 
    print(f"Serving style.css from {css_path}")
    return FileResponse(css_path)

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

@app.get("/api/search")
async def search_profiles_endpoint(
    query: str = Query(..., description="Search query to find matching developer profiles"),
    limit: int = Query(5, description="Maximum number of results to return", ge=1, le=50),
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
        
        print(f"Search request: query='{query}', type={search_type}, limit={limit}")
        
        # Perform the search using the enhanced search function
        if search_type == "hybrid":
            results = search_profiles(
                query=query,
                top_k=limit,
                search_type="hybrid",
                semantic_weight=semantic_weight,
                keyword_weight=keyword_weight,
                experience_weight=experience_weight
            )
        else:
            results = search_profiles(
                query=query,
                top_k=limit,
                search_type="semantic"
            )
        
        # Format the results for the API response
        formatted_results = format_search_results(results, search_type)
        
        response = {
            "status": "success",
            "query": query.strip(),
            "search_type": search_type,
            "result_count": len(formatted_results),
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
        print(f"Error in search: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return error response instead of raising exception
        return {
            "status": "error",
            "message": f"Search failed: {str(e)}",
            "query": query if 'query' in locals() else None,
            "result_count": 0,
            "results": []
        }

@app.get("/api/search/semantic")
async def semantic_search_endpoint(
    query: str = Query(..., description="Search query for semantic matching only"),
    limit: int = Query(5, description="Maximum number of results to return", ge=1, le=50)
):
    """
    Semantic search endpoint for backward compatibility.
    Uses only vector similarity matching.
    """
    try:
        if not query or query.strip() == "":
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        print(f"Semantic search request: query='{query}', limit={limit}")
        
        # Use the original semantic search function
        results = semantic_search(query, top_k=limit)
        
        # Format results for backward compatibility
        formatted_results = []
        for item in results:
            profile = item["profile"]
            formatted_results.append({
                "name": profile.get("name", "N/A"),
                "handle": profile.get("handle", "N/A"),
                "skills": profile.get("skill_tags", []),
                "experience": profile.get("years_of_experience", 0),
                "roles": profile.get("preferred_roles", []),
                "timezone": profile.get("availability_timezone", "N/A"),
                "interests": profile.get("project_interests", []),
                "score": round(item.get("semantic_score", 0.0), 4)
            })
        
        return {
            "status": "success",
            "query": query.strip(),
            "search_type": "semantic",
            "result_count": len(formatted_results),
            "results": formatted_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in semantic search: {str(e)}")
        return {
            "status": "error",
            "message": f"Semantic search failed: {str(e)}",
            "query": query if 'query' in locals() else None,
            "result_count": 0,
            "results": []
        }

@app.get("/api/stats")
async def get_database_stats():
    """Get database statistics and verify integrity."""
    try:
        # This will need to be implemented in your search module
        stats = verify_database_integrity()
        return {
            "status": "success",
            "database_healthy": stats,
            "message": "Database statistics retrieved successfully"
        }
    except Exception as e:
        print(f"Error getting database stats: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to get database stats: {str(e)}",
            "database_healthy": False
        }

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    try:
        # Test database connectivity by checking if we can get stats
        db_healthy = verify_database_integrity()
        
        return {
            "status": "healthy",
            "database": "connected" if db_healthy else "disconnected",
            "api": "operational"
        }
    except Exception as e:
        return {
            "status": "degraded",
            "database": "error",
            "api": "operational",
            "error": str(e)
        }

# Add startup event to verify database
@app.on_event("startup")
async def startup_event():
    """Verify database connection on startup."""
    try:
        print("Verifying database connection...")
        is_healthy = verify_database_integrity()
        if is_healthy:
            print("✅ Database connection verified successfully")
        else:
            print("⚠️ Database connection issues detected")
    except Exception as e:
        print(f"❌ Database verification failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print(f"Starting server with frontend files from: {frontend_dir}")
    # List frontend directory contents to verify
    if frontend_dir.exists():
        print(f"Frontend directory exists. Contents: {os.listdir(frontend_dir)}")
    else:
        print(f"WARNING: Frontend directory does not exist: {frontend_dir}")
    
    print("\nAvailable endpoints:")
    print("- GET  /api/search (hybrid/semantic search with parameters)")
    print("- GET  /api/search/semantic (backward compatible semantic search)")
    print("- GET  /api/stats (database statistics)")
    print("- GET  /health (health check)")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)