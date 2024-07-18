from playwright.async_api import  async_playwright, Page, BrowserContext
from keep_alive import keep_alive
from database import getNotices
from scrap import runScraper
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
countryCode = COUNTRY_CODE
chatName = CHAT_NAME
phoneNo = WHATSAPP_NO
chatId = CHAT_ID
token = TOKEN
isQRCode = IS_QR
delay = 10
#=====================#

#========XPATHS========#
downContextPath = DOWN_CONTEXT_BTN
fileInputPath = FILE_UPLOAD
attachButton = ATTACH_BTN
searchBoxPath = SEARCH_BOX
captionPath = CAPTION_AREA
sendButton = SEND_BTN
replyButton = REPLY_BTN
#====================#

#========FILTERS=========#
excludedDegrees = ['MTech', 'BBA', 'MBA', 'M.Tech', 'B.Arch', 'BARCH', 'M TECH']
includedDegrees = ['BTECH', 'B.Tech', 'B Tech', 'B TECH']
#========================#

async def send_telegram_message(text: str) -> None:
    formattedText = f"`{text}`"
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chatId}&text={formattedText}&parse_mode=MarkdownV2"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                logging.error(f"Failed to send message. Status code: {response.status}")
                
async def filterDegrees(title: str) -> bool:
    matchFound = False
    for exDegree in excludedDegrees:
        if exDegree.lower() in title.lower():
            matchFound = True
            break
        
    for inDegree in includedDegrees:
        if inDegree.lower() in title.lower():
            matchFound = False
            break
                
    return matchFound    

async def fetchLoginCode(loginPage: Page, retryCount: int = 3) -> str:
    for count in range(retryCount):
        logging.info(f'Attempt {count + 1}/{retryCount}: Search for code')
        await send_telegram_message(f'Attempt {count + 1}/{retryCount}: Search for code')
        
        codeElement = await loginPage.query_selector('div[aria-details="link-device-phone-number-code-screen-instructions"]')
        
        if codeElement:
            logging.info('Code element found')
            await send_telegram_message('Code element found')
            
            dataLinkCode = await codeElement.get_attribute('data-link-code')
            if dataLinkCode:
                loginCode = dataLinkCode.replace(",", " ")
                return loginCode
        
        if count < retryCount - 1:
            logging.info('Code not found. Waiting before next attempt...')
            await send_telegram_message('Code not found. Waiting before next attempt...')
            await asyncio.sleep(delay)
    
    logging.warning('Failed to find login code after all attempts')
    return None

async def login(context: BrowserContext, url: str) -> Page:
    try:
        loginPage = await context.new_page()
        logging.info(f'GET {url}')
        await send_telegram_message(f'GET {url}')
        await loginPage.goto(url, wait_until="networkidle", timeout=120000)
        
        if isQRCode:
            logging.info('SCAN QR code')
        
        else:
            logging.info('Logging in using phone number')
            await send_telegram_message('Logging in using phone number')
            
            await asyncio.sleep(60)
                        
            await loginPage.wait_for_selector('xpath=//span[@role="button" and text()="Link with phone number"]', state='visible', timeout=60000)
            await loginPage.locator('xpath=//span[@role="button" and text()="Link with phone number"]').dblclick()

            await asyncio.sleep(delay)
            
            await loginPage.locator('xpath=//*[@id="app"]/div/div[2]/div[3]/div[1]/div/div[3]/div[1]/div[1]/button/div/div/div').click()
            await loginPage.locator('xpath=//*[@id="wa-popovers-bucket"]/div/div[2]/div/div[1]/div/div[2]/div[1]/p').click()
            await loginPage.keyboard.type(countryCode)
            
            logging.info('Country code entered')
            await asyncio.sleep(5)
            
            await loginPage.locator('xpath=//*[@id="wa-popovers-bucket"]/div/div[2]/div/div[2]/div/div/div/div/div/div/button/div/div/div[2]/div/div/div').click()                    
            await loginPage.locator('xpath=//*[@id="app"]/div/div[2]/div[3]/div[1]/div/div[3]/div[1]/div[2]/div/div').click()
            await loginPage.keyboard.type(phoneNo)
            
            await asyncio.sleep(5)
            
            await loginPage.locator('xpath=//*[@id="app"]/div/div[2]/div[3]/div[1]/div/div[3]/div[2]/button/div/div').click()
            
            logging.info('Phone no entered')            
            await asyncio.sleep(delay)

            loginCode = await fetchLoginCode(loginPage)
            await asyncio.sleep(5)
            
            if loginCode:
                await send_telegram_message(loginCode)
                logging.info(f"Login code: {loginCode}")
        
        await loginPage.wait_for_selector(searchBoxPath)
        
        return loginPage
    except Exception as error:
        logging.error(f'{login.__name__}: {str(error)}')

async def sendMessage(chatPage: Page, savedPdfDocuments: dict) -> None:
    try:
        await asyncio.sleep(delay)
                
        await chatPage.locator(f'xpath={searchBoxPath}').click()
        await chatPage.keyboard.type(chatName)
        await chatPage.get_by_title(chatName, exact=True).click()
        
        await asyncio.sleep(delay)
        
        totalMessages = len(savedPdfDocuments)
        for messageNo in range(totalMessages, 0, -1):
            noticeData = await getNotices(messageNo)
            title, date, publishedBy  = noticeData['Title'], noticeData['Date'], noticeData['Published_By']            
            skipMessage = await filterDegrees(title)
            
            fileName = savedPdfDocuments[messageNo]
            currentDir = os.getcwd()
            filePath = os.path.join(currentDir, 'downloads', fileName)
            
            if not skipMessage:
                messageContent = f'''
                🔔NOTICE: *{title}*\n\n🗓️ Date: {date}\n\n✍️ Published by: {publishedBy}
                '''
                await chatPage.locator('xpath=//div[@contenteditable="true" and @data-lexical-editor="true" and @aria-label="Type a message"]').click()
                await chatPage.keyboard.insert_text(messageContent)
                await chatPage.locator(f'xpath={sendButton}').click()
                
                await asyncio.sleep(15)
                
                await chatPage.wait_for_selector('div[data-id]')
                elementDataId = await chatPage.query_selector_all('div[data-id]')
                lastMessageId = 0
                if elementDataId:
                    lastMessageId = await elementDataId[-1].get_attribute('data-id')
                            
                await chatPage.locator(f'div[data-id="{lastMessageId}"]').hover()
                downContextButton = await chatPage.locator(downContextPath).is_visible()
                if downContextButton:
                    await chatPage.locator(downContextPath).click()
                    await asyncio.sleep(5)
                    await chatPage.locator(replyButton).click()
                
                await asyncio.sleep(5)    
                
                await chatPage.locator(f'xpath={attachButton}').click()

                await asyncio.sleep(15)
                            
                await chatPage.set_input_files(f'xpath={fileInputPath}', filePath)
                
                await asyncio.sleep(delay)
                
                captionInput = chatPage.locator(captionPath)        
                if await captionInput.is_visible():
                    captionBlankTxt = '⠀'
                    await captionInput.click()
                    await captionInput.fill(captionBlankTxt, force=True)
                    
                await asyncio.sleep(5)
                
                await chatPage.locator(f'xpath={sendButton}').click()
                
                await asyncio.sleep(30)
                
                logging.info(f'MessageNo.{messageNo} sent.')

            else:
                logging.info(f'Skipping MessageNo.{messageNo}')
                
            os.remove(filePath)
            
    except Exception as error:
        logging.error(f'{sendMessage.__name__}: {str(error)}')

async def scraperTask(context: BrowserContext, whatsappPage: Page, url: str, retryCount: int = 3) -> None:
    for count in range(retryCount):
        try:
            noticePage = await context.new_page()
            logging.info(f'Attempt {count + 1}/{retryCount}: Checking for New Notices')
            await send_telegram_message(f'Attempt {count + 1}/{retryCount}: Checking for New Notices')
            
            scrapResult = await runScraper(noticePage, url)
            
            if isinstance(scrapResult, dict):
                totalNotices = len(scrapResult)
                logging.info(f'{totalNotices} New Notices Found!')        
                await send_telegram_message(f'{totalNotices} New Notices Found!')
                await sendMessage(whatsappPage, scrapResult)
                
            elif isinstance(scrapResult, int):
                logging.info('Notices are up to date')
                await send_telegram_message('Notices are up to date')
            else:
                logging.warning(f'Unexpected scraping result type: {type(scrapResult)}')
        
        except Exception as error:
            logging.error(f'{scraperTask.__name__}: {str(error)}')
        
        finally:
            await noticePage.close()
        
        logging.info('Sleeping for 600 seconds')
        await send_telegram_message('Sleeping for 600 seconds')
        await asyncio.sleep(600)
        
async def keepWhatsappActive(page: Page) -> bool:
    try:
        searchBox = page.locator(searchBoxPath)
        sessionClosed = True
        if await searchBox.count() > 0:
            await searchBox.focus()
            sessionClosed = False
            logging.info("WhatsApp session is active")
            await send_telegram_message("WhatsApp session is active")
        else:
            logging.warning("Could not find WhatsApp search box. Session might be logged out.")
            await send_telegram_message("Could not find WhatsApp search box. Session might be logged out.")
                
        return sessionClosed
    except Exception as e:
        logging.error(f'{keepWhatsappActive.__name__}: {str(e)}')

async def main():
    logging.info('Bot Started')
    await asyncio.sleep(20)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        try:            
            donwloadPath = os.path.join(os.getcwd(), "downloads")
            if not os.path.exists(donwloadPath):
                os.makedirs(donwloadPath)
                logging.info('Download directory created successfully')
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            context.set_default_navigation_timeout(900_000)  # 15 mins
            context.set_default_timeout(900_000)  # 15 mins
            whatsappPage = await login(context, url='https://web.whatsapp.com/')
            
            if whatsappPage is not None:
                while True:
                    isSessionClosed = await keepWhatsappActive(whatsappPage)
                    if isSessionClosed:
                        break
                    await scraperTask(context, whatsappPage, url='https://www.imsnsit.org/imsnsit/notifications.php')
                
        except Exception as error:
            logging.error(f'{main.__name__}: {str(error)}')
        finally:
            await browser.close()
            logging.info("Browser closed. Script finished.")

if __name__ == '__main__':
    keep_alive()
    asyncio.run(main())
    
