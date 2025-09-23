import requests
from src.config.settings import settings

BLAND_API_KEY = settings.bland_ai_key

def bland_start_interview(
        profile_id: str,
        course_name: str,

        interview_id: str,
        interview_topic: str,
        interview_max_duration: str,
        interview_questions: str,

        trainer_name: str,
        user_name: str, 
        phone_number: str, 
        ):

    if phone_number.startswith("+91"):
        phone_number = phone_number.replace("+91", "")
    elif phone_number.startswith("91") and len(phone_number) > 10:
        phone_number = phone_number[2:]

    phone_number = "+91" + phone_number
    phone_number = phone_number.strip()

    # Headers
    headers = {
        'Authorization': BLAND_API_KEY,
    }

    # Data
    data = {
        "phone_number": phone_number,
        "voice": "June",
        "wait_for_greeting": False,
        "record": True,
        "answered_by_enabled": True,
        "noise_cancellation": False,
        "interruption_threshold": 100,
        "block_interruptions": False,
        "max_duration": 3,
        "model": "base",
        "memory_id": "bec3c84b-346e-492d-a9dc-c245b30d7aa8",
        "language": "en-IN",
        "background_track": "none",
        "endpoint": "https://api.bland.ai",
        "voicemail_action": "hangup",
        "summary_prompt": "Asses his communication, knowledge, and overall scores out of 10",
        "isCallActive": False,
        "task": f'''
            You are conducting a skill assessment interview for {user_name}, 
            He/She is studying {course_name} in MedhaEduTech, Hyderabad's best IT education institute, trained by {trainer_name}
            Speak in a warm, professional, and engaging manner. 
            Use a conversational tone that builds rapport while maintaining credibility. 
            Show genuine interest in the student's potential.
            ---
            ## Opening
            "Hi! I'm calling on behalf of your trainer {trainer_name} from Medha EduTech for your interview on the topic - {interview_topic}. 
            This will take about {interview_max_duration} minutes
            and this will help us better assess you. Ready to start?"

            ## Questions (Ask in order)

            {interview_questions}

            ## Closing
            "Great talking to you. Based on our conversation, I will share the feedback in the portal after this call.

            Have a great day {user_name}. See you!"
            ---

            ## Key Behavioral Guidelines:
            - Keep responses concise and focused
            - Share course information clearly
            - Guide toward office visit
            - Keep conversations under 10 minutes
            - Collect required information naturally during conversation
            - Be helpful but not overly chatty
            - Wait for complete answers before moving on
            - If answer is too short, say "Can you tell me more about that?"
            - Keep a conversational, encouraging tone
            ''',
        # "first_sentence": f"\"Hi {user_name}, Hope you're doing well. This is an short mock interview call\"",
        "timezone": "Asia/Kolkata",
        "transfer_phone_number": "+917093370381",
        "webhook": "https://webhook.site/e4b575dc-ffc4-45d2-82d0-cc8bb88f32ba",
        "dispositions": [
            'canidate_performance_excellent', 
            'candidate_performance_good', 
            'candidate_performance_average',
            'candidate_performance_poor'
        ],
        "analysis_schema": {
            "performance_summary": "",
            "areas_of_improvement_summary": "",
            "strengths_of_candidate_summary": "",
            "weaknesses_of_candidate_summary": "",
            "communication_score_out_of_10": "",
            "knowledge_score_out_of_10": "",
            "overall_score_out_of_10": ""
        },
        "metadata": {
            "user_id": profile_id,
            "interview_id": interview_id,
            "interview_topic": interview_topic,
            "user_name": user_name,
            "course_name": course_name,
            "trainer_name": trainer_name
        }
    }

    # API request 
    response = requests.post('https://api.bland.ai/v1/calls', json=data, headers=headers)
    
    if response.status_code == 200:
        r = response.json()
        return r
    

def call_status(call_id: str):
    headers = {
        'Authorization': BLAND_API_KEY,
    }
    response = requests.get(f"https://api.bland.ai/v1/calls/{call_id}", headers=headers)
    if response.status_code == 200:
        response = response.json()
        return response
    


def bland_trigger_demo_call(user_name: str, phone_number: str):

    if phone_number.startswith("+91"):
        phone_number = phone_number.replace("+91", "")
    elif phone_number.startswith("91") and len(phone_number) > 10:
        phone_number = phone_number[2:]

    phone_number = "+91" + phone_number
    phone_number = phone_number.strip()

    # Headers
    headers = {
        'Authorization': BLAND_API_KEY,
    }

    # Data
    data = {
        "phone_number": phone_number,
        "voice": "June",
        "wait_for_greeting": False,
        "record": True,
        "answered_by_enabled": True,
        "noise_cancellation": False,
        "interruption_threshold": 100,
        "block_interruptions": False,
        "max_duration": 3,
        "model": "base",
        "memory_id": "e5032a96-d03c-4982-90be-c153d53a9882",
        "language": "en-IN",
        "background_track": "none",
        "endpoint": "https://api.bland.ai",
        "voicemail_action": "hangup",
        "summary_prompt": "Capture every intension of him towards joining a course in our institute",
        "isCallActive": False,
        "task": "# Medha EduTech (MET) AI Agent Prompt\n\n## Core Identity & Tone\nYou are an enthusiastic, knowledgeable AI representative for Medha EduTech (MET), India's premier technology education institute. Speak in a warm, professional, and engaging manner. Use a conversational tone that builds rapport while maintaining credibility. Address the caller respectfully and show genuine interest in their career aspirations.\n\n\n---\n\n## COURSE INFORMATION\n\n### MET Overview\n\"At Medha EduTech, we specialize in hands-on technology training with AI integration. Our 4-month programs combine practical skills with real projects.\"\n\n### Course Portfolio\n\n#### **Digital Marketing with AI** - ₹25,000 | 4 Months\n**Trainer: Mrs. Mounika Patel** (10+ years experience)\n- AI-powered marketing strategies and automation\n- Social media marketing and content creation\n- SEO, Google Ads, and analytics\n- Live campaign projects\n- **Outcome**: Digital Marketing roles, Social Media Manager positions\n\n#### **Python Full Stack with AI** - ₹25,000 | 4 Months  \n**Trainer: Mr. Chaitanya Vaddi** (Industry Professional)\n- Frontend: React.js, HTML5, CSS3, JavaScript\n- Backend: Python Django, APIs, databases\n- AI integration in web applications\n- Cloud deployment and real projects\n- **Outcome**: Full Stack Developer, Software Engineer roles\n\n#### **Python Data Science with AI** - ₹25,000 | 4 Months\n**Trainer: Shahul Shaik** (IIT Madras Alumni)\n- Data analysis with Python (Pandas, NumPy)\n- Machine learning and AI model development\n- Business analytics and visualization\n- Industry case studies\n- **Outcome**: Data Scientist, AI/ML Engineer positions\n\n#### **Additional Courses:**\n- **Cybersecurity**: Network security and ethical hacking\n- **Data Analytics**: Business intelligence and visualization tools\n- **Java Full Stack**: Enterprise development with Spring Boot\n\n### What Makes MET Unique\n- 100% hands-on training with real projects\n- Industry-experienced trainers\n- AI integration in all courses\n- Job placement support\n\n---\n\n## Transition to Office Visit\n\n\"I'd recommend visiting our campus to see our facilities and meet the trainers. You can attend a free demo session and get personalized guidance.\n\nWhen would be convenient for you to visit?\"\n\n---\n\n## Information Collection (Collect Naturally During Conversation)\n\nGather this information organically through conversation, not as a formal questionnaire:\n\n### Required Data Points:\n1. **Timeline**: \"How soon are you looking to start your tech journey?\"\n2. **Course Interest**: \"Based on our discussion, which program excites you most?\"  \n3. **Discovery Source**: \"By the way, how did you hear about MET? Was it through a friend's recommendation, online search, or somewhere else?\"\n\n### JSON Schema Format:\n```json\n{\n  \"how_soon_can_join\": \"string (e.g., 'immediately', 'within 2 weeks', 'next month')\",\n  \"course_interested\": \"string (exact course name)\",\n  \"how_heard_about_us\": \"string (e.g., 'referral from friend', 'Google search', 'social media')\"\n  \"user_stay_location\": \"string (e.g,. Hyderabad, Mumbai, Andhra Pradesh etc..)\"\n}\n```\n\n---\n\n## Closing Script\n\"Great! I'll send all course details and our location to your phone after this call.\n\nIs there anything specific you'd like to know about our programs?\"\n\n---\n\n## Key Behavioral Guidelines:\n- Keep responses concise and focused\n- Share course information clearly\n- Guide toward office visit\n- Keep conversations under 5 minutes\n- Collect required information naturally during conversation\n- Be helpful but not overly chatty",
        "first_sentence": f"\"Hi {user_name}, Hope you're doing well. What brings to medha edu tech today? How can I help you?\"",
        "timezone": "Asia/Kolkata",
        "transfer_phone_number": "+917093370381",
        "webhook": "https://met-ai-api.vercel.app/webhook/bland_ai_callback",
        "analysis_schema": {
            "interested_course_name": "",
            "how_soon_can_he_join": "",
            "is_potential_lead": "",
            "user_stay_location": ""
        },
        "metadata": {
            "source": "wp_home"
        }
    }

    # API request 
    requests.post('https://api.bland.ai/v1/calls', json=data, headers=headers)