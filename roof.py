#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

import logging, datetime, pytz
import requests
from datetime import timedelta
from bs4 import BeautifulSoup
import logging
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import Chat, ChatMember, ChatMemberUpdated, Update, ForceReply
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

ALLOWED_USERS = {
    5494039093: "Me",
}

# Глобальные переменные для диапазонов
RUB_RANGES = {9999: 0.25, 39999: 0.22, 69999: 0.20, 99999: 0.17, float('inf'): 0.14}
RUB_RANGES_COLOMBO = {9999: 0.39, 39999: 0.34, 69999: 0.32, 99999: 0.29, float('inf'): 0.25}
USDT_RANGES = {500: 16, 1000: 14, float('inf'): 11}
USDT_RANGES_COLOMBO = {500: 24, 1000: 21, float('inf'): 19}


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_html(
        rf"Привет {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )
    chat_id = update.effective_chat.id
    user = update.effective_user
    user_id = user.id
    #await update.message.reply_text(f"Your chat ID is {chat_id}")
    #await context.bot.send_message(5494039093, f"User ID is {user_id}")



async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")

async def get_rub(update, context):
    user = update.effective_user
    
    # Получаем аргумент после команды
    arg = None
    if context.args:
        try:
            arg = float(context.args[0])
        except ValueError:
            await update.message.reply_text("Некорректное значение. Введите число после команды.")
            return

    USDT_SELL = format_price(fetch_price("USDT", "LKR", "Sell", "BANK"))
    #RUB_BUY = format_price(fetch_price("USDT", "RUB", "BUY", "RaiffeisenBank"))
    RUB_LKR = float( format_price( float(USDT_SELL) / float(RUB_BYBIT) ) )
    
    response = f"Купить USDT/RUB: {RUB_BYBIT}\n"
    response += f"Продать USDT/LKR: {USDT_SELL}\n\n"
    response += format_info("Безубыток RUB", RUB_LKR, [0.40, 0.35, 0.30, 0.25, 0.20, 0.15], arg)
    await update.message.reply_text(response)

async def get_usdt(update, context):
    user = update.effective_user
        
    # Получаем аргумент после команды
    arg = None
    if context.args:
        try:
            arg = float(context.args[0])
        except ValueError:
            await update.message.reply_text("Некорректное значение. Введите число после команды.")
            return

    USDT_SELL = format_price(fetch_price("USDT", "LKR", "Sell", "BANK"))
    response = format_info("Безубыток USDT", USDT_SELL, [19, 17, 15, 13, 12.5, 11, 10], arg)
    response += "\n"
    await update.message.reply_text(response)


async def get_usdt_percentages(update, context):
    user = update.effective_user
    
    
    # Получаем аргумент после команды
    arg = None
    if context.args:
        try:
            arg = float(context.args[0])
        except ValueError:
            await update.message.reply_text("Некорректное значение. Введите число после команды.")
            return

    USDT_SELL = format_price(fetch_price("USDT", "LKR", "Sell", "BANK"))
    response = format_info_percentage("Безубыток USDT", USDT_SELL, [3, 2.5, 2, 1.5, 1], arg)
    response += "\n\n"
    await update.message.reply_text(response)


def format_info_add_percentage(prefix, price, percentages, multiplier=None):
    info = f"{prefix}: {price}\n\n"
    for percentage in percentages:
        new_price = format_price(float(price) * (1 + percentage / 100.0))
        if multiplier:
            USDT = multiplier / float(new_price)
            USDT_difference = float(new_price) - float(price)
            profit = format_profit(float(USDT_difference) * float(USDT))
            info += f"+{percentage}%: {new_price} \n - отдадим: {format_profit(USDT)} USDT \n - профит: {profit} LKR\n\n"
        else:
            info += f"+{percentage}%: {new_price}\n"
    info += "\n"
    return info

async def get_usdt_add_percentages(update, context):
    user = update.effective_user
        
    
    # Получаем аргумент после команды
    arg = None
    if context.args:
        try:
            arg = float(context.args[0])
        except ValueError:
            await update.message.reply_text("Некорректное значение. Введите число после команды.")
            return

    USDT_SELL = format_price(fetch_price("USDT", "LKR", "Sell", "BANK"))
    response = format_info_add_percentage("Безубыток USDT", USDT_SELL, [1, 1.5, 2, 2.5, 3], arg)
    response += "\n"
    await update.message.reply_text(response)

async def print_prices(update, context):
    user = update.effective_user

    # Получаем аргумент после команды
    arg = context.args[0].lower() if context.args else None

    USDT_SELL = float(format_price(fetch_price("USDT", "LKR", "Sell", "BANK")))
    #RUB_BUY = format_price(fetch_price("USDT", "RUB", "BUY", "RaiffeisenBank"))
    RUB_LKR = float( format_price( float(USDT_SELL) / float(RUB_BYBIT) ) )

    responses = []

    if arg in ['rub', None]:
        responses.append(f"Безубыток RUB: {format_price(RUB_LKR)}\n")
        responses.append(generate_price_response('RUB', RUB_RANGES.items(), RUB_LKR, 'Хиккадува - Матара'))
        responses.append(generate_price_response('RUB', RUB_RANGES_COLOMBO.items(), RUB_LKR, 'Коломбо, Бентота'))
        responses.append(f"\n")

    if arg in ['usdt', None]:
        responses.append(f"Безубыток USDT: {format_price(USDT_SELL)}\n")
        responses.append(generate_price_response('USDT', USDT_RANGES.items(), USDT_SELL, 'Хиккадува - Матара'))
        responses.append(generate_price_response('USDT', USDT_RANGES_COLOMBO.items(), USDT_SELL, 'Коломбо, Бентота'))

    full_response = "\n".join(responses)
    await update.message.reply_text(full_response)

def generate_price_response(currency, ranges, base_price, location):
    response = f"{location}:\n"    
    response += f"{currency}:\n"
    for limit, value in ranges:
        if limit == float('inf') and currency == "RUB":
            limit = 139999
        elif limit == float('inf') and currency == "USDT":
            limit = 2000
        response += f"До {format_profit(limit)} - {format_price(base_price - value)}\n"
    response += f"Выше в лс\n"
    return response


async def get_rub_lkr(update, context):
    user = update.effective_user

    # Получаем аргументы после команды
    summa = int(context.args[0]) if context.args else None

    # Запрашиваем курсы валют
    USDT_SELL = float(format_price(fetch_price("USDT", "LKR", "Sell", "BANK")))
    #RUB_BUY = format_price(fetch_price("USDT", "RUB", "BUY", "RaiffeisenBank"))
    RUB_LKR = float( format_price( float(USDT_SELL) / float(RUB_BYBIT) ) )

    response = f"Безубыток: {format_price(RUB_LKR)}\n"
    await update.message.reply_text(response)


    # Если задан второй аргумент
    try:
        second_arg = context.args[1]
        try:
            # Проверяем, является ли второй аргумент числом (курсом)
            custom_rate = float(second_arg)
            location = None
        except ValueError:
            # Если второй аргумент - не число, предполагаем, что это локация
            if second_arg.lower() == 'bn':
                location = 'bn'
                custom_rate = None
            else:
                raise ValueError("Неверный второй аргумент. Ожидалось число (курс) или 'bn' (Бентота).")
    except IndexError:
        # Если второй аргумент не задан
        custom_rate = None
        location = None

    # Если пользовательский курс не задан
    if custom_rate is None:
        ranges = RUB_RANGES_COLOMBO if location == "bn" else RUB_RANGES
        last_value = next(reversed(ranges.values()))

        response = f"Максимальная граница для торговли: {format_price(RUB_LKR - last_value)}\n"  
        await update.message.reply_text(response)

        for upper_limit, value in ranges.items():
            if summa < upper_limit:
                rate = RUB_LKR - value
                break
    else:
        rate = custom_rate

    response = f"Стоимость: {format_profit(summa)} рублей\n"
    response += f"Курс обмена: 1 рубль = {format_price(rate)} рупий\n"
    response += f"Получите: {format_profit(summa * rate)} рупий\n\n"
    response += f"🏦 Мы принимаем оплату через банковский перевод на Тинькофф\n\n"
    response += f"- - - -\n"
    response += f"🚨 Обратите внимание, что курс обмена может измениться в любое время из-за экономических и политических факторов."
    await update.message.reply_text(response)
   
    response = f"{format_profit(summa)} / {format_price(rate)} / {format_profit(summa * rate)}"
    await update.message.reply_text(response)

    response = f"Профит: {format_profit(summa * (RUB_LKR - rate))} рупий"
    await update.message.reply_text(response)

async def get_lkr_rub(update, context):
    user = update.effective_user

    # Получаем аргумент после команды
    summa = int(context.args[0]) if context.args else None

    # Запрашиваем курсы валют
    USDT_SELL = float(format_price(fetch_price("USDT", "LKR", "Sell", "BANK")))
    #RUB_BUY = format_price(fetch_price("USDT", "RUB", "BUY", "RaiffeisenBank"))
    RUB_LKR = float( format_price( float(USDT_SELL) / float(RUB_BYBIT) ) )

    response = f"Безубыток: {format_price(RUB_LKR)}\n"
    await update.message.reply_text(response)

    # Если задан второй аргумент
    try:
        second_arg = context.args[1]
        try:
            # Проверяем, является ли второй аргумент числом (курсом)
            custom_rate = float(second_arg)
            location = None
        except ValueError:
            # Если второй аргумент - не число, предполагаем, что это локация
            if second_arg.lower() == 'bn':
                location = 'bn'
                custom_rate = None
            else:
                raise ValueError("Неверный второй аргумент. Ожидалось число (курс) или 'bn' (Бентота).")
    except IndexError:
        # Если второй аргумент не задан
        custom_rate = None
        location = None

    # Если пользовательский курс не задан
    if custom_rate is None:
        ranges = RUB_RANGES_COLOMBO if location == "bn" else RUB_RANGES
        last_value = next(reversed(ranges.values()))

        response = f"Максимальная граница для торговли: {format_price(RUB_LKR - last_value)}\n"  
        await update.message.reply_text(response)

        for upper_limit, value in ranges.items():
            if upper_limit * (RUB_LKR - value) > summa:
                rate = RUB_LKR - value
                break
    else:
        rate = custom_rate

    response = f"Стоимость: {format_price(summa / rate)} рублей\n"
    response += f"Курс обмена: 1 рубль = {format_price(rate)} рупий\n"
    response += f"Получите: {format_profit(summa)} рупий\n\n"
    response += f"🏦 Мы принимаем оплату через банковский перевод на Тинькофф\n\n"
    response += f"- - - -\n"
    response += f"🚨 Обратите внимание, что курс обмена может измениться в любое время из-за экономических и политических факторов."
    await update.message.reply_text(response)

    response = f"{format_profit(summa / rate)} / {format_price(rate)} / {format_profit(summa)}"
    await update.message.reply_text(response)
    
    response = f"Профит: {format_profit((summa / rate) * (RUB_LKR - rate))} рупий"
    await update.message.reply_text(response)

async def get_usdt_lkr(update, context):
    user = update.effective_user

    # Получаем аргументы после команды
    summa = int(context.args[0]) if context.args else None

    # Получаем курс валюты
    USDT_SELL = float(format_price(fetch_price("USDT", "LKR", "Sell", "BANK")))

    response = f"Безубыток: {format_price(USDT_SELL)}\n"
    await update.message.reply_text(response)

    # Если задан второй аргумент
    try:
        second_arg = context.args[1]
        try:
            # Проверяем, является ли второй аргумент числом (курсом)
            custom_rate = float(second_arg)
            location = None
        except ValueError:
            # Если второй аргумент - не число, предполагаем, что это локация
            if second_arg.lower() == 'bn':
                location = 'bn'
                custom_rate = None
            else:
                raise ValueError("Неверный второй аргумент. Ожидалось число (курс) или 'bn' (Бентота).")
    except IndexError:
        # Если второй аргумент не задан
        custom_rate = None
        location = None

    # Если пользовательский курс не задан
    if custom_rate is None:
        ranges = USDT_RANGES_COLOMBO if location == "bn" else USDT_RANGES
        last_value = next(reversed(ranges.values()))

        response = f"Максимальная граница для торговли: {format_price(USDT_SELL - last_value)}\n"  
        await update.message.reply_text(response)

        for upper_limit, value in ranges.items():
            if summa < upper_limit:
                rate = USDT_SELL - value
                break
    else:
        rate = custom_rate

    response = f"Стоимость: {format_price(summa)} USDT\n"
    response += f"Курс обмена: 1 USDT = {format_price(rate)} рупий\n"
    response += f"Получите: {format_profit(summa * rate)} рупий\n\n"
    response += f"🏦 Мы принимаем оплату через TRC-20\n\n"
    response += f"- - - -\n"
    response += f"🚨 Обратите внимание, что курс обмена может измениться в любое время из-за экономических и политических факторов."
    await update.message.reply_text(response)

    response = f"{format_price(summa)} / {format_price(rate)} / {format_profit(summa * rate)}"
    await update.message.reply_text(response)

    response = f"Профит: {format_profit(summa * (USDT_SELL - rate))} рупий"
    await update.message.reply_text(response)

async def get_lkr_usdt(update, context):
    user = update.effective_user

    # Получаем аргументы после команды
    summa = int(context.args[0]) if context.args else None

    # Получаем курс валюты
    USDT_SELL = float(format_price(fetch_price("USDT", "LKR", "Sell", "BANK")))

    response = f"Безубыток: {format_price(USDT_SELL)}\n"
    await update.message.reply_text(response)

    # Если задан второй аргумент
    try:
        second_arg = context.args[1]
        try:
            # Проверяем, является ли второй аргумент числом (курсом)
            custom_rate = float(second_arg)
            location = None
        except ValueError:
            # Если второй аргумент - не число, предполагаем, что это локация
            if second_arg.lower() == 'bn':
                location = 'bn'
                custom_rate = None
            else:
                raise ValueError("Неверный второй аргумент. Ожидалось число (курс) или 'bn' (Бентота).")
    except IndexError:
        # Если второй аргумент не задан
        custom_rate = None
        location = None

    # Если пользовательский курс не задан
    if custom_rate is None:
        ranges = USDT_RANGES_COLOMBO if location == "bn" else USDT_RANGES
        last_value = next(reversed(ranges.values()))

        response = f"Максимальная граница для торговли: {format_price(USDT_SELL - last_value)}\n"  
        await update.message.reply_text(response)

        for upper_limit, value in ranges.items():
            if upper_limit * (USDT_SELL - value) > summa:
                rate = USDT_SELL - value
                break
    else:
        rate = custom_rate

    response = f"Стоимость: {format_price(summa / rate)} USDT\n"
    response += f"Курс обмена: 1 USDT = {format_price(rate)} рупий\n"
    response += f"Получите: {format_profit(summa)} рупий\n\n"
    response += f"🏦 Мы принимаем оплату через TRC-20\n\n"
    response += f"- - - -\n"
    response += f"🚨 Обратите внимание, что курс обмена может измениться в любое время из-за экономических и политических факторов."
    await update.message.reply_text(response)

    response = f"{format_price(summa / rate)} / {format_price(rate)} / {format_profit(summa)}"
    await update.message.reply_text(response)

    response = f"Профит: {format_profit((summa / rate) * (USDT_SELL - rate))} рупий"
    await update.message.reply_text(response)


def format_profit(profit):
    return "{:,.0f}".format(float(profit)).replace(",", " ")    

def fetch_price(asset: str, fiat: str, trade_type: str, pay_type: str):
    """
    Функция для получения цены криптовалюты от Binance P2P.
    """
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "content-type": "application/json",
        "Host": "p2p.binance.com",
        "Origin": "https://p2p.binance.com",
        "Pragma": "no-cache",
        "TE": "Trailers",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0"
    }

    data = {
        "asset": asset,
        "fiat": fiat,
        "merchantCheck": True,
        "page": 1,
        "payTypes": [pay_type],
        "publisherType": None,
        "rows": 5,
        "tradeType": trade_type
    }

    try:
        r = requests.post('https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search', headers=headers, json=data).json()

        if r['data']:
            return r['data'][4]['adv']['price']
        else:
            print(f"No data available for {asset}/{fiat}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def format_price(price):
    return "{:,.2f}".format(float(price)).replace(",", " ")

def format_info(prefix, price, deductions, multiplier=None):
    info = f"{prefix}: {price}\n\n"
    for deduction in deductions:
        new_price = format_price((float(price) - deduction))
        if multiplier:
            profit = format_profit(deduction * multiplier)
            info += f"Курс: {new_price}\n - Разница: {deduction}\n - Профит: {profit} Рупий\n\n"
        else:
            info += f"Курс: {new_price}\n - Разница: {deduction}\n\n"
    info += "\n"
    return info
    
def format_info_percentage(prefix, price, percentages, multiplier=None):
    info = f"{prefix}: {price}\n\n"
    for percentage in percentages:
        new_price = format_price(float(price) * (1 - percentage / 100.0))
        if multiplier:
            profit = format_profit((float(price) - float(new_price)) * multiplier)
            info += f"Процент: {percentage}%\n- Курс: {new_price}\n- Профит: {profit} Рупий\n\n"
        else:
            info += f"Процент: {percentage}%\n- Курс: {new_price}\n"
    info += "\n"
    return info

global RUB_BYBIT
RUB_BYBIT = 1

async def bybit(context):
    global RUB_BYBIT
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        firefox_options = Options()
        firefox_options.add_argument('-headless')
        
        logging.info("Starting Firefox driver in headless mode...")
        driver = webdriver.Firefox(options=firefox_options)

        logging.info("Navigating to URL...")
        driver.get("https://www.bybit.com/fiat/trade/otc/?actionType=1&token=USDT&fiat=RUB&paymentMethod=64")
        
        logging.info("Waiting for JavaScript to render...")

        time.sleep(4)
        
        try:
            element_to_delete = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CLASS_NAME, 'ant-modal-root')))
            driver.execute_script("arguments[0].remove();", element_to_delete)
        except TimeoutException:
            print("Looks like the element took a day off. Moving on!")

        time.sleep(2)
        
        # Find the 'paywayAnchorList' element and click it
        driver.find_element(By.XPATH, '//*[@id="paywayAnchorList"]').click()
        logging.info("Clicked on the 'paywayAnchorList' div.")
        
        time.sleep(2)

        # Find the span element and click it
        driver.find_element(By.CSS_SELECTOR,'span[title="Raiffeisenbank"]').click()
        logging.info("Clicked on the 'Raiffeisenbank' span.")

        time.sleep(2)
        
        # Find the confirm button and click it
        driver.find_element(By.CLASS_NAME, 'btn-confirm').click()
        logging.info("Clicked the 'Confirm' button.")

        time.sleep(2)
        
        # Explicit wait for 'price-amount'
        element_present = EC.presence_of_element_located((By.CLASS_NAME, 'price-amount'))

        time.sleep(2)
        
        logging.info("Fetching page source...")
        page_source = driver.page_source
        
        logging.info("Parsing HTML...")
        soup = BeautifulSoup(page_source, 'html.parser')
        
        logging.info("Finding the third price...")
        prices = soup.find_all(class_='price-amount')
        
        if len(prices) >= 3:
            RUB_BYBIT = format_price(float(prices[2].text))
            print(RUB_BYBIT)
        else:
            logging.warning("Less than 3 prices found.")
        
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        
    finally:
        logging.info("Closing browser...")
        driver.quit()

async def bb(context, update):
    global RUB_BYBIT
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        firefox_options = Options()
        firefox_options.add_argument('-headless')
        
        logging.info("Starting Firefox driver in headless mode...")
        driver = webdriver.Firefox(options=firefox_options)

        logging.info("Navigating to URL...")
        driver.get("https://www.bybit.com/fiat/trade/otc/?actionType=1&token=USDT&fiat=RUB&paymentMethod=64")
        
        logging.info("Waiting for JavaScript to render...")

        time.sleep(4)
        
        try:
            element_to_delete = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CLASS_NAME, 'ant-modal-root')))
            driver.execute_script("arguments[0].remove();", element_to_delete)
        except TimeoutException:
            print("Looks like the element took a day off. Moving on!")

        time.sleep(2)
        
        # Find the 'paywayAnchorList' element and click it
        driver.find_element(By.XPATH, '//*[@id="paywayAnchorList"]').click()
        logging.info("Clicked on the 'paywayAnchorList' div.")
        
        time.sleep(2)

        # Find the span element and click it
        driver.find_element(By.CSS_SELECTOR,'span[title="Raiffeisenbank"]').click()
        logging.info("Clicked on the 'Raiffeisenbank' span.")

        time.sleep(2)
        
        # Find the confirm button and click it
        driver.find_element(By.CLASS_NAME, 'btn-confirm').click()
        logging.info("Clicked the 'Confirm' button.")

        time.sleep(2)
        
        # Explicit wait for 'price-amount'
        element_present = EC.presence_of_element_located((By.CLASS_NAME, 'price-amount'))

        time.sleep(2)
        
        logging.info("Fetching page source...")
        page_source = driver.page_source
        
        logging.info("Parsing HTML...")
        soup = BeautifulSoup(page_source, 'html.parser')
        
        logging.info("Finding the third price...")
        prices = soup.find_all(class_='price-amount')
        
        if len(prices) >= 3:
            RUB_BYBIT = format_price(float(prices[2].text))
            print(RUB_BYBIT)
        else:
            logging.warning("Less than 3 prices found.")
        
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        
    finally:
        logging.info("Closing browser...")
        driver.quit()

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token("6220120380:AAFg1NQP68QwSDpfL_6j3pvvac73jg61kfI").build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("rub", get_rub))
    application.add_handler(CommandHandler("usdt", get_usdt))
    application.add_handler(CommandHandler("usdtp", get_usdt_percentages))
    application.add_handler(CommandHandler("usdtap", get_usdt_add_percentages))
    application.add_handler(CommandHandler("print", print_prices))
    application.add_handler(CommandHandler("rublkr", get_rub_lkr))
    application.add_handler(CommandHandler("lkrrub", get_lkr_rub))
    application.add_handler(CommandHandler("usdtlkr", get_usdt_lkr))
    application.add_handler(CommandHandler("lkrusdt", get_lkr_usdt))
    
    application.add_handler(CommandHandler("bybit", bb))

    application.job_queue.run_repeating(bybit, interval=timedelta(minutes=4))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
