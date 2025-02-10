import telebot
import os
from telebot.types import *
from pymongo import MongoClient
import matplotlib.pyplot as plt
import datetime

API_TOKEN = os.environ.get('API_TOKEN')
bot = telebot.TeleBot(API_TOKEN)

client = MongoClient('mongodb://localhost:27017/')

db = client['users']
collection = db['user']


@bot.message_handler(commands=['start'])
def start_bot(message):
    bot.reply_to(message, 'Welcome to the Personal Accountant Bot!\nبه بات حسابدار شخصی خوش آمدید')
    bot.reply_to(message, """برای استفاده و اموزش بر روی عبارت زیر کلیک کنید
                 کلید راهنما /help
                 """)


@bot.message_handler(commands=['help'])
def help_bot(message):
    bot.reply_to(message, """لطفا دستورالعمل زیر را با دقت بخوانید
                 اگر برای اولین بار است که از این بات استفاده میکنید نیاز است ثبت نام کنید
                 کلید ثبت نام /new_user
                 اگر از ثبت نام خود اطمینان حاصل کردید و میخواهید اطلاعات وارد کنید
                 کلید درج اطلاعات /get_new_data
                 اگر اطلاعات خود را به بات داده اید و میخواهید محاسبه انجام شود
                 کلید انجام محاسبات /get_chart
                 """)
    bot.reply_to(message, 'در صورت کار نکردن کلید های بالا میتوانید از منو استفاده کنید')


@bot.message_handler(commands=['new_user'])
def new_user(message):
    user = collection.find_one({'chat_id': str(message.chat.id)})
    if user is None:
        bot.reply_to(message, """برای ثبت نام اطلاعات خود را به صورت
                 نام و نام خانوادگی-کد ملی-شماره تلفن همراه
                 بفرستید
                 """)
        bot.register_next_step_handler(message, register)
    else:
        bot.reply_to(message, "شما قبلا ثبت نام کرده اید.")


def register(message):
    try:
        info = message.text.split('-')
        if len(info) != 3:
            bot.reply_to(message, "فرمت اطلاعات وارد شده صحیح نیست. لطفا دوباره تلاش کنید.")
            return

        name, id, phone = info
        collection.insert_one({
            'chat_id': str(message.chat.id),
            'user_name': message.from_user.username,
            'name': name,
            'id': id,
            'phone': phone,
            'income': [],
            'cost': [],
            'date': [],
        })
        bot.reply_to(message, """ثبت نام شما با موفقیت انجام شد
                     حالا میتوانید از بخش /get_new_data استفاده کنید
                     """)
    except Exception as e:
        bot.reply_to(message, f"خطا در ثبت نام: {e}")


@bot.message_handler(commands=['get_new_data'])
def get_new_data(message):
    user = collection.find_one({"chat_id": str(message.chat.id)})
    if user is not None:
        bot.reply_to(message, """اطلاعات هزینه و درآمد خود را به صورت زیر وارد کنید
                     +مقدار عددی درآمد
                     -مقدار عددی هزینه

                     توجه داشته باشید که درآمد و هزینه را باید باهم وارد کنید
                     اگر درآمدی ندارید به جای آن 
                     +0 قرار دهید
                     """)
        bot.register_next_step_handler(message, database)
    else:
        bot.reply_to(message, "شما ثبت نام نکرده اید. لطفا از دستور /new_user استفاده کنید.")


def database(message):
    try:
        user = collection.find_one({"chat_id": str(message.chat.id)})
        if user is not None:
            data = message.text.split("\n")
            if len(data) != 2:
                bot.reply_to(message, "فرمت اطلاعات وارد شده صحیح نیست. لطفا دوباره تلاش کنید.")
                return

            income = int(data[0].strip('+'))
            cost = int(data[1].strip('-'))
            date = datetime.datetime.now()
            collection.update_one({"chat_id": str(message.chat.id)}, {"$push": {"cost": cost, "income": income, "date": date}})
            bot.reply_to(message, """اطلاعات با موفقیت ذخیره شد. می‌توانید از دستور /get_chart استفاده کنید.""")
        else:
            bot.reply_to(message, "شما ثبت نام نکرده اید. لطفا از دستور /new_user استفاده کنید.")
    except Exception as e:
        bot.reply_to(message, f"خطا در ذخیره اطلاعات: {e}")


@bot.message_handler(commands=['get_chart'])
def get_chart(message):
    user = collection.find_one({'chat_id': str(message.chat.id)})
    if user is not None:
        income = user['income']
        cost = user['cost']
        date = user['date']
        total_income = sum(income)
        total_cost = sum(cost)

        plt.figure(figsize=(10, 5))
        plt.plot(date, income, label='Income')
        plt.title('Income Chart')
        plt.xlabel('Date')
        plt.ylabel('Income')
        plt.legend()
        plt.savefig('my_plot_income.png', dpi=300, transparent=True, bbox_inches="tight")
        plt.close()

        plt.figure(figsize=(10, 5))
        plt.plot(date, cost, label='Expense', color='red')
        plt.title('Expense Chart')
        plt.xlabel('Date')
        plt.ylabel('Expense')
        plt.legend()
        plt.savefig('my_plot_cost.png', dpi=300, transparent=True, bbox_inches="tight")
        plt.close()

        bot.reply_to(message, f"your total income : {total_income} \n your total cost : {total_cost} \n your balance : {total_income - total_cost}")
        chart_cost = open("my_plot_cost.png", "rb")
        chart_income = open("my_plot_income.png", "rb")
        bot.send_photo(message.chat.id, chart_income)
        bot.send_photo(message.chat.id, chart_cost)
    else:
        bot.reply_to(message, "شما ثبت نام نکرده اید. لطفا از دستور /new_user استفاده کنید.")


@bot.message_handler(func=lambda message: True)
def other_message(message):
    bot.reply_to(message, "ورودی نامعتبر است. لطفا از دستورات موجود استفاده کنید.")


bot.infinity_polling()