from threading import Thread
from flask import Flask
from config import PORT
import time

start_time = time.time()
bot = Flask(__name__)

@bot.route('/')
def home():
    end_time = time.time()
    uptime_seconds = end_time - start_time
    uptime_minutes = uptime_seconds / 60
    return f'Bot uptime: {uptime_minutes:.2f} minutes'

def run():
    bot.run(host='0.0.0.0', port=PORT)

def keep_alive():  
    t = Thread(target=run)
    t.start()



