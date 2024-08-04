from config import DB_URL
import pymongo
import logging
import asyncio

logging.basicConfig(level=logging.INFO,  
                    format='%(asctime)s  - %(name)s - %(levelname)s : %(message)s - [%(filename)s:%(lineno)d]',  
                    datefmt='[%Y-%m-%d | %H:%M:%S]') 

collectionUrl = DB_URL

client = pymongo.MongoClient(collectionUrl)
database = client.get_database('whatsapp_bot_db')
noticesCollection = database.get_collection('notices') 
if noticesCollection is None:
    noticesCollection = database['notices']
    
async def createNotices(scrapedNotices: dict) -> None:
    try:
        for noticeId in scrapedNotices.keys():
            noticeTitle, noticeDate, noticePublishedBy = scrapedNotices[noticeId]
            notice = {
            'NoticeId': noticeId,
            'Title': noticeTitle,
            'Date': noticeDate,
            'Published_By': noticePublishedBy
            }
            noticesCollection.insert_one(notice)
    except Exception as error:
        logging.error(f"{createNotices.__name__}: {str(error)}") 
    
async def updateNotices(scrapedNotices: dict) -> None:
    try:
        for noticeId, (scrapedTitle, scrapedDate, scrapedPublishedBy) in scrapedNotices.items(): 
            noticesCollection.find_one_and_update(
            {'NoticeId': noticeId}, 
            {'$set': {'Title': scrapedTitle, 'Date': scrapedDate, 'Published_By': scrapedPublishedBy}}
            )        
    except Exception as error:
        logging.error(f"{updateNotices.__name__}: {str(error)}")
        
async def compareNotices(scrapedNotices: dict) -> dict:
    try:
        existNoticeTitles = [document["Title"] for document in noticesCollection.find({},{"_id": 0,"Title": 1})] 
        unMatchedNotices = {}
        for noticeId, (scrapedTitle, scrapedDate, scrapedPublishedBy) in scrapedNotices.items():        
            if scrapedTitle not in existNoticeTitles:
                unMatchedNotices[noticeId] = [scrapedTitle, scrapedDate, scrapedPublishedBy]
    
        return unMatchedNotices
    except Exception as error:
        logging.error(f"{compareNotices.__name__}: {str(error)}")
        
async def processNotices(scrapedNotices: dict) -> dict:
    try:
        totalNotices = noticesCollection.count_documents({})
        if totalNotices == 0:
            await createNotices(scrapedNotices)
            return scrapedNotices
        
        elif totalNotices == 10:
            compareResult = await compareNotices(scrapedNotices)
            if len(compareResult) > 0 and len(compareResult) <= 10:
                await updateNotices(scrapedNotices) 
                return compareResult
            return {}
        else:
            logging.error(f'{processNotices.__name__}: Unexpected document count: {totalNotices}')
            
    except Exception as error:
        logging.error(f"{processNotices.__name__}: {str(error)}")
        
async def getNotices(index: int) -> dict:
    try:
        noticeData = noticesCollection.find_one(
        {"NoticeId" : index}, 
        {'_id' : 0, 'NoticeId' : 1, 'Title' : 1, 'Date': 1, 'Published_By' : 1}
    )
        return noticeData
    except Exception as error:
        logging.error(f"{getNotices.__name__}: {str(error)}")
