from flask import Flask, request, redirect, session, render_template_string
import os, psycopg2, hashlib

app = Flask(__name__)
app.secret_key = "nation-divide-2026-brutal"

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
    try:
        conn=get_db(); cur=conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id SERIAL PRIMARY KEY,
            login TEXT UNIQUE,
            password TEXT,
            money INT DEFAULT 100,
            level INT DEFAULT 1,
            exp INT DEFAULT 0,
            power INT DEFAULT 5,
            weapon INT DEFAULT 3,
            hp INT DEFAULT 100,
            wins INT DEFAULT 0
        )""")
        conn.commit(); cur.close(); conn.close()
    except Exception as e:
        print(e)

init_db()
def hash_pwd(p): return hashlib.sha256(p.encode()).hexdigest()

LOGIN_HTML = """
<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<link href="https://fonts.googleapis.com/css2?family=MedievalSharp&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}
body{
  margin:0; min-height:100vh; display:flex; justify-content:center; align-items:center;
  background:#d9c5a0 url('https://www.transparenttextures.com/patterns/old-map.png');
  font-family:'MedievalSharp', cursive;
}
.paper{
  width:95%; max-width:420px; min-height:95vh;
  background: #e8dcc0 url('https://www.transparenttextures.com/patterns/paper-fibers.png');
  border: 8px solid #5a3a1a;
  border-image: url('https://i.imgur.com/Qr5rR4V.png') 30 stretch;
  box-shadow: 0 0 40px rgba(0,0,0,0.6);
  padding:15px 18px 25px; text-align:center; position:relative;
}
.logo{width:300px; max-width:90%; margin:0 auto; filter: drop-shadow(0 8px 15px rgba(0,0,0,0.7));}
.title{font-size:38px; color:#3d1f08; margin:5px 0; letter-spacing:2px; text-shadow:1px 1px 0 #f5e6c8;}
.label{font-size:26px; margin:18px 0 6px; color:#2b1a08; text-decoration:underline; text-underline-offset:5px;}
.input-wrap{
  width:100%; height:58px; position:relative; margin:0 auto;
  background: #f2e5c4; border:3px solid #6b4a2a; border-radius:4px;
  box-shadow: inset 0 3px 8px rgba(0,0,0,0.4), 0 2px 0 #a07a4a;
  display:flex; align-items:center; padding:0 12px;
}
.input-wrap::before, .input-wrap::after{
  content:'⚜️'; position:absolute; font-size:12px; color:#6b4a2a;
}
.input-wrap::before{left:-2px; top:-8px} .input-wrap::after{right:-2px; bottom:-8px}
.input-wrap input{
  width:100%; border:none; background:transparent; outline:none;
  font-family:'MedievalSharp'; font-size:20px; color:#4a2c0a;
}
.btns{display:flex; gap:12px; margin-top:22px;}
.btn{
  flex:1; height:56px; font-family:'MedievalSharp'; font-size:22px; font-weight:bold;
  border:3px solid #3d1f08; border-radius:6px; cursor:pointer;
  box-shadow: 0 4px 0 #2b1505, inset 0 1px 0 rgba(255,255,255,0.3);
}
.btn:active{transform:translateY(4px); box-shadow:none;}
.btn-login{background:#3a3a3a; color:#e8c86a; text-shadow:1px 1px 0 #000; border-color:#1a1a1a;}
.btn-start{background:#5a3a1a; color:#ffdf8a; text-shadow:1px 1px 0 #000;}
.forgot{margin-top:20px; font-size:20px; text-decoration:underline; cursor:pointer;}
.footer{margin-top:18px; font-size:12px; opacity:0.6; font-family:Arial;}
.msg{color:#8b0000; font-weight:bold; background:rgba(255,0,0,0.1); padding:8px; border-radius:6px; margin-bottom:10px;}
</style></head>
<body>
<div class="paper">
  <img class="logo" src="/static/logo.jpeg" alt="shield">
  <!-- ЗАМЕНИ ССЫЛКУ ВЫШЕ НА СВОЮ КАРТИНКУ: после загрузки в GitHub поставь /static/logo.jpg -->
  <div style="font-size:50px; margin-top:-20px">🛡️</div>
  <div style="font-size:28px; font-weight:bold; background:#3d1f08; color:#ffcc66; display:inline-block; padding:4px 18px; border:3px solid #1a0f05; transform:rotate(-1deg); margin-bottom:10px;">NATION DIVIDE</div>
  {% if msg %}<div class="msg">{{msg}}</div>{% endif %}
  <form method="POST">
    <div class="label">LOGIN</div>
    <div style="font-size:22px; margin-bottom:4px;">Login</div>
    <div class="input-wrap"><input name="login" placeholder="Enter your login" required></div>
    <div style="font-size:22px; margin:18px 0 4px;">Password</div>
    <div class="input-wrap"><input type="password" name="password" placeholder="Enter your password" required><span style="font-size:20px;">👁️</span></div>
    <div class="btns">
      <button class="btn btn-login" name="action" value="login">Login</button>
      <button class="btn btn-start" name="action" value="reg">Start Game</button>
    </div>
  </form>
  <div class="forgot">Forgot password?</div>
  <div class="footer">v1.2.4 • Terms • Privacy</div>
</div>
</body></html>
"""

GAME_HTML = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{background:#111;color:#fff;font-family:Arial;text-align:center;padding:20px}
.card{background:#222;padding:15px;border-radius:12px;margin:12px 0}
a.btn{display:inline-block;padding:12px 18px;margin:5px;border-radius:8px;text-decoration:none;color:#fff;font-weight:bold}
.orange{background:#ff9800}.red{background:#f44336}.green{background:#4caf50}
</style></head>
<body><h1>🔥 МОБИТВА | NATION DIVIDE 🔥</h1>
<div class="card">Игрок: {{p[1]}} | Ур:{{p[4]}} | 💰{{p[3]}} | 💪{{p[6]}} | 🔪+{{p[7]}} | 🏆{{p[9]}}</div>
<div class="card"><b>ЛОКАЦИИ:</b><br>
<a class="btn" style="background:#555" href="/fight?loc=podvorotnya">🏚️ Подворотня</a>
<a class="btn orange" href="/fight?loc=promzona">🏭 Промзона</a>
<a class="btn red" href="/fight?loc=center">🏙️ Центр</a></div>
<div class="card"><b>МАГАЗИН:</b><br>
<a class="btn green" href="/buy?item=bita">🔪 Бита 200р</a>
<a class="btn green" href="/buy?item=pistol">🔫 Пистолет 800р</a></div>
<div class="card"><a href="/logout" style="color:#aaa">Выйти</a></div>
{% if msg %}<div class="card">{{msg}}</div>{% endif %}
</body></html>"""

@app.route("/", methods=["GET","POST"])
def index():
    if "uid" in session: return redirect("/game")
    msg=""
    if request.method=="POST":
        login=request.form.get("login","").strip()
        pwd=request.form.get("password","").strip()
        action=request.form.get("action")
        if not login or not pwd:
            msg="Введи логин и пароль!"
        else:
            conn=get_db(); cur=conn.cursor()
            if action=="reg":
                try:
                    cur.execute("INSERT INTO players (login,password) VALUES (%s,%s)", (login, hash_pwd(pwd)))
                    conn.commit()
                    cur.execute("SELECT id FROM players WHERE login=%s",(login,))
                    pid=cur.fetchone()[0]
                    session["uid"]=pid; session["login"]=login
                    cur.close(); conn.close()
                    return redirect("/game")
                except:
                    conn.rollback(); msg="Логин уже занят!"
            else:
                cur.execute("SELECT id FROM players WHERE login=%s AND password=%s",(login, hash_pwd(pwd)))
                row=cur.fetchone()
                if row:
                    session["uid"]=row[0]; session["login"]=login
                    cur.close(); conn.close()
                    return redirect("/game")
                else:
                    msg="Неверный логин или пароль!"
            cur.close(); conn.close()
    return render_template_string(LOGIN_HTML, msg=msg)

@app.route("/game")
def game():
    if "uid" not in session: return redirect("/")
    conn=get_db(); cur=conn.cursor()
    cur.execute("SELECT id,login,login,money,level,exp,power,weapon,hp,wins FROM players WHERE id=%s",(session["uid"],))
    r=cur.fetchone(); p=(r[0],r[1],"",r[3],r[4],r[5],r[6],r[7],r[8],r[9])
    cur.close(); conn.close()
    return render_template_string(GAME_HTML, p=p, msg=request.args.get("m",""))

@app.route("/fight")
def fight():
    if "uid" not in session: return redirect("/")
    conn=get_db(); cur=conn.cursor()
    cur.execute("UPDATE players SET wins=wins+1, money=money+50, exp=exp+25 WHERE id=%s",(session["uid"],))
    cur.execute("UPDATE players SET level=level+1, exp=0 WHERE exp>=100 AND id=%s",(session["uid"],))
    conn.commit(); cur.close(); conn.close()
    return redirect("/game?m=Победа! +50р")

@app.route("/buy")
def buy():
    if "uid" not in session: return redirect("/")
    item=request.args.get("item"); conn=get_db(); cur=conn.cursor()
    cur.execute("SELECT money FROM players WHERE id=%s",(session["uid"],))
    money=cur.fetchone()[0]
    m="Не хватает!"
    if item=="bita" and money>=200:
        cur.execute("UPDATE players SET money=money-200, weapon=weapon+5 WHERE id=%s",(session["uid"],)); conn.commit(); m="Купил биту!"
    elif item=="pistol" and money>=800:
        cur.execute("UPDATE players SET money=money-800, weapon=weapon+15 WHERE id=%s",(session["uid"],)); conn.commit(); m="Купил пистолет!"
    cur.close(); conn.close()
    return redirect(f"/game?m={m}")

@app.route("/logout")
def logout():
    session.clear(); return redirect("/")

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000)))
