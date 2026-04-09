import asyncio
import os
import textwrap
import json
import httpx
from typing import List, Optional

from openai import OpenAI
from my_env_v4 import MyEnvV4Action, MyEnvV4Env

# --------------------------------------------------------------------------
# CONFIGURATION (Strict V4 Compliance)
# --------------------------------------------------------------------------
IMAGE_NAME = os.getenv("IMAGE_NAME", "smart_inbox_lite:latest")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("GROQ_API_KEY") or os.getenv("API_KEY") # Prioritize HF_TOKEN for judges

API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.getenv("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"
TASK_NAME = os.getenv("SMART_INBOX_TASK", "easy")
BENCHMARK = os.getenv("SMART_INBOX_BENCHMARK", "smart_inbox_lite")

MAX_STEPS = 15
TEMPERATURE = 0.1
MAX_TOKENS = 512

# Our environment produces a normalized score [0.0, 1.0] internally.
# In the V4 spec loop, we calculate average or final score.
# We will use the final observation's goal_progress as the ground truth score.
SUCCESS_SCORE_THRESHOLD = 0.99 

# --------------------------------------------------------------------------
# MANDATORY STDOUT LOGGING (Strict Regex Patterns)
# --------------------------------------------------------------------------
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if (error and error != "null") else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    # Spec requires lowercase booleans and 3-decimal score in log_end usually, 
    # but the example showed 3 decimals for score.
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

# --------------------------------------------------------------------------
# AGENT BRAIN (Smart Inbox Pro)
# --------------------------------------------------------------------------
def format_inbox(emails):
    if not emails:
        return "INBOX IS EMPTY"
    lines = []
    for e in emails:
        flag_status = "[🚩] " if e.is_flagged else ""
        lines.append(f"{flag_status}[{e.id}] FROM: {e.sender} | SUBJECT: {e.subject} | SNIPPET: {e.snippet}")
    return "\n".join(lines)

def build_user_prompt(obs, history: List[str]) -> str:
    inbox_text = format_inbox(obs.emails)
    return textwrap.dedent(
        f"""
        Goal: Clean the inbox based on the task rules.
        Progress: {obs.goal_progress * 100}% Complete.
        Steps Remaining: {obs.steps_remaining}

        Recent History:
        {chr(10).join(history[-4:]) if history else "Start of task."}

        Visible Inbox Contents:
        {inbox_text}

        Reply in JSON format:
        {{
            "thinking": "Reasoning about your next move...",
            "action_type": "archive/flag/move_to_folder",
            "email_id": "Target ID",
            "folder_name": "Folder if move_to_folder (else null)"
        }}
        """
    ).strip()

async def get_model_action(client: OpenAI, obs, history: List[str]) -> MyEnvV4Action:
    user_prompt = build_user_prompt(obs, history)
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a Professional Smart Inbox Assistant. You ONLY use visible IDs. Return JSON."},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            response_format={"type": "json_object"},
            stream=False,
        )
        content = completion.choices[0].message.content or "{}"
        data = json.loads(content)
        
        # Extract fields
        a_type = str(data.get("action_type") or "none").lower()
        eid = str(data.get("email_id") or "0")
        folder = data.get("folder_name")
        
        return MyEnvV4Action(action_type=a_type, email_id=eid, folder_name=folder)
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return MyEnvV4Action(action_type="none", email_id="0")

# --------------------------------------------------------------------------
# MAIN COMPLIANCE LOOP
# --------------------------------------------------------------------------
async def main() -> None:
    # Use standard httpx client to avoid environment proxy issues
    http_client = httpx.Client(trust_env=False)
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY, http_client=http_client)

    env = await MyEnvV4Env.from_docker_image(IMAGE_NAME)

    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    final_score = 0.0
    success = False

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = await env.reset(task_id=TASK_NAME)
        obs = result.observation

        for step in range(1, MAX_STEPS + 1):
            if obs.done:
                break

            action = await get_model_action(client, obs, history)

            result = await env.step(action)
            obs = result.observation

            reward = result.reward or 0.0
            done = result.done
            
            # Extract error from info if present
            error = result.info.get("error") if hasattr(result, "info") and result.info else None
            if not error and "Incorrect/Ineffective" in obs.last_action_status:
                error = "Ineffective action"

            rewards.append(reward)
            steps_taken = step
            
            log_step(step=step, action=str(action), reward=reward, done=done, error=error)

            history.append(f"Step {step}: {action} -> reward {reward:+.2f}")

            if done:
                break

        final_score = obs.goal_progress
        success = final_score >= SUCCESS_SCORE_THRESHOLD

    finally:
        try:
            await env.close()
        except Exception as e:
            print(f"[DEBUG] env.close() error: {e}", flush=True)
        log_end(success=success, steps=steps_taken, score=final_score, rewards=rewards)


if __name__ == "__main__":
    asyncio.run(main())
