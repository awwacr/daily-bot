import os
import time
import threading
import requests
import schedule
from http.server import HTTPServer, BaseHTTPRequestHandler

BOT_TOKEN = "8810079431:AAHe077hsXsje5o4m-adQnvwFnWs4r03hjA"
CHAT_ID = "1406966655"

# Простой HTTP-сервер для проходимости Health Check на Render
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is live!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

def get_cbu_rates():
    url = "https://cbu.uz/ru/arkhiv-kursov-valyut/json/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        rates = {}
        for item in data:
            code = item.get("Ccy")
            if code in ["USD", "KRW", "RUB"]:
                rates[code] = {
                    "rate": item.get("Rate"),
                    "diff": item.get("Diff")
                }
        return rates
    except Exception as e:
        print(f"Ошибка ЦБ: {e}")
        return None

def get_tashkent_weather():
    url = "https://api.open-meteo.com/v1/forecast?latitude=41.2995&longitude=69.2401&current_weather=true&daily=temperature_2m_max,temperature_2m_min&timezone=Asia/Tashkent"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        return {
            "current": round(data["current_weather"]["temperature"]),
            "max": round(data["daily"]["temperature_2m_max"][0]),
            "min": round(data["daily"]["temperature_2m_min"][0])
        }
    except Exception as e:
        print(f"Ошибка погоды: {e}")
        return None

def send_daily_report():
    rates = get_cbu_rates()
    weather = get_tashkent_weather()
    
    if weather:
        weather_text = (
            f"☀️ <b>Погода в Ташкенте:</b>\n"
            f"• Сейчас: <b>{weather['current']}°C</b>\n"
            f"• Сегодня: от <b>{weather['min']}°C</b> до <b>{weather['max']}°C</b>\n"
        )
    else:
        weather_text = "☀️ <b>Погода:</b> Ошибка получения данных\n"

    if rates:
        def format_diff(diff):
            if not diff or diff == "0":
                return ""
            return f" ({'+' if not str(diff).startswith('-') else ''}{diff})"

        usd_rate = rates.get("USD", {}).get("rate", "N/A")
        usd_diff = rates.get("USD", {}).get("diff", "0")
        krw_rate = rates.get("KRW", {}).get("rate", "N/A")
        krw_diff = rates.get("KRW", {}).get("diff", "0")
        rub_rate = rates.get("RUB", {}).get("rate", "N/A")
        rub_diff = rates.get("RUB", {}).get("diff", "0")

        rates_text = (
            f"🏦 <b>Курсы валют ЦБ РУз:</b>\n"
            f"🇺🇸 1 USD = <b>{usd_rate}</b> сум{format_diff(usd_diff)}\n"
            f"🇰🇷 1 KRW = <b>{krw_rate}</b> сум{format_diff(krw_diff)}\n"
            f"🇷🇺 1 RUB = <b>{rub_rate}</b> сум{format_diff(rub_diff)}\n"
        )
    else:
        rates_text = "🏦 <b>Курсы валют:</b> Ошибка получения данных\n"

    full_message = f"📊 <b>Ежедневный отчет</b>\n\n{weather_text}\n{rates_text}"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": full_message, "parse_mode": "HTML"}
    
    try:
        res = requests.post(url, data=payload)
        print(f"Ответ Telegram: {res.status_code}")
    except Exception as e:
        print(f"Ошибка запроса: {e}")

def bot_loop():
    # Отправляем один тестовый отчет сразу при старте
    send_daily_report()
    
    # Ставим расписание каждый день на 08:30 по Ташкенту
    schedule.every().day.at("08:30").do(send_daily_report)
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    # 1. Запускаем бота и расписание в ФОНОВОМ ПОТОКЕ (не мешает серверу)
    threading.Thread(target=bot_loop, daemon=True).start()
    
    # 2. Запускаем веб-сервер в ГЛАВНОМ ПОТОКЕ (для Render Web Service)
    run_web_server()
