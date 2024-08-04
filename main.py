from playwright.async_api import  async_playwright, Page
from keep_alive import keep_alive
from database import getNotices
from scrap import runScraper
from config import * 
import asyncio
import logging
import aiohttp
import asyncio
import random
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
excludedText = ['MTech', 'BBA', 'MBA', 'M.Tech', 'B.Arch', 'BARCH', 'M TECH', 'West', 'East', 'M.Sc', 'Ph. D.', 'Ph.D', 'NCC']
includedText = ['BTECH', 'B.Tech', 'B Tech', 'B TECH']
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
    for exDegree in excludedText:
        if exDegree.lower() in title.lower():
            matchFound = True
            break
        
    for inDegree in includedText:
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
            await asyncio.sleep(10)
    
    logging.warning('Failed to find login code after all attempts')
    return None

#===================LOGIN-FUNCTION========================#
async def login(loginPage: Page, url: str) -> Page:   
    try:
        logging.info(f'GET {url}')
        await send_telegram_message(f'GET {url}')
        await loginPage.goto(url, wait_until="load", timeout=120000)
        
        await asyncio.sleep(60)
                
        searchBox = loginPage.locator(searchBoxPath)
        if await searchBox.count() > 0:
            return loginPage
    
        if isQRCode:
            logging.info('SCAN QR code')
        
        else:
            logging.info('Logging in using phone number')
            await send_telegram_message('Logging in using phone number')
            
            await loginPage.wait_for_selector('xpath=//span[@role="button" and text()="Link with phone number"]', state='visible', timeout=60000)
            await loginPage.locator('xpath=//span[@role="button" and text()="Link with phone number"]').click()

            await asyncio.sleep(10)
            
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
            await asyncio.sleep(10)

            loginCode = await fetchLoginCode(loginPage)
            await asyncio.sleep(5)
            
            if loginCode:
                await send_telegram_message(loginCode)
                logging.info(f"Login code: {loginCode}")
        
        await loginPage.wait_for_selector(searchBoxPath)
        
        return loginPage
    except Exception as error:
        logging.error(f'{login.__name__}: {str(error)}')
#======================================================#

#=================MESSAGE-FUNCTION=================#        
async def openChat(chatPage: Page, chatName: str) -> None:
    await asyncio.sleep(10)
    await chatPage.locator(f'xpath={searchBoxPath}').click()
    await chatPage.keyboard.press('Control+a')
    await chatPage.keyboard.press('Backspace')
    await chatPage.keyboard.type(chatName)
    await chatPage.get_by_title(chatName, exact=True).click()
    await asyncio.sleep(10)
    
    
async def sendText(chatPage: Page, message: str) -> None:
    await chatPage.locator('xpath=//div[@contenteditable="true" and @data-lexical-editor="true" and @aria-label="Type a message"]').click()
    await chatPage.keyboard.insert_text(message)
    await chatPage.locator(f'xpath={sendButton}').click()
    
    
async def sendAttachment(chatPage: Page, filePath: str)-> None:
    await chatPage.locator(f'xpath={attachButton}').click()
    await asyncio.sleep(5)
    await chatPage.set_input_files(f'xpath={fileInputPath}', filePath)
    await asyncio.sleep(10)

    captionInput = chatPage.locator(captionPath)        
    if await captionInput.is_visible():
        captionBlankTxt = '⠀'
        await captionInput.click()
        await captionInput.fill(captionBlankTxt, force=True)
        
    await asyncio.sleep(5)
    await chatPage.locator(f'xpath={sendButton}').click()
    await asyncio.sleep(30)
    
    if filePath and os.path.exists(filePath):
        os.remove(filePath)


async def replyToLastMessage(chatPage: Page, lastMessageId: str, fileContent: str | None) -> bool:
    if not fileContent:
        return False
    
    filePath = os.path.join(os.getcwd(), 'downloads', fileContent)
    try:
        await asyncio.sleep(5)
        await chatPage.locator(f'div[data-id="{lastMessageId}"]').hover()
        downContextButton = await chatPage.locator(downContextPath).is_visible(timeout=5000)
        if downContextButton:
            await chatPage.locator(downContextPath).click()
            await asyncio.sleep(5)
            await chatPage.locator(replyButton).click()
            await asyncio.sleep(5)
            await sendAttachment(chatPage, filePath)
    
    except Exception as error:
        logging.warning(f"Hover and context menu actions failed: {str(error)}. Trying fallback method.")
        await sendAttachment(chatPage, filePath)
            
    return True    
    
async def getLastMessage(chatPage: Page) -> int:
    await chatPage.wait_for_selector('div[data-id]')
    elementDataId = await chatPage.query_selector_all('div[data-id]')
    lastMessageId = 0
    if elementDataId:
        lastMessageId = await elementDataId[-1].get_attribute('data-id')
    return lastMessageId

async def isMessageDelivered(chatPage: Page, lastMessageId: str) -> bool:
    maxDeliveryWait = 400  
    deliveryCheckInterval = 5
    isDelivered = False  
    for _ in range(0, maxDeliveryWait, deliveryCheckInterval):
        dblCheckIcon = chatPage.locator(f'div[data-id="{lastMessageId}"] span[data-icon="msg-dblcheck"]')
        msgCheckIcon = chatPage.locator(f'div[data-id="{lastMessageId}"] span[data-icon="msg-check"]')
        
        if await dblCheckIcon.count() > 0 or await msgCheckIcon.count() > 0:
            isDelivered = True
            break
        await asyncio.sleep(deliveryCheckInterval)
    return isDelivered

async def sendMessageToWhatsapp(chatPage: Page, savedPdfDocuments: dict) -> None:
    try:
        await openChat(chatPage, chatName)
        messageCount = len(savedPdfDocuments)
        for messageNo in sorted(savedPdfDocuments.keys(), reverse=True):
            noticeContent = await getNotices(messageNo)
            noticeTitle = noticeContent['Title']
            noticeDate = noticeContent['Date']
            noticePublishedBy = noticeContent['Published_By']
            fileContent = savedPdfDocuments[messageNo]
            
            if await filterDegrees(noticeTitle):
                logging.info(f'Skipping MessageNo.{messageCount}')
                await send_telegram_message(f'Skipping MessageNo.{messageCount}')
                messageCount -= 1
                continue
            
            messageContent = f'''
            🔔NOTICE: *{noticeTitle}*\n\n🗓️ Date: {noticeDate}\n\n✍️ Published by: {noticePublishedBy}
            '''
            
            if fileContent and '.pdf' not in fileContent:
                attachmentUrlContent = f'\n{fileContent}'
                await sendText(chatPage, messageContent + attachmentUrlContent)
                logging.info(f'MessageNo.{messageCount} sent')
                await send_telegram_message(f'MessageNo.{messageCount} sent')
                messageCount -= 1
                continue

            await sendText(chatPage, messageContent)
                
            lastMessageId = await getLastMessage(chatPage)

            if await isMessageDelivered(chatPage, lastMessageId):
                if await replyToLastMessage(chatPage, lastMessageId, fileContent):
                    lastUploadMessageId = await getLastMessage(chatPage)
                    
                    if await isMessageDelivered(chatPage, lastUploadMessageId):
                        logging.info(f'MessageNo.{messageCount} sent')
                        await send_telegram_message(f'MessageNo.{messageCount} sent')
            
            messageCount -= 1

    except Exception as error:
        logging.error(f'{sendMessageToWhatsapp.__name__}: {str(error)}')
#============================================================# 

async def scraperTask(noticePage: Page, whatsappPage: Page, url: str) -> None:    
    try:
        logging.info('Checking for New Notices')
        await send_telegram_message('Checking for New Notices')
        
        scrapResult = await runScraper(noticePage, url)
        if isinstance(scrapResult, dict):
            logging.info(f'{len(scrapResult)} New Notices Found!')        
            await send_telegram_message(f'{len(scrapResult)} New Notices Found!')
            await sendMessageToWhatsapp(whatsappPage, scrapResult)
            
        elif isinstance(scrapResult, int):
            logging.info('Notices are up to date')
            await send_telegram_message('Notices are up to date')
        else:
            logging.warning(f'Unexpected scraping result type: {type(scrapResult)}')
    
    except Exception as error:
        logging.error(f'{scraperTask.__name__}: {str(error)}')
    
    finally:
        await noticePage.close()
    logging.info('Sleeping for 900 seconds')
    await send_telegram_message('Sleeping for 900 seconds')
    await asyncio.sleep(900)
    
async def keepWhatsappActive(page: Page) -> bool:
    try:
        searchBox = page.locator(searchBoxPath)
        if await searchBox.is_visible(timeout=5000):
            await searchBox.click()
            await asyncio.sleep(10)
            logging.info("WhatsApp session is active")
            await send_telegram_message("WhatsApp session is active")
        return False
            
    except Exception as e:
        logging.error(f'{keepWhatsappActive.__name__}: {str(e)}')
        return True  

async def main():
    while True:
        try:
            logging.info('Bot Started')
            await asyncio.sleep(20)

            userDir = os.path.join(os.getcwd(), 'user_data')
            if not os.path.exists(userDir):
                os.makedirs(userDir)
            
            async with async_playwright() as playwright:       
                browser = await playwright.chromium.launch_persistent_context(
                    user_data_dir=userDir,
                    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    headless=True,
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
            
                    whatsappPage = await browser.new_page()
                    if len(browser.pages) > 0:
                        await browser.pages[0].close()
        
                    chatPage = await login(whatsappPage, url='https://web.whatsapp.com/')
                    if chatPage is not None:
                        while True:
                            isSessionClosed = await keepWhatsappActive(chatPage)
                            if not isSessionClosed:
                                for _ in range(3):
                                    noticePage = await browser.new_page()
                                    await scraperTask(noticePage, whatsappPage, url='https://www.imsnsit.org/imsnsit/notifications.php')
                    
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
    
