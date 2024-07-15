# IMS-NoticeBot

An automated system for sending IMS (Information Management System) notices using Python and Playwright.

## Description

This project automates the process of retrieving notices from an IMS and sending them through a messaging platform (likely WhatsApp, based on previous context). It utilizes web scraping techniques to gather information and automates the sending process.


## Features

- Scrapes notices from IMS using Playwright.
- Tracks new notices and stores them in MongoDB.
- Sends notifications via WhatsApp and Telegram for logs.

## DISCLAIMER
- Using this bot with your personal account may lead to suspension. It is not recommended.

## Installation

### Locally
   ```
   git clone https://github.com/moetooo/IMS-NoticeBot.git 
   cd IMS-NoticeBot 
   pip3 install -r requirements.txt
   playwright install chromium
   playwright install-deps
   python3 main.py or chmod +x start.sh && ./start.sh
   ```

### Using Docker
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
## Screenshots

![LOG Screenshot]()

## Code Reference
- https://github.com/microsoft/playwright-python/issues/675
- https://www.way2automation.com/download-a-file-using-playwright-python/
- https://github.com/mridultuteja/BOT-for-Discord-using-python/blob/master/keep_alive.py
- Also used Chatgpt and Claude 