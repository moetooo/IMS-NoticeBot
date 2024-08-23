from dotenv import load_dotenv
from os import getenv

load_dotenv()

WHATSAPP_NO: int = getenv('WHATSAPP_NO', 0)
COUNTRY_CODE: str = getenv('COUNTRY_CODE', None)
DB_URL: str = getenv('DB_URL')
TOKEN: str = getenv('TOKEN')
LOG_CHAT_ID: int = getenv('LOG_CHAT_ID')
CHAT_NAME_1: str = getenv('CHAT_NAME_1', None)
CHAT_NAME_2: str = getenv('CHAT_NAME_2', None)
CHAT_NAME_3: str = getenv('CHAT_NAME_3', None)
PORT: int = getenv('PORT', 8010)
IS_QR: bool = getenv('IS_QR', False)

#======================================#
ATTACH_BTN = '//div[@title="Attach"]'
CAPTION_AREA = 'div[role="textbox"][aria-label="Add a caption"]'
DOWN_CONTEXT_BTN = '[data-icon="down-context"]'
FILE_UPLOAD = '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]'
REPLY_BTN = 'div[role="button"][aria-label="Reply"]'
SEARCH_BOX = '//div[@aria-label="Search" and @role="textbox"]'
SEND_BTN = '//span[@data-icon="send"]'