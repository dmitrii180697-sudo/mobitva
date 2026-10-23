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
    cur.execute("CREATE TABLE IF NOT EXISTS players (id SERIAL PRIMARY KEY, login TEXT UNIQUE, password TEXT, is_admin BOOLEAN DEFAULT FALSE, money INT DEFAULT 0, level INT DEFAULT 1)")
    cur.execute("CREATE TABLE IF NOT EXISTS locations (code TEXT PRIMARY KEY, name TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS enemies (code TEXT PRIMARY KEY, name TEXT, location_code TEXT)")
    cur.execute("SELECT COUNT(*) FROM locations")
    if cur.fetchone()[0]==0:
        cur.execute("INSERT INTO locations (code,name, description,min_level,reward_money,reward_exp) VALUES ('podvorotnya','Podvorotnya','For newbies',1,50,25),('promzona','Promzona','Dangerous',2,120,60),('center','Center','Elite',5,300,150)")
    conn.commit()
    try:
        cur.execute("UPDATE players SET is_admin=TRUE WHERE login=%s", (ADMIN_LOGIN,))
        conn.commit()
    except: pass
    cur.close(); conn.close()

init_db()
def hash_pwd(p): return hashlib.sha256(p.encode()).hexdigest()

LOGIN_HTML = '''
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700&family=MedievalSharp&display=swap');
body{background:#1a1206;margin:0;display:flex;justify-content:center;min-height:100vh;font-family:MedievalSharp,cursive;}
.wrap{width:100%;max-width:430px;background:#efe7c8;min-height:100vh;padding:0 0 30px;box-sizing:border-box;box-shadow:0 0 80px rgba(0,0,0,0.8);border-left:6px solid #2b1a08;border-right:6px solid #2b1a08;}
.logo-box img{width:100%;height:auto;display:block;}
.content{padding:14px 18px 10px;}
.label{font-size:30px;text-align:center;margin:10px 0 6px;color:#3e260a;font-family:Cinzel;}
.input-box{position:relative;margin:10px 2px 16px;}
.input-box input{width:100%;padding:16px 14px;font-size:19px;background:#f6eecb;border:3px solid #5a3a18;border-radius:10px;box-sizing:border-box;font-family:MedievalSharp,cursive;outline:none;}
.eye{position:absolute;right:12px;top:50%;transform:translateY(-50%);cursor:pointer;font-size:22px;}
.btns{display:flex;gap:12px;margin-top:16px;}
.btns button{flex:1;padding:15px 8px;border-radius:12px;border:3px solid #2b1a08;font-family:Cinzel,serif;font-size:19px;font-weight:700;cursor:pointer;box-shadow:0 4px 0 #1a160e;}
.btn-login{background:#1a1a1a;color:#eec96a;}
.btn-reg{background:#6d4a1f;color:#ffe9a0;}
.ver{color:#7a6a4a;text-align:center;font-family:Arial;font-size:12px;margin-top:16px;}
.msg{background:#5a1a1a;color:#ffdddd;padding:12px;border-radius:8px;text-align:center;margin:12px 0;font-family:Arial;}
</style></head><body><div class="wrap">
<div class="logo-box"><img src="/static/logo.jpg" alt="NATION DIVIDE"></div>
<div class="content">
<div class="label">LOGIN <small style="display:block;font-size:18px;">Login</small></div>
{% if msg %}<div class="msg">{{msg}}</div>{% endif %}
<form method="POST">
<div class="input-box"><input name="login" placeholder="Enter your login" required></div>
<div style="text-align:center;font-size:24px;margin-top:6px;color:#3e260a;">Password</div>
<div class="input-box"><input type="password" id="pwd" name="password" placeholder="Enter your password" required><span class="eye" onclick="document.getElementById('pwd').type=document.getElementById('pwd').type=='password'?'text':'password'">👁️</span></div>
<div class="btns">
<button class="btn-login" name="action" value="login">Login</button>
<button class="btn-reg" name="action" value="reg">Start Game</button>
</div>
</form>
<div class="ver">v1.2.5 with logo • Terms • Privacy</div>
</div></div></body></html>
'''

GAME_HTML = '''
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>
body{background:#d8c9a3;margin:0;padding:12px;font-family:MedievalSharp,cursive;}
.card{background:#efe7c8;border:3px solid #5a3a18;border-radius:12px;padding:14px;margin:12px auto;max-width:480px;}
h1{text-align:center;font-family:Cinzel;color:#3e260a;}
a.btn{display:inline-block;padding:10px 14px;margin:5px;border-radius:8px;text-decoration:none;color:#fff;font-weight:bold;background:#7a4a1e;border:2px solid #3e260a;}
a.btn.green{background:#2e7d32} a.btn.gold{background:#b78a0f}
</style></head><body>
<h1>MOBITVA</h1>
<div class="card" style="text-align:center"><img src="/static/logo.jpg" style="width:100%;max-width:320px;border-radius:10px;border:2px solid #5a3a18;"></div>
<div class="card">Player: {{p[1]}} | Lv:{{p[4]}} | Money:{{p[3]}} | Power:{{p[6]+p[7]}} | Wins:{{p[9]}} {% if is_admin %}| <a href="/admin" style="color:#8a1a1a;font-weight:bold">ADMIN PANEL</a>{% endif %}</div>
<div class="card"><b>LOCATIONS:</b><br>{% for loc in locations %}<a class="btn" href="/fight?loc={{loc[1]}}">{{loc[2]}}</a>{% endfor %}</div>
<div class="card"><b>BANK:</b><br><a class="btn gold" href="/bank?pack=1000">1000=500tg</a><a class="btn gold" href="/bank?pack=5000">5000=2000tg</a><a class="btn gold" href="/bank?pack=20000">20000=7000tg</a></div>
<div class="card"><b>SHOP:</b><br><a class="btn green" href="/buy?item=bita">Bita 200</a><a class="btn green" href="/buy?item=pistol">Pistol 800</a><a class="btn green" href="/buy?item=ak">AK 3000</a></div>
<div class="card" style="text-align:center"><a href="/logout" style="color:#555">Logout</a></div>
{% if msg %}<div class="card" style="background:#5a3a18;color:#ffe9a0">{{msg}}</div>{% endif %}
</body></html>
'''

ADMIN_LOGIN_HTML = '''
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>
body{background:#111;color:#fff;font-family:Arial;text-align:center;padding:40px}
input{padding:15px;width:280px;border-radius:8px;border:none;margin:10px}
button{padding:15px 30px;border-radius:8px;border:none;background:#ff9800;font-weight:bold;cursor:pointer}
</style></head><body><h1>Admin Login</h1><p>Login: {{login}} - enter password admin123</p>{% if msg %}<p style="color:#ff5555">{{msg}}</p>{% endif %}<form method="POST"><input type="password" name="admin_pass" placeholder="Admin password" required><br><button>Enter</button></form><br><a href="/game" style="color:#aaa">Back to game</a></body></html>
'''

ADMIN_HTML = '''
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>
body{background:#1a1a1a;color:#fff;font-family:Arial;padding:15px}.card{background:#2a2a2a;padding:15px;border-radius:10px;margin:10px 0}input,select{padding:10px;border-radius:6px;border:none;margin:5px;width:200px}button{padding:10px 15px;border-radius:6px;border:none;background:#ff9800;font-weight:bold;cursor:pointer;margin:5px}table{width:100%;border-collapse:collapse}th,td{border:1px solid #444;padding:6px}a{color:#ff0}
</style></head><body><h1>ADMIN PANEL</h1><a href="/game">Back to game</a> | <a href="/admin?logout_admin=1">Logout admin</a>
<div class="card"><h3>1. Give to player</h3><form method="POST"><input type="hidden" name="act" value="give"><select name="login">{% for pl in players %}<option>{{pl[0]}}</option>{% endfor %}</select><select name="type"><option value="money">Money</option><option value="exp">Exp</option><option value="weapon">Weapon</option><option value="level">Level</option></select><input name="amount" type="number" placeholder="amount" required><button>Give</button></form></div>
<div class="card"><h3>2. Create location</h3><form method="POST"><input type="hidden" name="act" value="add_loc"><input name="code" placeholder="code eng" required><input name="name" placeholder="Name" required><input name="description" placeholder="Description"><input name="min_level" type="number" value="1"><input name="reward_money" type="number" value="100"><input name="reward_exp" type="number" value="50"><button>Create</button></form></div>
<div class="card"><h3>3. Create quest</h3><form method="POST"><input type="hidden" name="act" value="add_quest"><input name="title" placeholder="Title" required><input name="desc" placeholder="Description"><input name="reward_money" type="number" value="200"><input name="reward_exp" type="number" value="100"><button>Create</button></form></div>
<div class="card"><h3>Players</h3><table><tr><th>Login</th><th>Lv</th><th>Money</th><th>Wins</th></tr>{% for pl in players_full %}<tr><td>{{pl[1]}} {% if pl[10] %}CROWN{% endif %}</td><td>{{pl[4]}}</td><td>{{pl[3]}}</td><td>{{pl[9]}}</td></tr>{% endfor %}</table></div>{% if msg %}<div class="card" style="background:#664400">{{msg}}</div>{% endif %}</body></html>
'''

@app.route("/", methods=["GET","POST"])
def index():
    if "uid" in session: return redirect("/game")
    msg=""
    if request.method=="POST":
        login=request.form.get("login","").strip(); pwd=request.form.get("password","").strip(); action=request.form.get("action")
        conn=get_db(); cur=conn.cursor()
        if action=="reg":
            try:
                is_admin=(login==ADMIN_LOGIN)
                cur.execute("INSERT INTO players (login,password,is_admin) VALUES (%s,%s,%s)", (login, hash_pwd(pwd), is_admin))
                conn.commit(); cur.execute("SELECT id FROM players WHERE login=%s",(login,)); pid=cur.fetchone()[0]
                session["uid"]=pid; session["login"]=login; cur.close(); conn.close(); return redirect("/game")
            except: conn.rollback(); msg="Login taken!"
        else:
            cur.execute("SELECT id FROM players WHERE login=%s AND password=%s",(login, hash_pwd(pwd))); row=cur.fetchone()
            if row:
                if login==ADMIN_LOGIN: cur.execute("UPDATE players SET is_admin=TRUE WHERE id=%s",(row[0],)); conn.commit()
                session["uid"]=row[0]; session["login"]=login; cur.close(); conn.close(); return redirect("/game")
            else: msg="Wrong login!"
        cur.close(); conn.close()
    return render_template_string(LOGIN_HTML, msg=msg)

@app.route("/game")
def game():
    if "uid" not in session: return redirect("/")
    conn=get_db(); cur=conn.cursor(); cur.execute("SELECT * FROM players WHERE id=%s",(session["uid"],)); p=cur.fetchone()
    cur.execute("SELECT * FROM locations ORDER BY min_level"); locs=cur.fetchall()
    cur.execute("SELECT * FROM quests ORDER BY id DESC LIMIT 5"); quests=cur.fetchall()
    cur.close(); conn.close(); is_admin=p[10] if len(p)>10 else False
    return render_template_string(GAME_HTML, p=p, is_admin=is_admin, locations=locs, quests=quests, msg=request.args.get("m",""))

@app.route("/admin", methods=["GET","POST"])
def admin():
    if "uid" not in session: return redirect("/")
    if request.args.get("logout_admin"): session.pop("admin_ok",None); return redirect("/admin")
    conn=get_db(); cur=conn.cursor(); cur.execute("SELECT * FROM players WHERE id=%s",(session["uid"],)); me=cur.fetchone()
    if not me or not me[10]: cur.close(); conn.close(); return "No access! Login as Dmitrii"
    if not session.get("admin_ok"):
        msg=""
        if request.method=="POST" and "admin_pass" in request.form:
            if request.form.get("admin_pass")==ADMIN_PASSWORD: session["admin_ok"]=True
            else: msg="Wrong password! Use admin123"
        if not session.get("admin_ok"):
            cur.close(); conn.close(); return render_template_string(ADMIN_LOGIN_HTML, login=me[1], msg=msg)
    msg=""
    if request.method=="POST":
        act=request.form.get("act")
        if act=="give":
            login=request.form.get("login"); typ=request.form.get("type"); amount=int(request.form.get("amount") or 0)
            col={"money":"money","exp":"exp","weapon":"weapon","level":"level"}[typ]
            cur.execute(f"UPDATE players SET {col}={col}+%s WHERE login=%s",(amount, login)); conn.commit(); msg=f"Gave {amount} {typ} to {login}"
        elif act=="add_loc":
            cur.execute("INSERT INTO locations (code,name,description,min_level,reward_money,reward_exp) VALUES (%s,%s,%s,%s,%s,%s)", (request.form.get("code"), request.form.get("name"), request.form.get("desc"), int(request.form.get("min_level") or 1), int(request.form.get("reward_money") or 50), int(request.form.get("reward_exp") or 25))); conn.commit(); msg="Location created!"
        elif act=="add_quest":
            cur.execute("INSERT INTO quests (title, description,reward_money,reward_exp,reward_item) VALUES (%s,%s,%s,%s,%s)", (request.form.get("title"), request.form.get("description"), int(request.form.get("reward_money") or 0), int(request.form.get("reward_exp") or 0), "")); conn.commit(); msg="Quest created!"
    cur.execute("SELECT login FROM players ORDER BY level DESC"); players=cur.fetchall()
    cur.execute("SELECT * FROM players ORDER BY level DESC"); players_full=cur.fetchall()
    cur.execute("SELECT * FROM locations"); locs=cur.fetchall()
    cur.close(); conn.close()
    return render_template_string(ADMIN_HTML, players=players, players_full=players_full, locs=locs, msg=msg)

@app.route("/fight")
def fight():
    if "uid" not in session: return redirect("/")
    loc_code=request.args.get("loc","podvorotnya")
    conn=get_db(); cur=conn.cursor(); cur.execute("SELECT * FROM locations WHERE code=%s",(loc_code,)); loc=cur.fetchone()
    if not loc: cur.close(); conn.close(); return redirect("/game?m=Location not found")
    cur.execute("SELECT level FROM players WHERE id=%s",(session["uid"],)); lvl=cur.fetchone()[0]
    if lvl < loc[4]: cur.close(); conn.close(); return redirect(f"/game?m=Need {loc[4]} lvl")
    cur.execute("UPDATE players SET wins=wins+1, money=money+%s, exp=exp+%s WHERE id=%s",(loc[5], loc[6], session["uid"])); cur.execute("UPDATE players SET level=level+1, exp=0 WHERE exp>=100 AND id=%s",(session["uid"],)); conn.commit(); cur.close(); conn.close()
    return redirect(f"/game?m=Win +{loc[5]}")

@app.route("/buy")
def buy():
    if "uid" not in session: return redirect("/")
    item=request.args.get("item"); conn=get_db(); cur=conn.cursor(); cur.execute("SELECT money FROM players WHERE id=%s",(session["uid"],)); money=cur.fetchone()[0]; m="Not enough!"
    if item=="bita" and money>=200: cur.execute("UPDATE players SET money=money-200, weapon=weapon+5 WHERE id=%s",(session["uid"],)); conn.commit(); m="Bought!"
    elif item=="pistol" and money>=800: cur.execute("UPDATE players SET money=money-800, weapon=weapon+15 WHERE id=%s",(session["uid"],)); conn.commit(); m="Bought!"
    elif item=="ak" and money>=3000: cur.execute("UPDATE players SET money=money-3000, weapon=weapon+50 WHERE id=%s",(session["uid"],)); conn.commit(); m="Bought!"
    cur.close(); conn.close(); return redirect(f"/game?m={m}")

@app.route("/bank")
def bank():
    if "uid" not in session: return redirect("/")
    pack=request.args.get("pack"); conn=get_db(); cur=conn.cursor(); add=0
    if pack=="1000": add=1000
    elif pack=="5000": add=6000
    elif pack=="20000": add=28000
    if add>0: cur.execute("UPDATE players SET money=money+%s WHERE id=%s",(add, session["uid"])); conn.commit(); m=f"Bank: {add} gold"
    else: m="Choose pack"
    cur.close(); conn.close(); return redirect(f"/game?m={m}")

@app.route("/quest")
def quest_done():
    if "uid" not in session: return redirect("/")
    qid=request.args.get("id"); conn=get_db(); cur=conn.cursor(); cur.execute("SELECT reward_money,reward_exp FROM quests WHERE id=%s",(qid,)); q=cur.fetchone()
    if q: cur.execute("UPDATE players SET money=money+%s, exp=exp+%s, wins=wins+1 WHERE id=%s",(q[0], q[1], session["uid"])); conn.commit(); m=f"Quest +{q[0]}"
    else: m="Not found"
    cur.close(); conn.close(); return redirect(f"/game?m={m}")

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

if __name__=="__main__": app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000)))
