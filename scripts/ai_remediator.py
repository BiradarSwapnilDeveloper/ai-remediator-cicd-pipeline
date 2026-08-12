import json
import os
import requests
import subprocess
import sys

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GITHUB_RUN_ID = os.getenv("GITHUB_RUN_ID", "local")
GITHUB_REPO = os.getenv("GITHUB_REPOSITORY", "repo")
GITHUB_BRANCH = os.getenv("GITHUB_HEAD_REF") or os.getenv("GITHUB_REF_NAME", "branch")

def log_debug(msg):
    print(msg)
    with open("ai_debug.log", "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")

def send_telegram_msg(msg):
    bot_token = TELEGRAM_BOT_TOKEN.strip() if TELEGRAM_BOT_TOKEN else ""
    chat_id = TELEGRAM_CHAT_ID.strip() if TELEGRAM_CHAT_ID else ""
    
    if bot_token.startswith("bot"):
        bot_token = bot_token[3:]
        
    if not bot_token or not chat_id:
        log_debug("Telegram credentials missing. Skipping message.")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": msg, "disable_web_page_preview": True}
    try:
        res = requests.post(url, json=payload)
        res.raise_for_status()
        log_debug("✅ Telegram message sent successfully!")
    except Exception as e:
        log_debug(f"❌ Failed to send Telegram message: {e}")

def read_trivy_report():
    try:
        with open('trivy-results.json', 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
            if '\x00' in content:
                with open('trivy-results.json', 'r', encoding='utf-16le', errors='ignore') as f2:
                    content = f2.read()
            return json.loads(content)
    except Exception as e:
        log_debug(f"Error reading Trivy report: {e}")
        return None

def extract_vulnerabilities(report):
    vuln_summary = []
    if "Results" in report:
        for result in report["Results"]:
            target = result.get("Target", "package-lock.json")
            if "Vulnerabilities" in result:
                for vuln in result["Vulnerabilities"]:
                    pkg = vuln.get("PkgName", "unknown")
                    installed = vuln.get("InstalledVersion", "unknown")
                    fixed = vuln.get("FixedVersion", "unknown")
                    severity = vuln.get("Severity", "unknown")
                    
                    if fixed != "unknown" and fixed != "":
                        vuln_summary.append(f"Target File: {target}, Package: {pkg}, Installed: {installed}, Fixed in: {fixed}, Severity: {severity}")
    return "\n".join(set(vuln_summary))

def ask_gemini_for_fix(vuln_details):
    if not vuln_details:
        log_debug("No fixable vulnerabilities found.")
        return None
        
    log_debug("Sending to Gemini:\n" + vuln_details)
    
    prompt = f"""You are a DevSecOps Expert. Read this list of vulnerabilities.
Your ONLY job is to provide exact terminal commands to update the vulnerable packages to their 'Fixed in' versions.

RULES:
1. If Target File is at root (e.g. package-lock.json), output: npm install package@version --save --legacy-peer-deps
2. If Target File is in a subfolder (e.g. scratch_imgly/package-lock.json), output: cd scratch_imgly && npm install package@version --save --legacy-peer-deps && cd ..
3. ONLY output raw terminal commands.
4. NO markdown, NO backticks, NO explanations.
5. Put each command on a new line.

Vulnerabilities:
{vuln_details}"""

    api_key = GEMINI_API_KEY.strip() if GEMINI_API_KEY else ""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        res_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        log_debug("Gemini Response:\n" + res_text)
        return res_text
    except Exception as e:
        log_debug(f"Gemini API Error: {e}")
        return None

def apply_ai_fix(commands_text):
    if not commands_text:
        return False
        
    commands = commands_text.strip().split('\n')
    success_count = 0
    
    for cmd in commands:
        cmd = cmd.strip().replace("`", "")
        if "npm install" in cmd:
            log_debug(f"Running Command: {cmd}")
            try:
                result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
                log_debug(f"Success! Output:\n{result.stdout}")
                success_count += 1
            except subprocess.CalledProcessError as e:
                log_debug(f"Failed! Output:\n{e.stderr}")
                return False
        elif cmd:
             log_debug(f"Ignored non-npm command: {cmd}")
             
    if success_count == 0:
        log_debug("No valid npm commands were executed!")
        return False
        
    return True

if __name__ == "__main__":
    trivy_data = read_trivy_report()
    run_url = f"https://github.com/{GITHUB_REPO}/actions/runs/{GITHUB_RUN_ID}"
    
    if trivy_data:
        vuln_details = extract_vulnerabilities(trivy_data)
        
        # Scenario 1: No fixable vulnerabilities
        if not vuln_details:
            msg = f"✅ PixelCraft AI Security Report ✅\n\n📌 Branch: {GITHUB_BRANCH}\n✨ Status: All security checks passed! Zero fixable vulnerabilities found.\n\n🔗 View Run: {run_url}"
            send_telegram_msg(msg)
            sys.exit(0)
            
        # Scenario 2: Vulnerabilities found
        alert_msg = f"🚨 PixelCraft AI Security Alert! 🚨\n\n📌 Branch: {GITHUB_BRANCH}\n⚠️ Status: Vulnerabilities detected!\n\n📋 Findings:\n{vuln_details[:800]}...\n\n🤖 Gemini AI is currently analyzing and generating fixes..."
        send_telegram_msg(alert_msg)
        
        ai_solution = ask_gemini_for_fix(vuln_details)
        if ai_solution:
            success = apply_ai_fix(ai_solution)
            if success:
                # Scenario 3: AI Fix Applied successfully
                fix_msg = f"🛠️ Gemini AI Fix Applied 🛠️\n\n📌 Branch: {GITHUB_BRANCH}\n🤖 Action: The AI has successfully executed npm commands to patch the vulnerabilities!\n\n📋 Executed Fixes:\n{ai_solution[:800]}\n\n🔗 Next step: Pushing changes back to GitHub...\nView Run: {run_url}"
                send_telegram_msg(fix_msg)
            else:
                send_telegram_msg(f"❌ Gemini AI Fix Failed ❌\n\n📌 Branch: {GITHUB_BRANCH}\n🤖 The AI generated commands, but they failed during execution.\n\n🔗 View Error: {run_url}")
                sys.exit(1)
        else:
            send_telegram_msg(f"⚠️ Gemini AI Error ⚠️\n\n📌 Branch: {GITHUB_BRANCH}\n🤖 Could not provide a fix for the vulnerabilities.\n\n🔗 View Error: {run_url}")
            sys.exit(1)