import telebot
import requests
from bs4 import BeautifulSoup
import time
import threading
import os

# --- הגדרות מערכת ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TOKEN = BOT_TOKEN
URL = "https://lp.vp4.me/jzze" 
USERS_FILE = "users.txt"
ADMIN_ID = 5721684998  

bot = telebot.TeleBot(TOKEN)

# משתנה גלובלי למעקב אחרי מצב החסימה (כדי לא להציף בהתראות שגיאה)
is_currently_blocked = False

# יצירת קובץ המשתמשים במידה ולא קיים
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        pass

def get_users_dict():
    """קריאת המשתמשים והשמות שלהם לתוך דיקשנרי {chat_id: name}"""
    users = {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        for line in f.readlines():
            line = line.strip()
            if not line:
                continue
            if "," in line:
                u_id, u_name = line.split(",", 1)
                users[u_id.strip()] = u_name.strip()
            else:
                users[line.strip()] = "משתמש ותיק (לא ידוע)"
    return users

def add_user(chat_id, first_name):
    """הוספת משתמש חדש יחד עם השם שלו לקובץ"""
    users = get_users_dict()
    chat_id_str = str(chat_id)
    
    if chat_id_str not in users or users[chat_id_str] == "משתמש ותיק (לא ידוע)":
        lines = []
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
        
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            for line in lines:
                if not line.startswith(chat_id_str + ",") and line.strip() != chat_id_str:
                    f.write(line)
            f.write(f"{chat_id_str},{first_name}\n")
        return True
    return False

# --- פקודות והאזנה לטלגרם ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    first_name = message.from_user.first_name if message.from_user.first_name else "חבר"
    
    is_new = add_user(chat_id, first_name)
    
    if is_new:
        bot.reply_to(
            message, 
            f"אהלן {first_name}! 👋\n"
            f"נרשמת בהצלחה למערכת הניטור של ערכת הלידה.\n"
            f"ברגע שהמלאי יתחדש וההרשמה תיפתח, תקבל כאן הודעה מיידית! 🚀"
        )
        print(f"[New User] {first_name} ({chat_id}) registered successfully.")
    else:
        bot.reply_to(message, f"אהלן {first_name}, אתה כבר רשום במערכת! נעדכן אותך ברגע שהמלאי יחזור. 🎯")

# 👑 פקודת מנהל בלעדית עבור אלעזר 👑
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id == ADMIN_ID:
        users = get_users_dict()
        total_users = len(users)
        
        status_msg = "🟢 תקין (סורק בכל דקה)" if not is_currently_blocked else "🔴 חסום / שגיאת תקשורת"
        
        report = f"📊 *דוח ניהול בוט שילב:*\n\n"
        report += f"🖥️ *סטטוס ניטור האתר:* {status_msg}\n"
        report += f"👥 *סה\"כ נרשמו:* {total_users} משתמשים.\n\n"
        report += f"👤 *רשימת הרשומים:*\n"
        
        for u_id, u_name in users.items():
            report += f"• *{u_name}* (ID: `{u_id}`)\n"
            
        bot.send_message(ADMIN_ID, report, parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ פקודה זו זמינה למנהל המערכת בלבד.")

# --- מנגנון הניטור הראשי ברקע ---
def monitor_loop():
    global is_currently_blocked
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    INTERVAL = 60 # בדיקה בכל דקה
    
    print("🕵️ מנגנון הניטור של הדף הופעל ברקע (בדיקה כל דקה)...")
    
    while True:
        try:
            response = requests.get(URL, headers=headers, timeout=10)
            
            # בדיקה אם האתר מחזיר קוד שגוי (חסימה, קריסה וכדומה)
            if response.status_code != 200:
                print(f"[{time.strftime('%H:%M:%S')}] שגיאה בגישה לאתר. סטטוס: {response.status_code}")
                
                # אם זו הפעם הראשונה שאנחנו מגלים את החסימה - נתריע לאלזר
                if not is_currently_blocked:
                    is_currently_blocked = True
                    error_text = f"⚠️ *אלעזר שים לב!* הבוט קיבל קוד שגיאה מהאתר: `{response.status_code}`.\nייתכן שה-IP נחסם או שיש תקלה זמנית באתר שילב. כדאי לבדוק."
                    bot.send_message(ADMIN_ID, error_text, parse_mode="Markdown")
                
                time.sleep(INTERVAL)
                continue

            # אם הגענו לכאן, הסטטוס הוא 200 (תקין)
            # אם היינו חסומים קודם והמצב הסתדר - נעדכן את אלעזר שהכל חזר לעבוד
            if is_currently_blocked:
                is_currently_blocked = False
                bot.send_message(ADMIN_ID, "✅ *החסימה שוחררה!* הבוט חזר לתקשר עם האתר כרגיל בהצלחה.")

            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text()
            
            if "המלאי אזל" not in page_text:
                print("🚨 המלאי חזר! שולח הודעות לכל רשימת התפוצה...")
                users = get_users_dict()
                
                message_text = (
                    f"🚨 *ההרשמה לערכת הלידה נפתחה מחדש!* 🚨\n\n"
                    f"נראה שהטקסט 'המלאי אזל' הוסר מהעמוד.\n"
                    f"כנסו מהר להירשם לפני שייגמר:\n{URL}"
                )
                
                for user_id in users.keys():
                    try:
                        bot.send_message(user_id, message_text, parse_mode="Markdown")
                        print(f"[Sent] Message delivered to {user_id}")
                    except Exception as e:
                        print(f"[Error] Could not send message to {user_id}: {e}")
                        
                break # עוצר את הלולאה לאחר שהמלאי נמצא וההתראות נשלחו
            else:
                print(f"[{time.strftime('%H:%M:%S')}] עדיין אזל המלאי...")
                
        except Exception as e:
            # תפיסת שגיאות רשת קשות (כמו למשל כשהאינטרנט מתנתק או השרת נופל)
            print(f"[{time.strftime('%H:%M:%S')}] שגיאת רשת/חיבור חמורה: {e}")
            if not is_currently_blocked:
                is_currently_blocked = True
                bot.send_message(ADMIN_ID, f"⚠️ *אלעזר, שגיאת רשת חמורה בבוט!*\nהסקריפט לא מצליח לגשת לשרת של האתר כלל.\nפירוט השגיאה: `{str(e)[:100]}...`", parse_mode="Markdown")
            
        time.sleep(INTERVAL)

if __name__ == "__main__":
    monitor_thread = threading.Thread(target=monitor_loop)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    print("🚀 הבוט באוויר ומאזין להודעות חדשות בטלגרם...")
    bot.infinity_polling()