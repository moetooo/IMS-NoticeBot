from config import DB_URL
import pymongo
import logging
import asyncio

logging.basicConfig(level=logging.INFO,  
                    format='%(asctime)s  - %(name)s - %(levelname)s : %(message)s - [%(filename)s:%(lineno)d]',  
                    datefmt='[%Y-%m-%d | %H:%M:%S]') 

client = pymongo.MongoClient(DB_URL)
database = client.get_database('test_db')
notice_collection = database.get_collection('notices') 
if notice_collection is None:
    notice_collection = database['notices']
    
async def create_notices(scraped_notices: list[dict]) -> None:
    try:
        notice_collection.insert_many(scraped_notices)
    except Exception as error:
        logging.error(f"{create_notices.__name__}: {str(error)}") 
    
async def update_notices(scraped_notices: list[dict]) -> None:
    try:
        for notice in scraped_notices:
            notice_collection.find_one_and_update(
            {'_id': notice["_id"]}, 
            {'$set': {'Title': notice["Title"], 'Date': notice["Date"], 'Published_By': notice["Published_By"]}}
            )   
    except Exception as error:
        logging.error(f"{update_notices.__name__}: {str(error)}")
        
async def compare_notices(scraped_notices: list[dict], exist_notices) -> dict:
    try:
        exist_notice_titles = {exist_notice["Title"] for exist_notice in exist_notices}
        logging.info(f'exist_notice_titles : {exist_notice_titles}')
        unmatched_notices = []
        for notice in scraped_notices:
            if notice["Title"] not in exist_notice_titles:
                unmatched_notices.append(notice)
        logging.info(f'unmatched_notices : {unmatched_notices}')
        return unmatched_notices
    
    except Exception as error:
        logging.error(f"{compare_notices.__name__}: {str(error)}")
        
async def process_notices(scraped_notices: list[dict], exist_notices: list) -> list[dict]:
    try:
        total_notices = notice_collection.count_documents({})
        if total_notices == 0:
            await create_notices(scraped_notices)
            return scraped_notices
        
        elif total_notices == 10:
            compare_result = await compare_notices(scraped_notices, exist_notices)            
            if len(compare_result) > 0 and len(compare_result) <= 10:
                await update_notices(scraped_notices) 
            return compare_result
        else:
            logging.error(f'{process_notices.__name__}: Unexpected document count: {total_notices}')
            
    except Exception as error:
        logging.error(f"{process_notices.__name__}: {str(error)}")
        
async def get_exist_notice_title() -> list:
    try:
        return notice_collection.find({},{"_id": 0,"Title": 1})
    
    except Exception as error:
        logging.error(f"{get_exist_notice_title.__name__}: {str(error)}")
