import telebot
from telebot import types
import sqlite3
import random
import time
import threading
from datetime import datetime

bot_token = '6815104243:AAHbI_dUY7vyjUfYPd1bcy6sJQ_4YSYCVqE'
bot = telebot.TeleBot(bot_token)
CHANNEL_ID = -1002093214840
admin_id = 1788067264
useer_id1 = 0


def rang1(message):
    connection = sqlite3.connect('lottery.sql')
    connection.isolation_level = None  # Устанавливаем isolation_level в None
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT rang FROM users WHERE id=?", (message.chat.id,))
        result = cursor.fetchone()
        cursor.execute("SELECT tickets FROM users WHERE id=?", (message.chat.id,))
        tickets = cursor.fetchone()
        bot.send_message(message.chat.id, f"{tickets[0]}, {result[0]}")

        if result:
            if str(result[0]) == '💎Алмаз':
                tickets = int(tickets[0]) + 20
                cursor.execute("UPDATE users SET tickets = ? WHERE id = ?", (int(tickets), message.chat.id))
                connection.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        cursor.close()
        connection.close()

def channel(message):
    member_info = bot.get_chat_member(CHANNEL_ID, message.from_user.id)
    connection = sqlite3.connect('lottery.sql')
    cursor = connection.cursor()
    cursor.execute("SELECT subscribe FROM users WHERE id=?", (message.chat.id,))
    flag = cursor.fetchone()
    if member_info.status in ['member', 'administrator', 'creator']:
        try:
            bot.send_message(message.chat.id, "Вам начислено 2 билета ")
            cursor.execute("SELECT tickets FROM users WHERE id=?", (message.chat.id,))
            fetched_data = str(cursor.fetchone())

            if fetched_data.isdigit():
                tickets = int(fetched_data)
                connection.commit()

                if flag is None:
                    cursor.execute("UPDATE users SET subscribe = ? WHERE id = ?", (1, message.chat.id))
                    cursor.execute("UPDATE users SET tickets = ? WHERE id = ?", (tickets + 2, message.chat.id))
                    connection.commit()
                else:
                    pass
            else:
                print("Fetched data is not a valid number")

        except Exception as e:
            print(f"An error occurred: {e}")
            # Обработка ошибки, например, вывод в лог или установка tickets в какое-то значение по умолчанию
            pass


def get_tickets(message):
    tickets = 0
    try:
        tickets += rang1(message)
    except TypeError:
        print("An error occurred while getting tickets.")
        # Можете выполнить другие действия в случае ошибки, например, установить tickets в какое-то значение по умолчанию
        pass

    return tickets


def rang(user_id1):
    useer_id1 = get_id()
    connection = sqlite3.connect('lottery.sql')
    cursor = connection.cursor()
    cursor.execute("SELECT rang, tickets FROM users WHERE id=?", (user_id1,))
    result = cursor.fetchone()

    if result:
        rang1, tickets = result
        if rang1 == '🥈Серебро':
            cursor.execute("UPDATE users SET tickets = ? WHERE id = ?", (tickets + 2, user_id1))
        elif rang1 == '🥇Золото':
            cursor.execute("UPDATE users SET tickets = ? WHERE id = ?", (tickets + 5, user_id1))
        elif rang1 == '🏆Платина':
            cursor.execute("UPDATE users SET tickets = ? WHERE id = ?", (tickets + 10, user_id1))
        elif rang1 == '💎Алмаз':
            cursor.execute("UPDATE users SET tickets = ? WHERE id = ?", (tickets + 20, user_id1))

        connection.commit()

    connection.close()


def get_user_name(user_id1):
    user_info = bot.get_chat(user_id1)
    return user_info.username

def get_id(message):
    user_id = message.chat.id
    return user_id

def background_task(user_id1, message):
    while True:
        channel(message)
        rang(user_id1)
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        if now.weekday() == 6 and current_time == '13:00:00':
            announce_winner()
        time.sleep(1)


def announce_winner():
    connection = sqlite3.connect('lottery.sql')
    cursor = connection.cursor()

    # Выбор случайного user_id из базы данных
    cursor.execute("SELECT id FROM users")
    all_user_ids = cursor.fetchall()

    if not all_user_ids:
        return  # Нет пользователей в базе данных

    winner_id = random.choice(all_user_ids)[0]
    winner_username = get_user_name(winner_id)

    if winner_username:
        # Отправка сообщения всем пользователям с объявлением победителя
        winner_message = f"🎉 Поздравляем, @{winner_username}! Вы - победитель лотереи! 🏆"
        for user_id in all_user_ids:
            bot.send_message(user_id[0], winner_message)

    connection.close()

def get_all_users():
    connection = sqlite3.connect('lottery.sql')
    cursor = connection.cursor()
    cursor.execute('SELECT id FROM users')
    users = cursor.fetchall()
    connection.close()
    return users

@bot.message_handler(commands=['start'])
def start(message):
    global useer_id1
    useer_id1 = message.chat.id
    if message.from_user.id == admin_id:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Повысить статус', callback_data='status'))
        bot.send_message(message.chat.id, 'Выберите действие', reply_markup=markup)
    user_id = message.text.split(' ')[1] if len(message.text.split(' ')) > 1 else None
    member_info = bot.get_chat_member(CHANNEL_ID, message.from_user.id)
    connection = sqlite3.connect('lottery.sql')
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER, tickets INTEGER, share INTEGER, rang TEXT, number_of_share INTEGER, subscribe INTEGER)''')
    if member_info.status in ['member', 'administrator', 'creator']:
        bot.send_message(message.chat.id, "Вам начислено 2 билета ")
        cursor.execute("SELECT tickets FROM users WHERE id=?", (message.chat.id,))
        current_rang = cursor.fetchone()
        if current_rang and current_rang[0] is not None:
            current_rang = int(current_rang[0]) + 2
        else:
            current_rang = 2
        cursor.execute("UPDATE users SET tickets = ? WHERE id = ?", (current_rang, message.chat.id))
        cursor.execute("INSERT OR REPLACE INTO users (id, rang) VALUES (?, ?)", (message.chat.id, str(current_rang)))
        cursor.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (message.chat.id,))
    else:
        current_rang = 0
        cursor.execute("UPDATE users SET tickets = ? WHERE id = ?", (current_rang, message.chat.id))
    if user_id is not None:
        cursor.execute("UPDATE users SET share = ? WHERE id = ?", (user_id, message.chat.id))
    cursor.execute("SELECT rang FROM users WHERE id=?", (message.chat.id,))
    rang = cursor.fetchone()
    if rang and rang[0] is None:
        rang = 'Новичок'
        cursor.execute("INSERT OR REPLACE INTO users (id, rang) VALUES (?, ?)", (message.chat.id, str(rang)))
    connection.commit()
    cursor.close()
    connection.close()
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Участвовать 🚀', callback_data='enter'))
    markup.add(types.InlineKeyboardButton('Получить билеты 🎟', 'https://t.me/notcoin_bot?start=r_574619_1940988'))
    markup.add(types.InlineKeyboardButton('Билеты за канал 🎫', 'https://t.me/notcoin_army'))
    markup.add(types.InlineKeyboardButton('Пригласить друга', callback_data='share'))
    markup.add(types.InlineKeyboardButton('Тех.поддержка', 'https://t.me/CrazyForce_support_bot'))
    bot.send_message(message.chat.id, f'👋 Привет, {message.from_user.first_name}! \n\nУчастие для всех полностью бесплатное!\n\n🤔 Как участвовать?  \n1. Вам нужно будет зарегистрироваться в ноткоине: https://t.me/notcoin_bot?start=r_574619_1940988\n2. Затем, набить уровень silver и купить tap bot (он бесплатный). \n3. После этого - пришлите скриншоты в тех.поддержку и ваш id (menu-id) и обязательно подпишите - "лотерея"\n\nМы вам начислим статус серебро и вы получите 2 билета 🎟 на розыгрыш!\n\n😌 Как получить ещё больше билетов и увеличить шанс на победу?За каждый уровень в notcoin - мы начисляем билеты:\n\n🥈Серебро - 2 билета 🎟\n🥇Золото - 5 билетов 🎟\n🏆Платина - 10 билетов 🎟\n💎Алмаз - 20 билетов 🎟\n\n😉 Но и это ещё не всё!\n1. Подписка на канал - дает +2 билета 🎟\n2. Пригласи друга, чтобы он получил статус серебра и получи ещё +2 билета за каждого! 🎟\n\nТвой ранг: {str(rang)[2:-3]}\nТвои билеты: {str(current_rang)} 🎟\n\nЖМИ УЧАСТВОВАТЬ!', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('share'))
def share(call):
    count = 0
    connection = sqlite3.connect('lottery.sql')
    cursor = connection.cursor()
    cursor.execute('SELECT share, rang FROM users')
    rows = cursor.fetchall()
    for row, rang in rows:
        if row == call.message.chat.id and rang == '🥈Серебро':
            count += 1
    cursor.execute("SELECT tickets FROM users WHERE id=?", (call.message.chat.id,))
    current_rang = cursor.fetchone()
    current_rang = int(str(current_rang)[1:-2])
    current_rang = current_rang + (2 * count)
    cursor.execute("UPDATE users SET tickets = ? WHERE id = ?", (current_rang, call.message.chat.id))
    connection.commit()
    connection.close()
    bot.send_message(call.message.chat.id, f'Твоя реферальная ссылка:\n https://t.me/lotteryy1_bot?start={call.message.chat.id}\n Количесвто приглашенных людей с рангом "🥈Серебро":{count}')


@bot.callback_query_handler(func=lambda call: call.data.startswith('status'))
def status(call):
    # Подключение к базе данных
    connection = sqlite3.connect('lottery.sql', check_same_thread=False)
    cursor = connection.cursor()

    text_id = ''
    text_status = ''
    markup = types.ForceReply(selective=False)

    # Функция, которая будет вызываться для получения идентификатора и статуса
    def get_id_and_status(message):
        nonlocal text_id, text_status  # Используем nonlocal для изменения значений внешних переменных
        text = message.text.split()
        text_id = text[0][:10]
        text_status = text[1][:255] if len(text) > 1 else ''
        bot.send_message(call.message.chat.id, f"ID: {text_id}, Статус: {text_status}")

        # Подключение к базе данных внутри функции
        inner_connection = sqlite3.connect('lottery.sql', check_same_thread=False)
        inner_cursor = inner_connection.cursor()
        inner_cursor.execute("UPDATE users SET rang = ? WHERE id = ?", (str(text_status), text_id))
        inner_connection.commit()
        inner_connection.close()  # Закрыть соединение внутри функции

    # Регистрируем обработчик следующего шага
    bot.register_next_step_handler(call.message, get_id_and_status)
    bot.send_message(call.message.chat.id, 'Введите ID и через пробел статус (не более 255 символов)',
                     reply_markup=markup)




@bot.callback_query_handler(func=lambda call: call.data.startswith('enter'))
def enter(call):
    connection = sqlite3.connect('lottery.sql')
    cursor = connection.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (call.message.chat.id,))
    cursor.execute("UPDATE users SET tickets = ? WHERE id = ?", (0, call.message.chat.id))
    connection.commit()
    bot.send_message(call.message.chat.id, 'Вы успешно зарегистрированы!')
def background_task(user_id1):
    while True:
        channel(user_id1)
        rang(user_id1)
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        if now.weekday() == 6 and current_time == '13:00:00':
            announce_winner()
        time.sleep(1)

if __name__ == "__main__":
    useer_id1 = 123456789  # Replace with the actual user_id1
    # Start the background task in a separate thread
    background_thread = threading.Thread(target=lambda: background_task(message))
    background_thread.start()

    # You may want to add the rest of your bot initialization here (e.g., bot.infinity_polling())
    bot.infinity_polling()
