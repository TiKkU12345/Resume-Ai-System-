
# """
# AI Resume Shortlisting - Web Interface using Streamlit
# Beautiful, interactive dashboard for resume screening and ranking
# FIXED VERSION - Session state initialization error resolved
# """

# import streamlit as st
# import pandas as pd
# import json
# import os
# import plotly.express as px
# from pathlib import Path
# import plotly.graph_objects as go
# from resume_parser import ResumeParser
# from job_resume_matcher import CandidateRanker, JobDescriptionParser
# from datetime import datetime
# from email_integration import EmailManager, render_email_panel
# from bulk_upload import render_bulk_upload_ui
# from interview_questions import render_question_generator_ui
# from database import SupabaseManager
# from agent_brain import AgentBrain, AgentDecision, ConfidenceLevel
# from generate_question import QuestionGenerator, AnswerEvaluator

# from ats_resume_validator import (
#     render_ats_guide, 
#     validate_and_show_feedback, 
#     show_ats_warning,
#     ATSResumeValidator
# )

# # Try to import authentication (optional)
# AUTH_AVAILABLE = False
# try:
#     from authentication import (
#         AuthManager, 
#         render_auth_page, 
#         render_auth_sidebar, 
#         require_auth
#     )
#     AUTH_AVAILABLE = True
# except ImportError:
#     AUTH_AVAILABLE = False
#     AuthManager = None
#     render_auth_page = None
#     render_auth_sidebar = None
#     require_auth = None
# except Exception as e:
#     # Catch any other errors during import
#     AUTH_AVAILABLE = False
#     AuthManager = None
#     render_auth_page = None
#     render_auth_sidebar = None
#     require_auth = None
#     print(f"Authentication module error: {e}")

# # Page configuration - MUST BE FIRST STREAMLIT COMMAND
# st.set_page_config(
#     page_title="AI Resume Shortlisting System",
#     page_icon="📋",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # Custom CSS for better styling
# st.markdown("""
#     <style>
#     .main {
#         padding: 0rem 1rem;
#     }
#     .stAlert {
#         margin-top: 1rem;
#     }
#     .candidate-card {
#         padding: 1.5rem;
#         border-radius: 0.5rem;
#         border: 1px solid #e0e0e0;
#         margin-bottom: 1rem;
#         background-color: #ffffff;
#     }
#     .metric-card {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         padding: 1rem;
#         border-radius: 0.5rem;
#         color: white;
#         text-align: center;
#     }
#     .score-excellent {
#         color: #10b981;
#         font-weight: bold;
#     }
#     .score-good {
#         color: #f59e0b;
#         font-weight: bold;
#     }
#     .score-moderate {
#         color: #ef4444;
#         font-weight: bold;
#     }
#     h1 {
#         color: #1e3a8a;
#     }
#     </style>
# """, unsafe_allow_html=True)

# # Import resources
# from resources import (
#     get_resume_parser,
#     get_ranker,
#     get_job_parser,
#     get_question_generator,
#     get_answer_evaluator,
#     get_supabase
# )


# class ResumeShortlistingApp:
#     """Main application class for the web interface"""
    
#     def __init__(self):
#         """Initialize the application - SESSION STATE MUST BE FIRST"""
        
#         # CRITICAL: Initialize session state BEFORE anything else
#         self._initialize_session_state()
        
#         # Now initialize all other components
#         self.parser = get_resume_parser()
#         self.ranker = get_ranker()
#         self.job_parser = get_job_parser()
#         self.question_generator = get_question_generator()
#         self.answer_evaluator = get_answer_evaluator()
        
#         # Initialize agent components
#         try:
#             self.agent_available = True
#         except Exception as e:
#             st.warning(f"⚠️ Agent features not available: {str(e)}")
#             self.agent_available = False
        
#         # Initialize database with error handling
#         try:
#             self.db = get_supabase()
#             self.db_available = True
#         except Exception as e:
#             st.error(f"⚠️ Database connection failed: {str(e)}")
#             st.info("The app will continue with limited functionality (no persistence).")
#             self.db_available = False
#             self.db = None
        
#         # Initialize authentication (optional - if module is not available, skip it)
#         if AUTH_AVAILABLE:
#             try:
#                 self.auth_manager = AuthManager()
#             except Exception as e:
#                 st.warning(f"⚠️ Authentication setup warning: {str(e)}")
#                 self.auth_manager = None
#         else:
#             self.auth_manager = None
    
#     def _initialize_session_state(self):
#         """Initialize all session state variables - ONLY place for initialization"""
#         defaults = {
#             'initialized': True,
#             'parsed_resumes': [],
#             'ranked_candidates': [],
#             'job_description': "",
#             'current_job_id': None,
#             'current_job_title': "",
#             'page': 'Dashboard',
#             'authenticated': False,
#             'user_email': None,
#             'qa_questions': {},  
#             'candidate_questions': {},  
#             'generated_questions': None,  
#             'selected_candidate_for_questions': None,
#             'show_ats_guide': False
#         }
        
#         for key, value in defaults.items():
#             if key not in st.session_state:
#                 st.session_state[key] = value
    
#     def navigate_to(self, page_name):
#         """Safe navigation helper"""
#         st.session_state.page = page_name
        
    
#     def run(self):
#         """Main application runner"""
        
#         # CRITICAL FIX: Initialize session state FIRST, before ANYTHING else
#         self._initialize_session_state()
        
#         # Fast authentication check (no blocking)
#         if self.auth_manager:
#             # This is now instant - just checks session state
#             if not self.auth_manager.is_authenticated():
#                 render_auth_page()
#                 st.stop()
#                 return
        
#         # Header
#         st.title("🎯 AI Resume Shortlisting System")
#         st.markdown("**Intelligent Resume Screening powered by Machine Learning**")
#         st.markdown("---")
        
#         # Sidebar
#         self.render_sidebar()
        
#         # Render auth sidebar if available
#         try:
#             if self.auth_manager:
#                 render_auth_sidebar()
#         except:
#             pass
        
#         # Main content based on selected page
#         page = st.session_state.get('page', 'Dashboard')

#         # Route to appropriate page
#         page_methods = {
#             'Dashboard': self.page_dashboard,
#             'Upload Resumes': self.page_upload_resumes,
#             'Bulk Upload': self.page_bulk_upload,
#             'Job Description': self.page_job_description,
#             'Rankings': self.page_rankings,
#             'Agent Q&A': self.page_agent_qa,
#             'Send Emails': self.page_send_emails,
#             'Interview Questions': self.page_interview_questions,
#             'Analytics': self.page_analytics,
#             'History': self.page_history,
#             'Search': self.page_search
#         }
        
#         page_method = page_methods.get(page, self.page_dashboard)

#         try:
#             page_method()
#         except Exception as e:
#             st.error(f"Error loading page: {str(e)}")
#             import traceback
#             st.code(traceback.format_exc())
            
    
#     def render_sidebar(self):
#         """Render sidebar navigation"""
#         with st.sidebar:
#             # Logo
#             st.image("images.jpg", width=200)
#             st.markdown("---")
            
#             # Navigation using callback to avoid state modification error
#             st.header("📋 Navigation")
            
#             # Store current selection
#             current_page = st.session_state.get('page', 'Dashboard')
            
#             pages = [
#                 "Dashboard",
#                 "Upload Resumes",
#                 "Bulk Upload",
#                 "Job Description",
#                 "Rankings",
#                 "Agent Q&A",
#                 "Send Emails",
#                 "Interview Questions",
#                 "Analytics",
#                 "History",
#                 "Search"
#             ]
            
#             # Use radio without modifying session_state in callback
#             selected_page = st.radio(
#                 "Go to:",
#                 pages,
#                 index=pages.index(current_page) if current_page in pages else 0
#             )
            
#             # Update page if changed
#             if selected_page != current_page:
#                 st.session_state.page = selected_page
                
            
#             st.markdown("---")
            
#             # Statistics
#             st.header("📊 Statistics")
#             st.metric("Resumes Uploaded", len(st.session_state.parsed_resumes))
            
#             if st.session_state.ranked_candidates:
#                 excellent = sum(1 for c in st.session_state.ranked_candidates 
#                               if c['overall_score'] >= 80)
#                 st.metric("Excellent Matches", excellent)
            
#             st.markdown("---")
            
#             # Clear data button with callback
#             def clear_all_data():
#                 st.session_state.parsed_resumes = []
#                 st.session_state.ranked_candidates = []
#                 st.session_state.job_description = ""
#                 st.session_state.current_job_id = None
#                 st.session_state.current_job_title = ""
            
#             if st.button("🗑️ Clear All Data", use_container_width=True, on_click=clear_all_data):
#                 st.success("Data cleared!")
                
    
#     # ============================================================
#     # PAGE METHODS
#     # ============================================================
    
#     def page_bulk_upload(self):
#         """Bulk resume upload page"""
#         try:
#             render_bulk_upload_ui(self.parser, self.db if self.db_available else None)
#         except Exception as e:
#             st.error(f"Error in bulk upload: {str(e)}")
#             st.info("Please check your parser configuration.")

#     def page_send_emails(self):
#         """Email sending page"""
#         if not st.session_state.ranked_candidates:
#             st.warning("⚠️ No candidates to email. Please rank candidates first!")
#             if st.button("Go to Rankings"):
#                 self.navigate_to('Rankings')
#             return
        
#         try:
#             render_email_panel(
#                 st.session_state.ranked_candidates,
#                 st.session_state.get('current_job_title', 'Open Position')
#             )
#         except Exception as e:
#             st.error(f"Email functionality error: {str(e)}")
#             st.info("""
#             **Email Setup Required:**
#             1. Enable 2-Factor Authentication on your Gmail account
#             2. Generate an App Password: https://myaccount.google.com/apppasswords
#             3. Update your email configuration with the 16-character app password
            
#             **Note:** Regular Gmail passwords won't work due to security restrictions.
#             """)

#     def page_interview_questions(self):
#         """Interview questions page"""
#         st.header("🎯 Generate Interview Questions")
        
#         if not st.session_state.ranked_candidates:
#             st.warning("⚠️ No candidates available. Please rank candidates first!")
#             if st.button("Go to Rankings"):
#                 self.navigate_to('Rankings')
#             return
        
#         # Select candidate
#         st.markdown("### Select Candidate")
        
#         candidate_names = [c['name'] for c in st.session_state.ranked_candidates]
#         selected_name = st.selectbox("Choose candidate:", candidate_names)
        
#         if selected_name:
#             selected_candidate = next(
#                 c for c in st.session_state.ranked_candidates 
#                 if c['name'] == selected_name
#             )
            
#             # Show candidate info
#             col1, col2, col3 = st.columns(3)
#             with col1:
#                 st.metric("Overall Score", f"{selected_candidate['overall_score']:.1f}%")
#             with col2:
#                 st.metric("Experience", f"{selected_candidate.get('total_experience', 0)} years")
#             with col3:
#                 st.metric("Matched Skills", len(selected_candidate.get('matched_skills', [])))
            
#             st.markdown("---")
            
#             job_title = st.text_input(
#                 "Job Title",
#                 value=st.session_state.get('current_job_title', 'Software Engineer')
#             )
            
#             # Generate button
#             if st.button("🚀 Generate Interview Questions", type="primary", use_container_width=True):
#                 try:
#                     with st.spinner("Generating personalized interview questions..."):
#                         # Store in session state
#                         st.session_state.selected_candidate_for_questions = selected_candidate
#                         st.session_state.generated_questions = {
#                             'candidate': selected_candidate,
#                             'job_title': job_title
#                         }
#                         st.success("✅ Questions generated successfully!")
#                 except Exception as e:
#                     st.error(f"Question generation error: {str(e)}")
#                     import traceback
#                     st.code(traceback.format_exc())
            
#             # Display questions if they exist
#             if st.session_state.generated_questions and \
#                st.session_state.generated_questions['candidate']['name'] == selected_name:
#                 render_question_generator_ui(
#                     st.session_state.generated_questions['candidate'],
#                     st.session_state.generated_questions['job_title']
#                 )

#     def page_dashboard(self):
#         """Analytics dashboard"""
#         st.header("📊 Dashboard")
        
#         # Get stats from database if available, otherwise from session
#         if self.db_available:
#             try:
#                 stats = self.db.get_analytics_summary()
#             except Exception as e:
#                 st.warning(f"Could not load database stats: {str(e)}")
#                 stats = {
#                     'total_resumes': len(st.session_state.parsed_resumes),
#                     'total_jobs': 0,
#                     'total_rankings': len(st.session_state.ranked_candidates)
#                 }
#         else:
#             stats = {
#                 'total_resumes': len(st.session_state.parsed_resumes),
#                 'total_jobs': 0,
#                 'total_rankings': len(st.session_state.ranked_candidates)
#             }
        
#         col1, col2, col3 = st.columns(3)
        
#         with col1:
#             st.metric("📄 Total Resumes", stats.get('total_resumes', 0))
        
#         with col2:
#             st.metric("💼 Job Postings", stats.get('total_jobs', 0))
        
#         with col3:
#             st.metric("🎯 Rankings Done", stats.get('total_rankings', 0))
        
#         # Add recruiter feedback stats
#         if self.db_available:
#             try:
#                 feedback_stats = self.db.get_recruiter_feedback_stats()
                
#                 if feedback_stats['total'] > 0:
#                     st.markdown("---")
#                     st.markdown("### 👨‍💼 Recruiter Decisions")
                    
#                     col1, col2, col3, col4 = st.columns(4)
                    
#                     with col1:
#                         st.metric("Total Decisions", feedback_stats['total'])
                    
#                     with col2:
#                         st.metric("✅ Hired", feedback_stats['hired'])
                    
#                     with col3:
#                         st.metric("📞 Interviews", feedback_stats['interview'])
                    
#                     with col4:
#                         st.metric("❌ Rejected", feedback_stats['rejected'])
#             except:
#                 pass
    
#         st.markdown("---")
#         st.markdown("### 📋 Recent Jobs")
        
#         if self.db_available:
#             try:
#                 jobs = self.db.get_all_job_postings()
                
#                 if jobs:
#                     for job in jobs[:5]:
#                         col_a, col_b = st.columns([3, 1])
#                         with col_a:
#                             st.write(f"**{job['title']}**")
#                         with col_b:
#                             st.write(job['created_at'][:10])
#                 else:
#                     st.info("No jobs yet! Go to Job Description tab to create one.")
#             except Exception as e:
#                 st.warning(f"Database error: {str(e)}")
#                 st.info("Could not load job history. Database tables may need to be created.")
#         else:
#             st.info("Database not available. Job history requires database connection.")
    
#     def page_history(self):
#         """View past job postings and rankings"""
#         st.header("📚 Ranking History")
        
#         if not self.db_available:
#             st.warning("⚠️ Database not available. History feature requires database connection.")
#             st.info("Recent rankings are available in the Rankings tab.")
#             if st.button("Go to Rankings"):
#                 self.navigate_to('Rankings')
#             return
        
#         try:
#             jobs = self.db.get_all_job_postings()
#         except Exception as e:
#             st.error(f"Failed to load job history: {str(e)}")
#             st.info("""
#             **Database tables may be missing.** Please run this SQL to create them:
            
#             ```sql
#             CREATE TABLE IF NOT EXISTS public.job_postings (
#                 id SERIAL PRIMARY KEY,
#                 job_title VARCHAR(255) NOT NULL,
#                 job_description TEXT NOT NULL,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             );
#             ```
#             """)
#             return
        
#         if not jobs:
#             st.info("No history yet. Match some candidates first!")
#             if st.button("Go to Job Description"):
#                 self.navigate_to('Job Description')
#             return
        
#         for job in jobs:
#             with st.expander(f"📋 {job['title']} ({job['created_at'][:10]})"):
#                 st.markdown(f"**Job Description:**")
#                 st.text(job['description'][:300] + "...")
                
#                 try:
#                     rankings = self.db.get_rankings_by_job(job['id'])
#                 except Exception as e:
#                     st.warning(f"Could not load rankings: {str(e)}")
#                     rankings = []
                
#                 if rankings:
#                     st.markdown(f"**📊 {len(rankings)} Candidates Ranked**")
                    
#                     sorted_rankings = sorted(rankings, 
#                                            key=lambda x: x['overall_score'], 
#                                            reverse=True)
                    
#                     st.markdown("**Top 3:**")
#                     for i, rank in enumerate(sorted_rankings[:3], 1):
#                         col1, col2 = st.columns([3, 1])
#                         with col1:
#                             st.write(f"{i}. Candidate #{i}")
#                         with col2:
#                             st.write(f"**{rank['overall_score']:.1f}%**")
                    
#                     def load_results(job_id, rankings_data):
#                         formatted_rankings = []
#                         for idx, rank in enumerate(rankings_data, 1):
#                             formatted_rankings.append({
#                                 'name': f"Candidate #{idx}",
#                                 'email': 'N/A',
#                                 'phone': 'N/A',
#                                 'overall_score': rank['overall_score'],
#                                 'skills_score': rank.get('skills_score', 0),
#                                 'experience_score': rank.get('experience_score', 0),
#                                 'education_score': rank.get('education_score', 0),
#                                 'total_experience': 0,
#                                 'matched_skills': rank.get('matched_skills', []),
#                                 'missing_skills': rank.get('missing_skills', []),
#                                 'explanation': rank.get('explanation', {})
#                             })
#                         st.session_state.ranked_candidates = formatted_rankings
                    
#                     if st.button(f"📊 View Full Results", 
#                                key=f"view_{job['id']}", 
#                                use_container_width=True,
#                                on_click=load_results,
#                                args=(job['id'], sorted_rankings)):
#                         st.success("Results loaded! Go to Rankings tab.")
#                 else:
#                     st.info("No rankings for this job yet.")
    
#     def page_search(self):
#         """Search candidates by skills"""
#         st.header("🔍 Search Candidates")
        
#         if not self.db_available:
#             st.warning("⚠️ Database not available. Search feature requires database connection.")
#             st.info("You can view uploaded resumes in the 'Upload Resumes' tab.")
#             if st.button("Go to Upload Resumes"):
#                 self.navigate_to('Upload Resumes')
#             return
        
#         col1, col2 = st.columns([3, 1])
        
#         with col1:
#             search_skill = st.text_input(
#                 "Enter skill to search",
#                 placeholder="e.g., Python, React, AWS, Machine Learning"
#             )
        
#         with col2:
#             st.write("")
#             st.write("")
#             search_button = st.button("🔍 Search", use_container_width=True, type="primary")
        
#         if search_button and search_skill:
#             with st.spinner(f"Searching for '{search_skill}'..."):
#                 try:
#                     results = self.db.search_candidates_by_skill(search_skill)
#                 except Exception as e:
#                     st.error(f"Search failed: {str(e)}")
#                     return
                
#                 if results:
#                     st.success(f"Found {len(results)} candidates with '{search_skill}'")
                    
#                     for resume in results:
#                         data = resume['parsed_data']
#                         name = data['contact'].get('name', 'Unknown')
                        
#                         with st.expander(f"📄 {name}"):
#                             col_a, col_b = st.columns(2)
                            
#                             with col_a:
#                                 st.markdown("**Contact:**")
#                                 st.write(f"📧 {data['contact'].get('email', 'N/A')}")
#                                 st.write(f"📱 {data['contact'].get('phone', 'N/A')}")
                            
#                             with col_b:
#                                 st.markdown("**Experience:**")
#                                 st.write(f"⏱️ {data.get('total_experience_years', 0)} years")
#                                 st.write(f"💼 {len(data.get('experience', []))} jobs")
                            
#                             st.markdown("**Skills:**")
#                             all_skills = []
#                             for skills in data.get('skills', {}).values():
#                                 all_skills.extend(skills)
                            
#                             if all_skills:
#                                 skills_text = ", ".join(all_skills[:15])
#                                 st.write(skills_text)
                                
#                                 if len(all_skills) > 15:
#                                     st.caption(f"+{len(all_skills) - 15} more skills")
#                             else:
#                                 st.write("No skills found")
#                 else:
#                     st.warning(f"No candidates found with skill '{search_skill}'")
#                     st.info("💡 Try searching for: Python, JavaScript, AWS, Machine Learning, React")
        
#         elif search_button and not search_skill:
#             st.error("Please enter a skill to search!")
    
#     def page_upload_resumes(self):
#         """Resume upload and parsing page with ATS validation"""
#         st.header("📤 Upload & Parse Resumes")

#         # Tabs for Upload and Guide
#         tab1, tab2 = st.tabs(["📤 Upload Resumes", "📋 ATS Format Guide"])

#         with tab1:
#             # Show ATS warning
#             show_ats_warning()

#             st.markdown("---")

#             col1, col2 = st.columns([2, 1])

#             with col1:
#                 st.markdown("### Upload Resume Files")
#                 st.markdown("**Supported formats:** PDF, DOCX")
#                 st.caption("⚠️ For best results, upload ATS-friendly resumes")

#                 uploaded_files = st.file_uploader(
#                     "Choose resume files",
#                     type=['pdf', 'docx'],
#                     accept_multiple_files=True,
#                     help="Upload ATS-formatted resumes for accurate parsing"
#                 )

#                 if uploaded_files:
#                     if st.button("🔍 Parse All Resumes", type="primary", use_container_width=True):
#                         self.parse_uploaded_files_with_ats_check(uploaded_files)

#             with col2:
#                 st.markdown("### Quick Stats")
#                 st.info(f"**Total Resumes:** {len(st.session_state.parsed_resumes)}")

#                 if st.session_state.parsed_resumes:
#                     avg_exp = sum(r.get('total_experience_years', 0) 
#                                 for r in st.session_state.parsed_resumes) / len(st.session_state.parsed_resumes)
#                     st.info(f"**Avg Experience:** {avg_exp:.1f} years")

#                     # Show ATS scores if available
#                     if any('ats_score' in r for r in st.session_state.parsed_resumes):
#                         avg_ats = sum(r.get('ats_score', 0) 
#                                     for r in st.session_state.parsed_resumes) / len(st.session_state.parsed_resumes)
#                         st.info(f"**Avg ATS Score:** {avg_ats:.0f}/100")

#             if st.session_state.parsed_resumes:
#                 st.markdown("---")
#                 st.markdown("### 📋 Parsed Resumes")
#                 self.display_parsed_resumes_with_ats()

#         with tab2:
#             # Show ATS Guide
#             render_ats_guide()

#     def parse_uploaded_files_with_ats_check(self, uploaded_files):
#         """Parse uploaded resume files with ATS validation"""
#         ats_validator = ATSResumeValidator()

#         progress_bar = st.progress(0)
#         status_text = st.empty()

#         parsed_count = 0

#         for i, uploaded_file in enumerate(uploaded_files):
#             status_text.text(f"Parsing: {uploaded_file.name}")

#             try:
#                 temp_path = f"temp_{uploaded_file.name}"
#                 with open(temp_path, "wb") as f:
#                     f.write(uploaded_file.getbuffer())

#                 resume_data = self.parser.parse_resume(temp_path)
#                 resume_data['filename'] = uploaded_file.name

#                 # ATS Validation
#                 is_ats, ats_score, issues = ats_validator.validate_resume(resume_data)
#                 resume_data['ats_score'] = ats_score
#                 resume_data['ats_friendly'] = is_ats
#                 resume_data['ats_issues'] = issues

#                 # Save to database if available
#                 if self.db_available:
#                     try:
#                         resume_id = self.db.save_resume(uploaded_file.name, resume_data)
#                         resume_data['id'] = resume_id
#                         self.db.log_action('resume_uploaded', {'filename': uploaded_file.name})
#                     except Exception as e:
#                         st.warning(f"Database save failed: {str(e)}")

#                 st.session_state.parsed_resumes.append(resume_data)
#                 parsed_count += 1

#                 # Clean up temp file
#                 if os.path.exists(temp_path):
#                     os.remove(temp_path)

#             except Exception as e:
#                 st.error(f"Failed to parse {uploaded_file.name}: {str(e)}")

#             progress_bar.progress((i + 1) / len(uploaded_files))

#         status_text.empty()
#         progress_bar.empty()

#         # Show summary
#         ats_friendly_count = sum(1 for r in st.session_state.parsed_resumes if r.get('ats_friendly', False))

#         st.success(f"✅ Successfully parsed {parsed_count}/{len(uploaded_files)} resumes!")

#         if ats_friendly_count < parsed_count:
#             st.warning(f"""
#             ⚠️ **ATS Compatibility:** {ats_friendly_count}/{parsed_count} resumes are ATS-friendly

#             Non-ATS resumes may have parsing issues. Check the ATS Guide for better results.
#             """)

        

#     def display_parsed_resumes_with_ats(self):
#         """Display list of parsed resumes with ATS scores"""
#         for i, resume in enumerate(st.session_state.parsed_resumes):
#             # Determine ATS badge
#             ats_score = resume.get('ats_score', 0)
#             if ats_score >= 80:
#                 ats_badge = "🟢 ATS: Excellent"
#             elif ats_score >= 60:
#                 ats_badge = "🟡 ATS: Good"
#             else:
#                 ats_badge = "🔴 ATS: Needs Work"

#             with st.expander(f"📄 {resume['contact'].get('name', 'Unknown')} - {resume.get('filename', '')} | {ats_badge}"):
#                 # Show ATS Score prominently
#                 col_ats1, col_ats2, col_ats3 = st.columns([1, 2, 1])

#                 with col_ats1:
#                     st.metric("ATS Score", f"{ats_score}/100")

#                 with col_ats2:
#                     if resume.get('ats_issues'):
#                         st.markdown("**ATS Issues:**")
#                         for issue in resume.get('ats_issues', [])[:3]:
#                             st.caption(issue)

#                 with col_ats3:
#                     if ats_score < 70:
#                         if st.button("📖 Fix Issues", key=f"fix_{i}"):
#                             st.session_state.show_ats_guide = True
                            

#                 st.markdown("---")

#                 # Regular resume display
#                 col1, col2, col3 = st.columns(3)

#                 with col1:
#                     st.markdown("**Contact Info**")
#                     st.write(f"📧 {resume['contact'].get('email', 'N/A')}")
#                     st.write(f"📱 {resume['contact'].get('phone', 'N/A')}")
#                     st.write(f"💼 {resume['contact'].get('linkedin', 'N/A')}")

#                 with col2:
#                     st.markdown("**Experience**")
#                     st.write(f"⏱️ {resume.get('total_experience_years', 0)} years")
#                     st.write(f"💼 {len(resume.get('experience', []))} jobs")
#                     st.write(f"🎓 {len(resume.get('education', []))} degrees")

#                 with col3:
#                     st.markdown("**Skills**")
#                     total_skills = sum(len(v) for v in resume.get('skills', {}).values())
#                     st.write(f"🛠️ {total_skills} skills")

#                     all_skills = []
#                     for skills in resume.get('skills', {}).values():
#                         all_skills.extend(skills)
#                     if all_skills:
#                         st.write(f"Top: {', '.join(all_skills[:3])}")

#                 def remove_resume(index):
#                     st.session_state.parsed_resumes.pop(index)

#                 if st.button(f"🗑️ Remove", key=f"remove_{i}", on_click=remove_resume, args=(i,)):
#                     pass
    
#     def page_job_description(self):
#         """Job description input page"""
#         st.header("📝 Job Description")
        
#         col1, col2 = st.columns([2, 1])
        
#         with col1:
#             st.markdown("### Enter Job Requirements")
            
#             job_description = st.text_area(
#                 "Paste the complete job description here:",
#                 value=st.session_state.job_description,
#                 height=400,
#                 placeholder="""Example:
#         Senior Python Developer

#         Requirements:
#         - 3-5 years of Python experience
#         - Machine Learning expertise
#         - AWS/Cloud experience
#         - Bachelor's in Computer Science

#         Must Have Skills:
#         - Python, TensorFlow, SQL, REST API

#         Nice to Have:
#         - Docker, Kubernetes, React
#         """,
#                         help="Include requirements, skills, experience, and responsibilities"
#             )
            
#             st.session_state.job_description = job_description
            
#             col_btn1, col_btn2 = st.columns(2)
            
#             def use_sample():
#                 st.session_state.job_description = self.get_sample_job_description()
            
#             with col_btn1:
#                 if st.button("✨ Use Sample Job", use_container_width=True, on_click=use_sample):
#                     pass
            
#             with col_btn2:
#                 if st.button("🚀 Match Candidates", type="primary", use_container_width=True):
#                     if not st.session_state.parsed_resumes:
#                         st.error("Please upload resumes first!")
#                     elif not job_description.strip():
#                         st.error("Please enter a job description!")
#                     else:
#                         self.match_candidates(job_description)
        
#         with col2:
#             if job_description:
#                 st.markdown("### 🔍 Job Analysis")
                
#                 try:
#                     job_data = self.job_parser.parse_job_description(job_description)
                    
#                     st.info(f"**Position:** {job_data['title']}")
#                     st.info(f"**Min Experience:** {job_data['min_experience']} years")
                    
#                     if job_data['required_skills']:
#                         with st.expander("Required Skills"):
#                             for skill in job_data['required_skills'][:10]:
#                                 st.write(f"• {skill}")
                    
#                     if job_data['preferred_skills']:
#                         with st.expander("Preferred Skills"):
#                             for skill in job_data['preferred_skills'][:10]:
#                                 st.write(f"• {skill}")
#                 except Exception as e:
#                     st.warning(f"Job parsing error: {str(e)}")
    
#     def match_candidates(self, job_description):
#         """Match candidates with job description"""
#         with st.spinner("🤖 Analyzing candidates..."):
#             try:
#                 # Parse job description first
#                 job_data = self.job_parser.parse_job_description(job_description)
#                 st.session_state.current_job_title = job_data['title']
                
#                 # Rank candidates
#                 ranked = self.ranker.rank_candidates(
#                     st.session_state.parsed_resumes,
#                     job_description
#                 )
                
#                 st.session_state.ranked_candidates = ranked
                
#                 # Try to save to database (but don't fail if it doesn't work)
#                 job_id = None
#                 if self.db_available and self.db:
#                     try:
#                         job_id = self.db.save_job_posting(
#                             job_data['title'],
#                             job_description,
#                             job_data
#                         )
#                         st.session_state.current_job_id = job_id
                        
#                         # Try to save rankings
#                         if job_id:
#                             saved = self.db.save_ranking(job_id, ranked)
#                             if saved:
#                                 st.info(f"💾 Saved {saved} rankings to database")
                        
#                     except Exception as db_error:
#                         error_msg = str(db_error)
                        
#                         # Show helpful error message
#                         if 'row-level security' in error_msg.lower() or 'policy' in error_msg.lower():
#                             st.warning("""
#                             ⚠️ **Database Permission Issue**
                            
#                             Your Supabase database has Row-Level Security enabled. 
                            
#                             **Quick Fix:**
#                             1. Go to your Supabase Dashboard
#                             2. Click on "Authentication" → "Policies"
#                             3. For tables `job_postings`, `rankings`, and `recruiter_feedback`:
#                                - Click "New Policy"
#                                - Choose "Enable insert access for all users"
#                                - Click "Save"
                            
#                             **Or disable RLS completely:**
#                             ```sql
#                             ALTER TABLE job_postings DISABLE ROW LEVEL SECURITY;
#                             ALTER TABLE rankings DISABLE ROW LEVEL SECURITY;
#                             ALTER TABLE recruiter_feedback DISABLE ROW LEVEL SECURITY;
#                             ```
                            
#                             The app will continue working without database persistence.
#                             """)
#                         elif 'does not exist' in error_msg.lower():
#                             st.warning(f"""
#                             ⚠️ **Database Table Missing**
                            
#                             Table not found. Please create it in Supabase:
                            
#                             {error_msg}
                            
#                             The app will continue working without database persistence.
#                             """)
#                         else:
#                             st.warning(f"⚠️ Database save failed: {error_msg}")
#                             st.info("Results are available in memory but not persisted.")
                
#                 # Show success summary
#                 total = len(ranked)
                
#                 # Check if agent decisions exist
#                 if ranked and 'agent_decision' in ranked[0]:
#                     shortlisted = sum(1 for c in ranked if c.get('agent_decision') == 'auto_shortlist')
#                     questions_needed = sum(1 for c in ranked if c.get('agent_decision') == 'ask_questions')
#                     rejected = sum(1 for c in ranked if c.get('agent_decision') == 'auto_reject')
                    
#                     st.success(f"""
#                     ✅ **Analysis Complete!**
                    
#                     📊 **Results:**
#                     - 🟢 Auto-Shortlisted: **{shortlisted}** candidates
#                     - 🟡 Questions Needed: **{questions_needed}** candidates
#                     - 🔴 Auto-Rejected: **{rejected}** candidates
                    
#                     👉 Go to **Rankings** tab to view detailed results.
#                     """)
#                 else:
#                     # Fallback for simple ranking
#                     excellent = sum(1 for c in ranked if c.get('overall_score', 0) >= 80)
#                     good = sum(1 for c in ranked if 60 <= c.get('overall_score', 0) < 80)
#                     moderate = sum(1 for c in ranked if c.get('overall_score', 0) < 60)
                    
#                     st.success(f"""
#                     ✅ **Ranking Complete!**
                    
#                     📊 **Results:**
#                     - 🟢 Excellent Match (80%+): **{excellent}** candidates
#                     - 🟡 Good Match (60-79%): **{good}** candidates
#                     - 🟠 Moderate Match (<60%): **{moderate}** candidates
                    
#                     👉 Go to **Rankings** tab to view detailed results.
#                     """)
                
#             except AttributeError as e:
#                 st.error(f"❌ Method not found: {str(e)}")
#                 st.info("""
#                 **The ranking method doesn't exist.** 
                
#                 Please check your `job_resume_matcher.py` file and verify the correct method name.
#                 Common names: `rank_candidates()`, `rank()`, `evaluate_candidates()`
#                 """)
                
#             except Exception as e:
#                 st.error(f"❌ Matching failed: {str(e)}")
                
#                 with st.expander("🔍 Show Error Details"):
#                     import traceback
#                     st.code(traceback.format_exc())
    
#     def page_rankings(self):
#         """Display ranked candidates with AGENT decisions"""
#         st.header("🏆 AI Agent Rankings")

#         if not st.session_state.ranked_candidates:
#             st.warning("⚠️ No rankings yet! Please match candidates with a job description first.")
#             if st.button("Go to Job Description"):
#                 self.navigate_to('Job Description')
#             return

#         # Agent summary metrics
#         candidates = st.session_state.ranked_candidates

#         col1, col2, col3, col4 = st.columns(4)

#         shortlisted = [c for c in candidates if c.get('agent_decision') == 'auto_shortlist']
#         questions_needed = [c for c in candidates if c.get('agent_decision') == 'ask_questions']
#         rejected = [c for c in candidates if c.get('agent_decision') == 'auto_reject']

#         with col1:
#             st.metric("Total Candidates", len(candidates))

#         with col2:
#             st.metric("🟢 Auto-Shortlisted", len(shortlisted))

#         with col3:
#             st.metric("🟡 Questions Needed", len(questions_needed))

#         with col4:
#             st.metric("🔴 Auto-Rejected", len(rejected))

#         st.markdown("---")

#         # Filters
#         col1, col2, col3 = st.columns(3)

#         with col1:
#             filter_decision = st.selectbox(
#                 "Filter by Decision",
#                 ["All", "Auto-Shortlisted", "Questions Needed", "Auto-Rejected"]
#             )

#         with col2:
#             min_confidence = st.slider("Minimum Confidence", 0.0, 1.0, 0.0, 0.1)

#         with col3:
#             sort_by = st.selectbox("Sort By", ["Overall Score", "Confidence", "Skills Score"])

#         # Apply filters
#         filtered = candidates.copy()

#         if filter_decision == "Auto-Shortlisted":
#             filtered = shortlisted
#         elif filter_decision == "Questions Needed":
#             filtered = questions_needed
#         elif filter_decision == "Auto-Rejected":
#             filtered = rejected

#         filtered = [c for c in filtered if c.get('confidence_score', 0) >= min_confidence]

#         # Sort
#         if sort_by == "Overall Score":
#             filtered.sort(key=lambda x: x['overall_score'], reverse=True)
#         elif sort_by == "Confidence":
#             filtered.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
#         elif sort_by == "Skills Score":
#             filtered.sort(key=lambda x: x['skills_score'], reverse=True)

#         st.markdown(f"### Showing {len(filtered)} Candidates")

#         # Display candidates with agent info
#         for i, candidate in enumerate(filtered, 1):
#             self.display_agent_candidate_card(i, candidate)

#         st.markdown("---")

#         # Download options
#         col1, col2 = st.columns(2)

#         with col1:
#             if st.button("📥 Download Report (JSON)", use_container_width=True):
#                 self.download_json_report()

#         with col2:
#             if st.button("📊 Download Report (CSV)", use_container_width=True):
#                 self.download_csv_report()

#     def display_agent_candidate_card(self, rank, candidate):
#         """Display candidate card WITH agent decision info AND recruiter feedback"""

#         # Determine status based on agent decision
#         decision = candidate.get('agent_decision', 'unknown')
#         confidence = candidate.get('confidence_score', 0)

#         if decision == 'auto_shortlist':
#             emoji = "🟢"
#             status = "AUTO-SHORTLISTED"
#             color = "green"
#         elif decision == 'ask_questions':
#             emoji = "🟡"
#             status = "QUESTIONS NEEDED"
#             color = "orange"
#         elif decision == 'auto_reject':
#             emoji = "🔴"
#             status = "AUTO-REJECTED"
#             color = "red"
#         else:
#             emoji = "⚪"
#             status = "PENDING"
#             color = "gray"

#         score = candidate['overall_score']

#         # Check if recruiter has already made a decision
#         recruiter_decision = candidate.get('recruiter_decision')

#         with st.expander(
#             f"{emoji} **RANK #{rank}: {candidate['name']}** - "
#             f"Score: {score:.1f}% | Confidence: {confidence:.2f} | {status}",
#             expanded=(rank <= 3 and decision == 'auto_shortlist')
#         ):
#             # RECRUITER DECISION BANNER (if exists)
#             if recruiter_decision:
#                 if recruiter_decision == 'hired':
#                     st.success("✅ **HIRED** - This candidate has been hired by the recruiter")
#                 elif recruiter_decision == 'rejected':
#                     st.error("❌ **REJECTED** - This candidate has been rejected by the recruiter")
#                 elif recruiter_decision == 'interview':
#                     st.info("📞 **INTERVIEW SCHEDULED** - Candidate selected for interview")
#                 st.markdown("---")

#             # Header row
#             col1, col2, col3 = st.columns([2, 1, 1])

#             with col1:
#                 st.markdown(f"**📧 Email:** {candidate['email']}")
#                 st.markdown(f"**📱 Phone:** {candidate['phone']}")
#                 st.markdown(f"**⏱️ Experience:** {candidate['total_experience']} years")

#             with col2:
#                 st.markdown("**Match Score**")
#                 st.markdown(f"<h2 style='color: {color};'>{score:.1f}%</h2>", unsafe_allow_html=True)

#             with col3:
#                 st.markdown("**Confidence**")
#                 st.markdown(f"<h2 style='color: {color};'>{confidence:.2f}</h2>", unsafe_allow_html=True)
#                 confidence_level = candidate.get('confidence_level', 'unknown').upper()
#                 st.markdown(f"**Level:** {confidence_level}")

#             st.markdown("---")

#             # Agent Decision Section
#             st.markdown("### 🤖 Agent Decision")

#             col1, col2 = st.columns([1, 1])

#             with col1:
#                 st.markdown(f"**Decision:** {status}")

#                 # Show reasoning
#                 if candidate.get('agent_reasoning'):
#                     st.markdown("**Reasoning:**")
#                     for reason in candidate['agent_reasoning']:
#                         st.markdown(f"• {reason}")

#             with col2:
#                 # Show critical gaps if any
#                 if candidate.get('critical_gaps'):
#                     st.markdown("**⚠️ Critical Gaps:**")
#                     for gap in candidate['critical_gaps']:
#                         st.markdown(f"• {gap}")

#                 # Show missing info
#                 if candidate.get('missing_info'):
#                     st.markdown("**Missing Information:**")
#                     for info in candidate['missing_info'][:3]:
#                         st.caption(f"• {info}")

#             # Generate questions button for candidates needing questions
#             if decision == 'ask_questions' and self.agent_available:
#                 st.markdown("---")

#                 if st.button(f"❓ Generate Follow-up Questions", key=f"gen_q_{rank}"):
#                     with st.spinner("Generating intelligent questions..."):
#                         try:
#                             job_data = self.job_parser.parse_job_description(
#                                 st.session_state.job_description
#                             )

#                             questions = self.question_generator.generate_questions(
#                                 job_data,
#                                 candidate['resume_data'],
#                                 candidate.get('critical_gaps', []),
#                                 candidate.get('missing_info', []),
#                                 confidence
#                             )

#                             st.success("✅ Questions Generated!")

#                             st.markdown("**📝 Follow-up Questions:**")
#                             for i, q in enumerate(questions, 1):
#                                 st.markdown(f"**Q{i}:** {q['question']}")
#                                 st.caption(f"Gap: {q['gap_addressed']} | Priority: {q['priority']}")
#                                 st.markdown("")

#                             # Store questions in session for later use
#                             if 'candidate_questions' not in st.session_state:
#                                 st.session_state.candidate_questions = {}

#                             st.session_state.candidate_questions[candidate['email']] = questions

#                         except Exception as e:
#                             st.error(f"Failed to generate questions: {str(e)}")

#             st.markdown("---")

#             # Score breakdown
#             st.markdown("### 📊 Score Breakdown")

#             scores_df = pd.DataFrame({
#                 'Category': ['Skills', 'Experience', 'Education'],
#                 'Score': [
#                     candidate['skills_score'],
#                     candidate['experience_score'],
#                     candidate['education_score']
#                 ]
#             })

#             fig = px.bar(
#                 scores_df,
#                 x='Category',
#                 y='Score',
#                 color='Score',
#                 color_continuous_scale='RdYlGn',
#                 range_color=[0, 100]
#             )
#             fig.update_layout(height=250, showlegend=False)
#             st.plotly_chart(fig, use_container_width=True, key=f"score_chart_{rank}")

#             # Skills
#             col1, col2 = st.columns(2)

#             with col1:
#                 st.markdown("### ✅ Matched Skills")
#                 if candidate['matched_skills']:
#                     for skill in candidate['matched_skills'][:10]:
#                         st.markdown(f"✓ {skill}")
#                     if len(candidate['matched_skills']) > 10:
#                         st.markdown(f"*+{len(candidate['matched_skills']) - 10} more*")
#                 else:
#                     st.markdown("*No exact skill matches*")

#             with col2:
#                 st.markdown("### ❌ Missing Skills")
#                 if candidate['missing_skills']:
#                     for skill in candidate['missing_skills'][:10]:
#                         st.markdown(f"✗ {skill}")
#                     if len(candidate['missing_skills']) > 10:
#                         st.markdown(f"*+{len(candidate['missing_skills']) - 10} more*")
#                 else:
#                     st.markdown("*All required skills present*")

#             # RECRUITER FEEDBACK SECTION
#             st.markdown("---")
#             st.markdown("### 👨‍💼 Recruiter Decision")

#             if not recruiter_decision:
#                 st.markdown("*Make your hiring decision for this candidate:*")

#                 col1, col2, col3 = st.columns(3)

#                 with col1:
#                     if st.button("✅ Hire", key=f"hire_{rank}", use_container_width=True, type="primary"):
#                         self._record_recruiter_decision(candidate, 'hired', rank)

#                 with col2:
#                     if st.button("📞 Interview", key=f"interview_{rank}", use_container_width=True):
#                         self._record_recruiter_decision(candidate, 'interview', rank)

#                 with col3:
#                     if st.button("❌ Reject", key=f"reject_{rank}", use_container_width=True):
#                         self._record_recruiter_decision(candidate, 'rejected', rank)
#             else:
#                 st.info(f"Decision already recorded: **{recruiter_decision.upper()}**")

#                 if st.button("🔄 Change Decision", key=f"change_{rank}"):
#                     # Allow changing decision
#                     candidate['recruiter_decision'] = None
                    

#     def _record_recruiter_decision(self, candidate, decision, rank):
#         """Record recruiter's hiring decision"""

#         # Show feedback form
#         st.markdown("---")
#         feedback = st.text_area(
#             f"Optional feedback for {candidate['name']}:",
#             placeholder="e.g., Strong technical skills, good cultural fit, needs more experience in X...",
#             key=f"feedback_{decision}_{rank}"
#         )

#         if st.button(f"Confirm {decision.upper()}", key=f"confirm_{decision}_{rank}", type="primary"):
#             # Update candidate in session state
#             for i, c in enumerate(st.session_state.ranked_candidates):
#                 if c['email'] == candidate['email']:
#                     st.session_state.ranked_candidates[i]['recruiter_decision'] = decision
#                     st.session_state.ranked_candidates[i]['recruiter_feedback'] = feedback
#                     break
                
#             # Save to database
#             if self.db_available:
#                 try:
#                     self.db.save_recruiter_feedback(
#                         candidate['email'],
#                         decision,
#                         feedback
#                     )
#                 except Exception as e:
#                     st.warning(f"Could not save to database: {str(e)}")

#             st.success(f"✅ Decision recorded: {decision.upper()}")
            
            

#     def page_agent_qa(self):
#         """Agent Q&A - Interactive follow-up questions and re-evaluation"""
#         st.header("💬 Agent Q&A - Interactive Follow-up")
        
#         if not st.session_state.ranked_candidates:
#             st.warning("⚠️ No candidates to interact with. Please rank candidates first!")
#             if st.button("Go to Rankings"):
#                 self.navigate_to('Rankings')
#             return
        
#         # Filter candidates that need questions
#         candidates_needing_questions = [
#             c for c in st.session_state.ranked_candidates 
#             if c.get('agent_decision') == 'ask_questions'
#         ]
        
#         if not candidates_needing_questions:
#             st.info("✅ No candidates currently need follow-up questions!")
#             st.markdown("All candidates have been either auto-shortlisted or auto-rejected.")
#             if st.button("View Rankings"):
#                 self.navigate_to('Rankings')
#             return
        
#         st.markdown(f"### 🟡 {len(candidates_needing_questions)} Candidates Need Follow-up")
        
#         # Select candidate
#         candidate_names = [c['name'] for c in candidates_needing_questions]
#         selected_name = st.selectbox("Select candidate:", candidate_names)
        
#         if selected_name:
#             candidate = next(c for c in candidates_needing_questions if c['name'] == selected_name)
            
#             # Show candidate summary
#             col1, col2, col3 = st.columns(3)
#             with col1:
#                 st.metric("Match Score", f"{candidate['overall_score']:.1f}%")
#             with col2:
#                 st.metric("Current Confidence", f"{candidate.get('confidence_score', 0):.2f}")
#             with col3:
#                 st.metric("Critical Gaps", len(candidate.get('critical_gaps', [])))
            
#             st.markdown("---")
            
#             # Show critical gaps
#             if candidate.get('critical_gaps'):
#                 st.markdown("**⚠️ Critical Gaps Identified:**")
#                 for gap in candidate['critical_gaps']:
#                     st.markdown(f"• {gap}")
#                 st.markdown("")
            
#             candidate_key = candidate['email']
            
#             # Generate questions button
#             if candidate_key not in st.session_state.qa_questions:
#                 if st.button("🚀 Generate Follow-up Questions", type="primary", use_container_width=True):
#                     with st.spinner("Generating intelligent questions..."):
#                         try:
#                             job_data = self.job_parser.parse_job_description(
#                                 st.session_state.job_description
#                             )
                            
#                             questions = self.question_generator.generate_questions(
#                                 job_data,
#                                 candidate['resume_data'],
#                                 candidate.get('critical_gaps', []),
#                                 candidate.get('missing_info', []),
#                                 candidate.get('confidence_score', 0.5)
#                             )
                            
#                             st.session_state.qa_questions[candidate_key] = {
#                                 'questions': questions,
#                                 'answers': [''] * len(questions),
#                                 'job_data': job_data
#                             }
                            
#                             st.success("✅ Questions generated!")
                            
                            
#                         except Exception as e:
#                             st.error(f"Failed to generate questions: {str(e)}")
#                             import traceback
#                             st.code(traceback.format_exc())
            
#             # Show questions and collect answers
#             if candidate_key in st.session_state.qa_questions:
#                 qa_data = st.session_state.qa_questions[candidate_key]
#                 questions = qa_data['questions']
                
#                 st.markdown("### 📝 Follow-up Questions")
#                 st.markdown("*Please provide detailed answers to help us better assess your fit for this position.*")
#                 st.markdown("")
                
#                 # Collect answers
#                 answers = []
#                 for i, q in enumerate(questions):
#                     st.markdown(f"**Question {i+1}:** {q['question']}")
#                     st.caption(f"Addressing: {q['gap_addressed']} | Priority: {q['priority']}")
                    
#                     answer = st.text_area(
#                         f"Your answer:",
#                         value=qa_data['answers'][i],
#                         height=100,
#                         key=f"answer_{candidate_key}_{i}",
#                         placeholder="Provide specific examples and details..."
#                     )
#                     answers.append(answer)
                    
#                     st.markdown("")
                
#                 # Update answers in session state
#                 st.session_state.qa_questions[candidate_key]['answers'] = answers
                
#                 # Evaluate button
#                 st.markdown("---")
                
#                 col1, col2 = st.columns([2, 1])
                
#                 with col1:
#                     all_answered = all(len(a.strip()) > 10 for a in answers)
                    
#                     if not all_answered:
#                         st.warning("⚠️ Please answer all questions (minimum 10 characters each)")
                    
#                     evaluate_button = st.button(
#                         "🔄 Evaluate Answers & Re-rank",
#                         type="primary",
#                         use_container_width=True,
#                         disabled=not all_answered
#                     )
                
#                 with col2:
#                     if st.button("🗑️ Clear & Regenerate", use_container_width=True):
#                         del st.session_state.qa_questions[candidate_key]
                        
                
#                 # Evaluate answers
#                 if evaluate_button and all_answered:
#                     with st.spinner("🤖 Agent is evaluating your answers..."):
#                         try:
#                             self._evaluate_and_rerank(candidate, questions, answers, qa_data['job_data'])
#                         except Exception as e:
#                             st.error(f"Evaluation failed: {str(e)}")
#                             import traceback
#                             st.code(traceback.format_exc())

#     def _evaluate_and_rerank(self, candidate, questions, answers, job_data):
#         """Evaluate answers and re-rank candidate"""
        
#         # Check if any answers are empty or too short
#         unanswered = [i+1 for i, a in enumerate(answers) if len(a.strip()) < 10]
        
#         if unanswered:
#             st.error(f"⚠️ Questions {', '.join(map(str, unanswered))} not answered properly!")
#             st.markdown("### ❌ Auto-Rejecting Candidate")
#             st.markdown("**Reason:** Failed to provide adequate responses to follow-up questions")
            
#             # Update to auto-reject
#             for i, c in enumerate(st.session_state.ranked_candidates):
#                 if c['email'] == candidate['email']:
#                     st.session_state.ranked_candidates[i]['agent_decision'] = 'auto_reject'
#                     st.session_state.ranked_candidates[i]['confidence_score'] = 0.2
                    
#                     reasoning = candidate.get('agent_reasoning', []).copy()
#                     reasoning.append("Auto-rejected: Did not respond to follow-up questions")
#                     st.session_state.ranked_candidates[i]['agent_reasoning'] = reasoning
#                     break
            
#             st.warning("This candidate has been moved to AUTO-REJECTED")
            
#             if st.button("📊 View Updated Rankings"):
#                 self.navigate_to('Rankings')
            
#             return

#         # Continue with normal evaluation
#         old_confidence = candidate.get('confidence_score', 0)

#         # Evaluate answers using AnswerEvaluator
#         try:
#             evaluation_result = self.answer_evaluator.evaluate_answers(
#                 questions, answers, job_data, candidate
#             )
#             total_confidence_boost = evaluation_result.get('confidence_boost', 0.0)
#         except Exception as e:
#             st.warning(f"Answer evaluation failed: {str(e)}")
#             total_confidence_boost = 0.0

#         new_confidence = min(1.0, old_confidence + total_confidence_boost)

#         st.markdown("---")
#         st.markdown("### 📊 Evaluation Results")

#         col1, col2, col3 = st.columns(3)

#         with col1:
#             st.metric("Previous Confidence", f"{old_confidence:.2f}")

#         with col2:
#             st.metric("Total Boost", f"{total_confidence_boost:+.2f}")

#         with col3:
#             st.metric("New Confidence", f"{new_confidence:.2f}", delta=f"{total_confidence_boost:+.2f}")

#         # Determine new decision
#         job_parsed = self.job_parser.parse_job_description(st.session_state.job_description)
#         temp_agent = AgentBrain(job_parsed)

#         confidence_level = temp_agent._determine_confidence_level(new_confidence)
#         new_decision = temp_agent._make_decision(
#             confidence_level,
#             candidate.get('critical_gaps', []),
#             candidate['overall_score']
#         )

#         old_decision = candidate.get('agent_decision', 'unknown')

#         st.markdown("---")
#         st.markdown("### 📋 Decision Update")

#         col1, col2 = st.columns(2)

#         with col1:
#             st.markdown("**Previous Decision:**")
#             if old_decision == 'auto_shortlist':
#                 st.success("🟢 Auto-Shortlisted")
#             elif old_decision == 'ask_questions':
#                 st.warning("🟡 Questions Needed")
#             else:
#                 st.error("🔴 Auto-Rejected")

#         with col2:
#             st.markdown("**New Decision:**")
#             if new_decision == AgentDecision.AUTO_SHORTLIST:
#                 st.success("🟢 Auto-Shortlisted")
#             elif new_decision == AgentDecision.ASK_QUESTIONS:
#                 st.warning("🟡 More Questions Needed")
#             else:
#                 st.error("🔴 Auto-Rejected")

#         # Update candidate in session state
#         for i, c in enumerate(st.session_state.ranked_candidates):
#             if c['email'] == candidate['email']:
#                 st.session_state.ranked_candidates[i]['confidence_score'] = new_confidence
#                 st.session_state.ranked_candidates[i]['agent_decision'] = new_decision.value

#                 new_reasoning = candidate.get('agent_reasoning', []).copy()
#                 new_reasoning.append(f"Re-evaluated after Q&A: confidence {old_confidence:.2f} → {new_confidence:.2f}")
#                 st.session_state.ranked_candidates[i]['agent_reasoning'] = new_reasoning
#                 break
            
#         st.success("✅ Candidate re-evaluated successfully!")

#         if st.button("📊 View Updated Rankings", type="primary"):
#             self.navigate_to('Rankings')

#     def page_analytics(self):
#         """Analytics and insights page"""
#         st.header("📈 Analytics & Insights")
        
#         if not st.session_state.ranked_candidates:
#             st.warning("No data to analyze. Please rank candidates first!")
#             if st.button("Go to Job Description"):
#                 self.navigate_to('Job Description')
#             return
        
#         candidates = st.session_state.ranked_candidates
        
#         # Agent Decision Distribution
#         st.markdown("### 🤖 Agent Decision Distribution")
        
#         shortlisted = sum(1 for c in candidates if c.get('agent_decision') == 'auto_shortlist')
#         questions = sum(1 for c in candidates if c.get('agent_decision') == 'ask_questions')
#         rejected = sum(1 for c in candidates if c.get('agent_decision') == 'auto_reject')
        
#         fig = go.Figure(data=[go.Pie(
#             labels=['Auto-Shortlisted', 'Questions Needed', 'Auto-Rejected'],
#             values=[shortlisted, questions, rejected],
#             marker_colors=['#10b981', '#f59e0b', '#ef4444'],
#             hole=0.3
#         )])
#         fig.update_layout(height=350)
#         st.plotly_chart(fig, use_container_width=True)
        
#         st.markdown("---")
        
#         # Score Distribution
#         st.markdown("### 📊 Score Distribution")
        
#         scores = [c['overall_score'] for c in candidates]
#         fig = go.Figure(data=[go.Histogram(x=scores, nbinsx=10, marker_color='#667eea')])
#         fig.update_layout(
#             title="Candidate Score Distribution",
#             xaxis_title="Overall Score",
#             yaxis_title="Number of Candidates",
#             height=350
#         )
#         st.plotly_chart(fig, use_container_width=True)
        
#         # Confidence vs Score
#         st.markdown("### 🎯 Confidence vs Match Score")
        
#         df = pd.DataFrame({
#             'Match Score': [c['overall_score'] for c in candidates],
#             'Confidence': [c.get('confidence_score', 0) for c in candidates],
#             'Name': [c['name'] for c in candidates],
#             'Decision': [c.get('agent_decision', 'unknown') for c in candidates]
#         })
        
#         fig = px.scatter(
#             df,
#             x='Match Score',
#             y='Confidence',
#             hover_data=['Name'],
#             color='Decision',
#             color_discrete_map={
#                 'auto_shortlist': '#10b981',
#                 'ask_questions': '#f59e0b',
#                 'auto_reject': '#ef4444'
#             },
#             size=[10]*len(df)
#         )
#         fig.update_layout(height=400)
#         st.plotly_chart(fig, use_container_width=True)
        
#         col1, col2 = st.columns(2)
        
#         with col1:
#             st.markdown("### 💪 Most Common Skills")
#             all_matched_skills = []
#             for c in candidates:
#                 all_matched_skills.extend(c.get('matched_skills', []))
            
#             if all_matched_skills:
#                 skills_count = pd.Series(all_matched_skills).value_counts().head(10)
#                 fig = px.bar(
#                     x=skills_count.values,
#                     y=skills_count.index,
#                     orientation='h',
#                     labels={'x': 'Count', 'y': 'Skill'}
#                 )
#                 fig.update_layout(height=400)
#                 st.plotly_chart(fig, use_container_width=True)
#             else:
#                 st.info("No matched skills data available")
        
#         with col2:
#             st.markdown("### ⚠️ Most Missing Skills")
#             all_missing_skills = []
#             for c in candidates:
#                 all_missing_skills.extend(c.get('missing_skills', []))
            
#             if all_missing_skills:
#                 missing_count = pd.Series(all_missing_skills).value_counts().head(10)
#                 fig = px.bar(
#                     x=missing_count.values,
#                     y=missing_count.index,
#                     orientation='h',
#                     labels={'x': 'Count', 'y': 'Skill'},
#                     color_discrete_sequence=['#ef4444']
#                 )
#                 fig.update_layout(height=400)
#                 st.plotly_chart(fig, use_container_width=True)
#             else:
#                 st.info("No missing skills data available")
        
#         # Critical Gaps Analysis
#         st.markdown("---")
#         st.markdown("### 🔍 Critical Gaps Analysis")
        
#         all_critical_gaps = []
#         for c in candidates:
#             all_critical_gaps.extend(c.get('critical_gaps', []))
        
#         if all_critical_gaps:
#             gaps_count = pd.Series(all_critical_gaps).value_counts().head(10)
            
#             col1, col2 = st.columns([2, 1])
            
#             with col1:
#                 fig = px.bar(
#                     x=gaps_count.values,
#                     y=gaps_count.index,
#                     orientation='h',
#                     labels={'x': 'Number of Candidates', 'y': 'Critical Gap'},
#                     color_discrete_sequence=['#f59e0b']
#                 )
#                 fig.update_layout(height=350)
#                 st.plotly_chart(fig, use_container_width=True)
            
#             with col2:
#                 st.markdown("**Top Critical Gaps:**")
#                 for gap, count in gaps_count.head(5).items():
#                     st.metric(gap, f"{count} candidates")
#         else:
#             st.info("No critical gaps identified across candidates")
        
#         st.markdown("### Experience vs Match Score")
        
#         exp_data = pd.DataFrame({
#             'Experience': [c.get('total_experience', 0) for c in candidates],
#             'Score': [c['overall_score'] for c in candidates],
#             'Name': [c['name'] for c in candidates]
#         })
        
#         fig = px.scatter(
#             exp_data,
#             x='Experience',
#             y='Score',
#             hover_data=['Name'],
#             size=[10]*len(exp_data),
#             color='Score',
#             color_continuous_scale='RdYlGn'
#         )
#         fig.update_layout(height=400)
#         st.plotly_chart(fig, use_container_width=True, key="exp_vs_score")
    
#     def download_json_report(self):
#         """Generate JSON report for download"""
#         report_data = {
#             'generated_at': datetime.now().isoformat(),
#             'total_candidates': len(st.session_state.ranked_candidates),
#             'candidates': st.session_state.ranked_candidates
#         }
        
#         json_str = json.dumps(report_data, indent=2)
#         st.download_button(
#             label="📥 Download JSON",
#             data=json_str,
#             file_name=f"ranking_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
#             mime="application/json"
#         )
    
#     def download_csv_report(self):
#         """Generate CSV report for download"""
#         candidates = st.session_state.ranked_candidates
        
#         csv_data = []
#         for c in candidates:
#             csv_data.append({
#                 'Name': c['name'],
#                 'Email': c['email'],
#                 'Phone': c['phone'],
#                 'Overall Score': c['overall_score'],
#                 'Skills Score': c['skills_score'],
#                 'Experience Score': c['experience_score'],
#                 'Education Score': c['education_score'],
#                 'Total Experience': c.get('total_experience', 0),
#                 'Matched Skills': ', '.join(c.get('matched_skills', [])[:5]),
#                 'Missing Skills': ', '.join(c.get('missing_skills', [])[:5])
#             })
        
#         df = pd.DataFrame(csv_data)
#         csv = df.to_csv(index=False)
        
#         st.download_button(
#             label="📊 Download CSV",
#             data=csv,
#             file_name=f"ranking_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
#             mime="text/csv"
#         )
    
#     def get_sample_job_description(self):
#         """Return sample job description"""
#         return """Senior Python Developer

# We are seeking an experienced Python Developer to join our AI/ML team.

# Requirements:
# - 3-5 years of professional Python development experience
# - Strong experience with Machine Learning frameworks (TensorFlow, PyTorch)
# - Experience with cloud platforms (AWS preferred)
# - Bachelor's degree in Computer Science or related field

# Must Have Skills:
# - Python (expert level)
# - Machine Learning & Deep Learning
# - TensorFlow or PyTorch
# - SQL databases (MySQL, PostgreSQL)
# - REST API development
# - Git version control

# Nice to Have:
# - AWS/Azure/GCP experience
# - Docker and Kubernetes
# - React or frontend experience
# - Experience with NLP projects
# - CI/CD pipelines

# Responsibilities:
# - Develop and deploy machine learning models
# - Build scalable ML pipelines
# - Collaborate with data scientists and engineers
# - Write clean, maintainable, well-documented code
# - Participate in code reviews
# """


# # Main application entry point
# if __name__ == "__main__":
#     app = ResumeShortlistingApp()
#     app.run()
