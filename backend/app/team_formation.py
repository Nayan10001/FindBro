import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import os
import time
import random
from functools import wraps
import google.generativeai as genai

# --- Integration with search.py ---
SEARCH_MODULE_IMPORTED = False
try:
    from search import hybrid_search, load_and_index_profiles, verify_database_integrity
    print("Successfully imported from search.py. Qdrant setup should be initiated if required.")
    SEARCH_MODULE_IMPORTED = True
except ImportError as e:
    print(f"ERROR: Could not import from search.py: {e}")
    print("Falling back to MOCK search functions. REAL CANDIDATE SEARCH WILL NOT WORK.")
    
    def hybrid_search(query: str, top_k: int = 10, **kwargs) -> List[Dict]:
        print(f"MOCK hybrid_search (fallback) for: {query}")
        return [
            {"profile": {"name": f"Mock Candidate {i}", 
                         "handle": f"mock_candidate{i}", 
                         "skill_tags": ["Python", "Mocking", "Fallback"], 
                         "years_of_experience": i+1, 
                         "preferred_roles": ["Mock Developer"], 
                         "project_interests": ["Testing"]}, 
             "hybrid_score": 0.9 - i*0.02,
             "id": f"mock_id_{i}"
            }
            for i in range(top_k)
        ]
    
    def load_and_index_profiles(force_reload: bool = False):
        print("MOCK load_and_index_profiles (fallback) called. No actual indexing.")
        pass
    
    def verify_database_integrity():
        print("MOCK verify_database_integrity (fallback) called. No actual verification.")
        return False

# --- Quota Management Decorator ---
def rate_limited_gemini_call(max_retries=3, base_delay=2):
    """Decorator to handle rate limiting and quota issues with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    error_msg = str(e).lower()
                    if any(quota_term in error_msg for quota_term in ['quota', 'rate limit', 'exceeded', '429']):
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                            print(f"Quota/rate limit hit. Retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                            time.sleep(delay)
                            continue
                        else:
                            print(f"Max retries exceeded for quota limit. Using fallback.")
                            return self._handle_quota_exceeded(*args, **kwargs)
                    else:
                        print(f"Non-quota error in Gemini call: {e}")
                        raise e
            return None # Should ideally not be reached if max_retries leads to _handle_quota_exceeded
        return wrapper
    return decorator

@dataclass
class ProjectRequirements:
    project_type: str
    description: str
    tech_stack: List[str]
    complexity: str
    timeline: Optional[str] = None
    special_requirements: List[str] = field(default_factory=list)

@dataclass
class RoleRequirement:
    role_name: str
    priority: str
    required_skills: List[str]
    preferred_experience: int
    description: str

@dataclass
class TeamRecommendation:
    members: List[Dict[str, Any]]
    total_score: float
    role_coverage: Dict[str, str]
    reasoning: str
    potential_gaps: List[str] = field(default_factory=list)


class TeamFormationAgent:
    def __init__(self, 
                 gemini_api_key: Optional[str] = None, 
                 model_name: str = "gemini-1.5-flash",
                 config_file_path: Optional[str] = None,
                 enable_batch_processing: bool = True):
        
        self.enable_batch_processing = enable_batch_processing
        self.api_call_count = 0
        self.max_api_calls_per_session = 20
        
        api_key_to_use = gemini_api_key
        
        if config_file_path is None:
            try:
                # Try to determine path relative to the script's location, then go up one level to project root
                # Assuming this script (team_formation.py) is in backend/app/
                current_script_dir = os.path.dirname(os.path.abspath(__file__)) # Use __file__
                # Path to config: backend/config/gemini_config.json
                # So from backend/app/ go up to backend/, then to config/
                default_config_path_relative_to_app_dir = os.path.join(current_script_dir, '..', 'config', 'gemini_config.json')
                config_file_path = default_config_path_relative_to_app_dir

            except NameError: # __file__ is not defined (e.g. in interactive interpreter)
                 try:
                    # Fallback for when __file__ is not available (e.g. __main__ in some contexts)
                    current_script_dir = os.path.dirname(os.path.abspath(__import__('__main__').__file__))
                    default_config_path_relative_to_app_dir = os.path.join(current_script_dir, '..', 'config', 'gemini_config.json')
                    config_file_path = default_config_path_relative_to_app_dir
                 except Exception:
                    print("Could not determine default config path automatically.")
                    pass


        if not api_key_to_use and config_file_path:
            if os.path.exists(config_file_path):
                try:
                    with open(config_file_path, 'r') as f:
                        config_data = json.load(f)
                        api_key_to_use = config_data.get("api_key")
                        if api_key_to_use:
                            print(f"Successfully loaded Gemini API key from {config_file_path}")
                except Exception as e:
                    print(f"Error reading/parsing Gemini config file {config_file_path}: {e}")

        if not api_key_to_use:
            api_key_to_use = os.getenv("GOOGLE_API_KEY")
            if api_key_to_use:
                print("Successfully loaded Gemini API key from GOOGLE_API_KEY environment variable.")

        if not api_key_to_use:
            raise ValueError(
                "Gemini API key not found. Please provide it directly, "
                "in the config file, or set the GOOGLE_API_KEY environment variable."
            )
        
        genai.configure(api_key=api_key_to_use)
        
        self.generation_config_json = genai.types.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.1
        )
        self.model_name = model_name
        self.llm_client = genai.GenerativeModel(model_name)
        print(f"Using Gemini model: {model_name} (optimized for quota management)")

        if SEARCH_MODULE_IMPORTED:
            print("Verifying search database integrity on agent initialization...")
            if not verify_database_integrity():
                print("WARNING: Search database integrity check failed or reported issues.")
            else:
                print("Search database integrity check passed.")
        else:
            print("WARNING: Search module not imported. Candidate search will use MOCK data.")

    def _handle_quota_exceeded(self, *args, **kwargs):
        print("⚠️ Quota exceeded - using fallback logic")
        return "{\"error\": \"quota_exceeded\", \"fallback\": true}"

    @rate_limited_gemini_call(max_retries=3, base_delay=2)
    def _call_gemini(self, prompt: str, temperature: float = 0.1, expect_json: bool = True) -> str:
        if self.api_call_count >= self.max_api_calls_per_session:
            print(f"⚠️ Session API call limit ({self.max_api_calls_per_session}) reached. Using fallback.")
            return self._handle_quota_exceeded()
        
        self.api_call_count += 1
        print(f"📞 API Call #{self.api_call_count}/{self.max_api_calls_per_session}")
        
        current_config = self.generation_config_json if expect_json and ("1.5" in self.model_name or "gemini-pro" not in self.model_name) \
                         else genai.types.GenerationConfig()
        current_config.temperature = temperature
        if expect_json and ("1.5" in self.model_name or "gemini-pro" not in self.model_name):
             current_config.response_mime_type="application/json"


        try:
            response = self.llm_client.generate_content(
                prompt,
                generation_config=current_config
            )
            return response.text
        except Exception as e:
            print(f"Error calling Gemini: {e}")
            raise e

    def analyze_project(self, prompt: str) -> ProjectRequirements:
        analysis_prompt = f"""
        Analyze this project request and extract structured information:
        Project Request: "{prompt}"
        
        Provide a JSON response with this exact schema:
        {{
            "project_type": "web_app|mobile_app|ai_project|ecommerce|saas|other",
            "description": "brief description (max 100 chars)",
            "tech_stack": ["technology1", "technology2"],
            "complexity": "simple|medium|complex",
            "timeline": "estimated timeline if mentioned, otherwise null",
            "special_requirements": ["requirement1", "requirement2"]
        }}
        
        Be concise and focus on key technical requirements only.
        """
        response_text = self._call_gemini(analysis_prompt, temperature=0.1, expect_json=True)
        try:
            result = json.loads(response_text)
            if result.get("error") == "quota_exceeded":
                return self._fallback_project_analysis(prompt)
            result['timeline'] = result.get('timeline') 
            result['special_requirements'] = result.get('special_requirements', [])
            return ProjectRequirements(**result)
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            print(f"Error parsing JSON from Gemini for project analysis: {e}\nResponse: {response_text}")
            return self._fallback_project_analysis(prompt)
    
    def plan_team_roles(self, project_req: ProjectRequirements) -> List[RoleRequirement]:
        role_planning_prompt = f"""
        Based on this project, determine 2-3 optimal team roles:
        Type: {project_req.project_type}, Complexity: {project_req.complexity}
        Tech: {', '.join(project_req.tech_stack)}, Timeline: {project_req.timeline}
        
        Return JSON with this schema:
        {{
            "roles": [
                {{
                    "role_name": "role name",
                    "priority": "critical|important|nice-to-have",
                    "required_skills": ["skill1", "skill2"],
                    "preferred_experience": 3,
                    "description": "brief role description"
                }}
            ]
        }}
        
        Focus on essential roles only. Keep descriptions under 50 characters.
        """
        response_text = self._call_gemini(role_planning_prompt, temperature=0.1, expect_json=True)
        try:
            result = json.loads(response_text)
            if result.get("error") == "quota_exceeded":
                return self._fallback_role_planning(project_req)
            if "roles" in result and isinstance(result["roles"], list):
                return [RoleRequirement(**role) for role in result["roles"]]
            else:
                return self._fallback_role_planning(project_req)
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            print(f"Error parsing JSON from Gemini for role planning: {e}\nResponse: {response_text}")
            return self._fallback_role_planning(project_req)
    
    def find_candidates_for_role(self, role_req: RoleRequirement, project_req: ProjectRequirements) -> List[Dict]:
        search_query = (
            f"{role_req.role_name} {' '.join(role_req.required_skills[:3])} "
            f"{project_req.project_type} {' '.join(project_req.tech_stack[:2])}"
        )
        print(f"Searching for role '{role_req.role_name}' with query: {search_query}")
        candidates = hybrid_search(query=search_query, top_k=8)
        if not candidates:
            print(f"No candidates found for role: {role_req.role_name}")
            return []
        if self.enable_batch_processing and len(candidates) > 1:
            return self._batch_evaluate_candidates(candidates, role_req, project_req)
        else:
            return self._individual_evaluate_candidates(candidates[:3], role_req, project_req)

    def _batch_evaluate_candidates(self, candidates: List[Dict], role_req: RoleRequirement, project_req: ProjectRequirements) -> List[Dict]:
        candidates_summary = []
        for i, candidate_data in enumerate(candidates[:5]):
            profile = candidate_data.get('profile', {})
            candidates_summary.append(
                f"{i+1}. {profile.get('name', 'N/A')} - Skills: {', '.join(profile.get('skill_tags', [])[:4])} - Exp: {profile.get('years_of_experience', 0)}yrs"
            )
        batch_eval_prompt = f"""
        Evaluate these candidates for role: {role_req.role_name}
        Required skills: {', '.join(role_req.required_skills)}
        Project: {project_req.project_type} using {', '.join(project_req.tech_stack[:3])}
        
        Candidates:
        {chr(10).join(candidates_summary)}
        
        Return JSON array with fit scores:
        {{
            "evaluations": [
                {{"candidate_index": 1, "fit_score": 0.85, "key_strengths": ["strength1"], "main_concern": "concern"}},
                {{"candidate_index": 2, "fit_score": 0.72, "key_strengths": ["strength1"], "main_concern": "concern"}}
            ]
        }}
        
        Score 0.0-1.0 based on skill match and experience relevance.
        """
        response_text = self._call_gemini(batch_eval_prompt, temperature=0.1, expect_json=True)
        try:
            result = json.loads(response_text)
            if result.get("error") == "quota_exceeded":
                return self._fallback_candidate_scoring(candidates)
            
            evaluations = result.get("evaluations", [])
            enhanced_candidates = []
            
            for eval_data in evaluations:
                idx = eval_data.get("candidate_index", 1) - 1
                if 0 <= idx < len(candidates):
                    candidate = candidates[idx]
                    
                    llm_fit_score_raw = eval_data.get("fit_score", 0.0)
                    try:
                        llm_fit_score_value = float(llm_fit_score_raw)
                    except (ValueError, TypeError):
                        print(f"Warning: LLM fit_score ('{llm_fit_score_raw}') for candidate is not a valid float. Defaulting to 0.0.")
                        llm_fit_score_value = 0.0

                    hybrid_score_raw = candidate.get("hybrid_score", 0.0)
                    try:
                        hybrid_score_value = float(hybrid_score_raw)
                    except (ValueError, TypeError):
                        print(f"Warning: Candidate hybrid_score ('{hybrid_score_raw}') is not a valid float. Defaulting to 0.0.")
                        hybrid_score_value = 0.0
                    
                    combined_score = (hybrid_score_value * 0.6 + 
                                    llm_fit_score_value * 0.4)
                    
                    enhanced_candidate = {
                        **candidate,
                        "llm_fit_score": llm_fit_score_value,
                        "llm_reasoning": f"Strengths: {', '.join(eval_data.get('key_strengths', []))}. Concern: {eval_data.get('main_concern', 'None')}",
                        "combined_score": combined_score
                    }
                    enhanced_candidates.append(enhanced_candidate)
            
            enhanced_candidates.sort(key=lambda x: x.get("combined_score", 0.0), reverse=True)
            return enhanced_candidates[:3]
            
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            print(f"Error in batch evaluation JSON parsing: {e}. Using fallback scoring.")
            return self._fallback_candidate_scoring(candidates)

    def _individual_evaluate_candidates(self, candidates: List[Dict], role_req: RoleRequirement, project_req: ProjectRequirements) -> List[Dict]:
        enhanced_candidates = []
        for candidate_data in candidates:
            profile = candidate_data.get('profile', {})
            if not profile: continue
            
            skill_match = len(set(role_req.required_skills) & set(profile.get('skill_tags', []))) / max(len(role_req.required_skills), 1)
            exp_score = min(float(profile.get('years_of_experience', 0)) / max(float(role_req.preferred_experience), 1.0), 1.0) # Ensure float division
            fit_score = (skill_match * 0.7 + exp_score * 0.3)
            
            hybrid_score_val = float(candidate_data.get("hybrid_score", 0.0)) # Ensure float
            combined_score = (hybrid_score_val * 0.6 + fit_score * 0.4)
            
            enhanced_candidate = {
                **candidate_data,
                "llm_fit_score": fit_score,
                "llm_reasoning": f"Skill match: {skill_match:.2f}, Experience fit: {exp_score:.2f}",
                "combined_score": combined_score
            }
            enhanced_candidates.append(enhanced_candidate)
        
        enhanced_candidates.sort(key=lambda x: x.get("combined_score", 0.0), reverse=True)
        return enhanced_candidates

    def _fallback_candidate_scoring(self, candidates: List[Dict]) -> List[Dict]:
        for candidate in candidates:
            hybrid_score = float(candidate.get("hybrid_score", 0.5)) # Ensure float
            candidate["llm_fit_score"] = hybrid_score
            candidate["combined_score"] = hybrid_score
            candidate["llm_reasoning"] = "Fallback scoring due to quota limits or batch eval error"
        return sorted(candidates, key=lambda x: x.get("combined_score", 0.0), reverse=True)[:3]
    
    def form_optimal_team(self, 
                         role_requirements: List[RoleRequirement], 
                         project_req: ProjectRequirements) -> TeamRecommendation:
        role_candidates = {}
        for role_req in role_requirements:
            candidates = self.find_candidates_for_role(role_req, project_req)
            role_candidates[role_req.role_name] = candidates
        
        best_team_rec = self._evaluate_team_combinations(role_candidates, role_requirements, project_req)
        return best_team_rec
    
    def _evaluate_team_combinations(self, 
                                   role_candidates: Dict[str, List[Dict]], 
                                   role_requirements: List[RoleRequirement],
                                   project_req: ProjectRequirements) -> TeamRecommendation:
        team_members_for_eval = []
        role_coverage = {}
        temp_selected_candidates_info = {}

        for role_req in sorted(role_requirements, key=lambda r: r.priority != "critical"):
            if role_req.role_name in role_candidates and role_candidates[role_req.role_name]:
                selected_candidate = None
                for candidate in role_candidates[role_req.role_name]:
                    candidate_handle = candidate.get('profile', {}).get('handle')
                    if candidate_handle and candidate_handle not in temp_selected_candidates_info:
                        selected_candidate = candidate
                        break
                if not selected_candidate: # Fallback if all preferred candidates are taken
                    selected_candidate = role_candidates[role_req.role_name][0]

                if selected_candidate:
                    team_members_for_eval.append(selected_candidate)
                    profile_name = selected_candidate.get('profile', {}).get('name', 'Unknown Candidate')
                    role_coverage[role_req.role_name] = profile_name
                    candidate_handle = selected_candidate.get('profile', {}).get('handle')
                    if candidate_handle:
                         temp_selected_candidates_info[candidate_handle] = profile_name

        if not team_members_for_eval:
             return TeamRecommendation(members=[], total_score=0.0, role_coverage={},
                reasoning="No suitable candidates found for any role.", potential_gaps=["All roles unfilled"])

        unique_team_members_dict = {}
        for member in team_members_for_eval:
            handle = member.get('profile', {}).get('handle')
            if handle:
                if handle not in unique_team_members_dict: unique_team_members_dict[handle] = member
            else: unique_team_members_dict[id(member)] = member # Fallback for missing handle
        final_team_members = list(unique_team_members_dict.values())

        avg_score = 0.0
        if self.api_call_count >= self.max_api_calls_per_session - 1: # Adjusted threshold slightly
            print("⚠️ Skipping LLM team validation due to tight quota limits")
            if final_team_members:
                try:
                    member_scores = [float(m.get("combined_score", 0.0)) for m in final_team_members]
                    avg_score = sum(member_scores) / len(member_scores) if member_scores else 0.0
                except (ValueError, TypeError):
                    print("Warning: Non-float combined_score found calculating team score (quota skip). Defaulting to 0.0.")
                    avg_score = 0.0
            return TeamRecommendation(
                members=final_team_members, total_score=avg_score, role_coverage=role_coverage,
                reasoning="Team formed: individual scores (LLM validation skipped for quota).",
                potential_gaps=["LLM team validation not performed due to quota."]
            )

        validation_prompt = f"""
        Quick team assessment for {project_req.project_type} project:
        Team size: {len(final_team_members)} members
        Roles covered: {', '.join(role_coverage.keys())}
        Tech stack needed: {', '.join(project_req.tech_stack[:3])}
        
        JSON response:
        {{
            "team_score": 0.85, "reasoning": "brief assessment",
            "main_strength": "key strength", "main_gap": "key concern or 'none'"
        }}
        """
        response_text = self._call_gemini(validation_prompt, temperature=0.1, expect_json=True)
        
        try:
            validation_result = json.loads(response_text)
            if validation_result.get("error") == "quota_exceeded":
                if final_team_members:
                    try:
                        member_scores = [float(m.get("combined_score", 0.0)) for m in final_team_members]
                        avg_score = sum(member_scores) / len(member_scores) if member_scores else 0.0
                    except (ValueError, TypeError):
                        print("Warning: Non-float combined_score calculating team score (quota fallback). Defaulting to 0.0.")
                        avg_score = 0.0
                reasoning = "Team formed: individual scores (LLM validation quota limit reached)."
                potential_gaps = ["LLM team validation unavailable (quota)."]
            else:
                team_score_raw = validation_result.get("team_score", 0.0)
                try:
                    avg_score = float(team_score_raw)
                except (ValueError, TypeError):
                    print(f"Warning: LLM team_score ('{team_score_raw}') is not a valid float. Defaulting to 0.0.")
                    avg_score = 0.0
                
                reasoning = validation_result.get("reasoning", "N/A")
                main_gap = validation_result.get("main_gap", "none")
                potential_gaps = [main_gap] if main_gap != "none" else []
            
            return TeamRecommendation(
                members=final_team_members, total_score=avg_score, role_coverage=role_coverage,
                reasoning=reasoning, potential_gaps=potential_gaps
            )
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            print(f"Error parsing team validation JSON: {e}")
            if final_team_members:
                try:
                    member_scores = [float(m.get("combined_score", 0.0)) for m in final_team_members]
                    avg_score = sum(member_scores) / len(member_scores) if member_scores else 0.0
                except (ValueError, TypeError):
                    print("Warning: Non-float combined_score calculating team score (JSON error fallback). Defaulting to 0.0.")
                    avg_score = 0.0
            return TeamRecommendation(
                members=final_team_members, total_score=avg_score, role_coverage=role_coverage,
                reasoning="Team formed: fallback validation (LLM response parsing error).", 
                potential_gaps=["LLM team validation error (JSON parsing)."])
    
    def recommend_team(self, prompt: str) -> TeamRecommendation:
        print(f"🔍 Analyzing project: {prompt[:100]}...")
        print(f"📊 Starting with {self.max_api_calls_per_session - self.api_call_count} API calls remaining")
        
        project_req = self.analyze_project(prompt)
        print(f"Project Analysis Result: {project_req}")
        if not project_req or not project_req.project_type: # Check if fallback created a minimal valid object
            return TeamRecommendation(members=[], total_score=0.0, role_coverage={}, 
                                      reasoning="Critical failure in project analysis.", 
                                      potential_gaps=["Project requirements not understood."])

        print(f"\n📋 Planning team roles for {project_req.project_type}")
        role_requirements = self.plan_team_roles(project_req)
        print(f"Planned Roles: {[r.role_name for r in role_requirements]}")
        if not role_requirements:
            return TeamRecommendation(members=[], total_score=0.0, role_coverage={}, 
                                      reasoning="Failure in planning team roles.", 
                                      potential_gaps=["No roles defined."])

        print(f"\n👥 Forming team for {len(role_requirements)} roles")
        print(f"📊 {self.max_api_calls_per_session - self.api_call_count} API calls remaining")
        
        team_recommendation = self.form_optimal_team(role_requirements, project_req)
        
        print(f"✅ Team formation complete. Used {self.api_call_count} API calls total.")
        return team_recommendation
    
    def _format_team_for_llm(self, team_members: List[Dict]) -> str:
        formatted = []
        for i, member_data in enumerate(team_members, 1):
            profile = member_data.get('profile', {})
            formatted.append(
                f"{i}. {profile.get('name', 'N/A')} - {', '.join(profile.get('skill_tags', [])[:3])} - {profile.get('years_of_experience', 0)}yrs"
            )
        return '; '.join(formatted)
    
    def _fallback_project_analysis(self, prompt: str) -> ProjectRequirements:
        print("⚠️ Using fallback project analysis.")
        prompt_lower = prompt.lower()
        project_type = "web_app" # Default
        tech_stack = ["JavaScript", "Python"] # Default
        if any(w in prompt_lower for w in ['mobile', 'app', 'android', 'ios']):
            project_type = "mobile_app"; tech_stack = ["React Native", "Mobile"]
        elif any(w in prompt_lower for w in ['ai', 'ml', 'chatbot', 'nlp']):
            project_type = "ai_project"; tech_stack = ["Python", "AI/ML"]
        elif any(w in prompt_lower for w in ['ecommerce', 'shop', 'store']):
            project_type = "ecommerce"; tech_stack = ["React", "Node.js"]
        return ProjectRequirements(
            project_type=project_type, description=f"Fallback analysis: {prompt[:50]}...", 
            tech_stack=tech_stack, complexity="medium", timeline="3-6 months", special_requirements=[])
    
    def _fallback_role_planning(self, project_req: ProjectRequirements) -> List[RoleRequirement]:
        print("⚠️ Using fallback role planning.")
        roles = []
        if project_req.project_type == "ai_project":
            roles = [RoleRequirement("AI Developer", "critical", ["Python", "ML"], 3, "AI/ML specialist"),
                     RoleRequirement("Backend Developer", "important", ["Python", "API"], 2, "Backend integration")]
        elif project_req.project_type == "mobile_app":
            roles = [RoleRequirement("Mobile Developer", "critical", ["Mobile", "React Native"], 3, "Mobile app dev"),
                     RoleRequirement("UI/UX Designer", "important", ["Design", "UI"], 2, "Mobile UI design")]
        else: # Default/web_app
            roles = [RoleRequirement("Full Stack Developer", "critical", ["JS", "Python"], 3, "Full stack dev"),
                     RoleRequirement("Frontend Developer", "important", ["React", "UI"], 2, "Frontend specialist")]
        return roles

def main():
    try:
        team_agent = TeamFormationAgent(model_name="gemini-1.5-flash", enable_batch_processing=True)
    except ValueError as e:
        print(f"Error initializing agent: {e}")
        return
    except Exception as e:
        print(f"An unexpected error occurred during agent initialization: {e}")
        return

    project_prompt = "We need  customer support chatbot for e-commerce. Python backend, React frontend, Ui-UX designer. 4-6 months timeline. Small team preferred."
    
    try:
        recommendation = team_agent.recommend_team(project_prompt)
        
        print("\n" + "="*60)
        print("🎯 TEAM RECOMMENDATION")
        print("="*60)
        # Ensure total_score is float before formatting
        total_score_val = recommendation.total_score
        if not isinstance(total_score_val, (int, float)):
            try:
                total_score_val = float(total_score_val)
            except (ValueError, TypeError):
                print(f"Warning: recommendation.total_score ('{recommendation.total_score}') is not a valid number. Displaying as is.")
                total_score_val = recommendation.total_score # Display as is if not convertible
        
        if isinstance(total_score_val, (int, float)):
            print(f"Overall Team Score: {total_score_val:.2f}")
        else:
            print(f"Overall Team Score: {total_score_val}") # Print as is if it couldn't be converted

        print(f"\n💡 Reasoning: {recommendation.reasoning}")
        
        print(f"\n👥 RECOMMENDED TEAM MEMBERS ({len(recommendation.members)}):")
        if recommendation.members:
            for i, member_data in enumerate(recommendation.members, 1):
                profile = member_data.get('profile', {})
                assigned_role = "Unassigned"
                for role, name in recommendation.role_coverage.items():
                    if name == profile.get('name'): assigned_role = role; break
                
                print(f"\n{i}. {profile.get('name', 'N/A')} - {assigned_role}")
                
                combined_score_val = member_data.get('combined_score', 0.0)
                # Ensure combined_score is float for formatting
                if not isinstance(combined_score_val, (int, float)):
                    try:
                        combined_score_val = float(combined_score_val)
                    except (ValueError, TypeError):
                        # Keep as is if not convertible, will be printed without .2f
                        pass # combined_score_val remains original

                if isinstance(combined_score_val, (int, float)):
                    print(f"   📊 Score: {combined_score_val:.2f}")
                else:
                    print(f"   📊 Score: {combined_score_val}") # Print as is

                print(f"   🛠️  Skills: {', '.join(profile.get('skill_tags', [])[:5])}")
                print(f"   💼 Experience: {profile.get('years_of_experience', 0)} years")
        else:
            print("No members recommended.")
            
        if recommendation.potential_gaps:
            print(f"\n⚠️  POTENTIAL GAPS:")
            for gap in recommendation.potential_gaps: print(f"   • {gap}")
        
        print(f"\n📋 ROLE COVERAGE:")
        for role, name in recommendation.role_coverage.items(): print(f"   • {role}: {name}")
            
        print(f"\n📊 API Usage: {team_agent.api_call_count}/{team_agent.max_api_calls_per_session} calls used")
        
    except Exception as e:
        print(f"Error during team recommendation: {e}")
        import traceback
        traceback.print_exc() # Print full traceback for better debugging
        print("This might be due to quota limits or API issues.")

if __name__ == "__main__":
    print("🚀 Starting Optimized Team Formation Process...")
    # ... (rest of the initial prints)
    print("📝 Quota Management Features:")
    print("   • Rate limiting with exponential backoff")
    print("   • Batch candidate evaluation")
    print("   • Fallback scoring methods")
    print("   • API call counting and limits")
    print("   • Using Gemini Flash model for efficiency")
    
    if not SEARCH_MODULE_IMPORTED:
        print("\n⚠️  CRITICAL: search.py module could not be loaded.")
        print("   Candidate search will use MOCK data.")
        print("   Make sure Qdrant is running and search.py is correctly placed.")
    
    print("\n" + "="*60)
    main()