from playwright.async_api import Page
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



async def data_format(notices: list[str], publish: list[str], dates:list[str]) -> dict:
    formated_data = {}
    for i in range(1, 11):
        formated_data[i] = [notices[i - 1], publish[i - 1], dates[i - 1]]
        
    return formated_data

async def clean_title(title_name):
    for char in special_chars:
        title_name = title_name.replace(char, " ")
    
    return title_name
    
async def get_notice_pdfs(page: Page, index: int) -> dict:
    try:
        filenames = {}    
        while index >= 1:
            id_no = 2 * index + 2
            title_name = page.locator(f'xpath=/html/body/form/table/tbody/tr[{id_no}]/td[2]/a')
            title_name = await title_name.inner_text()
            title_name = await clean_title(title_name)
            async with page.expect_download() as download_info:            
                donwload_file_element = page.locator(f'xpath=/html/body/form/table/tbody/tr[{id_no}]/td[2]/a')
                await donwload_file_element.click(modifiers=["Alt", ]) 
                
            current_dir = fr'{os.getcwd()}\downloads'
            filename = f'{title_name}.pdf'
            file_path = os.path.join(current_dir, filename)
            download = await download_info.value
            
            await download.save_as(file_path)
            
            filenames.update({index : file_path})
            index -= 1
        
        return filenames
    except Exception as error:
        logging.error(f'{get_notice_pdfs.__name__}: {error}')

async def scrap_notices(page: Page, url: str) -> dict:
    try:
        await page.goto(url,  wait_until="networkidle")
        logging.info(f'GET {url}')
        
        # await asyncio.sleep(60)
        
        notices = []
        publish = []
        dates = []
        
        for index in range(1, 11):#MAX 10 NOTICES
            id_no = 2 * index + 2
            title = page.locator(f'xpath=/html/body/form/table/tbody/tr[{id_no}]/td[2]/a')
            date = page.locator(f'xpath=/html/body/form/table/tbody/tr[{id_no}]/td[1]/font')
            publish_by = page.locator(f'xpath=/html/body/form/table/tbody/tr[{id_no}]/td[2]/font/b')
            
            tasks = [title.inner_text(),publish_by.inner_text(), date.inner_text()]
            results = await asyncio.gather(*tasks)
            
            notice_text = results[0].replace(":", "")
            publish_by_text = results[1].replace("Published By: ", "").strip()
            date_text = results[2].strip()

            notices.append(notice_text)
            dates.append(date_text)
            publish.append(publish_by_text)
            
            id_no += 2
            
        formated_data = await data_format(notices, publish, dates)
        
        return formated_data
    except Exception as error:
        logging.error(f'{scrap_notices.__name__}: {error}')
    
async def run_scraper(notice_page: Page, url: str) -> dict | int:
    try:
        scraped_data = await scrap_notices(notice_page, url)
        total_new_message = await process_notices(scraped_data)

        if total_new_message > 0 and total_new_message <= 10:
            filenames = await get_notice_pdfs(notice_page, total_new_message)
        
        return filenames 
        
    except Exception as error:
        logging.error(f"{run_scraper.__name__}: {str(error)}")
    finally:
        await notice_page.close()
        
    