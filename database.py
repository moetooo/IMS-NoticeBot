from config import DB_URL
import pymongo
import logging
import asyncio

logging.basicConfig(level=logging.INFO,  
                    format='%(asctime)s  - %(name)s - %(levelname)s : %(message)s - [%(filename)s:%(lineno)d]',  
                    datefmt='[%Y-%m-%d | %H:%M:%S]') 

client = pymongo.MongoClient(DB_URL)
database = client.get_database('whatsapp_bot_db')
notice_collection = database.get_collection('notices') 
if notice_collection is None:
    notice_collection = database['notices']
    
async def create_notices(scraped_notices: dict) -> None:
    try:
        notices = []
        for notice_id in scraped_notices.keys():
            notice_title, notice_date, notice_published_by = scraped_notices[notice_id]
            notice = {
            '_id': len(notices) + 1,
            'NoticeId': notice_id,
            'Title': notice_title,
            'Date': notice_date,
            'Published_By': notice_published_by
            }
            notices.append(notice)
            
        if notices:
            notice_collection.insert_many(notices)

    except Exception as error:
        logging.error(f"{create_notices.__name__}: {str(error)}") 
    
async def update_notices(scraped_notices: dict) -> None:
    try:
        for notice_id, (scraped_title, scraped_date, scraped_published_by) in scraped_notices.items(): 
            notice_collection.find_one_and_update(
            {'NoticeId': notice_id}, 
            {'$set': {'Title': scraped_title, 'Date': scraped_date, 'Published_By': scraped_published_by}}
            )        
    except Exception as error:
        logging.error(f"{update_notices.__name__}: {str(error)}")
        
async def compare_notices(scraped_notices: dict) -> dict:
    try:
        exist_notice_titles = [document["Title"] for document in notice_collection.find({},{"_id": 0,"Title": 1})]
        print(exist_notice_titles)
        unmatched_notices = {}
        for notice_id, (scraped_title, scraped_date, scraped_published_by) in scraped_notices.items():        
            if scraped_title not in exist_notice_titles:
                unmatched_notices[notice_id] = [scraped_title, scraped_date, scraped_published_by]
        print(unmatched_notices)
        return unmatched_notices
    
    except Exception as error:
        logging.error(f"{compare_notices.__name__}: {str(error)}")
        
async def process_notices(scraped_notices: dict) -> dict:
    try:
        total_notices = notice_collection.count_documents({})
        if total_notices == 0:
            await create_notices(scraped_notices)
            return scraped_notices
        
        elif total_notices == 10:
            compare_result = await compare_notices(scraped_notices)            
            if len(compare_result) > 0 and len(compare_result) <= 10:
                await update_notices(scraped_notices) 
                return compare_result
            return {}
        else:
            logging.error(f'{process_notices.__name__}: Unexpected document count: {total_notices}')
            
    except Exception as error:
        logging.error(f"{process_notices.__name__}: {str(error)}")
        
async def get_notices(index: int) -> dict:
    try:
        notice_data = notice_collection.find_one(
        {"_id" : index}, 
        {'_id' : 1, 'Title' : 1, 'Date': 1, 'Published_By' : 1}
    )
        return notice_data
    except Exception as error:
        logging.error(f"{get_notices.__name__}: {str(error)}")
