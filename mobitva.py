from flask import Flask, request, redirect, session, render_template_string
import os, psycopg2, hashlib

app = Flask(__name__)
app.secret_key = "nation-divide-2026-brutal"
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_LOGIN = "Dmitrii"
ADMIN_PASSWORD = "admin123"

def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode='require')
def add_silver(uid, amount_silver):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT gold, silver FROM players WHERE id=%s", (uid,))
    row = cur.fetchone()
    g = row[0] if row and row[0] is not None else 0
    s = row[1] if row and len(row)>1 and row[1] is not None else 0
    s += amount_silver
    g += s // 100
    s = s % 100
    cur.execute("UPDATE players SET gold=%s, silver=%s WHERE id=%s", (g, s, uid))
    conn.commit()
    cur.close()
    conn.close()
    return g, s

def init_db():
    conn=get_db(); cur=conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS players (id SERIAL PRIMARY KEY, login TEXT UNIQUE, password TEXT, money INT DEFAULT 0, gold INT DEFAULT 0, silver INT DEFAULT 0, rubies INT DEFAULT 0, level INT DEFAULT 1, exp INT DEFAULT 0, weapon INT DEFAULT 0, strength INT DEFAULT 5, defense INT DEFAULT 0, hp INT DEFAULT 25, wins INT DEFAULT 0, is_admin BOOLEAN DEFAULT FALSE, location TEXT DEFAULT 'center')")
    cur.execute("CREATE TABLE IF NOT EXISTS inventory (id SERIAL PRIMARY KEY, player_id INT, item_name TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS locations (code TEXT PRIMARY KEY, name TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS enemies (id SERIAL PRIMARY KEY, name TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS quests (id SERIAL PRIMARY KEY, title TEXT)")
    cur.execute("SELECT COUNT(*) FROM locations")
    if cur.fetchone()[0]==0:
        cur.execute("INSERT INTO locations VALUES ('center')")
    cur.execute("SELECT * FROM players WHERE login=%s",(ADMIN_LOGIN,))
    if not cur.fetchone():
        cur.execute("INSERT INTO players (login,password,is_admin,money,level,strength) VALUES (%s,%s,TRUE,100,1,10)",(ADMIN_LOGIN,ADMIN_PASSWORD))
    conn.commit()
    cur.close()
    conn.close()

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
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{background:#d8c4a0; margin:0; padding:0 0 70px 0; font-family:Arial;}
.top{ background:#e8dcc0; border:2px solid #5a3a18; border-radius:10px; margin:5px; padding:5px 8px; display:flex; justify-content:space-between;}
.frame{ margin:5px; border:4px solid #5a3a18; border-left:8px solid #5a3a18; border-right:8px solid #5a3a18; background:rgba(232,220,192,0.92); border-radius:10px; overflow:hidden;}
.frame img{width:100%; display:block; height:210px; object-fit:cover;}
.loc-name{ background:#e8dcc0; padding:8px; font-weight:bold; text-align:center; font-size:18px;}
.btns{display:flex; justify-content:space-between; margin:10px 10px;}
.btn{ background:#48a2c2; border:2px solid #5a3a18; padding:10px 0; width:48%; text-align:center; font-weight:bold; border-radius:8px; text-decoration:none; color:#000; display:block;}
.menu{ background:#e8dcc0; border:2px solid #5a3a18; margin:5px 10px; padding:0 12px; border-radius:10px; background:rgba(232,220,192,0.95);}
.row{ display:flex; justify-content:space-between; align-items:center; padding:14px 0; border-bottom:1px solid #b8a080;}
.row:last-child{border:none}
.bottom{position:fixed; bottom:0; left:0; right:0; background:#4b2e14; color:#fff; display:flex; justify-content:space-around; padding:8px 0; font-size:13px;}
.bottom a{color:#fff; text-decoration:none}
</style>
<div class="top">
<span>⭐ {{p[7]}}</span>
<span>❤️ {{p[12] if p[12]!=0 else 25}}</span>
<span>🔵 {{p[6]}}</span>
<span>🟡 {{p[4]}}</span>
<span>⚪ {{p[5]}}</span>
</div>

<div class="frame">
<img src="{{ bg_image }}" onerror="this.src='/static/logo.jpg'">
</div>

<div class="loc-name">{% if current_loc == 'lager' %}Лагерь{% elif current_loc == 'zastava' %}Застава{% elif current_loc == 'oboz' %}Обоз{% else %}Лагерь{% endif %}</div>

<div class="btns">
<a class="btn" href="/hunt">Промысел</a>
<a class="btn" href="/duel">Арена</a>
</div>

<div class="menu">
<div class="row"><a href="/loc/lager" style="text-decoration:none; color:#000; display:flex; justify-content:space-between; width:100%;"><span>🏕️ Лагерь</span><span>➡️</span></a></div>
<div class="row"><a href="/loc/zastava" style="text-decoration:none; color:#000; display:flex; justify-content:space-between; width:100%;"><span>🛡️ Застава</span><span>➡️</span></a></div>
<div class="row"><a href="/loc/oboz" style="text-decoration:none; color:#000; display:flex; justify-content:space-between; width:100%;"><span>🛒 Обоз</span><span>➡️</span></a></div>
<div class="row"><span>Player: {{p[1]}} | Lv:{{p[4]}} | Money:{{p[3]}}</span> {% if is_admin %}<a href="/admin" style="color:#ff2222;font-weight:bold;margin-left:12px;border:1px solid red;padding:2px 6px;border-radius:6px;">⚙ ADMIN</a>{% endif %}</div>
{% if msg %}<div style="padding:10px; background:#5a3a18; color:#ffe9a0">{{msg}}</div>{% endif %}
</div>

<div class="bottom"><a href="/menu">Меню</a><span id="clock">00:00:00</span><a href="/logout">Выход</a>
<script>setInterval(()=>{document.getElementById('clock').innerText=new Date().toLocaleTimeString()},1000)</script>
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
    conn=get_db(); cur=conn.cursor()
    cur.execute("SELECT * FROM players WHERE id=%s",(session["uid"],))
    p=cur.fetchone()
    if not p: session.clear(); return redirect("/")
    try:
        cur.execute("SELECT * FROM locations ORDER BY min_level")
        locs=cur.fetchall()
    except:
        locs=[]
    try:
        cur.execute("SELECT * FROM quests ORDER BY id DESC LIMIT 5")
        quests=cur.fetchall()
    except:
        quests=[]
    cur.close(); conn.close()

    current_code = request.args.get("loc") or session.get("current_loc") or "lager"
    alias = {"kremnev":"lager", "gati":"zastava", "yarmarka":"oboz"}
    current_code = alias.get(current_code, current_code)
    bg_map = {
        "lager": "/static/lager.jpg",
        "zastava": "/static/zastava.jpg",
        "oboz": "/static/oboz.jpg",
        "bank": "/static/oboz.jpg"
    }
    bg_image = bg_map.get(current_code, "/static/lager.jpg")
    is_admin = p[10] if len(p)>10 else False
    return render_template_string(GAME_HTML, p=p, is_admin=is_admin, locations=locs, quests=quests, msg=request.args.get("m"), bg_image=bg_image, current_loc=current_code)
@app.route("/attack")
def attack():
    return "Ты ударил Гриба! +5 золота<br><a href='/hunt'>Назад</a>"

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
@app.route("/loc/<code>")
def go_loc(code):
    if "uid" not in session: return redirect("/")
    alias = {"kremnev":"lager", "gati":"zastava", "yarmarka":"oboz"}
    real_code = alias.get(code, code)
    session["current_loc"] = real_code
    return redirect(f"/game?loc={real_code}")
@app.route("/gati")
def gati_page():
    return redirect("/loc/zastava")
@app.route("/shop")
def shop_page():
    return redirect("/loc/oboz")

@app.route("/bank_page")
def bank_page_go():
    return redirect("/loc/bank")
@app.route("/quest")
def quest_done():
    if "uid" not in session: return redirect("/")
    qid=request.args.get("id"); conn=get_db(); cur=conn.cursor(); cur.execute("SELECT reward_money,reward_exp FROM quests WHERE id=%s",(qid,)); q=cur.fetchone()
    if q:
        cur.execute("UPDATE players SET money=money+%s, exp=exp+%s, wins=wins+1 WHERE id=%s",(q[0], q[1], session["uid"]))
        # --- +20 ХП ЗА КАЖДЫЙ УРОВЕНЬ ---
        cur.execute("SELECT level, exp, hp FROM players WHERE id=%s",(session["uid"],))
        lvl, ex, hp_cur = cur.fetchone()
        if hp_cur is None: hp_cur = 25
        while ex >= lvl*100:
            ex -= lvl*100
            lvl += 1
            hp_cur += 20
        cur.execute("UPDATE players SET level=%s, exp=%s, hp=%s WHERE id=%s",(lvl, ex, hp_cur, session["uid"]))
        conn.commit(); m=f"Quest +{q[0]}"
    else:
        m="Not found"
    cur.close(); conn.close(); return redirect(f"/game?m={m}")
MONSTERS = {
    "grib": {"name": "Гриб", "full": "Лесной гриб", "hp": 30, "dmg": 5, "gold": 29, "exp": 1, "trophy": "Шляпка гриба", "img": "grib.png", "trophy_img": "grib.png"}
}

@app.route("/camp")
def camp():
    if "uid" not in session:
        return redirect("/")
    m = MONSTERS["grib"]
    return render_template_string('''
    <div style="max-width:420px;margin:0 auto;background:#dcc89c;min-height:100vh;font-family:serif;border:4px solid #3d2a14">
      <div style="background:#3d2a14;color:#ffcc66;display:flex;justify-content:space-between;padding:8px"><span>Меню</span><span>Лагерь</span><a href="/game" style="color:#ffcc66;text-decoration:none">В город</a></div>
      <div style="background:linear-gradient(#4a7c2e,#2a4a1a);padding:20px;text-align:center;color:#fff">🌲 Локация: Лагерь 🌲</div>
      <div style="padding:10px">
        <div style="background:#e8d5a3;border:2px solid #3d2a14;display:flex;align-items:center;padding:8px">
          <img src="/static/grib.png" style="width:60px;background:#fff;border:1px solid #000">
          <div style="flex:1;padding-left:10px"><b>{{m.full}}</b><br><small>30 ❤ | Награда: {{m.gold}}💰</small></div>
          <a href="/hunt/grib" style="background:#c00;color:#fff;padding:10px 15px;text-decoration:none;border:2px outset #800;border-radius:6px">НАПАСТЬ</a>
        </div>
      </div>
    </div>
    ''', m=m)

def get_name(uid):
    # Берем логин прямо из сессии - это твой логин при регистрации
    login = session.get("login") or session.get("username") or session.get("user")
    if login:
        return login
    return "Герой"
@app.route("/hunt/<mid>")
def hunt(mid):
    if "uid" not in session:
        return redirect("/")
    if mid not in MONSTERS:
        return redirect("/camp")
    mon = MONSTERS[mid]
    player_name = get_name(session["uid"])

    return render_template_string('''
    <div style="max-width:420px;margin:0 auto;background:#dcc89c;min-height:100vh;font-family:serif;border:4px solid #3d2a14">
      <div style="background:#3d2a14;color:#ffcc66;display:flex;justify-content:space-between;padding:8px;font-size:13px"><span>Лагерь</span><span>Бой с {{mon.full}}</span><a href="/camp" style="color:#ffcc66;text-decoration:none">Сбежать</a></div>
      
      <div style="position:relative;height:260px;background:linear-gradient(#4a7c2e,#2a4a1a);border-bottom:4px solid #3d2a14;overflow:hidden">
        <!-- Вот тут теперь имя персонажа -->
        <div style="display:flex;justify-content:space-between;padding:6px;background:rgba(0,0,0,0.6);color:#fff;font-weight:bold;font-size:14px">
          <span>{{player_name}} <span id="php">90</span>❤</span>
          <span>{{mon.name}} <span id="ehp">{{mon.hp}}</span>❤</span>
        </div>
        <div style="position:absolute;bottom:0;width:100%;height:50px;background:#5a3a1a"></div>
        <div id="hero" style="position:absolute;left:10px;bottom:15px;transition:0.2s"><img src="/static/hero_f.png" style="width:100px;background:#fff"></div>
        <div id="enemy" style="position:absolute;right:15px;bottom:15px;transition:0.3s"><img src="/static/{{mon.img}}" style="width:95px;background:#fff"></div>
        <div id="my_dmg" style="position:absolute;left:25%;top:70px;color:#ff0;font-size:36px;font-weight:bold;display:none;z-index:10">-10</div>
        <div id="en_dmg" style="position:absolute;right:25%;top:70px;color:#f55;font-size:36px;font-weight:bold;display:none;z-index:10">-{{mon.dmg}}</div>
        <div id="log" style="position:absolute;bottom:0;left:0;width:100%;text-align:center;background:rgba(0,0,0,0.8);color:#0f0;font-size:13px;padding:6px">Твой ход!</div>
      </div>
      <div style="background:#b89a6a;padding:12px"><div style="display:flex;justify-content:space-around;gap:8px">
          <button id="b0" onclick="hit()" style="flex:1;height:60px;background:#e8d5a3;border:3px outset #8b6d4a;border-radius:6px;font-weight:bold">⚔️<br><small>ГОЛОВА</small></button>
          <button id="b1" onclick="hit()" style="flex:1;height:60px;background:#e8d5a3;border:3px outset #8b6d4a;border-radius:6px;font-weight:bold">🗡️<br><small>ТЕЛО</small></button>
          <button id="b2" onclick="hit()" style="flex:1;height:60px;background:#e8d5a3;border:3px outset #8b6d4a;border-radius:6px;font-weight:bold">⚔️<br><small>НОГИ</small></button>
      </div></div>
    </div>
    <script>
    let ehp={{mon.hp}}, php=90, pdmg=10, edmg={{mon.dmg}}, total=0, turn=true;
    function hit(){
      if(!turn) return; turn=false; b0.disabled=b1.disabled=b2.disabled=true;
      let h=document.getElementById('hero'); h.style.transform='translateX(90px)'; setTimeout(()=>h.style.transform='',180);
      setTimeout(()=>{
        ehp-=pdmg; total+=pdmg; if(ehp<0) ehp=0; document.getElementById('ehp').innerText=ehp;
        let d=document.getElementById('my_dmg'); d.innerText='-'+pdmg; d.style.display='block'; setTimeout(()=>d.style.display='none',700);
        let e=document.getElementById('enemy'); e.style.transform='translateX(30px) scale(0.8)'; setTimeout(()=>e.style.transform='',300);
        if(ehp<=0){ location.href='/hunt_result/grib?dmg='+total; return; }
        setTimeout(enemyHit,800);
      },180);
    }
    function enemyHit(){
      let e=document.getElementById('enemy'); e.style.transform='translateX(-70px)'; setTimeout(()=>e.style.transform='',180);
      setTimeout(()=>{
        php-=edmg; if(php<0) php=0; document.getElementById('php').innerText=php;
        let d=document.getElementById('en_dmg'); d.innerText='-'+edmg; d.style.display='block'; setTimeout(()=>d.style.display='none',700);
        let h=document.getElementById('hero'); h.style.transform='translateX(-20px)'; setTimeout(()=>h.style.transform='',300);
        if(php<=0){ location.href='/camp'; return; }
        turn=true; b0.disabled=b1.disabled=b2.disabled=false;
      },180);
    }
    </script>
    ''', mon=mon, player_name=player_name)

@app.route("/hunt_result/<mid>")
def hunt_result(mid):
    if "uid" not in session:
        return redirect("/")
    mon = MONSTERS.get(mid, MONSTERS["grib"])
    total_dmg = request.args.get("dmg", "33")
    
    # Берем ник игрока из базы
    player_name = get_name(session["uid"])
    try:
        conn=get_db(); cur=conn.cursor()
        cur.execute("SELECT username FROM players WHERE id=%s", (session["uid"],))
        row=cur.fetchone()
        if row:
            player_name = row[0]
        cur.execute("UPDATE players SET gold=gold+%s, exp=exp+%s WHERE id=%s", (mon["gold"], mon["exp"], session["uid"]))
        conn.commit(); cur.close(); conn.close()
    except:
        pass

    return render_template_string('''
    <div style="max-width:420px;margin:0 auto;background:#3d2a14;min-height:100vh;padding:10px;font-family:serif">
      <div style="background:#e8d5a3;border:4px solid #8b6d4a;border-radius:4px;position:relative;padding-top:30px">
        <div style="position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:#5a3a1a;color:#ffcc66;padding:2px 20px;border-radius:15px;border:2px solid #000;white-space:nowrap">-Результаты боя-</div>
        <a href="/camp" style="position:absolute;top:8px;right:8px;background:#dcc89c;border:2px solid #5a3a1a;width:28px;height:28px;text-align:center;text-decoration:none;color:#000;font-weight:bold;border-radius:4px;line-height:24px">X</a>
        
        <div style="padding:15px 15px 5px 15px">
          <div style="color:#6b4c2a;font-size:18px">Победители:</div>
          <div style="background:#c9a86a;display:flex;justify-content:space-between;padding:6px 8px;font-weight:bold;font-size:15px;border:1px solid #8b6d4a">
            <span>Имя</span><span>Урон</span><span>Опыт</span>
          </div>
          <div style="display:flex;justify-content:space-between;padding:10px 8px;border-bottom:1px solid #a88a5a">
            <span style="font-weight:bold;font-size:18px">{{player_name}}</span>
            <span style="margin-left:auto;margin-right:40px">{{total_dmg}}</span>
            <span>{{mon.exp}}</span>
          </div>
          
          <div style="color:#6b4c2a;font-size:18px;margin-top:18px">Побежденные:</div>
          <div style="background:#c9a86a;display:flex;justify-content:space-between;padding:6px 8px;font-weight:bold;font-size:15px;border:1px solid #8b6d4a">
            <span>Имя</span><span>Урон</span><span>Опыт</span>
          </div>
          <div style="display:flex;justify-content:space-between;padding:8px">
            <span>{{mon.full}}</span><span style="margin-left:auto;margin-right:40px">0</span><span>0</span>
          </div>
          
          <div style="color:green;font-size:18px;margin-top:12px">Трофеи:</div>
          <div style="padding:5px 10px;color:#0a5a0a;font-weight:bold;font-size:18px">
            + 🪙 {{mon.gold}} золота
          </div>
        </div>
        
        <div style="height:12px;background:linear-gradient(#8b6d4a,#5a3a1a);border-radius:0 0 3px 3px;margin-top:10px"></div>
      </div>
      
      <a href="/camp" style="display:block;margin:25px auto;width:80%;background:linear-gradient(#ff8c00,#cc6600);color:#000;text-align:center;padding:14px;font-size:22px;font-weight:bold;border:3px outset #8b6d4a;border-radius:6px;text-decoration:none">Далее</a>
    </div>
    ''', mon=mon, total_dmg=total_dmg, player_name=player_name)
@app.route("/hunt")
def hunt_list():
    return redirect("/camp")

@app.route("/hunt_win")
def hunt_win():
    return redirect("/camp")
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    port=int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0",port=port)
