from dotenv import load_dotenv
from os import getenv

load_dotenv()
DB_URL: str = getenv('DB_URL')
WHATSAPP_NO: int = getenv('WHATSAPP_NO')
COUNTRY_CODE: str = getenv('COUNTRY_CODE')
TOKEN: str = getenv('TOKEN')
CHAT_ID: int = getenv('CHAT_ID')
GROUP_NAME: str = getenv('GROUP_NAME')
IS_QR: bool = getenv('IS_QR', False)
PORT: int = getenv('PORT', 8010)

#======================================#
SEARCH_BOX = '//div[@contenteditable="true" and @data-tab="3"]'
SEND_BTN = '//span[@data-icon="send"]'
ATTACH_BTN = '//div[@title="Attach"]'
DOWN_CONTEXT_BTN = '[data-icon="down-context"]'
REPLY_BTN = 'div[role="button"][aria-label="Reply"]'
CAPTION_AREA = 'div[role="textbox"][aria-label="Add a caption"]'
FILE_UPLOAD = '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]'