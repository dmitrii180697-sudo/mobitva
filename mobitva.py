from flask import Flask, request, redirect, session, render_template_string
import os, psycopg2, hashlib

app = Flask(__name__)
app.secret_key = "nation-divide-2026-brutal"
DATABASE_URL = os.getenv("DATABASE_URL")

ADMIN_LOGIN = "Dmitrii"
ADMIN_PASSWORD = "admin123"

def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
    conn=get_db(); cur=conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS players (
        id SERIAL PRIMARY KEY, login TEXT UNIQUE, password TEXT,
        money INT DEFAULT 100, level INT DEFAULT 1, exp INT DEFAULT 0,
        power INT DEFAULT 5, weapon INT DEFAULT 3, hp INT DEFAULT 100,
        wins INT DEFAULT 0, is_admin BOOLEAN DEFAULT FALSE)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS locations (
        id SERIAL PRIMARY KEY, code TEXT UNIQUE, name TEXT, desc TEXT,
        min_level INT DEFAULT 1, reward_money INT DEFAULT 50, reward_exp INT DEFAULT 25)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS quests (
        id SERIAL PRIMARY KEY, title TEXT, desc TEXT,
        reward_money INT, reward_exp INT, reward_item TEXT)""")
    cur.execute("SELECT COUNT(*) FROM locations")
    if cur.fetchone()[0]==0:
        cur.execute("INSERT INTO locations (code,name,desc,min_level,reward_money,reward_exp) VALUES ('podvorotnya','Подворотня','Для новичков',1,50,25),('promzona','Промзона','Опасно',2,120,60),('center','Центр','Элита',5,300,150)")
    conn.commit()
    try:
        cur.execute("UPDATE players SET is_admin=TRUE WHERE login=%s", (ADMIN_LOGIN,))
        conn.commit()
    except: pass
    cur.close(); conn.close()

init_db()
def hash_pwd(p): return hashlib.sha256(p.encode()).hexdigest()

LOGIN_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=MedievalSharp&display=swap" rel="stylesheet">
<style>*{box-sizing:border-box}body{margin:0;min-height:100vh;display:flex;justify-content:center;align-items:center;background:#d9c5a0;font-family:'MedievalSharp',cursive}
.paper{width:95%;max-width:420px;background:#e8dcc0;border:8px solid #5a3a1a;box-shadow:0 0 40px rgba(0,0,0,0.6);padding:15px;text-align:center}
.input-wrap{width:100%;height:58px;background:#f2e5c4;border:3px solid #6b4a2a;border-radius:4px;display:flex;align-items:center;padding:0 12px;margin:8px 0}
.input-wrap input{width:100%;border:none;background:transparent;outline:none;font-family:'MedievalSharp';font-size:20px}
.btns{display:flex;gap:12px;margin-top:22px}.btn{flex:1;height:56px;font-family:'MedievalSharp';font-size:22px;font-weight:bold;border:3px solid #3d1f08;border-radius:6px;cursor:pointer}
.btn-login{background:#3a3a3a;color:#e8c86a}.btn-start{background:#5a3a1a;color:#ffdf8a}
.msg{color:#8b0000;background:rgba(255,0,0,0.1);padding:8px;border-radius:6px;margin-bottom:10px}
</style></head><body><div class="paper">
<div style="font-size:50px">🛡️</div><div style="font-size:28px;font-weight:bold;background:#3d1f08;color:#ffcc66;display:inline-block;padding:4px 18px;border:3px solid #1a0f05">NATION DIVIDE</div>
{% if msg %}<div class="msg">{{msg}}</div>{% endif %}
<form method="POST"><div style="font-size:22px;margin:10px 0 4px">Login</div><div class="input-wrap"><input name="login" required></div>
<div style="font-size:22px;margin:10px 0 4px">Password</div><div class="input-wrap"><input type="password" name="password" required></div>
<div class="btns"><button class="btn btn-login" name="action" value="login">Login</button><button class="btn btn-start" name="action" value="reg">Start Game</button></div></form></div></body></html>
"""

GAME_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{background:#111;color:#fff;font-family:Arial;text-align:center;padding:20px}
.card{background:#222;padding:15px;border-radius:12px;margin:12px 0}
a.btn{display:inline-block;padding:12px 18px;margin:5px;border-radius:8px;text-decoration:none;color:#fff;font-weight:bold}
.orange{background:#ff9800}.red{background:#f44336}.green{background:#4caf50}.gold{background:#c9a227}
</style></head><body><h1>🔥 МОБИТВА</h1>
<div class="card 
