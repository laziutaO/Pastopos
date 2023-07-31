from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import sqlite3

print_name_q = "SELECT name FROM restaurant"
insert_q = 'INSERT INTO rating (restaurant_id, criteria_1, criteria_2, criteria_3, criteria_4, rating) VALUES (?, ?, ?, ?, ?, ?)'
insert_rev = 'INSERT INTO review (restaurant_id, review) VALUES (?, ?)'
find_indx_q = 'SELECT id FROM restaurant WHERE name = ? '
count_reviews_q = 'SELECT review FROM review WHERE restaurant_id = ? ORDER BY restaurant_id DESC LIMIT ?'
update_total_rating_q = 'UPDATE restaurant SET total_rating = COALESCE((SELECT AVG(rating) FROM rating WHERE restaurant_id = ?), 0) WHERE id = ?'
find_name_q = 'SELECT district, address, name, phone, total_rating FROM restaurant WHERE name LIKE ?'
find_address_q = 'SELECT district, address, name, phone, total_rating FROM restaurant WHERE address LIKE ?'

def set_db_connection():
    try:
        conn = sqlite3.connect('sql/pastopos1.db') 
        
    except sqlite3.Error as error:
        print("Error connecting to database:", error)

    return conn


async def send_restaurant_details(update: Update, results):
    message = ''
    for row in results:
        district = row[0]
        address = row[1]
        name = row[2]
        phone = row[3]
        rating_post = 'немає інформації про рейтинг' if row[4] is None else row[4]
        message += f"District: {district}\nAddress: {address}\nName: {name}\nPhone: {phone}\nRating: {rating_post}\n"
        #setting up buttons
        keyboard = [[InlineKeyboardButton('Оцінити', callback_data='rate')],
                [InlineKeyboardButton('Залиши відгук', callback_data='leave_review')],
                [InlineKeyboardButton('Прочитати відгуки', callback_data='read_reviews')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        #sending message with buttons
        await update.message.reply_text(message, reply_markup=reply_markup)
        message = ''


async def find_bar(update: Update, restaurant: str):
    connection = set_db_connection()
    cursor = connection.cursor()
    cursor.execute(find_name_q, ('%' + restaurant + '%',))
    results = cursor.fetchall()
    
    if not results:
        await update.message.reply_text('Такого закладу не існує. Перевірте чи правильно ви ввели назву')
        cursor.close()
        connection.close()
        return
    await send_restaurant_details(update, results)
    cursor.close()
    connection.close()

async def find_nearest_bar(update: Update, street: str):
    connection = set_db_connection()
    cursor = connection.cursor()
    cursor.execute(find_address_q, ('%' + street + '%',))
    results = cursor.fetchall()

    if not results:
        await update.message.reply_text('На даній вулиці немає жодного закладу харчування')
        cursor.close()
        connection.close()
        return
    await send_restaurant_details(update, results)
    cursor.close()
    connection.close()

async def atm_rate(query, restaurant: str):
    await query.message.reply_text(f'Чудово! Оцініть {restaurant} (від 1 до 5) за наступними критеріями:')
    
    keyboard = [[InlineKeyboardButton('          1', callback_data='Arate_1'),
                InlineKeyboardButton('           2', callback_data='Arate_2'),
                InlineKeyboardButton('           3', callback_data='Arate_3'),
                InlineKeyboardButton('           4', callback_data='Arate_4'),
                InlineKeyboardButton('           5', callback_data='Arate_5')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text('Атмосфера (1 - зовсім не сподобалась, 5 - дуже сподобалась)', reply_markup=reply_markup)

async def serv_rate(query):
    keyboard = [[InlineKeyboardButton('          1', callback_data='Srate_1'),
                InlineKeyboardButton('           2', callback_data='Srate_2'),
                InlineKeyboardButton('           3', callback_data='Srate_3'),
                InlineKeyboardButton('           4', callback_data='Srate_4'),
                InlineKeyboardButton('           5', callback_data='Srate_5')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text('Обслуговування (1 - неякісне, 5 - якісне)', reply_markup=reply_markup)\
    
async def cost_rate(query):
    keyboard = [[InlineKeyboardButton('          1', callback_data='Crate_1'),
                InlineKeyboardButton('           2', callback_data='Crate_2'),
                InlineKeyboardButton('           3', callback_data='Crate_3'),
                InlineKeyboardButton('           4', callback_data='Crate_4'),
                InlineKeyboardButton('           5', callback_data='Crate_5')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text('Вартість (1 - дорого, 5 - дешево)', reply_markup=reply_markup)

async def qual_rate(query):
    keyboard = [[InlineKeyboardButton('          1', callback_data='Qrate_1'),
                InlineKeyboardButton('           2', callback_data='Qrate_2'),
                InlineKeyboardButton('           3', callback_data='Qrate_3'),
                InlineKeyboardButton('           4', callback_data='Qrate_4'),
                InlineKeyboardButton('           5', callback_data='Qrate_5')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text('Якість продукції(1 - неякісна, 5 - якісна)', reply_markup=reply_markup)
    


async def save_rating_to_db(cur_restaurant ,list_rating, query):
    connection = set_db_connection()
    cursor = connection.cursor()
    print('set connection')
    cursor.execute(find_indx_q, (cur_restaurant,))
    id = cursor.fetchone()
    if not id:
        print('failed to get id')
    else:
        id = id[0]
        print(id)
        average = sum(list_rating) / len(list_rating)
        cursor.execute(insert_q, (id, list_rating[0], list_rating[1], list_rating[2], list_rating[3], average))
        await query.message.reply_text(f'Готово! Ми записали вашу оцінку закладу)')
        cursor.execute(update_total_rating_q, (id, id))

    connection.commit()
    cursor.close()
    connection.close()

async def save_review_to_db(cur_restaurant: str, text_review: str, update):
    connection = set_db_connection()
    cursor = connection.cursor()
    print('set connection')
    cursor.execute(find_indx_q, (cur_restaurant,))
    id = cursor.fetchone()
    if not id:
        print('failed to get id')
    else:
        id = id[0]
        print(id)
        print(text_review)
        cursor.execute(insert_rev, (id, text_review))
        await update.message.reply_text(f'Дякуємо за відгук!')

    connection.commit()
    cursor.close()
    connection.close()

async def print_reviews(cur_restaurant:str, text:str, update):
    amount = int(text)
    connection = set_db_connection()
    cursor = connection.cursor()
    print('set connection')
    cursor.execute(find_indx_q, (cur_restaurant,))
    id = cursor.fetchone()
    if not id:
        print('failed to get id')
    else:
        id = id[0]
        print(id)
        print(amount)
        cursor.execute(count_reviews_q, (id, amount))
        results = cursor.fetchall()
        if not results:
            await update.message.reply_text('На даний заклад ще не написано жодного відгуку')
            cursor.close()
            connection.close()
            return
        for row in results:
            review_text = row[0]
            message = review_text
            await update.message.reply_text(message)
            message = ''


    connection.commit()
    cursor.close()
    connection.close()