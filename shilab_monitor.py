import requests
from bs4 import BeautifulSoup
import time

# --- הגדרות ---
# שים לב: החלף את הקישור הזה בקישור המדויק של עמוד ערכת הלידה באתר של שילב!
URL = "https://lp.vp4.me/jzze" 

# הנתונים הרשמיים של הבוט והחשבון שלך
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_TOKEN = BOT_TOKEN
TELEGRAM_CHAT_ID = "5721684998"

def send_telegram_message(text):
    """פונקציה השולחת הודעה ישירות לטלגרם שלך"""
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(telegram_url, json=payload, timeout=10)
        print("Telegram alert sent successfully!")
    except Exception as e:
        print(f"Error sending telegram message: {e}")

def check_shilab_stock():
    # הגדרת User-Agent כדי שהאתר לא יחסום אותנו
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"[{time.strftime('%H:%M:%S')}] שגיאה בגישה לאתר. סטטוס קוד: {response.status_code}")
            return False
            
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text()
        
        # הלוגיקה שמחפשת את טקסט "אזל המלאי"
        if "המלאי אזל" not in page_text:
            print("🚨 המלאי חזר או שהדף השתנה! שולח התראה מיידית בטלגרם... 🚨")
            message_text = (
                f"🚨 *ההרשמה לערכת הלידה של שילב נפתחה!* 🚨\n\n"
                f"נראה שהטקסט 'המלאי אזל' הוסר מהעמוד.\n"
                f"לחץ כאן כדי להיכנס מהר ולממש:\n{URL}"
            )
            send_telegram_message(message_text)
            return True # מחזיר True כדי לעצור את הלולאה שלא יציף אותך
        else:
            print(f"[{time.strftime('%H:%M:%S')}] עדיין אזל המלאי... בודק שוב בקרוב.")
            return False
            
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] שגיאה במהלך הבדיקה: {e}")
        return False

if __name__ == "__main__":
    print("🚀 סקריפט הניטור של שילב התחיל לרוץ...")
    print(f"הבוט ישלח התראות לחשבון טלגרם ID: {TELEGRAM_CHAT_ID}")
    
    # תדירות הבדיקה: כל 5 דקות (300 שניות)
    # אם אתה רוצה להיות אגרסיבי יותר, שנה ל-60 (כל דקה)
    INTERVAL = 300 
    
    while True:
        stock_found = check_shilab_stock()
        if stock_found:
            break
        time.sleep(INTERVAL)