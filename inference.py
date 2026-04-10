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

# CRITICAL: The judge checks for [START]/[STEP]/[END] blocks for ALL 3 tasks.
# Running only one task = "Not enough tasks with graders" error.
TASKS = ["easy", "medium", "hard"]

# Match openenv.yaml steps: 3 per task.
# The judge expects exactly `steps` worth of [STEP] log lines per task.
MAX_STEPS = 3

TEMPERATURE = 0.1
MAX_TOKENS = 512
SUCCESS_SCORE_THRESHOLD = 0.8

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
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

# --------------------------------------------------------------------------
# AGENT BRAIN (Pro Reasoning with CoT)
# --------------------------------------------------------------------------
SYSTEM_PROMPT = textwrap.dedent("""
    You are a Professional Smart Inbox Assistant. Your goal is to clean the inbox with maximum efficiency.
    
    CRITICAL RULES:
    1. Only use visible Email IDs.
    2. Be decisive. Every step costs -0.01 points (Temporal Pressure).
    3. Be precise. Incorrect actions cost -0.15 points.
    4. Use Chain-of-Thought: always reason through the task rules before choosing an action.
    5. Return your plan and action in valid JSON format.
""").strip()

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
        TASK: {TASK_NAME.upper()}
        Progress: {obs.goal_progress * 100}% Complete.
        Steps Remaining: {obs.steps_remaining}

        INBOX STATUS:
        {inbox_text}

        OPERATIONAL HISTORY (Last 4):
        {chr(10).join(history[-4:]) if history else "Start of task."}

        REWARD FEEDBACK:
        Current Step Cost: -0.01
        Mistake Penalty: -0.15
        Success Reward: +Progress Gain

        INSTRUCTIONS:
        1. Analyze the inbox.
        2. Identify the highest priority email according to the task difficulty rules.
        3. Explain your reasoning in the 'thinking' field.
        4. Provide the 'action_type', 'email_id', and 'folder_name' (if needed).

        JSON RESPONSE FORMAT:
        {{
            "thinking": "Reasoning about the task rules and visible emails...",
            "action_type": "archive/flag/move_to_folder",
            "email_id": "Target ID",
            "folder_name": "Folder Name (e.g., 'Work') or null"
        }}
        """
    ).strip()

async def get_model_action(client: OpenAI, obs, history: List[str], task_id: str) -> MyEnvV4Action:
    # Use the current task_id in the prompt
    user_prompt = build_user_prompt(obs, history).replace(f"TASK: {TASK_NAME.upper()}", f"TASK: {task_id.upper()}")
    
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
            stream=False,
        )
        content = completion.choices[0].message.content or "{}"
        data = json.loads(content)

        a_type = str(data.get("action_type") or "none").lower()
        eid = str(data.get("email_id") or "0")
        folder = data.get("folder_name")

        # Log the thinking process for debugging
        thinking = data.get("thinking", "No reasoning provided")
        # print(f"[DEBUG] Thinking: {thinking}", flush=True)

        return MyEnvV4Action(action_type=a_type, email_id=eid, folder_name=folder)
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return MyEnvV4Action(action_type="none", email_id="0")

# --------------------------------------------------------------------------
# SINGLE TASK RUNNER — Produces exactly one [START]/[STEP]x3/[END] block
# --------------------------------------------------------------------------
async def run_task(client: OpenAI, env: MyEnvV4Env, task_name: str) -> None:
    """
    Runs a single task and emits the mandatory [START], [STEP], [END] logs.
    This is called once per task in TASKS so the judge sees 3 distinct graded runs.
    """
    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    final_score = 0.0
    success = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = await env.reset(task_id=task_name)
        obs = result.observation

        # CRITICAL: Loop for at most MAX_STEPS (=3), matching openenv.yaml steps: 3
        # Break immediately when done. Judge counts [STEP] lines to verify task ran.
        for step in range(1, MAX_STEPS + 1):
            if obs.done:
                break

            action = await get_model_action(client, obs, history, task_name)
            result = await env.step(action)
            obs = result.observation

            reward = result.reward or 0.0
            done = result.done

            error = result.info.get("error") if hasattr(result, "info") and result.info else None
            if not error and obs.last_action_status and "Incorrect" in obs.last_action_status:
                error = "Ineffective action"

            rewards.append(reward)
            steps_taken = step

            log_step(step=step, action=str(action), reward=reward, done=done, error=error)

            history.append(f"Step {step}: {action} -> reward {reward:+.2f}")

            if done:
                break

        final_score = obs.score if hasattr(obs, "score") else (obs.goal_progress or 0.0)
        success = final_score >= SUCCESS_SCORE_THRESHOLD

    except Exception as e:
        print(f"[DEBUG] Task '{task_name}' error: {e}", flush=True)

    finally:
        log_end(success=success, steps=steps_taken, score=final_score, rewards=rewards)

# --------------------------------------------------------------------------
# MAIN — Loops over ALL tasks so judge sees 3 graded task blocks
# --------------------------------------------------------------------------
async def main() -> None:
    http_client = httpx.Client(trust_env=False)
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY, http_client=http_client)

    env = await MyEnvV4Env.from_docker_image(IMAGE_NAME)

    try:
        # Run ALL tasks in sequence — this is what produces the 3 grader results
        for task_name in TASKS:
            await run_task(client, env, task_name)
    finally:
        try:
            await env.close()
        except Exception as e:
            print(f"[DEBUG] env.close() error: {e}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
