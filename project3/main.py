import telebot
from telebot.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
import time
from message import start_message, help_message, start_quiz_message
from data_quiz import question_list, option_list

with open(".env", "r") as file:
    TOKEN = file.read()

bot = telebot.TeleBot(TOKEN)

results = {}
user_data = {}

@bot.message_handler(commands=["start"])
def start_message_command(message: Message):
    bot.send_message(message.chat.id, text=start_message)

@bot.message_handler(commands=["help"])
def help_message_command(message: Message):
    bot.send_message(message.chat.id, text=help_message)

@bot.message_handler(commands=["start_quiz"])
def start_quiz_command(message: Message):
    global start_time
    start_time = time.time()

    user_data[message.chat.id] = {"current_question": 0, "score": 0}

    send_next_question(message.chat.id)

def send_next_question(chat_id):
    current_question = user_data[chat_id]["current_question"]
    if current_question >= len(question_list):
        return

    question_data = question_list[current_question]
    question_text = f"{current_question + 1}. {question_data['question']}"
    markup = InlineKeyboardMarkup()
    answers = []

    for num, option in enumerate(question_data['options']):
        button = InlineKeyboardButton(text=option, callback_data=option_list[num])
        answers.append(button)

    markup.add(*answers)

    bot.send_message(chat_id, text=question_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in option_list)
def callback_handler(call: CallbackQuery):
    user_id = call.message.chat.id
    current_question = user_data[user_id]["current_question"]

    old_question_data = question_list[current_question]
    if old_question_data["correct_option"] == call.data:
        bot.answer_callback_query(callback_query_id=call.id, text="Правильный ответ!")
        user_data[user_id]["score"] += 1
    else:
        bot.answer_callback_query(callback_query_id=call.id, text="Неправильный ответ")

    user_data[user_id]["current_question"] += 1

    send_next_question(user_id)

    if user_data[user_id]["current_question"] >= len(question_list):
        end_time = time.time()
        duration_seconds = end_time - start_time
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        results[call.from_user.username] = user_data[user_id]["score"]
        bot.send_message(user_id, text="Конец викторины.\n"
                                        f"Количество правильных ответов: {user_data[user_id]['score']}\n"
                                        f"Продолжительность: {minutes} и {seconds} секунд")

@bot.message_handler(commands=["record_table"])
def record(message: Message):
    if not results:
        bot.send_message(message.chat.id, text="Результаты отсутствуют.")
        return

    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    records_text = "Лучшие результаты:\n\n"

    for i, (username, score) in enumerate(sorted_results, start=1):
        records_text += f"{i}. @{username} Правильных ответов: {score}\n"

    bot.send_message(message.chat.id, text=records_text)

bot.polling()
