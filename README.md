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
- **Normalized Progress:** Scoring strictly from 0.01 to 0.99 for full compliance.
- **PII Shield Security:** Integrated benchmark for PII detection and redaction.
- **Multi-Task Support:** 5 levels ranging from Easy (Spam) to Insane (Chaos Triage).
- **Spec-Compliant API:** Built with FastAPI (`server/app.py`) for automated validation.
- **Trajectory Logging:** Captures every thought and action for RL training.

## 🔒 Privacy & Safety Disclaimer
**All data, emails, and scenarios presented in this environment are 100% synthetically generated.** There is no Real PII (Personally Identifiable Information) or real-world credentials included. This simulation is built entirely for RL evaluation purposes.

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
- `redact`: **MANDATORY** for any email containing PII. Failure to redact before other actions triggers a Security Breach.

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
- **Easy:** Identify and archive promotional emails.
- **Medium:** Flag urgent security/HR alerts and archive newsletters.
- **Hard:** Flag critical alerts, move project emails, and **redact PII**.
- **Expert:** Enterprise Triage: Multi-category management with high-stakes security.
- **Insane:** Chaos Mode: High volume inbox with aggressive dynamic spawning.

## 🔒 Security Benchmark (PII Shield)
This environment includes a "Zero-Tolerance" security layer. If an agent archives, flags, or moves an email containing sensitive data (SSNs, Passwords, etc.) without first calling the `redact` action, the task score is automatically pinned to `0.01` and a `SecurityBreach` is recorded in the metadata.
