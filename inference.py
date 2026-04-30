import asyncio
import os
import textwrap
import json
import httpx
from typing import List, Optional

from openai import OpenAI
from my_env_v4 import MyEnvV4Action, MyEnvV4Env

# --------------------------------------------------------------------------
# CONFIGURATION
# --------------------------------------------------------------------------
IMAGE_NAME = os.getenv("IMAGE_NAME", "smart_inbox_lite:latest")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("GROQ_API_KEY") or os.getenv("API_KEY")

API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.getenv("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"
BENCHMARK = os.getenv("SMART_INBOX_BENCHMARK", "smart_inbox_lite")

# Consolidated 3 levels for Phase 1 Competitiveness
TASKS = ["easy-triage", "medium-triage", "hard-triage"]

# Updated steps: Generative tasks require more reasoning and moves.
MAX_STEPS = 10 

TEMPERATURE = 0.1
MAX_TOKENS = 512
SUCCESS_SCORE_THRESHOLD = 0.85

# --------------------------------------------------------------------------
# MANDATORY STDOUT LOGGING (Strict Regex Patterns for Evaluation)
# --------------------------------------------------------------------------
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if (error and error != "null") else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.3f} done={done_val} error={error_val}",
        flush=True,
    )

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.3f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

# --------------------------------------------------------------------------
# AGENT BRAIN (Advanced Reasoning with Security Focus)
# --------------------------------------------------------------------------
SYSTEM_PROMPT = textwrap.dedent("""
    You are a Senior Security & Triage Assistant. You must process a corporate inbox with extreme rigor.
    
    CRITICAL WORKFLOW:
    1. Identification: Look for PII (passwords/keys) or Phishing (spoofed domains like @c0mpany.com).
    2. Verification: If a request is high-stakes (account changes, data requests), use 'verify_identity' first.
    3. Action: Archive spam, Flag urgent legitimate alerts, Redact PII, Report phishing.
    4. Compliance: Every step costs points. Don't repeat yourself.
    
    Response MUST be a JSON object with 'thinking' and the action fields.
""").strip()

def format_inbox(emails):
    if not emails:
        return "INBOX IS EMPTY"
    lines = []
    for e in emails:
        pii = "[🔒 PII] " if e.has_pii else ""
        lines.append(f"{pii}[{e.id}] FROM: {e.sender} <{e.sender_email}> | SUBJECT: {e.subject} | SNIPPET: {e.snippet}")
    return "\n".join(lines)

def build_user_prompt(obs, history: List[str], task_id: str) -> str:
    inbox_text = format_inbox(obs.emails)
    return textwrap.dedent(
        f"""
        TASK: {task_id.upper()}
        Progress: {obs.goal_progress * 100:.1f}% | Steps Remaining: {obs.steps_remaining}

        VISIBLE INBOX:
        {inbox_text}

        LAST ACTION RESULT: {obs.last_action_status}

        JSON RESPONSE FORMAT:
        {{
            "thinking": "Check for phishing/PII. Verify identity if requested. Execute plan...",
            "action_type": "archive/flag/redact/report_as_phishing/verify_identity",
            "email_id": "ID",
            "folder_name": "Work" (optional)
        }}
        """
    ).strip()

async def get_model_action(client: OpenAI, obs, history: List[str], task_id: str) -> MyEnvV4Action:
    user_prompt = build_user_prompt(obs, history, task_id)
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            response_format={"type": "json_object"},
        )
        data = json.loads(completion.choices[0].message.content or "{}")
        return MyEnvV4Action(
            action_type=str(data.get("action_type", "none")),
            email_id=str(data.get("email_id", "0")),
            folder_name=data.get("folder_name")
        )
    except Exception as exc:
        print(f"[DEBUG] Model error: {exc}")
        return MyEnvV4Action(action_type="none", email_id="0")

async def run_task(client: OpenAI, env: MyEnvV4Env, task_name: str) -> None:
    history: List[str] = []
    rewards: List[float] = []
    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)
    
    try:
        result = await env.reset(task_id=task_name)
        obs = result.observation
        
        for step in range(1, MAX_STEPS + 1):
            if obs.done: break
            
            action = await get_model_action(client, obs, history, task_name)
            result = await env.step(action)
            obs = result.observation
            
            reward = result.reward or 0.0
            error = result.info.get("error", "null") if result.info else "null"
            rewards.append(reward)
            
            log_step(step=step, action=str(action), reward=reward, done=obs.done, error=error)
            if obs.done: break

        final_score = obs.goal_progress
        log_end(success=final_score >= SUCCESS_SCORE_THRESHOLD, steps=len(rewards), score=final_score, rewards=rewards)
    except Exception as e:
        print(f"[DEBUG] Error: {e}")
        log_end(success=False, steps=0, score=0.0, rewards=[])

async def main() -> None:
    http_client = httpx.Client(trust_env=False)
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY, http_client=http_client)
    env = await MyEnvV4Env.from_docker_image(IMAGE_NAME)
    for task_name in TASKS:
        await run_task(client, env, task_name)
    await env.close()

if __name__ == "__main__":
    asyncio.run(main())
