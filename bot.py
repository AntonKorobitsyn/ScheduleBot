import telebot
import requests
import json
from datetime import datetime, timedelta

API_TOKEN = '7750964025:AAGi1yyk1lGGFKsW7yhpuNTFZUgLV7_GjWk'  # Замените на ваш токен
bot = telebot.TeleBot(API_TOKEN)

# Словарь для хранения групп пользователей
user_groups = {}

class ScheduleBot:
    def __init__(self):
        self.base_url = 'https://digital.etu.ru/api/mobile/schedule'  # URL API

    def get_schedule(self, group_number, date=None):
        params = {
            'groupNumber[]': group_number,  # Передаем номер группы
        }
        if date:
            params['weekDay'] = [date.strftime('%a').upper()]  # Добавляем день недели в запрос
        response = requests.get(self.base_url, params=params)
        return response.json()  # Возвращаем JSON-ответ

    def format_schedule(self, group_number, schedule_data):
        formatted_schedule = ""
        
        # Проверяем, есть ли данные для группы
        if group_number not in schedule_data:
            return "Расписание не найдено для указанной группы."
        
        group_schedule = schedule_data[group_number]
        days = group_schedule.get('days', {})

        for day_key, day_info in days.items():
            day_name = day_info['name']
            formatted_schedule += f"{day_name}:\n"
            lessons = day_info.get('lessons', [])
            
            # Используем множество для отслеживания уникальных занятий
            unique_lessons = set()

            if not lessons:
                formatted_schedule += "  Нет занятий\n"
            for lesson in lessons:
                subject = lesson['name']
                teacher = lesson['teacher']
                start_time = lesson['start_time']
                end_time = lesson['end_time']
                lesson_info = (subject, teacher, start_time, end_time)

                # Добавляем занятие в множество, чтобы избежать дублирования
                if lesson_info not in unique_lessons:
                    unique_lessons.add(lesson_info)
                    formatted_schedule += f"  {subject} (Преподаватель: {teacher}, Время: {start_time} - {end_time})\n"
            
            formatted_schedule += "\n"
        
        return formatted_schedule.strip()  # Удаляем лишние пробелы в конце

schedule_bot = ScheduleBot()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    print("Received /start command")  # Отладочное сообщение
    bot.reply_to(message, "Добро пожаловать! Я бот для получения расписания. Пожалуйста, установите вашу группу с помощью команды /set_group. Используйте команду /help для получения списка доступных команд.")

@bot.message_handler(commands=['set_group'])
def set_group(message):
    user_id = message.from_user.id
    group_number = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    
    if group_number:
        user_groups[user_id] = group_number
        bot.reply_to(message, f"Ваша группа {group_number} сохранена.")
    else:
        bot.reply_to(message, "Пожалуйста, укажите номер вашей группы после команды /set_group.")

@bot.message_handler(commands=['help'])
def send_help(message):
    print("Received /help command")  # Отладочное сообщение
    help_text = (
        "/start - Приветствие\n"
        "/set_group <номер группы> - Установить вашу группу\n"
        "/schedule - Получить полное расписание для вашей группы\n"
        "/today - Получить расписание на сегодня для вашей группы\n"
        "/tomorrow - Получить расписание на завтра для вашей группы"
    )
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['schedule'])
def handle_schedule(message):
    user_id = message.from_user.id
    group_number = user_groups.get(user_id)

    if not group_number:
        bot.reply_to(message, "Сначала установите вашу группу с помощью команды /set_group.")
        return

    try:
        print(f"Fetching full schedule for group: {group_number}")  # Отладочное сообщение
        response_data = schedule_bot.get_schedule(group_number)

        # Форматируем расписание
        formatted_schedule = schedule_bot.format_schedule(group_number, response_data)

        # Проверка длины сообщения и разбиение на части, если необходимо
        max_length = 4096
        if len(formatted_schedule) > max_length:
            for i in range(0, len(formatted_schedule), max_length):
                bot.send_message(message.chat.id, formatted_schedule[i:i + max_length])
        else:
            bot.reply_to(message, formatted_schedule)  # Ответ с расписанием

    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")

@bot.message_handler(commands=['today'])
def handle_today(message):
    user_id = message.from_user.id
    group_number = user_groups.get(user_id)

    if not group_number:
        bot.reply_to(message, "Сначала установите вашу группу с помощью команды /set_group.")
        return

    try:
        print(f"Fetching today's schedule for group: {group_number}")  # Отладочное сообщение
        today = datetime.now()
        response_data = schedule_bot.get_schedule(group_number, today)

        # Форматируем расписание
        formatted_schedule = schedule_bot.format_schedule(group_number, response_data)

        # Проверка длины сообщения и разбиение на части, если необходимо
        max_length = 4096
        if len(formatted_schedule) > max_length:
            for i in range(0, len(formatted_schedule), max_length):
                bot.send_message(message.chat.id, formatted_schedule[i:i + max_length])
        else:
            bot.reply_to(message, formatted_schedule)  # Ответ с расписанием

    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")

@bot.message_handler(commands=['tomorrow'])
def handle_tomorrow(message):
    user_id = message.from_user.id
    group_number = user_groups.get(user_id)

    if not group_number:
        bot.reply_to(message, "Сначала установите вашу группу с помощью команды /set_group.")
        return

    try:
        print(f"Fetching tomorrow's schedule for group: {group_number}")  # Отладочное сообщение
        tomorrow = datetime.now() + timedelta(days=1)
        response_data = schedule_bot.get_schedule(group_number, tomorrow)

        # Форматируем расписание
        formatted_schedule = schedule_bot.format_schedule(group_number, response_data)

        # Проверка длины сообщения и разбиение на части, если необходимо
        max_length = 4096
        if len(formatted_schedule) > max_length:
            for i in range(0, len(formatted_schedule), max_length):
                bot.send_message(message.chat.id, formatted_schedule[i:i + max_length])
        else:
            bot.reply_to(message, formatted_schedule)  # Ответ с расписанием

    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")

if __name__ == '__main__':
    print("Bot is polling...")  # Отладочное сообщение
    bot.polling()
