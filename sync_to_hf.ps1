# Smart Inbox Sync Script (Using GitHub Desktop Git)
$GIT_PATH = "C:\Users\mohan\AppData\Local\GitHubDesktop\app-3.5.4\resources\app\git\cmd\git.exe"
$HF_REMOTE = "https://huggingface.co/spaces/S-M-R/smart-inbox-openenv"

# Ensure we are in the script's directory
Set-Location -Path $PSScriptRoot

Write-Host "[SYNC] Starting Sync to Hugging Face..." -ForegroundColor Cyan

# 1. Initialize Git if not exists
if (!(Test-Path ".git")) {
    & $GIT_PATH init
    & $GIT_PATH remote add origin $HF_REMOTE
    Write-Host "[OK] Initialized Git and added HF Remote." -ForegroundColor Green
}

# 2. Add and Commit
& $GIT_PATH add .
& $GIT_PATH commit -m "Round 1: Pro Gym Update with Temporal Pressure and Case Study"

# 3. Push to main
Write-Host "[PUSHING] Sending code to Hugging Face Space..." -ForegroundColor Yellow
& $GIT_PATH push origin master:main -f

Write-Host "[DONE] Sync Complete! Check your Space at: $HF_REMOTE" -ForegroundColor Green
