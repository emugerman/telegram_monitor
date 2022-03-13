import argparse
import os
import time
import traceback
import json
import asyncio
import uuid
import platform
import pytesseract
import ntpath
import sys

from PIL import Image
from pathlib import Path
from telethon import TelegramClient, events, errors
from logging.config import fileConfig
import logging.handlers
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '../..')))

Path("log").mkdir(parents=True, exist_ok=True)
Path("files").mkdir(parents=True, exist_ok=True)
Path("conf").mkdir(parents=True, exist_ok=True)

# Set binary location for OCR, Need to install Tesseract OCR on the machine
if platform.system() == 'Windows':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

log_path = os.path.abspath(os.path.join(os.path.dirname( __file__ ))) + os.sep + 'conf' + os.sep + 'log_conf.ini'
fileConfig(log_path, disable_existing_loggers=False)
log = logging.getLogger(__name__)

class TelegramMonitor():
    def __init__(self):
        self.api_id = "your_api_id"
        self.api_hash = "your_api_hash"
        self.account_phone = "your_phone_number" # in the format of +97254....
        self.allowed_files = ('.png', '.jpg', '.jpeg')

    async def start_monitoring(self):

        client = TelegramClient(f"{'files' + os.sep + self.account_phone}", self.api_id, self.api_hash)
        await client.connect()

        if not await client.is_user_authorized():
            logging.info('Client is currently not logged in')
            await client.send_code_request(self.account_phone)

            try:
                await client.sign_in(phone=self.account_phone,code=input('Enter the code: '))
            except errors.rpcerrorlist.SessionPasswordNeededError:
                # Relevant for 2FA telegram account
                await client.sign_in(password=r'your_2fa_password')
            
            logging.info('logged in successfully')

        writer_lock = asyncio.Lock()

        @client.on(events.NewMessage)
        async def document_message(event):
            chat = await event.get_chat()
            sender = await event.get_sender()

            image_name = None
            image_path = None
            chat_text = None
            user_name = None
            group_name_value = None
            group_name_value_id = None
            message_id = None

            try:
                group_name = str(chat.title)
            except AttributeError:
                group_name = None

            try:
                group_name_value = chat.username
            except:
                group_name_value = None

            try:
                group_name_value_id = chat.id
            except:
                group_name_value_id = None

            try:
                message_id = event._message_id
            except:
                message_id = None

            if event.photo:
                image_path = await event.download_media(f"{'files' + os.sep}")

                if os.path.getsize(image_path) == 0 or not image_path.endswith(self.allowed_files):
                    os.remove(image_path)
                    image_path = None

                else:
                    try:
                        image_name = ntpath.basename(image_path)
                        image_name_with_hash = f"{uuid.uuid4().hex}_{image_name}"
                        os.rename(image_path, str(Path(image_path).parents[0]) + os.sep + image_name_with_hash)

                        # new name and path
                        image_name = image_name_with_hash
                        image_path = str(Path(image_path).parents[0]) + os.sep + image_name_with_hash
                    except:
                        image_name = None
                        image_path = None

            try:
                if sender.username:
                    user_name = sender.username
            except AttributeError:
                user_name = None

            if event.raw_text and len(event.raw_text) > 0:
                chat_text = str(event.raw_text)

            if chat_text or image_name:
                async with writer_lock:
                    doc = {}
                    doc["_images"] = image_name
                    try:
                        doc["image_ocr"] = pytesseract.image_to_string(Image.open(image_path)) if image_name else None
                    except pytesseract.TesseractNotFoundError:
                        doc["image_ocr"] = ''
                    doc["chat_text"] = chat_text
                    doc["chat_timestamp"] = event.date.strftime("%Y/%m/%d %H:%M:%S")
                    doc["group_name"] = group_name
                    doc["user_name"] = user_name

                    # Add url to the dict
                    if group_name_value and message_id:
                        doc["url"] = f"https://t.me/{group_name_value}/{message_id}"
                    elif group_name_value_id and message_id:
                        doc["url"] = f"https://t.me/c/{group_name_value_id}/{message_id}"

                    if doc["chat_text"] or doc["image_ocr"]:
                        log.info(doc)

        await client.run_until_disconnected()

if __name__=="__main__":
    try:
        log.info("Start running")

        monitor = TelegramMonitor()
        asyncio.run(monitor.start_monitoring())

    except Exception as e:
        log.critical(traceback.format_exc())
    finally:
        log.info("Finish running")