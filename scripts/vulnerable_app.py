import os
import sqlite3

# VERY BAD: Hardcoded secrets
AWS_SECRET_KEY = "AKIAIOSFODNN7EXAMPLE"
GITHUB_TOKEN = "ghp_xxXYyZZAaBbCcDdEeFfGgHhIiJjKkLlMmNn"

def vulnerable_login(username, password):
    # VERY BAD: SQL Injection vulnerability
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    return cursor.fetchall()

def execute_command(user_input):
    # VERY BAD: Remote Code Execution (OS Command Injection)
    os.system(f"echo {user_input}")

if __name__ == "__main__":
    print("This app is full of vulnerabilities!")
