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

async def filter_title(title: str) -> str:
    for char in special_chars:
        title = title.replace(char, "")
    return title
        
async def download_pdf(page: Page, updated_notices: list[dict]) -> dict:
    try:
        new_notices = []    
        for up_notice in updated_notices:
            element_id = 2 * up_notice["_id"] + 2
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
                    file_path = os.path.join(os.getcwd(),'downloads', filename)
                    download = await download_info.value
                    
                    await download.save_as(file_path)
                    
                    up_notice["Attachment"] = file_path

                    new_notices.append(up_notice)
                else:
                    up_notice["Attachment"] = notice_url
                    new_notices.append(up_notice)
                
            elif await title_without_url.count() > 0:
                up_notice["Attachment"] = None
                new_notices.append(up_notice)
                
        return new_notices
        
    except Exception as error:
        logging.error(f'{download_pdf.__name__}: {error}')

async def scrap_notices(page: Page, url: str) -> dict:
    try:
        await page.goto(url, wait_until="networkidle", timeout=120000)
        logging.info(f'GET {url}')
                
        tasks = [] 
        results = []
        notices = []    
        
        for index in range(1, 11):#MAX 10 NOTICES
            element_id = 2 * index + 2
            base_path = f'/html/body/form/table/tbody/tr[{element_id}]'
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
            fetched_date = results[2].strip()
            fetched_published_by = results[1].replace("Published By: ", "").strip()
            
            notices.append(
                {
                    "_id" : index,
                    "Title" : fetched_notice,
                    "Date" : fetched_date,
                    "Published_By" : fetched_published_by
                }
            )
            element_id += 2
            
        return notices

    except Exception as error:
        logging.error(f'{scrap_notices.__name__}: {error}')
    
async def run_scraper(notice_page: Page, exist_notices: list, url: str) -> list[dict] | int:
    try:
        scraped_notices = await scrap_notices(notice_page, url)
        total_messages = await process_notices(scraped_notices, exist_notices)
        new_notices = 0 
        if len(total_messages) > 0 and len(total_messages) <= 10:
            new_notices = await download_pdf(notice_page, total_messages)
        return new_notices

    except Exception as error:
        logging.error(f"{run_scraper.__name__}: {str(error)}")

    finally:
        await notice_page.close()