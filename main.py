from playwright.async_api import  async_playwright, Page
from web import keep_alive
from database import get_notices
from scrap import run_scraper
from config import * 
import asyncio
import logging
import aiohttp
import asyncio
import qrcode
import os
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s : %(message)s',  
                    datefmt='[%Y-%m-%d | %H:%M:%S]')

#=======VARS==========#
country_code = COUNTRY_CODE
chat_names = [CHAT_NAME_1, CHAT_NAME_2, CHAT_NAME_3]
phone_no = WHATSAPP_NO
log_chat_id = LOG_CHAT_ID
token = TOKEN
is_qr = IS_QR
#=====================#

#========XPATHS========#
down_context_button = DOWN_CONTEXT_BTN
file_input_path = FILE_UPLOAD
attach_button = ATTACH_BTN
search_box_path = SEARCH_BOX
caption_path = CAPTION_AREA
send_button = SEND_BTN
reply_button = REPLY_BTN
#====================#

#========FILTERS=========#
excluded_text = ['MTech', 'BBA', 'MBA', 'M.Tech', 'B.Arch', 'BARCH', 'M TECH', 'West', 'East', 'M.Sc', 'Ph. D.', 'Ph.D', 'NCC']
included_text = ['BTECH', 'B.Tech', 'B Tech', 'B TECH']
#========================#
            
async def send_telegram_message(text: str) -> None:
    formatted_text = f"`{text}`"
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={log_chat_id}&text={formatted_text}&parse_mode=MarkdownV2"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                logging.error(f"Failed to send message. Status code: {response.status}")

#=========FILTER-TEXT===========#              
async def filter_text(title: str) -> bool:
    match_found = False
    for ex_text in excluded_text:
        if ex_text.lower() in title.lower():
            match_found = True
            break
        
    for inc_text in included_text:
        if inc_text.lower() in title.lower():
            match_found = False
            break
    return match_found  

#===============GET-LOGIN-CODEL================#
async def fetch_login_code(login_page: Page, retry_count: int = 3) -> str:
    for count in range(retry_count):
        logging.info(f'Attempt {count + 1}/{retry_count}: Search for code')
        await send_telegram_message(f'Attempt {count + 1}/{retry_count}: Search for code')
        
        code_element = await login_page.query_selector('div[aria-details="link-device-phone-number-code-screen-instructions"]')
        
        if code_element:
            logging.info('Code element found')
            await send_telegram_message('Code element found')
            
            data_link_code = await code_element.get_attribute('data-link-code')
            if data_link_code:
                login_code = data_link_code.replace(",", " ")
                return login_code
        
        if count < retry_count - 1:
            logging.info('Code not found. Waiting before next attempt...')
            await send_telegram_message('Code not found. Waiting before next attempt...')
            await asyncio.sleep(10)
    
    logging.warning('Failed to find login code after all attempts')
    return None

#==============GET-QR=============#
async def get_qr(login_page: Page) -> None:
    qr_element = await login_page.wait_for_selector("div[data-ref]", timeout=60000)

    value = await qr_element.get_attribute("data-ref")
    dir_path = os.path.join(os.getcwd(),"server" ,"static")
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    
    qr_image_path = os.path.join(dir_path, "qr.png")
    qrcode.make(value).save(qr_image_path)
    
    logging.info("login using QR. Session will expire in 60 seconds!")    
    await asyncio.sleep(60)
    logging.info("Session expired!")
    os.remove(qr_image_path)

#==============LOGIN-FUNCTION=============#
async def login(login_page: Page, url: str) -> Page:   
    try:
        logging.info(f'GET {url}')
        await send_telegram_message(f'GET {url}')
        await login_page.goto(url, wait_until="load", timeout=120000)
        
        await asyncio.sleep(60)
        
        search_box = login_page.locator(search_box_path)
        if await search_box.count() > 0:
            return login_page
    
        if is_qr:
            await get_qr(login_page)

        else:
            logging.info('Logging in using phone number')
            await send_telegram_message('Logging in using phone number')
            
            await login_page.wait_for_selector('xpath=//span[@role="button" and text()="Link with phone number"]', state='visible', timeout=60000)
            await login_page.locator('xpath=//span[@role="button" and text()="Link with phone number"]').click()

            await asyncio.sleep(10)
            
            await login_page.locator('xpath=//*[@id="app"]/div/div[2]/div[3]/div[1]/div/div[3]/div[1]/div[1]/button/div/div/div').click()
            await login_page.locator('xpath=//*[@id="wa-popovers-bucket"]/div/div[2]/div/div[1]/div/div[2]/div[1]/p').click()
            await login_page.keyboard.type(country_code)
            
            logging.info('Country code entered')
            await asyncio.sleep(5)
            
            await login_page.locator('xpath=//*[@id="wa-popovers-bucket"]/div/div[2]/div/div[2]/div/div/div/div/div/div/button/div/div/div[2]/div/div/div').click()                    
            await login_page.locator('xpath=//*[@id="app"]/div/div[2]/div[3]/div[1]/div/div[3]/div[1]/div[2]/div/div').click()
            await login_page.keyboard.type(phone_no)
            
            await asyncio.sleep(5)
            
            await login_page.locator('xpath=//*[@id="app"]/div/div[2]/div[3]/div[1]/div/div[3]/div[2]/button/div/div').click()
            
            logging.info('Phone no entered')            
            await asyncio.sleep(10)

            login_code = await fetch_login_code(login_page)
            await asyncio.sleep(5)
            
            if login_code:
                await send_telegram_message(login_code)
                logging.info(f"Login code: {login_code}")
        
        await login_page.wait_for_selector(search_box_path)
        
        return login_page
    except Exception as error:
        logging.error(f'{login.__name__}: {str(error)}')
        
#=================MESSAGE-FUNCTION=================#        
async def open_chat(chat_page: Page, chat_name: str) -> None:
    await asyncio.sleep(5)
    await chat_page.locator(f'xpath={search_box_path}').click()
    await chat_page.keyboard.press('Control+a')
    await chat_page.keyboard.press('Backspace')
    await chat_page.keyboard.type(chat_name)
    await chat_page.get_by_title(chat_name, exact=True).click()
    # await asyncio.sleep(5)
    
#===================SEND-TEXT====================#
async def send_text(chat_page: Page, message: str) -> None:
    await chat_page.locator('xpath=//div[@aria-placeholder="Type a message"]').click()
    await chat_page.keyboard.insert_text(message)
    await chat_page.locator(f'xpath={send_button}').click()
    
#===================SEND-FILE======================#
async def send_file(chat_page: Page, file_path: str)-> None:
    await chat_page.locator(f'xpath={attach_button}').click()
    await asyncio.sleep(5)
    await chat_page.set_input_files(f'xpath={file_input_path}', file_path)
    await asyncio.sleep(5)
    
    caption_input = chat_page.locator(f'xpath=//div[@aria-placeholder="Add a caption"]')        
    if await caption_input.is_visible():
        blank_txt = 'ㅤ' #Invisible Char
        await caption_input.click()
        await asyncio.sleep(1)
        await caption_input.fill(blank_txt, force=True)
        
    await asyncio.sleep(5)
    await chat_page.locator(f'xpath={send_button}').click()
    await asyncio.sleep(30)

#===============REPLY-TO-LAST-MESSAGE================#
async def reply_to_last_message(chat_page: Page, last_message_id: str, file_path: str | None) -> bool:
    if not file_path:
        return False
    
    try:
        await asyncio.sleep(5)
        await chat_page.locator(f'div[data-id="{last_message_id}"]').hover()
        drop_button = await chat_page.locator(down_context_button).is_visible(timeout=5000)
        if drop_button:
            await chat_page.locator(down_context_button).click()
            await asyncio.sleep(5)
            await chat_page.locator(reply_button).click()
            await asyncio.sleep(5)
            await send_file(chat_page, file_path)
                
    except Exception as error:
        logging.warning(f"Hover and context menu actions failed: {str(error)}.")
        await send_file(chat_page, file_path)
            
    return True

#===============GET-LAST-MESSAGE================#
async def get_last_message(chat_page: Page) -> int:
    await chat_page.wait_for_selector('div[data-id]')
    element_data_id = await chat_page.query_selector_all('div[data-id]')
    last_message_id = 0
    if element_data_id:
        last_message_id = await element_data_id[-1].get_attribute('data-id')
    return last_message_id

#===============MESSAGE-DELIVERED================#
async def is_message_delivered(chat_page: Page, last_message_id: str) -> bool:
    max_delivery_wait = 400  
    delivery_check_interval = 5
    is_delivered = False  
    for _ in range(0, max_delivery_wait, delivery_check_interval):
        dbl_check_icon = chat_page.locator(f'div[data-id="{last_message_id}"] span[data-icon="msg-dblcheck"]')
        msg_check_icon = chat_page.locator(f'div[data-id="{last_message_id}"] span[data-icon="msg-check"]')
        
        if await dbl_check_icon.count() > 0 or await msg_check_icon.count() > 0:
            is_delivered = True
            break
        await asyncio.sleep(delivery_check_interval)
    return is_delivered

#===============MESSAGE-WITH-URL================#
async def send_message_with_url(chat_page: Page, chat_name: str, message_content: str, message_count: int) -> None:
    await send_text(chat_page, message_content)
    logging.info(f'MessageNo.{message_count} sent in chat {chat_name}')
    await send_telegram_message(f'MessageNo.{message_count} sent in chat {chat_name}')

#===============MESSAGE-WITH-FILE================#
async def send_message_with_file(chat_page: Page, chat_name: str, message_content: str, file_path: str, message_count) -> None:
    await send_text(chat_page, message_content)
    
    last_message_id = await get_last_message(chat_page)
        
    if await is_message_delivered(chat_page, last_message_id):
        if await reply_to_last_message(chat_page, last_message_id, file_path):
            lastUploadMessageId = await get_last_message(chat_page)
            
            if await is_message_delivered(chat_page, lastUploadMessageId):
                logging.info(f'MessageNo.{message_count} sent in chat {chat_name}')
                await send_telegram_message(f'MessageNo.{message_count} sent in chat {chat_name}')
                
    if chat_name == chat_names[-1] and os.path.exists(file_path):
        os.remove(file_path)

async def send_to_whatsapp(chat_page: Page, saved_pdf_documents: dict) -> None:
    try:
        
        message_count = len(saved_pdf_documents)
        for message_no in sorted(saved_pdf_documents.keys(), reverse=True):
            notice_content = await get_notices(message_no)
            notice_title = notice_content['Title']
            notice_date = notice_content['Date']
            notice_published_by = notice_content['Published_By']
            file_content = saved_pdf_documents[message_no]
            
            
            message_content = f'''
            🔔NOTICE: *{notice_title}*\n\n🗓️ Date: {notice_date}\n\n✍️ Published by: {notice_published_by}
            '''
            
            if await filter_text(notice_title):
                logging.info(f'Skipping MessageNo.{message_count}')
                await send_telegram_message(f'Skipping MessageNo.{message_count}')
                message_count -= 1
                continue
                        
            for chat_name in chat_names:
                if chat_name is None:
                    continue
                
                await open_chat(chat_page, chat_name)
                
                if not file_content.endswith('.pdf'):
                    attached_url_content = f'\n{file_content}'
                    await send_message_with_url(chat_page, chat_name, message_content + attached_url_content, message_count)
                else:
                    file_path = os.path.join(os.getcwd(), 'downloads', file_content)
                    await send_message_with_file(chat_page, chat_name, message_content, file_path, message_count)                 
                
            message_count -= 1

    except Exception as error:
        logging.error(f'{send_to_whatsapp.__name__}: {str(error)}')

#===============SCRAP-TASK================#
async def scraper_task(notice_page: Page, whatsapp_page: Page, url: str) -> None:    
    try:
        logging.info('Checking for New Notices')
        await send_telegram_message('Checking for New Notices')
        
        scrap_result = await run_scraper(notice_page, url)
        if isinstance(scrap_result, dict):
            logging.info(f'{len(scrap_result)} New Notices Found!')        
            await send_telegram_message(f'{len(scrap_result)} New Notices Found!')
            await send_to_whatsapp(whatsapp_page, scrap_result)
            
        elif isinstance(scrap_result, int):
            logging.info('Notices are up to date')
            await send_telegram_message('Notices are up to date')
        else:
            logging.warning(f'Unexpected scraping result type: {type(scrap_result)}')
    
    except Exception as error:
        logging.error(f'{scraper_task.__name__}: {str(error)}')
    
    finally:
        await notice_page.close()
    logging.info('Sleeping for 900 seconds')
    await send_telegram_message('Sleeping for 900 seconds')
    await asyncio.sleep(900)
    
async def keep_session_alive(page: Page) -> bool:
    try:
        search_box = page.locator(search_box_path)
        if await search_box.is_visible(timeout=5000):
            await search_box.click()
            await asyncio.sleep(10)
            logging.info("WhatsApp session is active")
            await send_telegram_message("WhatsApp session is active")
        return False
            
    except Exception as e:
        logging.error(f'{keep_session_alive.__name__}: {str(e)}')
        return True  

async def main():
    while True:
        try:
            logging.info('Bot Started')
            userDir = os.path.join(os.getcwd(), 'user_data')
            if not os.path.exists(userDir):
                os.makedirs(userDir)
            
            async with async_playwright() as playwright:       
                browser = await playwright.chromium.launch_persistent_context(
                    user_data_dir=userDir,
                    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    headless=False,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--no-first-run',
                        '--no-zygote',
                        '--single-process',
                        '--disable-gpu'
                    ]
                )
                try:
                    browser.set_default_navigation_timeout(300_000)  # 5 minutes
                    browser.set_default_timeout(300_000)  # 5 minutes
            
                    whatsapp_page = await browser.new_page()
                    if len(browser.pages) > 0:
                        await browser.pages[0].close()
        
                    chat_page = await login(whatsapp_page, url='https://web.whatsapp.com/')
                    if chat_page is not None:
                        while True:
                            is_session_closed = await keep_session_alive(chat_page)
                            if not is_session_closed:
                                for _ in range(3):
                                    notice_page = await browser.new_page()
                                    await scraper_task(notice_page, whatsapp_page, url='https://www.imsnsit.org/imsnsit/notifications.php')
                    
                            await asyncio.sleep(30)
                except Exception as error:
                    logging.error(f'{main.__name__}: {str(error)}')
                finally:
                    await browser.close()
                    logging.info("Browser context closed. Attempting to restart.")
                    
        except Exception as outer_error:
            logging.error(f'Outer exception in {main.__name__}: {str(outer_error)}')
            logging.info("Restarting main function in 60 seconds...")
            await asyncio.sleep(60)

if __name__ == '__main__':
    keep_alive()
    asyncio.run(main())
    
