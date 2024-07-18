from config import DB_URL
import pymongo
import logging


logging.basicConfig(level=logging.INFO,  
                    format='%(asctime)s  - %(name)s - %(levelname)s : %(message)s - [%(filename)s:%(lineno)d]',  
                    datefmt='[%Y-%m-%d | %H:%M:%S]') 

collectionUrl = DB_URL

client = pymongo.MongoClient(collectionUrl)
database = client.get_database('whatsapp_bot_db')
noticesCollection = database.get_collection('notices') 
if noticesCollection is None:
    noticesCollection = database['notices']
    
async def createNotices(scapedData: list[str]) -> dict:
    try:
        index = 1
        created = False
        while index <= 10:
            noticeDetails = scapedData[index]
            title, publishedBy, date = noticeDetails
            notice = {
            'NoticeId' : index,
            'Title' : title,
            'Date' : date,
            'Published_By' :publishedBy
            }
            
            noticesCollection.insert_one(notice)
            index += 1
            created = True if index == 11 else False
            
        return {createNotices.__name__ : created, 'NoticeId' : index - 1}
            
    except Exception as error:
        logging.error(f"{createNotices.__name__}: {str(error)}") 
    
async def updateNotices(index: int, scapedData: dict) -> dict:
    try:
        while index >= 1:
            title, publishedBy, date = scapedData[index]            
            noticesCollection.find_one_and_update(
            {'NoticeId' : index}, 
            {'$set' : {'Title': title, 'Date' : date, 'Published_By' : publishedBy}}
            )
            
            index -= 1

    except Exception as error:
        logging.error(f"{updateNotices.__name__}: {str(error)}")
    
async def compareNotices(scapedData: dict) -> dict:
    try:
        index = 10
        allMatched = False
        scrapedTitle = scapedData[index][0]
        
        while index >= 1:
            scrapedTitle = scapedData[index][0]
            
            isTitleExist = noticesCollection.find_one(
            {"Title" : scrapedTitle}, {'NoticeId': 1}
    )       
            
            if isTitleExist is None:
                break
            
            index -= 1
            allMatched = True if index == 0 else False
        
        return {compareNotices.__name__ : allMatched, 'NoticeId' : index}
        
    except Exception as error:
        logging.error(f"{compareNotices.__name__}: {str(error)}")
        
async def processNotices(scapedData: dict) -> dict:
    totalNotices = noticesCollection.count_documents({})
    if totalNotices == 0:
        createResult = await createNotices(scapedData)
        messageToSend = createResult['NoticeId']
        return messageToSend
    
    elif totalNotices == 10:
        compareResult = await compareNotices(scapedData)
        allMatched, totalMessages = compareResult['compareNotices'], compareResult['NoticeId']
        if not allMatched:
            await updateNotices(10, scapedData)    
        messageToSend = totalMessages if not allMatched else 0         
        return messageToSend
    else:
        logging.error(f'Duplicate data in the Document')
        
async def getNotices(index: int) -> dict:
    noticeData = noticesCollection.find_one(
    {"NoticeId" : index}, 
    {'_id' : 0, 'NoticeId' : 1, 'Title' : 1, 'Date': 1, 'Published_By' : 1}
)
    return noticeData
