# IMS-NoticeBot

An automated system for sending IMS (Information Management System) notices to Whatsapp using Python.

## Description

The IMS Notice Scraper Bot is a powerful and efficient tool designed to automate the process of scraping notices from the IMS (Institute Management System) portal and sending them directly to a specified WhatsApp chat. This bot is ideal for students who want to stay updated with the latest announcements without having to manually check the IMS portal regularly.

## Features

- Scrapes notices from IMS using Playwright.
- Tracks new notices and stores them in MongoDB.
- Sends notifications via WhatsApp and Telegram for logs.

## DISCLAIMER

- USING THIS BOT WITH YOUR PERSONAL NUMBER MAY LEAD TO SUSPENSION. IT IS NOT RECOMMENDED.

## Installation

   - Using python
   ```
   git clone https://github.com/moetooo/IMS-NoticeBot.git 
   cd IMS-NoticeBot 
   pip3 install -r requirements.txt
   playwright install chromium
   playwright install-deps
   python3 main.py
   ```

  - Using Bash script
   ```
   git clone https://github.com/moetooo/IMS-NoticeBot.git 
   cd IMS-NoticeBot 
   chmod +x start.sh
   ./start.sh or bash start.sh
   ```
   
   - Using Docker
   ```
   sudo docker build -t build imsbot
   sudo docker run -p 8010:8010 imsbot
   ```

## Configuration

Create a `.env` file in the root directory of the project and add your configuration variables:

```
DB_URL=<your_mongodb_url>
WHATSAPP_NO=<your_whatsapp_number>
COUNTRY_CODE=<your_country_code>
TOKEN=<your_telegram_bot_token>
CHAT_ID=<your_telegram_chat_id>
GROUP_NAME=<your_group_name>
IS_QR=<whether_qr_code_is_used> False by Default
PORT=<port_number> 8010 by Default
```

## Code Reference
- https://github.com/microsoft/playwright-python/issues/675#issuecomment-841667109
- https://github.com/mridultuteja/BOT-for-Discord-using-python/blob/master/keep_alive.py
- Also used Chatgpt and Claude 
