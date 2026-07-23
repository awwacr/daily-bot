import os
import time
import requests
import schedule

BOT_TOKEN = "8810079431:AAHe077hsXsje5o4m-adQnvwFnWs4r03hjA"
CHAT_ID = "1406966655"

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
    print("Отправка отчета в Telegram...")
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
        print(f"Ответ Telegram API: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Ошибка отправки: {e}")

if __name__ == "__main__":
    # Сразу отправляем тестовый отчет
    send_daily_report()
    
    # Запускаем планировщик
    schedule.every().day.at("08:30").do(send_daily_report)
    while True:
        schedule.run_pending()
        time.sleep(60)
