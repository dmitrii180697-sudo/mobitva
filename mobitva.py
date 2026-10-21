from flask import Flask
import threading, os
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is alive!"
def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
threading.Thread(target=run_web, daemon=True).start()

import asyncio, random, sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Добавь BOT_TOKEN в Render -> Environment")

ADMINS = [842769679]
bot = Bot(token=TOKEN)
dp = Dispatcher()
db = sqlite3.connect("mobitva.db", check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS players (user_id INTEGER PRIMARY KEY, lvl INTEGER, exp INTEGER, money INTEGER, str INTEGER, agi INTEGER, hp INTEGER, max_hp INTEGER, weapon INTEGER)")
db.commit()
admin_states = {}

def get_player(uid):
    cur = db.execute("SELECT * FROM players WHERE user_id=?", (uid,))
    row = cur.fetchone()
    if not row:
        db.execute("INSERT INTO players VALUES (?,?,?,?,?,?,?,?,?)", (uid, 1, 0, 100, 5, 5, 100, 100, 0))
        db.commit()
        return {"user_id": uid, "lvl": 1, "exp": 0, "money": 100, "str": 5, "agi": 5, "hp": 100, "max_hp": 100, "weapon": 0}
    return {"user_id": row[0], "lvl": row[1], "exp": row[2], "money": row[3], "str": row[4], "agi": row[5], "hp": row[6], "max_hp": row[7], "weapon": row[8]}

def save_player(p):
    db.execute("UPDATE players SET lvl=?, exp=?, money=?, str=?, agi=?, hp=?, max_hp=?, weapon=? WHERE user_id=?", (p['lvl'], p['exp'], p['money'], p['str'], p['agi'], p['hp'], p['max_hp'], p['weapon'], p['user_id']))
    db.commit()
def is_admin(uid): return uid in ADMINS
def main_kb(uid):
    rows = [[KeyboardButton(text="👊 Искать бой"), KeyboardButton(text="👤 Профиль")], [KeyboardButton(text="🛒 Магазин")]]
    if is_admin(uid): rows.append([KeyboardButton(text="👑 Админка")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💰 Выдать деньги", callback_data="adm_money")], [InlineKeyboardButton(text="📈 Выдать уровень", callback_data="adm_lvl")], [InlineKeyboardButton(text="❤️ Вылечить всех", callback_data="adm_heal")], [InlineKeyboardButton(text="📊 Статистика", callback_data="adm_stats")]])

@dp.message(Command("start"))
async def start(m: types.Message):
    get_player(m.from_user.id)
    await m.answer(f"Добро пожаловать в МобиБитву, {m.from_user.first_name}! 🔥", reply_markup=main_kb(m.from_user.id))

@dp.message(lambda m: m.text == "👤 Профиль")
async def profile(m: types.Message):
    p = get_player(m.from_user.id)
    mark = " 👑 АДМИН" if is_admin(m.from_user.id) else ""
    await m.answer(f"👤 {m.from_user.first_name}{mark}\nID: {p['user_id']}\nУровень: {p['lvl']} | Опыт: {p['exp']}/100\n💰 Деньги: {p['money']} руб\n💪 Сила: {p['str']} | 🔫 Оружие: +{p['weapon']}\n❤️ Здоровье: {p['hp']}/{p['max_hp']}")

@dp.message(lambda m: m.text == "👊 Искать бой")
async def fight_start(m: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="В ГОЛОВУ 🧠", callback_data="hit_head")], [InlineKeyboardButton(text="В КОРПУС 🦾", callback_data="hit_body")], [InlineKeyboardButton(text="В НОГИ 🦵", callback_data="hit_legs")]])
    await m.answer("Куда бьешь? Выбирай:", reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("hit_"))
async def fight(c: types.CallbackQuery):
    p = get_player(c.from_user.id)
    if random.random() < 0.33:
        await c.answer("Противник заблокировал! 🛡️"); return
    dmg = p['str'] + p['weapon'] + random.randint(1, 5)
    p['exp'] += 15; p['money'] += 25
    if p['exp'] >= 100:
        p['lvl'] += 1; p['exp'] = 0; p['str'] += 2; p['max_hp'] += 10; p['hp'] = p['max_hp']
    save_player(p)
    await c.message.edit_text(f"💥 Попал на {dmg} урона! +25 руб и +15 опыта.")

@dp.message(lambda m: m.text == "🛒 Магазин")
async def shop(m: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Бита - 200 руб (+3)", callback_data="buy_bita")], [InlineKeyboardButton(text="Пистолет - 800 руб (+12)", callback_data="buy_pistol")]])
    await m.answer("Барыга: Что надо?", reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("buy_"))
async def buy(c: types.CallbackQuery):
    p = get_player(c.from_user.id)
    if c.data == "buy_bita" and p['money'] >= 200:
        p['money'] -= 200; p['weapon'] = 3; save_player(p)
        await c.answer("Купил биту!")
    elif c.data == "buy_pistol" and p['money'] >= 800:
        p['money'] -= 800; p['weapon'] = 12; save_player(p)
        await c.answer("Купил ствол! 🔫")
    else: await c.answer("Денег нет!")

@dp.message(lambda m: m.text == "👑 Админка")
async def admin_menu_msg(m: types.Message):
    if not is_admin(m.from_user.id): return
    await m.answer("👑 Админ-панель:", reply_markup=admin_kb())
@dp.message(Command("admin"))
async def admin_menu_cmd(m: types.Message):
    if not is_admin(m.from_user.id): return
    await m.answer("👑 Админ-панель:", reply_markup=admin_kb())

@dp.callback_query(lambda c: c.data.startswith("adm_"))
async def admin_click(c: types.CallbackQuery):
    if not is_admin(c.from_user.id): return
    if c.data == "adm_money":
        admin_states[c.from_user.id] = "wait_money"
        await c.message.answer("Напиши: ID сумма\nПример: 842769679 10000")
    elif c.data == "adm_lvl":
        admin_states[c.from_user.id] = "wait_lvl"
        await c.message.answer("Напиши: ID уровень")
    elif c.data == "adm_heal":
        db.execute("UPDATE players SET hp=max_hp"); db.commit()
        await c.message.answer("❤️ Всех вылечил!")
    elif c.data == "adm_stats":
        cur = db.execute("SELECT COUNT(*), SUM(money) FROM players")
        count, total = cur.fetchone()
        await c.message.answer(f"📊 Игроков: {count}\nВсего денег: {total}")

@dp.message()
async def admin_input(m: types.Message):
    if m.from_user.id not in admin_states: return
    state = admin_states[m.from_user.id]
    try:
        parts = m.text.split()
        tid = int(parts[0]); val = int(parts[1])
        p = get_player(tid)
        if state == "wait_money": p['money'] += val; save_player(p)
        if state == "wait_lvl": p['lvl'] = val; save_player(p)
        await m.answer(f"✅ Готово для {tid}: {val}")
        del admin_states[m.from_user.id]
    except Exception as e: await m.answer(f"Ошибка: {e}")

async def main(): await dp.start_polling(bot)
if __name__ == "__main__": asyncio.run(main())
