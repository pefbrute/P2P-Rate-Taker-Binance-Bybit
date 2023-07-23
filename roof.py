#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

import asyncio
import logging
import requests
import os
from dotenv import load_dotenv
from abc import ABC, abstractmethod

load_dotenv()

load_dotenv(dotenv_path='token.env')
token = os.getenv('TELEGRAM_TOKEN')

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
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

ALLOWED_USERS = {
    5494039093: "Me",
}

# Глобальные переменные для диапазонов
RUB_RANGES = {9999: 0.24, 39999: 0.21, 69999: 0.19, 99999: 0.17, float('inf'): 0.15}
RUB_RANGES_COLOMBO = {9999: 0.37, 39999: 0.32, 69999: 0.29, 99999: 0.27, float('inf'): 0.23}
USDT_RANGES = {500: 15, 1000: 13, float('inf'): 10}
USDT_RANGES_COLOMBO = {500: 23.5, 1000: 20.5, float('inf'): 18.5}


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
        "rows": 3,
        "tradeType": trade_type
    }

    try:
        r = requests.post('https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search', headers=headers, json=data).json()

        if r['data']:
            return r['data'][2]['adv']['price']
        else:
            print(f"No data available for {asset}/{fiat}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

async def fetch_and_format_price(symbol, currency, action, provider):
    try:
        return format_price(fetch_price(symbol, currency, action, provider))
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None

async def get_arg(context):
    if context.args:
        try:
            return float(context.args[0])
        except ValueError:
            return None



class ExchangeProcessor:
    def __init__(self, update, context, response_generator, get_rates_func):
        self.update = update
        self.context = context
        self.response_generator = response_generator
        self.get_rates_func = get_rates_func

    async def process(self):
        summa, custom_rate, location = await get_user_arguments(self.context)

        if self.get_rates_func:
            rate = await self.get_rates_func()
        else:
            rate = float(format_price(fetch_price("USDT", "LKR", "Sell", "BANK")))

        response = f"Безубыток: {format_price(rate)}\n"
        await self.reply(response)

        responses = await self.response_generator.generate(summa, custom_rate, location, rate)

        for response in responses:
            await self.reply(response)

    async def reply(self, response):
        # Assuming self.update has a method for sending messages
        await self.context.bot.send_message(chat_id=self.update.effective_chat.id, text=response)

class UsdtLkrProcessor(ExchangeProcessor):
    def __init__(self, update, context, response_generator, conversion):
        # Pass all arguments to the superclass
        super().__init__(update, context, response_generator, None)  # We pass None as get_rates_func is not used in this class
        self.conversion = conversion

    async def process(self):
        user = self.update.effective_user
        summa, custom_rate, location = await get_user_arguments(self.context)

        rate = float(format_price(fetch_price("USDT", "LKR", "Sell", "BANK")))

        response = f"Безубыток: {format_price(rate)}\n"
        await self.reply(response)

        responses = await self.response_generator(summa, custom_rate, location, rate, self.conversion)

        for response in responses:
            await self.reply(response)

class LkrUsdtProcessor(ExchangeProcessor):
    def __init__(self, update, context, response_generator, conversion):
        super().__init__(update, context, response_generator, None)
        self.response_generator = response_generator
        self.conversion = conversion

    async def process(self):
        user = self.update.effective_user
        summa, custom_rate, location = await get_user_arguments(self.context)

        rate = float(format_price(fetch_price("USDT", "LKR", "Sell", "BANK")))

        response = f"Безубыток: {format_price(rate)}\n"
        await self.reply(response)

        responses = await self.response_generator(summa, custom_rate, location, rate, self.conversion)

        for response in responses:
            await self.reply(response)



class ResponseGenerator:
    def generate(self, summa, custom_rate, location, rate):
        raise NotImplementedError()

class RubToLkrResponseGenerator(ResponseGenerator):
    async def generate(self, summa, custom_rate, location, rate):
        calculated_rate, response = await calculate_rate(summa, custom_rate, location, rate, RUB_RANGES_COLOMBO, RUB_RANGES)
        response2 = await generate_common_response(summa, calculated_rate, 'рублей')
        response3 = f"{format_profit(summa)} / {format_price(calculated_rate)} / {format_profit(summa * calculated_rate)}"
        response4 = f"Профит: {format_profit(summa * (rate - calculated_rate))} рупий"

        return response, response2, response3, response4

class LkrToRubResponseGenerator(ResponseGenerator):
    async def generate(self, summa, custom_rate, location, rate):
        calculated_rate, response = await calculate_rate(summa, custom_rate, location, rate, RUB_RANGES_COLOMBO, RUB_RANGES, True)
        response2 = await generate_common_response(summa / calculated_rate, calculated_rate, 'рублей')
        response3 = f"{format_profit(summa / calculated_rate)} / {format_price(calculated_rate)} / {format_profit(summa)}"
        response4 = f"Профит: {format_profit((summa / calculated_rate) * (rate - calculated_rate))} рупий"

        return response, response2, response3, response4
 
class UsdtToLkrResponseGenerator(ResponseGenerator):
    async def generate(self, summa, custom_rate, location, rate):
        calculated_rate, response = await calculate_rate(summa, custom_rate, location, rate, USDT_RANGES_COLOMBO, USDT_RANGES)
        response2 = await generate_common_response(summa, calculated_rate, 'USDT')
        response3 = f"{format_price(summa)} / {format_price(calculated_rate)} / {format_profit(summa * calculated_rate)}"
        response4 = f"Профит: {format_profit(summa * (rate - calculated_rate))} рупий"

        return response, response2, response3, response4

class LkrToUsdtResponseGenerator(ResponseGenerator):
    async def generate(self, summa, custom_rate, location, rate):
        calculated_rate, response = await calculate_rate(summa, custom_rate, location, rate, USDT_RANGES_COLOMBO, USDT_RANGES, True)
        response2 = await generate_common_response(summa / calculated_rate, calculated_rate, 'USDT')
        response3 = f"{format_price(summa / calculated_rate)} / {format_price(calculated_rate)} / {format_profit(summa)}"
        response4 = f"Профит: {format_profit((summa / calculated_rate) * (rate - calculated_rate))} рупий"

        return response, response2, response3, response4


async def calculate_rate(summa, custom_rate, location, currency_value, ranges, default_ranges, is_reverse=False):
    if custom_rate is None:        
        ranges = ranges if location == "bn" else default_ranges            
            
        last_value = next(reversed(ranges.values()))
        response = f"Максимальная граница для торговли: {format_price(currency_value - last_value)}\n"  

        if (is_reverse):
            for upper_limit, value in ranges.items():
                if summa < upper_limit * (currency_value - value):
                    rate = currency_value - value
                    break
        else:
             for upper_limit, value in ranges.items():
                print(upper_limit, value, summa)                
                if summa < upper_limit:
                    rate = currency_value - value
                    break           
    else:
        rate = custom_rate

    return rate, response

async def generate_common_response(summa, rate, payment_type):
    response = f"Стоимость: {format_profit(summa)} {payment_type}\n"
    response += f"Курс обмена: 1 {payment_type} = {format_price(rate)} рупий\n"
    response += f"Получите: {format_profit(summa * rate)} рупий\n\n"
    response += f"🏦 Мы принимаем оплату через {payment_type}\n\n"
    response += f"- - - -\n"
    response += f"🚨 Обратите внимание, что курс обмена может измениться в любое время из-за экономических и политических факторов."
    return response


class PriceFetcher:
    @staticmethod
    async def get_price(symbol, currency, action, provider):
        try:
            return float(format_price(fetch_price(symbol, currency, action, provider)))
        except Exception as e:
            print(f"Error fetching price: {e}")
            return None

class ResponseGenerator:
    @staticmethod
    async def generate_responses(arg, symbol, price, ranges, ranges_colombo, location, location_colombo):
        responses = [
            f"Безубыток {symbol}: {format_price(price)}\n",
            ResponseGenerator.generate_price_response(symbol, ranges.items(), price, location),
            ResponseGenerator.generate_price_response(symbol, ranges_colombo.items(), price, location_colombo),
            "\n"
        ]
        return responses if arg in [symbol.lower(), None] else []
        
    @staticmethod
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




def calculate_new_price(price, percentage):
    return format_price(float(price) * (1 + percentage / 100.0))

def format_info_with_multiplier(new_price, percentage, price, multiplier):
    USDT = multiplier / float(new_price)
    USDT_difference = float(new_price) - float(price)
    profit = format_profit(float(USDT_difference) * float(USDT))
    return (
        f"+{percentage}%: {new_price} \n"
        f"- отдадим: {format_profit(USDT)} USDT \n"
        f"- профит: {profit} LKR\n\n"
    )

def format_info_add_percentage(prefix, price, percentages, multiplier=None):
    info = [f"{prefix}: {price}\n\n"]
    for percentage in percentages:
        new_price = calculate_new_price(price, percentage)
        if multiplier:
            info.append(format_info_with_multiplier(new_price, percentage, price, multiplier))
        else:
            info.append(f"+{percentage}%: {new_price}\n")
    info.append("\n")
    return "".join(info)




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


async def get_user_arguments(context):
    summa = int(context.args[0]) if context.args else None
    try:
        second_arg = context.args[1]
        try:
            custom_rate = float(second_arg)
            location = None
        except ValueError:
            if second_arg.lower() == 'bn':
                location = 'bn'
                custom_rate = None
            else:
                raise ValueError("Неверный второй аргумент. Ожидалось число (курс) или 'bn' (Бентота).")
    except IndexError:
        custom_rate = None
        location = None

    return summa, custom_rate, location

async def get_rates():
    USDT_SELL = float(format_price(fetch_price("USDT", "LKR", "Sell", "BANK")))
    RUB_BUY = format_price(fetch_price("USDT", "RUB", "BUY", "TinkoffNew"))
    RUB_LKR = float(format_price(float(USDT_SELL) / float(RUB_BUY)))

    return RUB_LKR



def format_profit(profit):
    return "{:,.0f}".format(float(profit)).replace(",", " ")    



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











async def generate_response_usdt_lkr(summa, custom_rate, location, USDT_SELL):
    if custom_rate is None:
        ranges = USDT_RANGES_COLOMBO if location == "bn" else USDT_RANGES
        last_value = next(reversed(ranges.values()))
        response = f"Максимальная граница для торговли: {format_price(USDT_SELL - last_value)}\n"  

        for upper_limit, value in ranges.items():
            if summa < upper_limit:
                rate = USDT_SELL - value
                break
    else:
        rate = custom_rate

    response2 = f"Стоимость: {format_price(summa)} USDT\n"
    response2 += f"Курс обмена: 1 USDT = {format_price(rate)} рупий\n"
    response2 += f"Получите: {format_profit(summa * rate)} рупий\n\n"
    response2 += f"🏦 Мы принимаем оплату через TRC-20\n\n"
    response2 += f"- - - -\n"
    response2 += f"🚨 Обратите внимание, что курс обмена может измениться в любое время из-за экономических и политических факторов."
   
    response3 = f"{format_price(summa)} / {format_price(rate)} / {format_profit(summa * rate)}"
    response4 = f"Профит: {format_profit(summa * (USDT_SELL - rate))} рупий"

    return response, response2, response3, response4

async def generate_response_lkr_usdt(summa, custom_rate, location, USDT_SELL):
    if custom_rate is None:
        ranges = USDT_RANGES_COLOMBO if location == "bn" else USDT_RANGES
        last_value = next(reversed(ranges.values()))
        response = f"Максимальная граница для торговли: {format_price(USDT_SELL - last_value)}\n"  

        for upper_limit, value in ranges.items():
            if upper_limit * (USDT_SELL - value) > summa:
                rate = USDT_SELL - value
                break
    else:
        rate = custom_rate

    response2 = f"Стоимость: {format_price(summa / rate)} USDT\n"
    response2 += f"Курс обмена: 1 USDT = {format_price(rate)} рупий\n"
    response2 += f"Получите: {format_profit(summa)} рупий\n\n"
    response2 += f"🏦 Мы принимаем оплату через TRC-20\n\n"
    response2 += f"- - - -\n"
    response2 += f"🚨 Обратите внимание, что курс обмена может измениться в любое время из-за экономических и политических факторов."

    response3 = f"{format_price(summa / rate)} / {format_price(rate)} / {format_profit(summa)}"
    response4 = f"Профит: {format_profit((summa / rate) * (USDT_SELL - rate))} рупий"

    return response, response2, response3, response4



async def get_rub(update, context):
    user = update.effective_user

    arg = await get_arg(context)
    if arg is None:
        await update.message.reply_text("Некорректное значение. Введите число после команды.")
        return

    USDT_SELL = await fetch_and_format_price("USDT", "LKR", "Sell", "BANK")
    RUB_BUY = await fetch_and_format_price("USDT", "RUB", "BUY", "TinkoffNew")
    RUB_LKR = format_price(float(USDT_SELL) / float(RUB_BUY))

    if any(x is None for x in [USDT_SELL, RUB_BUY, RUB_LKR]):
        await update.message.reply_text("Error fetching some prices, please try again later.")
        return

    response = (
        f"Купить USDT/RUB: {RUB_BUY}\n"
        f"Продать USDT/LKR: {USDT_SELL}\n\n"
        f"{format_info('Безубыток RUB', RUB_LKR, [0.40, 0.35, 0.30, 0.25, 0.20, 0.15], arg)}"
    )

    await update.message.reply_text(response)

async def get_usdt(update, context):
    user = update.effective_user

    arg = await get_arg(context)
    if arg is None:
        await update.message.reply_text("Некорректное значение. Введите число после команды.")
        return

    USDT_SELL = await fetch_and_format_price("USDT", "LKR", "Sell", "BANK")
    if USDT_SELL is None:
        await update.message.reply_text("Error fetching prices, please try again later.")
        return

    response = f"{format_info('Безубыток USDT', USDT_SELL, [19, 17, 15, 13, 12.5, 11, 10], arg)}\n"

    await update.message.reply_text(response)

async def get_usdt_percentages(update, context):
    user = update.effective_user

    arg = await get_arg(context)
    if arg is None:
        await update.message.reply_text("Некорректное значение. Введите число после команды.")
        return

    USDT_SELL = await fetch_and_format_price("USDT", "LKR", "Sell", "BANK")
    if USDT_SELL is None:
        await update.message.reply_text("Error fetching prices, please try again later.")
        return

    response = f"{format_info_percentage('Безубыток USDT', USDT_SELL, [3, 2.5, 2, 1.5, 1], arg)}\n\n"

    await update.message.reply_text(response)

async def get_usdt_add_percentages(update, context):
    user = update.effective_user

    arg = await get_arg(context)
    if arg is None:
        await update.message.reply_text("Некорректное значение. Введите число после команды.")
        return

    USDT_SELL = await fetch_and_format_price("USDT", "LKR", "Sell", "BANK")
    if USDT_SELL is None:
        await update.message.reply_text("Error fetching prices, please try again later.")
        return

    response = f"{format_info_add_percentage('Безубыток USDT', USDT_SELL, [1, 1.5, 2, 2.5, 3], arg)}\n"

    await update.message.reply_text(response)

async def print_prices(update, context):
    user = update.effective_user

    arg = context.args[0].lower() if context.args else None

    USDT_SELL = await PriceFetcher.get_price("USDT", "LKR", "Sell", "BANK")
    RUB_LKR = await PriceFetcher.get_price("USDT", "RUB", "BUY", "TinkoffNew")

    if USDT_SELL is None or RUB_LKR is None:
        await update.message.reply_text("Error fetching prices, please try again later.")
        return

    responses = await asyncio.gather(
        ResponseGenerator.generate_responses(arg, 'RUB', USDT_SELL / RUB_LKR, RUB_RANGES, RUB_RANGES_COLOMBO, 'Хиккадува - Матара', 'Коломбо, Бентота'),
        ResponseGenerator.generate_responses(arg, 'USDT', USDT_SELL, USDT_RANGES, USDT_RANGES_COLOMBO, 'Хиккадува - Матара', 'Коломбо, Бентота')
    )

    full_response = "\n".join(sum(responses, []))
    await update.message.reply_text(full_response)

async def get_rub_lkr(update, context):
    response_generator = RubToLkrResponseGenerator()
    processor = ExchangeProcessor(update, context, response_generator, get_rates)
    await processor.process()

async def get_lkr_rub(update, context):
    response_generator = LkrToRubResponseGenerator()
    processor = ExchangeProcessor(update, context, response_generator, get_rates)
    await processor.process()

async def get_usdt_lkr(update, context):
    response_generator = UsdtToLkrResponseGenerator()
    processor = ExchangeProcessor(update, context, response_generator, None)
    await processor.process()

async def get_lkr_usdt(update, context):
    response_generator = LkrToUsdtResponseGenerator()
    processor = ExchangeProcessor(update, context, response_generator, None)
    await processor.process()


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(token).build()

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

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()