from threading import Thread
from flask import Flask, render_template, send_from_directory
from config import PORT
import time
import os


start_time = time.time()
bot = Flask(__name__,
            static_folder="server/static",
            template_folder="server/templates")

@bot.route('/')
def home():
    end_time = time.time()
    uptime_seconds = end_time - start_time
    uptime_minutes = uptime_seconds / 60
    return f'Bot uptime: {uptime_minutes:.2f} minutes'

@bot.route(f"/login")
def login():
    qr_image_path = os.path.join(os.getcwd(), "server", "static", "qr.png")
    if not os.path.exists(qr_image_path):
        return "QR code not available!"
    
    return render_template("login.html")
    

def run():
    bot.run(host='0.0.0.0', port=PORT)

def keep_alive():  
    t = Thread(target=run)
    t.start()

