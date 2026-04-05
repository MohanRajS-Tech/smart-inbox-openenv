import os
import json
import time
from dotenv import load_dotenv
from openai import OpenAI
from environment import SmartInboxEnv
from models import InboxAction

# Automatically load the .env file from the project root
load_dotenv()

# Configuration for Groq
API_BASE_URL = "https://api.groq.com/openai/v1"
MODEL_NAME = "llama-3.1-8b-instant"

def get_llm_action(client, obs):
    """Ask the AI to decide on an email action."""
    
    prompt = f"""
    You are a Smart Email Assistant. Your goal is to keep the inbox clean.
    
    Current Inbox:
    {obs.inbox_view}
    
    Priority Rules:
    1. FLAG emails that are URGENT or IMPORTANT (e.g., Security, Boss, HR, Meetings).
    2. ARCHIVE emails that are Promotional, Social, or News (e.g., Pizza, Shopping, Tool lists).
    3. Use ONLY the numeric ID shown in the [ brackets ].
    
    Reply in JSON format:
    {{
        "thinking": "Brief explanation of why you chose this action",
        "action_type": "flag or archive",
        "email_id": "The numeric ID of the email"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={ "type": "json_object" }
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        
        # Robust handling for List vs Dictionary
        if isinstance(data, list):
            data = data[0] if len(data) > 0 else {}
        
        thinking = data.get("thinking", "No explanation")
        action = data.get("action_type", "none").lower()
        eid = str(data.get("email_id", "none"))
        
        return thinking, action, eid
            
    except Exception as e:
        return f"Brain Error: {str(e)}", "none", "none"

def run_inbox_agent():
    # 1. Setup API Access
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ ERROR: GROQ_API_KEY environment variable not found.")
        print("Set it: $env:GROQ_API_KEY = 'your_key_here'")
        return

    client = OpenAI(base_url=API_BASE_URL, api_key=api_key)
    
    # 2. Setup Environment
    env = SmartInboxEnv()
    obs = env.reset()
    
    total_reward = 0.0
    turns = 0
    
    print("-" * 60)
    print("💌 SMART INBOX LITE: INITIAL STATE")
    print("-" * 60)
    print(obs.inbox_view)
    print("-" * 60)
    
    # 3. Episode Loop
    while not obs.done:
        turns += 1
        print(f"\n[TURN {turns}]")
        
        # BRAIN calls
        thinking, action_type, email_id = get_llm_action(client, obs)
        
        print(f"🤖 THINKING: {thinking}")
        print(f"👉 ACTION: {action_type} for Email ID {email_id}")
        
        # Validate move
        if action_type not in ["flag", "archive", "delete"]:
            print(f"⚠️ Agent tried an invalid action: {action_type}. Ending episode.")
            break
            
        # Execute in Environment
        obs = env.step(InboxAction(action_type=action_type, email_id=email_id.strip()))
        total_reward += obs.reward
        
        # Display Result
        print(obs.inbox_view)
        print(f"RESULT: {obs.last_action_status}")
        print(f"POINTS: {obs.reward} | CURRENT SCORE: {total_reward}")
        
        # Small delay
        time.sleep(1)
        
        # Safety break for loops
        if turns > 10:
            break
            
    print("\n" + "🏁" * 30)
    print(f"SUMMARY: Inbox cleared in {turns} turns.")
    print(f"FINAL REWARD SCORE: {total_reward}")
    print("🏁" * 30)

if __name__ == "__main__":
    run_inbox_agent()
