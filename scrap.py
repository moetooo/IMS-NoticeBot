from playwright.async_api import Page, async_playwright
from database import process_notices
import asyncio
import logging
import os
logging.basicConfig(level=logging.INFO,  
                    format='%(asctime)s - %(levelname)s : %(message)s',  
                    datefmt='[%Y-%m-%d | %H:%M:%S]') 

special_chars = [
    "#", "%", "&", "{", "}", "\\", "<", ">", "*", "?", "/", "$", "!", "'", '"',
    ":", "@", "+", "`", "|", "=", "[", "]"
]

async def process_data(notices: list[str], publish: list[str], dates:list[str]) -> dict:
    formatted_data = {}
    for i in range(1, 11):
        formatted_data[i] = [notices[i - 1], dates[i - 1], publish[i - 1]]
    return formatted_data

async def filter_title(title: str) -> str:
    for char in special_chars:
        title = title.replace(char, "")
    return title
        
async def download_pdf(page: Page, notice_data: dict) -> dict:
    try:
        filenames = {}    
        for notice_id in notice_data.keys():
            element_id = 2 * notice_id + 2
            base_path = f'/html/body/form/table/tbody/tr[{element_id}]'
            title_with_url = page.locator(f'xpath={base_path}/td[2]/a')
            title_without_url = page.locator(f'xpath={base_path}/td[2]/b')
            
            if await title_with_url.count() > 0:
                notice_url = await title_with_url.get_attribute('href')
                if 'plum_url.php' in notice_url:
                    fetched_title = await title_with_url.inner_text()
                    title = await filter_title(fetched_title)
                    async with page.expect_download() as download_info:            
                        donwload_file_element = page.locator(f'xpath={base_path}/td[2]/a')
                        await donwload_file_element.click(modifiers=["Alt", ])
                        
                    filename = f'{title}.pdf'
                    filePath = os.path.join(os.getcwd(),'downloads', filename)
                    download = await download_info.value
                    
                    await download.save_as(filePath)
                    filenames.update({notice_id : filePath})
                else:
                    filenames.update({notice_id : notice_url})
                
            elif await title_without_url.count() > 0:
                filenames.update({notice_id : None})
                
        return filenames
        
    except Exception as error:
        logging.error(f'{download_pdf.__name__}: {error}')

async def scrap_notices(page: Page, url: str) -> dict:
    try:
        await page.goto(url, wait_until="networkidle", timeout=120000)
        logging.info(f'GET {url}')
                
        notice_list = []
        published_by_list = []
        date_list = []
        tasks = [] 
        results = []    
        
        for index in range(1, 11):#MAX 10 NOTICES
            Id = 2 * index + 2
            base_path = f'/html/body/form/table/tbody/tr[{Id}]'
            title_with_url = page.locator(f'xpath={base_path}/td[2]/a')
            title_without_url = page.locator(f'xpath={base_path}/td[2]/b')
            
            if await title_with_url.count() > 0:#Notices with url
                date = page.locator(f'xpath=({base_path})/td[1]/font')
                published_by = page.locator(f'xpath={base_path}/td[2]/font/b')
                
                tasks = [title_with_url.inner_text(),published_by.inner_text(), date.inner_text()]
                results = await asyncio.gather(*tasks)
                
            elif await title_without_url.count() > 0:#Notices without url
                textData = await title_without_url.inner_text()
                published_data_index = textData.find('Published')
                if published_data_index != -1:
                    title = str(textData[:published_data_index]).strip()
                    published_by = str(textData[published_data_index:]).strip()
                    date = page.locator(f'xpath=({base_path})/td[1]/font')
                    date = await date.inner_text()
                    
                    results = [title,published_by, date]
    
            fetched_notice = results[0].replace(":", "")
            fetched_published_by = results[1].replace("Published By: ", "").strip()
            fetched_date = results[2].strip()

            notice_list.append(fetched_notice)
            published_by_list.append(fetched_published_by)
            date_list.append(fetched_date)
            
            Id += 2
            
        formatted_data = await process_data(notice_list, published_by_list, date_list)
        return formatted_data

    except Exception as error:
        logging.error(f'{scrap_notices.__name__}: {error}')
    
async def run_scraper(notice_page: Page, url: str) -> dict | int:
    try:
        scraped_notices = await scrap_notices(notice_page, url)
        total_messages = await process_notices(scraped_notices)
        filenames = 0 
        if len(total_messages) > 0 and len(total_messages) <= 10:
            filenames = await download_pdf(notice_page, total_messages)        
        return filenames

    except Exception as error:
        logging.error(f"{run_scraper.__name__}: {str(error)}")

    finally:
        await notice_page.close()
