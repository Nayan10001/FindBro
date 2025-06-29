from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import sys
import pathlib
from typing import Optional, List, Dict, Any

# Add the app directory to the path so we can import the search modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- ADDITION: Import the new intelligent_search function ---
from search import (
    search_profiles,
    semantic_search,
    hybrid_search,
    intelligent_search,  # <-- Added
    verify_database_integrity
)
from project_search import search_projects, verify_projects_database_integrity
from startup import search_startups, verify_startups_database_integrity

app = FastAPI(title="FindBro API", description="API for searching developer profiles, projects, and startups")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define paths
current_dir = pathlib.Path(__file__).parent.absolute()
project_root = current_dir.parent  # This should be the main project directory
frontend_build_dir = project_root / "frontend" / "dist"  # Vite build output
frontend_src_dir = project_root / "frontend"  # React source

print(f"Project root: {project_root}")
print(f"Frontend build directory: {frontend_build_dir}")

def format_search_results(results: List[Dict[str, Any]], search_type: str = "hybrid") -> List[Dict[str, Any]]:
    """Format search results for API response into a detailed, structured format."""
    formatted_results = []
    
    for item in results:
        profile = item.get("profile", {})
        education_data = profile.get("education", {})
        
        # Handle different score types based on search method
        score = item.get("hybrid_score", 0.0) if search_type == "hybrid" else item.get("semantic_score", 0.0)
        
        # Reformat work history to match the requested structure
        work_history = [
            {
                "company": work.get("company", "N/A"),
                "role": work.get("role", "N/A"),
                "duration_years": work.get("duration_years", 0)
            } for work in profile.get("work_history", [])
        ]
        
        formatted_item = {
            "id": item.get("id"),
            "score": round(score, 4),
            "score_details": {
                "hybrid_score": item.get("hybrid_score", 0.0),
                "semantic_score": item.get("semantic_score", 0.0),
                "keyword_score": item.get("keyword_score", 0.0),
                "experience_score": item.get("experience_score", 0.0),
                "reputation_score": item.get("reputation_score", 0.0),
                "role_alignment_score": item.get("role_alignment_score", 0.0)
            },
            "basic_info": {
                "name": profile.get("name", "N/A"),
                "handle": profile.get("handle", "N/A"),
            },
            "skills_and_roles": {
                "skill_tags": profile.get("skill_tags", []),
                "preferred_roles": profile.get("preferred_roles", []),
                "years_of_experience": profile.get("years_of_experience", 0),
                "availability_timezone": profile.get("availability_timezone", "N/A"),
            },
            "interests": {
                "project_interests": profile.get("project_interests", [])
            },
            "work_history": work_history,
            "education": {
                "institution": education_data.get("institution", "N/A"),
                "degree": education_data.get("degree", "N/A")
            }
        }
        
        # This part handles the extra data from intelligent_search for the main response
        if "parsed_query" in item:
            parsed = item["parsed_query"]
            parsed_dict = {}
            if parsed:
                 parsed_dict = {f.name: getattr(parsed, f.name) for f in parsed.__dataclass_fields__.values()}
                 if 'query_type' in parsed_dict:
                     parsed_dict['query_type'] = parsed_dict['query_type'].value

            formatted_item["query_analysis"] = {
                "parsed_query": parsed_dict,
                "enhanced_query": item.get("enhanced_query"),
                "applied_filters": item.get("applied_filters")
            }
        
        formatted_results.append(formatted_item)
    
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

def format_startup_search_results(results: List[Dict[str, Any]], search_type: str = "hybrid") -> List[Dict[str, Any]]:
    """Format startup search results for API response"""
    formatted_results = []
    
    for item in results:
        startup = item["startup"]
        
        # Handle different score types based on search method
        if search_type == "hybrid":
            score = item.get("hybrid_score", 0.0)
            score_details = {
                "hybrid_score": item.get("hybrid_score", 0.0),
                "semantic_score": item.get("semantic_score", 0.0),
                "keyword_score": item.get("keyword_score", 0.0),
                "stage_score": item.get("stage_score", 0.0),
                "market_score": item.get("market_score", 0.0)
            }
        else:  # semantic search
            score = item.get("semantic_score", 0.0)
            score_details = {
                "semantic_score": score
            }
        
        formatted_results.append({
            "name": startup.get("name", "N/A"),
            "description": startup.get("description", ""),
            "alt": startup.get("alt", ""),
            "link": startup.get("link", ""),
            "city": startup.get("city", ""),
            "images": startup.get("images", ""),
            "industries": startup.get("industries", []),
            "technologies": startup.get("technologies", []),
            "stage": startup.get("stage", "unknown"),
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
    semantic_weight: float = Query(0.4, description="Weight for semantic similarity in hybrid search", ge=0.0, le=1.0),
    keyword_weight: float = Query(0.25, description="Weight for keyword matching in hybrid search", ge=0.0, le=1.0),
    experience_weight: float = Query(0.1, description="Weight for experience relevance in hybrid search", ge=0.0, le=1.0),
    reputation_weight: float = Query(0.15, description="Weight for company/institute reputation in hybrid search", ge=0.0, le=1.0),
    role_alignment_weight: float = Query(0.1, description="Weight for preferred role alignment in hybrid search", ge=0.0, le=1.0)
):
    """
    Search for developer profiles based on the query string.
    
    Supports both semantic and hybrid search methods:
    - semantic: Uses only vector similarity
    - hybrid: Combines semantic similarity, keyword matching, experience relevance, reputation, and role alignment
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
            total_weight = (
                semantic_weight + 
                keyword_weight + 
                experience_weight +
                reputation_weight +
                role_alignment_weight
            )
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
                experience_weight=experience_weight,
                reputation_weight=reputation_weight,
                role_alignment_weight=role_alignment_weight
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
                "experience_weight": experience_weight,
                "reputation_weight": reputation_weight,
                "role_alignment_weight": role_alignment_weight
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

# --- START OF ADD-ON CODE ---

@app.get("/api/search/intelligent")
async def intelligent_search_endpoint(
    query: str = Query(..., description="Intelligent search query that understands natural language"),
    limit: int = Query(5, description="Maximum number of results to return", ge=1, le=50),
):
    """
    Search for developer profiles using the intelligent query understanding module.
    This endpoint automatically parses skills, roles, experience, etc. from the query.
    """
    try:
        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        print(f"Intelligent search request: query='{query}', limit={limit}")

        # Call the intelligent_search function from search.py
        results = intelligent_search(query=query, top_k=limit)

        # Use the original formatter. The intelligent search uses a hybrid model, so we pass "hybrid".
        formatted_results = format_search_results(results, search_type="hybrid")

        # Extract the query analysis from the first result (it's the same for all)
        query_analysis_data = None
        if formatted_results and "query_analysis" in formatted_results[0]:
            query_analysis_data = formatted_results[0]["query_analysis"]
            # Clean up per-result analysis to avoid redundant data in the response
            for res in formatted_results:
                del res["query_analysis"]
        
        response = {
            "status": "success",
            "query": query.strip(),
            "search_mode": "intelligent",
            "query_analysis": query_analysis_data,  # Add the analysis to the top level
            "result_count": len(formatted_results),
            "results": formatted_results
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in intelligent search: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

# --- END OF ADD-ON CODE ---


@app.get("/api/search/projects")
async def search_projects_endpoint(
    query: str = Query(..., description="Search query to find matching projects"),
    limit: int = Query(8, description="Maximum number of results to return", ge=1, le=50),
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
        
        print(f"Project search request: query='{query}', type={search_type}, limit={limit}")
        
        # Perform the project search
        if search_type == "hybrid":
            results = search_projects(
                query=query,
                top_k=limit,
                search_type="hybrid",
                semantic_weight=semantic_weight,
                keyword_weight=keyword_weight,
                status_weight=status_weight
            )
        else:
            results = search_projects(
                query=query,
                top_k=limit,
                search_type="semantic"
            )
        
        # Format the results for the API response
        formatted_results = format_project_search_results(results, search_type)
        
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
                "status_weight": status_weight
            }
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Error in project search: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return error response instead of raising exception
        return {
            "status": "error",
            "message": f"Project search failed: {str(e)}",
            "query": query if 'query' in locals() else None,
            "result_count": 0,
            "results": []
        }

@app.get("/api/search/startups")
async def search_startups_endpoint(
    query: str = Query(..., description="Search query to find matching startups"),
    limit: int = Query(8, description="Maximum number of results to return", ge=1, le=50),
    search_type: str = Query("hybrid", description="Search type: 'semantic' or 'hybrid'"),
    semantic_weight: float = Query(0.6, description="Weight for semantic similarity in hybrid search", ge=0.0, le=1.0),
    keyword_weight: float = Query(0.2, description="Weight for keyword matching in hybrid search", ge=0.0, le=1.0),
    stage_weight: float = Query(0.1, description="Weight for stage relevance in hybrid search", ge=0.0, le=1.0),
    market_weight: float = Query(0.1, description="Weight for market relevance in hybrid search", ge=0.0, le=1.0)
):
    """
    Search for startups based on the query string.
    
    Supports both semantic and hybrid search methods:
    - semantic: Uses only vector similarity
    - hybrid: Combines semantic similarity, keyword matching, stage relevance, and market fit
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
            total_weight = semantic_weight + keyword_weight + stage_weight + market_weight
            if abs(total_weight - 1.0) > 0.1:  # Allow small tolerance
                raise HTTPException(
                    status_code=400, 
                    detail=f"Weights should sum to 1.0, got {total_weight}"
                )
        
        print(f"Startup search request: query='{query}', type={search_type}, limit={limit}")
        
        # Perform the startup search
        if search_type == "hybrid":
            results = search_startups(
                query=query,
                top_k=limit,
                search_type="hybrid",
                semantic_weight=semantic_weight,
                keyword_weight=keyword_weight,
                stage_weight=stage_weight,
                market_weight=market_weight
            )
        else:
            results = search_startups(
                query=query,
                top_k=limit,
                search_type="semantic"
            )
        
        # Format the results for the API response
        formatted_results = format_startup_search_results(results, search_type)
        
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
                "stage_weight": stage_weight,
                "market_weight": market_weight
            }
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Error in startup search: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return error response instead of raising exception
        return {
            "status": "error",
            "message": f"Startup search failed: {str(e)}",
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
        # Check all three databases
        profiles_healthy = verify_database_integrity()
        projects_healthy = verify_projects_database_integrity()
        
        # Check if startups database verification function exists
        try:
            startups_healthy = verify_startups_database_integrity()
        except (NameError, AttributeError):
            # If the function doesn't exist, assume healthy if no errors
            startups_healthy = True
            print("Note: verify_startups_database_integrity function not found, assuming healthy")
        
        return {
            "status": "success",
            "profiles_database_healthy": profiles_healthy,
            "projects_database_healthy": projects_healthy,
            "startups_database_healthy": startups_healthy,
            "overall_healthy": profiles_healthy and projects_healthy and startups_healthy,
            "message": "Database statistics retrieved successfully"
        }
    except Exception as e:
        print(f"Error getting database stats: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to get database stats: {str(e)}",
            "profiles_database_healthy": False,
            "projects_database_healthy": False,
            "startups_database_healthy": False,
            "overall_healthy": False
        }

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    try:
        # Test database connectivity by checking if we can get stats
        profiles_healthy = verify_database_integrity()
        projects_healthy = verify_projects_database_integrity()
        
        # Check startups database
        try:
            startups_healthy = verify_startups_database_integrity()
        except (NameError, AttributeError):
            startups_healthy = True
        
        return {
            "status": "healthy",
            "profiles_database": "connected" if profiles_healthy else "disconnected",
            "projects_database": "connected" if projects_healthy else "disconnected",
            "startups_database": "connected" if startups_healthy else "disconnected",
            "api": "operational"
        }
    except Exception as e:
        return {
            "status": "degraded",
            "profiles_database": "error",
            "projects_database": "error",
            "startups_database": "error",
            "api": "operational",
            "error": str(e)
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
        print("Verifying database connections...")
        profiles_healthy = verify_database_integrity()
        projects_healthy = verify_projects_database_integrity()
        
        # Check startups database
        try:
            startups_healthy = verify_startups_database_integrity()
        except (NameError, AttributeError):
            startups_healthy = True
            print("Note: verify_startups_database_integrity function not available")
        
        if profiles_healthy:
            print("✅ Profiles database connection verified successfully")
        else:

            print("⚠️ Profiles database connection issues detected")
            
        if projects_healthy:
            print("✅ Projects database connection verified successfully")
        else:
            print("⚠️ Projects database connection issues detected")
            
        if startups_healthy:
            print("✅ Startups database connection verified successfully")
        else:
            print("⚠️ Startups database connection issues detected")
            
    except Exception as e:
        print(f"❌ Database verification failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print(f"Starting server...")
    print(f"Frontend build directory: {frontend_build_dir}")
    
    # Check if frontend is built
    if frontend_build_dir.exists():
        print(f"✅ Frontend build found. Full-stack app will be served.")
        print(f"Frontend build contents: {list(frontend_build_dir.iterdir())}")
    else:
        print(f"⚠️ Frontend not built. Only API will be available.")
        print(f"To build frontend: cd frontend && npm run build")
    
    # --- MODIFIED: Added the new endpoint to the list ---
    print("\nAvailable endpoints:")
    print("- GET  /api/search (Manual hybrid/semantic search for profiles)")
    print("- GET  /api/search/intelligent (NEW: Intelligent search for profiles)")
    print("- GET  /api/search/projects (Hybrid/semantic search for projects)")
    print("- GET  /api/search/startups (Hybrid/semantic search for startups)")
    print("- GET  /api/search/semantic (Backward compatible semantic search)")
    print("- GET  /api/stats (Database statistics)")
    print("- GET  /health (Health check)")
    print("- GET  /docs (API documentation)")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)