---
title: "Smart Inbox OpenEnv"
emoji: "📧"
colorFrom: "blue"
colorTo: "indigo"
sdk: "docker"
app_port: 8000
tags:
  - openenv
  - rl-environment
  - pytorch-hackathon
---

# Smart Inbox OpenEnv Assistant

A professional, spec-compliant email triage environment for the Scaler/Meta OpenEnv Hackathon.

## 🚀 Overview
This environment simulates a real-world email inbox where an AI agent must prioritize, archive, and organize emails based on specific task descriptions. 

### Features:
- **Normalized Progress:** Scoring from 0.0 to 1.0 using a differential reward system.
- **Multi-Task Support:** Includes Easy (Spam), Medium (Urgent), and Hard (Organization) tasks.
- **Spec-Compliant API:** Built with FastAPI (`server/app.py`) for automated validation.
- **Trajectory Logging:** Captures every thought and action for RL training.

## 📂 Project Structure
- `environment.py`: Core RL-style environment logic.
- `models.py`: Pydantic data models for Observations and Actions.
- `server/app.py`: FastAPI server for OpenEnv communication.
- `inference.py`: Baseline LLM agent using Groq.
- `openenv.yaml`: Metadata for the OpenEnv registry.
- `pyproject.toml`: Package configuration and entry points.

## 🕹️ Action Space
The agent interacts with the inbox using structured JSON actions:
- `archive`: For spam or newsletters.
- `flag`: For urgent or high-priority emails.
- `move_to_folder`: To move project-related emails (e.g., to `/Work`).

## 👁️ Observation Space
The environment provides a structured view of the inbox:
- `emails`: A list of active emails (ID, Sender, Subject, Snippet).
- `goal_progress`: A percentage (0.0 - 1.0) of task completion.
- `last_action_status`: Feedback on the previous move.

## 🛠️ Installation & Usage
1. **Clone & Setup:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Configure API:**
   Add your `GROQ_API_KEY` to the `.env` file.
3. **Run Local Test Agent:**
   ```bash
   python inference.py
   ```

## 📋 Task Details
- **Easy:** Identify and archive 2 promotional emails.
- **Medium:** Flag 2 high-priority alerts and archive newsletters.
- **Hard:** Flag 2 critical alerts and move 2 project-related emails to the `/Work` folder.
