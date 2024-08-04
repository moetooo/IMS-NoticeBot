from playwright.async_api import Page, async_playwright
from database import processNotices
import asyncio
import logging
import os
logging.basicConfig(level=logging.INFO,  
                    format='%(asctime)s - %(levelname)s : %(message)s',  
                    datefmt='[%Y-%m-%d | %H:%M:%S]') 

specialChars = [
    "#", "%", "&", "{", "}", "\\", "<", ">", "*", "?", "/", "$", "!", "'", '"',
    ":", "@", "+", "`", "|", "=", "[", "]"
]

async def processData(notices: list[str], publish: list[str], dates:list[str]) -> dict:
    formattedData = {}
    for i in range(1, 11):
        formattedData[i] = [notices[i - 1], dates[i - 1], publish[i - 1]]
    return formattedData

async def filterTitle(title: str) -> str:
    for char in specialChars:
        title = title.replace(char, "")
    return title
        
async def downloadPdfs(page: Page, noticeData: dict) -> dict:
    try:
        filenames = {}    
        for noticeId in noticeData.keys():
            elementId = 2 * noticeId + 2
            baseXpath = f'/html/body/form/table/tbody/tr[{elementId}]'
            titleWithUrl = page.locator(f'xpath={baseXpath}/td[2]/a')
            titleWithoutUrl = page.locator(f'xpath={baseXpath}/td[2]/b')
            
            if await titleWithUrl.count() > 0:
                noticeUrl = await titleWithUrl.get_attribute('href')
                if 'plum_url.php' in noticeUrl:
                    fetchedTitle = await titleWithUrl.inner_text()
                    title = await filterTitle(fetchedTitle)
                    async with page.expect_download() as download_info:            
                        donwload_file_element = page.locator(f'xpath={baseXpath}/td[2]/a')
                        await donwload_file_element.click(modifiers=["Alt", ])
                        
                    currentDir = fr'{os.getcwd()}\downloads'
                    filename = f'{title}.pdf'
                    filePath = os.path.join(currentDir, filename)
                    download = await download_info.value
                    
                    await download.save_as(filePath)
                    filenames.update({noticeId : filePath})
                else:
                    filenames.update({noticeId : noticeUrl})
                
            elif await titleWithoutUrl.count() > 0:
                filenames.update({noticeId : None})
                
        return filenames
        
    except Exception as error:
        logging.error(f'{downloadPdfs.__name__}: {error}')

async def scrapNotices(page: Page, url: str) -> dict:
    try:
        await page.goto(url, wait_until="networkidle", timeout=120000)
        logging.info(f'GET {url}')
                
        noticesList = []
        publishedByList = []
        datesList = []
        tasks = [] 
        results = []    
        
        for index in range(1, 11):#MAX 10 NOTICES
            Id = 2 * index + 2
            baseXpath = f'/html/body/form/table/tbody/tr[{Id}]'
            titleWithUrl = page.locator(f'xpath={baseXpath}/td[2]/a')
            titleWithoutUrl = page.locator(f'xpath={baseXpath}/td[2]/b')
            
            if await titleWithUrl.count() > 0:#Notices with url
                date = page.locator(f'xpath=({baseXpath})/td[1]/font')
                publishedBy = page.locator(f'xpath={baseXpath}/td[2]/font/b')
                
                tasks = [titleWithUrl.inner_text(),publishedBy.inner_text(), date.inner_text()]
                results = await asyncio.gather(*tasks)
                
            elif await titleWithoutUrl.count() > 0:#Notices without url
                textData = await titleWithoutUrl.inner_text()
                publishedDataIndex = textData.find('Published')
                if publishedDataIndex != -1:
                    title = str(textData[:publishedDataIndex]).strip()
                    publishedBy = str(textData[publishedDataIndex:]).strip()
                    date = page.locator(f'xpath=({baseXpath})/td[1]/font')
                    date = await date.inner_text()
                    
                    results = [title,publishedBy, date]
    
            fetchNotice = results[0].replace(":", "")
            fetchPublishedBy = results[1].replace("Published By: ", "").strip()
            fetchDate = results[2].strip()

            noticesList.append(fetchNotice)
            publishedByList.append(fetchPublishedBy)
            datesList.append(fetchDate)
            
            Id += 2
            
        formattedData = await processData(noticesList, publishedByList, datesList)
        return formattedData

    except Exception as error:
        logging.error(f'{scrapNotices.__name__}: {error}')
    
async def runScraper(noticePage: Page, url: str) -> dict | int:
    try:
        scrapedNotices = await scrapNotices(noticePage, url)
        totalMessages = await processNotices(scrapedNotices)
        filenames = 0 
        if len(totalMessages) > 0 and len(totalMessages) <= 10:
            filenames = await downloadPdfs(noticePage, totalMessages)        
        return filenames

    except Exception as error:
        logging.error(f"{runScraper.__name__}: {str(error)}")

    finally:
        await noticePage.close()
