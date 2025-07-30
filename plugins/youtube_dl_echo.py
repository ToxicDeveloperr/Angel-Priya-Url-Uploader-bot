#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K | X-Noid

import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import urllib.parse
import filetype
import shutil
import time
import tldextract
import asyncio
import json
import math
import os
import requests
from PIL import Image

if bool(os.environ.get("WEBHOOK", False)):
    from sample_config import Config
else:
    from config import Config

from translation import Translation

import pyrogram
logging.getLogger("pyrogram").setLevel(logging.WARNING)
from helper_funcs.display_progress import humanbytes
from helper_funcs.help_uploadbot import DownLoadFile
from helper_funcs.display_progress import progress_for_pyrogram
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant
from pyrogram import Client, enums

def is_valid_direct_url(url):
    if not url:
        return False
    return url.startswith("http://") or url.startswith("https://")

@pyrogram.Client.on_message(pyrogram.filters.regex(pattern=".*http.*"))
async def echo(bot: Client, update: Message):
    if update.from_user.id not in Config.AUTH_USERS:
        return

    logger.info(update.from_user)

    url = update.text.strip()
    youtube_dl_username = None
    youtube_dl_password = None
    file_name = None
    folder = f'./downloads/{update.from_user.id}/'

    # Aggressive check: only direct links allowed
    if not is_valid_direct_url(url):
        await update.reply_text("Please provide a valid direct download link starting with http:// or https://")
        return

    # Prepare folder
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Attempt to get filename from url or user input
    if "|" in url:
        parts = url.split("|")
        if len(parts) >= 2:
            url = parts[0].strip()
            file_name = parts[1].strip()
            if len(parts) == 4:
                youtube_dl_username = parts[2].strip()
                youtube_dl_password = parts[3].strip()
        else:
            # fallback
            file_name = None
    else:
        file_name = None

    if not file_name:
        # Try to infer file name from url path
        path = urllib.parse.urlparse(url).path
        file_name = os.path.basename(path) or "file"

    # Full path for file download
    dldir = os.path.join(folder, file_name)

    # Download file with requests
    try:
        r = requests.get(url, stream=True, timeout=60)
        r.raise_for_status()
        with open(dldir, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    except Exception as e:
        await update.reply_text(f"Failed to download file: {str(e)}")
        shutil.rmtree(folder, ignore_errors=True)
        return

    # Detect file type for uploading
    try:
        file = filetype.guess(dldir)
        xfiletype = file.mime if file else None
    except Exception:
        xfiletype = None

    duration = None
    if xfiletype in ['video/mp4', 'video/x-matroska', 'video/webm', 'audio/mpeg']:
        metadata = extractMetadata(createParser(dldir))
        if metadata is not None:
            if metadata.has("duration"):
                duration = metadata.get('duration').seconds

    await update.reply_text("Uploading your file...")

    try:
        if xfiletype in ['video/mp4', 'video/x-matroska', 'video/webm']:
            await bot.send_video(
                chat_id=update.chat.id,
                video=dldir,
                caption=file_name,
                duration=duration,
                reply_to_message_id=update.id,
                progress=progress_for_pyrogram,
                progress_args=(Translation.UPLOAD_START, update, time.time())
            )
        elif xfiletype == 'audio/mpeg':
            await bot.send_audio(
                chat_id=update.chat.id,
                audio=dldir,
                caption=file_name,
                duration=duration,
                reply_to_message_id=update.id,
                progress=progress_for_pyrogram,
                progress_args=(Translation.UPLOAD_START, update, time.time())
            )
        else:
            await bot.send_document(
                chat_id=update.chat.id,
                document=dldir,
                caption=file_name,
                reply_to_message_id=update.id,
                progress=progress_for_pyrogram,
                progress_args=(Translation.UPLOAD_START, update, time.time())
            )
    except Exception as e:
        await update.reply_text(f"Failed to upload file: {str(e)}")
    finally:
        # Clean up
        shutil.rmtree(folder, ignore_errors=True)
