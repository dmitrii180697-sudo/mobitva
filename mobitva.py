import os, threading, random, asyncio
import psycopg2
from flask import Flask, request, jsonify
from aiogram import Bot, Dispatcher
TOKEN=os.getenv("BOT_TOKEN","8829639637:AAFLGihpuAGQhYYQ3TViCXqwFMNl8G22y_4")
DATABASE_URL=os.getenv("DATABASE_URL")
ADMINS=[842769679]
def get_conn(): return psycopg2.connect(DATABASE_URL)
try:
 c=get_conn();cur=c.cursor()
 cur.execute("CREATE TABLE IF NOT EXISTS players (user_id BIGINT PRIMARY KEY, lvl INT DEFAULT 1, exp INT DEFAULT 0, money INT DEFAULT 100, str INT DEFAULT 5, hp INT DEFAULT 100, max_hp INT DEFAULT 100, weapon INT DEFAULT 0, wins INT DEFAULT 0)")
 c.commit();c.close()
except Exception as e: print(e)
def get_player(uid):
 conn=get_conn();cur=conn.cursor()
 cur.execute("SELECT * FROM players WHERE user_id=%s",(uid,));r=cur.fetchone()
 if not r:
  cur.execute("INSERT INTO players (user_id) VALUES (%s)",(uid,));conn.commit()
  cur.execute("SELECT * FROM players WHERE user_id=%s",(uid,));r=cur.fetchone()
 conn.close()
 return {"user_id":r[0],"lvl":r[1],"exp":r[2],"money":r[3],"str":r[4],"hp":r[5],"max_hp":r[6],"weapon":r[7],"wins":r[8]}
def save(p):
 conn=get_conn();cur=conn.cursor()
 cur.execute("UPDATE players SET lvl=%s,exp=%s,money=%s,str=%s,hp=%s,max_hp=%s,weapon=%s,wins=%s WHERE user_id=%s",(p['lvl'],p['exp'],p['money'],p['str'],p['hp'],p['max_hp'],p['weapon'],p['wins'],p['user_id']))
 conn.commit();conn.close()
app=Flask('')
@app.route('/')
def game():
 return """<!DOCTYPE html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>Мобитва</title><style>body{background:#111;color:#fff;font-family:Arial;text-align:center;padding:15px}.card{background:#1e1e1e;padding:15px;border-radius:15px;margin:10px 0}button{padding:12px 18px;margin:5px;border-radius:10px;border:none;font-weight:bold}.loc1{background:#555;color:#fff}.loc2{background:#ff9800}.loc3{background:#f44336;color:#fff}.shop{background:#4caf50;color:#fff}</style></head><body><h1>🔥 МОБИТВА 3 ЛОКАЦИИ 🔥</h1><div class=card id=info>Загрузка...</div><div class=card><b>ЛОКАЦИИ:</b><br><button class=loc1 onclick=fight(1)>🏚️ Подворотня</button><button class=loc2 onclick=fight(2)>🏭 Промзона</button><button class=loc3 onclick=fight(3)>🏙️ Центр</button></div><div class=card><b>МАГАЗИН:</b><br><button class=shop onclick=buy(200,3)>🔪 Бита 200р</button><button class=shop onclick=buy(800,12)>🔫 Пистолет 800р</button></div><div class=card id=quest></div><div class=card><a id=admLink style=color:#2196f3>👑 Админка</a></div><script>let uid=localStorage.getItem('uid')||Math.floor(Math.random()*900000)+100000;localStorage.setItem('uid',uid);document.getElementById('admLink').href='/admin?uid='+uid;async function load(){let r=await fetch('/api/player?uid='+uid);let p=await r.json();document.getElementById('info').innerHTML=`ID:${p.user_id} | Ур:${p.lvl} | EXP:${p.exp}/100<br>💰${p.money} 💪${p.str} 🔫+${p.weapon} ❤️${p.hp}/${p.max_hp} 🏆${p.wins}`;let q=p.wins<5?`📜 Победи 5 раз (${p.wins}/5) +500р`:p.lvl<3?`📜 Достигни 3 ур +1000р`:`✅ Все квесты!`;document.getElementById('quest').innerHTML=q}async function fight(loc){let r=await fetch('/api/fight?uid='+uid+'&loc='+loc,{method:'POST'});let d=await r.json();alert(d.msg);load()}async function buy(pr,wp){let r=await fetch('/api/buy?uid='+uid+'&price='+pr+'&wp='+wp,{method:'POST'});let d=await r.json();alert(d.msg);load()}load();</script></body></html>"""
@app.route('/api/player')
def api_player(): return jsonify(get_player(int(request.args.get('uid'))))
@app.route('/api/fight',methods=['POST'])
def api_fight():
 uid=int(request.args.get('uid'));loc=int(request.args.get('loc',1));p=get_player(uid)
 cfg={1:{"n":"Гопник","hp":30,"dmg":5,"m":30,"e":15},2:{"n":"Охранник","hp":70,"dmg":12,"m":80,"e":35},3:{"n":"Мажор","hp":150,"dmg":25,"m":200,"e":80}}[loc]
 if random.random()<0.3:
  p['hp']-=cfg['dmg']
  if p['hp']<=0: p['hp']=p['max_hp'];msg=f"💀 Тебя вырубил {cfg['n']}!"
  else: msg=f"🛡️ {cfg['n']} блок! -{cfg['dmg']} HP"
 else:
  dmg=p['str']+p['weapon']+random.randint(1,10);p['wins']+=1;p['money']+=cfg['m'];p['exp']+=cfg['e'];msg=f"💥 Вынес {cfg['n']} на {dmg}! +{cfg['m']}р +{cfg['e']} опыта"
  if p['wins']==5: p['money']+=500;msg+=" | 📜 Квест +500р!"
  if p['exp']>=100: p['lvl']+=1;p['exp']=0;p['str']+=3;p['max_hp']+=15;p['hp']=p['max_hp'];msg+=f" | 🎉 LVL UP {p['lvl']}!"; 
  if p['lvl']==3: p['money']+=1000;msg+=" | Квест Ур3 +1000р!"
 save(p);return jsonify({"msg":msg})
@app.route('/api/buy',methods=['POST'])
def api_buy():
 uid=int(request.args.get('uid'));price=int(request.args.get('price'));wp=int(request.args.get('wp'));p=get_player(uid)
 if p['money']>=price: p['money']-=price;p['weapon']=wp;save(p);return jsonify({"msg":f"Купил +{wp} урона"})
 return jsonify({"msg":"Денег нет!"})
@app.route('/admin')
def admin_page():
 uid=int(request.args.get('uid',0))
 if uid not in ADMINS: return f"Нет доступа ID {uid}. Открой /admin?uid=842769679"
 conn=get_conn();cur=conn.cursor();cur.execute("SELECT user_id,lvl,money,wins FROM players ORDER BY lvl DESC LIMIT 100");rows=cur.fetchall();conn.close()
 html=f"<body style='background:#111;color:#fff;text-align:center;padding:20px;font-family:Arial'><h2>👑 АДМИНКА</h2><form method=POST action='/admin/give?uid={uid}'><input name=target placeholder='ID игрока' required><br><br><input name=money type=number placeholder='Денег'><br><br><input name=exp type=number placeholder='Опыта'><br><br><button style='padding:10px;background:green;color:white'>Выдать</button></form><hr>"
 for r in rows: html+=f"{r[0]} - Ур {r[1]} - {r[2]}р - {r[3]} побед<br>"
 return html
@app.route('/admin/give',methods=['POST'])
def admin_give():
 uid=int(request.args.get('uid')); 
 if uid not in ADMINS: return "Нет доступа"
 target=int(request.form['target']);money=int(request.form.get('money')or 0);exp=int(request.form.get('exp')or 0)
 conn=get_conn();cur=conn.cursor();cur.execute("UPDATE players SET money=money+%s,exp=exp+%s WHERE user_id=%s",(money,exp,target));conn.commit();conn.close()
 return f"✅ Выдал {target}: {money}р и {exp} опыта! <a href='/admin?uid={uid}'>Назад</a>"
def run_web(): app.run(host='0.0.0.0',port=int(os.environ.get("PORT",10000)))
bot=Bot(token=TOKEN);dp=Dispatcher()
threading.Thread(target=run_web,daemon=True).start()
async def bot_main(): await dp.start_polling(bot)
if __name__=="__main__": asyncio.run(bot_main())
