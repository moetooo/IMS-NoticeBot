from playwright.async_api import  async_playwright, Page, BrowserContext
from keep_alive import keep_alive
from database import get_notices
from scrap import run_scraper
from config import *
import asyncio
import logging
import aiohttp
import asyncio
import os

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s : %(message)s',  
                    datefmt='[%Y-%m-%d | %H:%M:%S]')


#=======VARS==========#
country_code = COUNTRY_CODE
group_name = GROUP_NAME
phone_no = WHATSAPP_NO
chat_id = CHAT_ID
token = TOKEN
is_qr = IS_QR
delay = 10
#=====================#

#========XPATHS========#
down_context_path = DOWN_CONTEXT_BTN
file_input_xpath = FILE_UPLOAD
attach_btn_xpath = ATTACH_BTN
search_box_path = SEARCH_BOX
caption_path = CAPTION_AREA
send_btn_xpath = SEND_BTN
reply_path = REPLY_BTN
#====================#

async def send_telegram_message(text):
    monospaced_message = f"`{text}`"
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={monospaced_message}&parse_mode=MarkdownV2"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                logging.error(f"Failed to send message. Status code: {response.status}")

async def scrape_login_code(login_page: Page, max_attempts=3):
    for attempt in range(max_attempts):
        logging.info(f'Attempt {attempt + 1} to search for code')
        await send_telegram_message(f'Attempt {attempt + 1} to search for code')
        
        code_element = await login_page.query_selector('div[aria-details="link-device-phone-number-code-screen-instructions"]')
        
        if code_element:
            logging.info('Code element found')
            await send_telegram_message('Code element found')
            
            data_link_code = await code_element.get_attribute('data-link-code')
            if data_link_code:
                login_code = data_link_code.replace(",", " ")
                return login_code
        
        if attempt < max_attempts - 1:
            logging.info('Code not found. Waiting before next attempt...')
            await send_telegram_message('Code not found. Waiting before next attempt...')
            await asyncio.sleep(delay)
    
    logging.warning('Failed to find login code after all attempts')
    return None

async def login(context: BrowserContext, url: str) -> Page:
    try:
        login_page = await context.new_page()
        logging.info(f'GET {url}')
        await send_telegram_message(f'GET {url}')
        await login_page.goto(url, wait_until="networkidle", timeout=120000)
        
        if is_qr:
            logging.info('SCAN QR code')
        else:
            logging.info('Logging in using phone number')
            await send_telegram_message('Logging in using phone number')
            
            await asyncio.sleep(60)
                        
            await login_page.wait_for_selector('xpath=//span[@role="button" and text()="Link with phone number"]', state='visible', timeout=60000)
            await login_page.locator('xpath=//span[@role="button" and text()="Link with phone number"]').dblclick()

            await asyncio.sleep(delay)
            
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
            await asyncio.sleep(delay)

            login_code = await scrape_login_code(login_page)
            await asyncio.sleep(5)
            
            if login_code:
                await send_telegram_message(login_code)
                logging.info(f"Login code: {login_code}")
            else:
                logging.info("Failed to scrape login code")
        
        await login_page.wait_for_selector(search_box_path)
        
        return login_page
    except Exception as error:
        logging.error(f'{login.__name__}: {error}')

async def send_message(webpage: Page, total_messages: dict):
    try:
        await asyncio.sleep(delay)
                
        await webpage.locator(f'xpath={search_box_path}').click()
        await webpage.keyboard.type(group_name)
        await webpage.get_by_title(group_name, exact=True).click()
        
        await asyncio.sleep(delay)
        message_no = len(total_messages)
        while message_no >= 1:
            notice_data = await get_notices(message_no)
            title, publish_by, date  = notice_data['Title'], notice_data['Publish_by'], notice_data['Date']
            
            message_txt = f'''
            🔔NOTICE: *{title}*\n\n🗓️ Date: {date}\n\n✍️ Published by: {publish_by}
            '''
            await webpage.locator('xpath=//div[@contenteditable="true" and @data-lexical-editor="true" and @aria-label="Type a message"]').click()
            await webpage.keyboard.insert_text(message_txt)
            await webpage.locator(f'xpath={send_btn_xpath}').click()
            
            await asyncio.sleep(15)
            
            await webpage.wait_for_selector('div[data-id]')
            elements_with_data_id = await webpage.query_selector_all('div[data-id]')
            last_message_id = 0
            if elements_with_data_id:
                last_message_id = await elements_with_data_id[-1].get_attribute('data-id')
                        
            await webpage.locator(f'div[data-id="{last_message_id}"]').hover()
            down_context_btn = await webpage.locator(down_context_path).is_visible()
            if down_context_btn:
                await webpage.locator(down_context_path).click()
                await asyncio.sleep(5)
                await webpage.locator(reply_path).click()
            
            await asyncio.sleep(5)    
            
            await webpage.locator(f'xpath={attach_btn_xpath}').click()

            await asyncio.sleep(15)
                        
            filename = total_messages[message_no]
            current_dir = os.getcwd()
            file_path = os.path.join(current_dir, 'downloads', filename)

            await webpage.set_input_files(f'xpath={file_input_xpath}', file_path)
            
            await asyncio.sleep(delay)
            
            caption_input = webpage.locator(caption_path)        
            if await caption_input.is_visible():
                caption_txt = '⠀' #BLANK TXT
                await caption_input.click()
                await caption_input.fill(caption_txt, force=True)
                
            await asyncio.sleep(5)
            
            await webpage.locator(f'xpath={send_btn_xpath}').click()
            
            await asyncio.sleep(30)
            
            os.remove(file_path)
                    
            logging.info(f'{message_no} Message sent. Remaining {message_no - 1} more!')
            await send_telegram_message(f'{message_no} Message sent. Remaining {message_no - 1} more!')
                
            message_no -= 1
    except Exception as error:
        logging.error(f'{send_message.__name__}: {str(error)}')

async def temp_task(context: BrowserContext, whatsapp_page: Page, url: str) -> None:
    while True:
        try:
            notice_page = await context.new_page()
            await send_telegram_message('Checking for New Notices')
            scrap_result = await run_scraper(notice_page, url)
            
            if isinstance(scrap_result, dict):
                logging.info(f'{len(scrap_result)} New Notices Found!')
                await send_telegram_message(f'{len(scrap_result)} new Notices Found!')
                await send_message(whatsapp_page, scrap_result)
                
            elif isinstance(scrap_result, int):
                logging.info('Notices are up to date')
                await send_telegram_message(f'Notices are up to date')
            else:
                logging.warning(f'Unexpected scraping result type: {type(scrap_result)}')
            
        except Exception as error:
            logging.error(f'{temp_task.__name__}: {str(error)}')
        await notice_page.close()
        logging.info('Sleeping for 600 secs')
        await send_telegram_message('Sleeping for 600 secs')
        await asyncio.sleep(600)#10 mins
        
async def keep_whatsapp_active(page: Page):
    while True:
        try:
            if page.is_closed():
                logging.error("WhatsApp page is closed. Exiting keep-alive function.")
                break

            search_box = page.locator(search_box_path)
            if await search_box.count() > 0:
                await search_box.focus()
                logging.info("Kept WhatsApp session active")
                await send_telegram_message("Kept WhatsApp session active")
            else:
                logging.warning("Could not find WhatsApp search box. Session might be logged out.")
    
        except Exception as e:
            logging.error(f'{keep_whatsapp_active.__name__}: {str(e)}')

        await asyncio.sleep(1800)#30 mins
        
async def main():
    logging.info('Bot Started')
    await asyncio.sleep(20)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        try:            
            download_path = os.path.join(os.getcwd(), "downloads")
            if not os.path.exists(download_path):
                os.makedirs(download_path)
                logging.info('Download directory created successfully')
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            context.set_default_navigation_timeout(900_000)  # 15 mins
            context.set_default_timeout(900_000)  # 15 mins
            whatsapp_page = await login(context, url='https://web.whatsapp.com/')
            
            if whatsapp_page is not None:
                keep_active_task = asyncio.create_task(keep_whatsapp_active(whatsapp_page))
                scraper_task = asyncio.create_task(temp_task(context, whatsapp_page, url='https://www.imsnsit.org/imsnsit/notifications.php'))
                
                await asyncio.gather(keep_active_task, scraper_task)

        except Exception as error:
            logging.error(f'{main.__name__}: {str(error)}')
        finally:
            await browser.close()
            logging.info("Browser closed. Script finished.")

if __name__ == '__main__':
    keep_alive()
    asyncio.run(main())