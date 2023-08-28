from typing import Final
from io import BytesIO
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler)
import googlemaps

import db



#Important data
TOKEN: Final = '6286538633:AAHKe8VbQYBflslOQbMcUuUhFX2SAOWJ2JA'
BOT_USERNAME: Final = '@pastopos_bot'


#Parameters
place = ''
restaurant = ''
street = ''
list_rating = [0, 0, 0, 0]
review_mode = False
review_read_mode = False
pattern_emoji = "[" u"\U0001F600-\U0001F64F" u"\U0001F300-\U0001F5FF"u"\U0001F680-\U0001F6FF"u"\U0001F1E0-\U0001F1FF"u"\U00002702-\U000027B0"u"\U000024C2-\U0001F251" "]+"
city = 'Львів'
API_KEY = 'AIzaSyButKq_BE0QiKWI12e_s0j-xMJ0W9DZhKY'
                                   
#Answers
start_answer = 'Привіт! Введи адресу для знаходження закладу харчування! Всі доступні команди можеш переглянути за допомогою команди /help'
help_answer = '/start - Розпочати роботу з ботом\n/help - Переглянути доступні команди\n/find - знайти заклад харчування\n/find_nearest - знайти найближчий заклад харчування'
not_enough_args = 'Недостатньо аргументів. Використовуйте /find "Назва Ресторану"'

async def find_gplace_photo(restaurant_name, city, chat_id):
    print(restaurant_name)
    gmaps = googlemaps.Client(key = API_KEY)
    query_str = f'{restaurant_name}, {city}'
    response = gmaps.places_autocomplete(input_text=query_str)
    
    if 'candidates' in response and len(response['candidates']) > 0:
        print('found candidates!')
        place_id = response['candidates'][0]['place_id']
        myfields = ['photo']
        
        place_details = gmaps.place(place_id=place_id, fields=myfields)
        
        if 'result' in place_details and 'photos' in place_details['result']:
            photo_id = place_details['result']['photos'][0]['photo_reference']
            photo_response = gmaps.places_photo(photo_reference=photo_id, max_height = 250, max_width = 250)
            
            photo_data = photo_response.content
            photo_file = BytesIO(photo_data)
            await bot.send_photo(chat_id=chat_id, photo=photo_file)
        else:
            print('No photos available for this place.')
    else:
        print('No candidates found for the given query.')

#Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(start_answer)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(help_answer)

async def find_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 1:
        # Якщо недостатньо аргументів, повідомити користувача
        await update.message.reply_text(not_enough_args)
    
    else:
        restaurant = ' '.join(args[0:])
        #await find_gplace_photo(restaurant_name=restaurant, city=city, chat_id=update.message.chat.id)
        await db.find_bar(update, restaurant)
       
        
async def find_nearest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 1:
        # Якщо недостатньо аргументів, повідомити користувача
        await update.message.reply_text(not_enough_args)
    
    else:
        street = ' '.join(args[0:])
        await db.find_nearest_bar(update, street)
               

#Replies

def handle_responce(text: str) -> str:
    proccessed: str = text.lower()

    return 'here is your answer'

async def handle_rate_button(update, context):
    query = update.callback_query
    user = query.from_user

    global list_rating
    global restaurant
    global review_mode
    global review_read_mode
    
    if query.data == 'rate':
        message_text = query.message.text
        name_match = re.search(r"Name: (.+)", message_text)
        if name_match:
            restaurant = name_match.group(1)
            await db.atm_rate(query, restaurant)  # Pass the query object instead of update
        else:
            print("Name not found in the string")
    
    if query.data == 'leave_review':
        print('leave_review functionality....')
        message_text = query.message.text
        name_match = re.search(r"Name: (.+)", message_text)
        if name_match:
            review_mode = True
            restaurant = name_match.group(1)
            await query.message.reply_text(f'Чудово! Залиште відгук на {restaurant} одним повідомленням')  # Pass the query object instead of update
        else:
            print("Name not found in the string")

    if query.data == 'read_reviews':
        print('we are about to read reviews....')
        message_text = query.message.text
        name_match = re.search(r"Name: (.+)", message_text)
        if name_match:
            review_read_mode = True
            restaurant = name_match.group(1)
            await query.message.reply_text('Вкажіть кількість ревю які ви хотіли б прочитати')
        else:
            print("Name not found in the string")

    if query.data.startswith('Arate_'):
        list_rating[0] = int(query.data.split('_')[1])
        print(f'button to assess atmosphere was clicked on {list_rating[0]}')
        await db.serv_rate(query)
    elif query.data.startswith('Srate_'):
        list_rating[1] = int(query.data.split('_')[1])
        await db.cost_rate(query)
    elif query.data.startswith('Crate_'):
        list_rating[2] = int(query.data.split('_')[1])
        await db.qual_rate(query)
    elif query.data.startswith('Qrate_'):
        list_rating[3] = int(query.data.split('_')[1])
        await db.save_rating_to_db(restaurant, list_rating, query)
        list_rating = [0, 0, 0, 0]
    # Answer the callback query to remove the "loading" state from the button
    await query.answer()



async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type = update.message.chat.type
    message = update.message
    
    if message.text:
        text = update.message.text
        global review_mode
        global review_read_mode
        # Check for emojis using regular expression
        emoji_pattern = re.compile(pattern_emoji, flags = re.UNICODE)
        if emoji_pattern.search(text):
            await context.bot.send_message(chat_id = message.chat_id, text = "На жаль, емодзі заборонені).")
            return
        # Check for stickers and GIFs
        if message.sticker or message.animation:
            # Handle the message accordingly (e.g., ignore, send error response)
            await context.bot.send_message(chat_id = message.chat_id, text = "На жаль, ви не можете відправляти стікери та GIF повідомлення.")
            return
        
        print(f'{update.message.chat.id} user in {message_type}: {text}')

        if review_mode:
            review_mode = False
            await db.save_review_to_db(restaurant, text.strip(), update)

        if review_read_mode: 
            if text.isdigit():
                review_read_mode = False
                await db.print_reviews(restaurant, text, update)
            else:
                await context.bot.send_message(chat_id = message.chat_id, text = "Виввели не число")

        if message_type == 'group':
            if BOT_USERNAME in text:
                transform_text = text.replace(BOT_USERNAME, '').strip()
                responce = handle_responce(transform_text)
            else:
                return
    else:
        await context.bot.send_message(chat_id = message.chat_id, text = "На жаль, даний бот не приймає емодзі, стікери та GIF повідомлення.")
  
    

    print(f'Bot responded: {responce}')
    await update.message.reply_text(responce)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'{update} caused error: {context.error}')

if __name__ == '__main__':
    print('bot launched....')
    bot = Application.builder().token(TOKEN).build()

    #Commands
    bot.add_handler(CommandHandler('start', start_command))
    bot.add_handler(CommandHandler('help', help_command))
    bot.add_handler(CommandHandler('find', find_command))
    bot.add_handler(CommandHandler('find_nearest', find_nearest_command))

    #Messages
    bot.add_handler(MessageHandler(filters.TEXT, handle_message))

    #Buttons
    bot.add_handler(CallbackQueryHandler(handle_rate_button))

    #Errors
    bot.add_error_handler(error_handler)

    print('Polling...')
    bot.run_polling(poll_interval = 2)

