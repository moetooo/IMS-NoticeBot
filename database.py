from config import DB_URL
import pymongo
import logging


logging.basicConfig(level=logging.INFO,  
                    format='%(asctime)s  - %(name)s - %(levelname)s : %(message)s - [%(filename)s:%(lineno)d]',  
                    datefmt='[%Y-%m-%d | %H:%M:%S]') 

collection_Url = DB_URL

client = pymongo.MongoClient(collection_Url)
Database = client.get_database('test_db')
NoticesCollection = Database.get_collection('notices') 
if NoticesCollection is None:
    NoticesCollection = Database['notices']
    
async def create_notices(scraped_data: list[str]) -> dict:
    try:
        index = 1
        created = False
        while index <= 10:
            notice_details = scraped_data[index]
            title, publish_by, date = notice_details
            notice = {
            'NoticeId' : index,
            'Title' : title,
            'Publish_by' :publish_by,
            'Date' : date   
            }
            
            NoticesCollection.insert_one(notice)
            index += 1
            created = True if index == 11 else False
            
        return {create_notices.__name__ : created, 'NoticeId' : index - 1}
            
    except Exception as error:
        logging.error(f"{create_notices.__name__}: {str(error)}") 
    
async def update_notices(index: int, scraped_data: dict) -> dict:
    try:
        while index >= 1:
            title, publish_by, date = scraped_data[index]            
            NoticesCollection.find_one_and_update(
            {'NoticeId' : index}, 
            {'$set' : {'Title': title, 'Publish_by' : publish_by, 'Date' : date}}
            )
            
            index -= 1

    except Exception as error:
        logging.error(f"{update_notices.__name__}: {str(error)}")
    
async def compare_notices(scraped_data: dict) -> dict:
    try:
        index = 10
        all_matched = False
        scrapped_title = scraped_data[index][0]
        
        while index >= 1:
            scrapped_title = scraped_data[index][0]
            
            is_title_exist = NoticesCollection.find_one(
            {"Title" : scrapped_title}, {'NoticeId': 1}
    )       
            
            if is_title_exist is None:
                break
            
            index -= 1
            all_matched = True if index == 0 else False
        
        return {compare_notices.__name__ : all_matched, 'NoticeId' : index}
        
    except Exception as error:
        logging.error(f"{compare_notices.__name__}: {str(error)}")
        
async def process_notices(scraped_data: dict) -> dict:
    total_notices = NoticesCollection.count_documents({})
    if total_notices == 0:
        create_result = await create_notices(scraped_data)
        return create_result
    
    elif total_notices == 10:
        compare_result = await compare_notices(scraped_data)
        all_matched, total_new_message = compare_result['compare_notices'], compare_result['NoticeId']
        if not all_matched:
            await update_notices(10, scraped_data)
                
        return total_new_message if not all_matched else 0 #Sen
    else:
        logging.error(f'Duplicate data in the Document')
        
async def get_notices(index: int):
    notice_db_info = NoticesCollection.find_one(
    {"NoticeId" : index}, 
    {'_id' : 0, 'NoticeId' : 1, 'Title' : 1, 'Publish_by' : 1, 'Date': 1}
)
    return notice_db_info
