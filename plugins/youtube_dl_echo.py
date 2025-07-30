#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K | X-Noid

import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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

# Removed lk21 import and bypass-related code completely

# Simple URL validation function
def is_valid_url(url):
    if not url:
        return False
    # Only allow http or https URLs
    if not (url.startswith("http://") or url.startswith("https://")):
        return False
    return True


@pyrogram.Client.on_message(pyrogram.filters.regex(pattern=".*http.*"))
async def echo(bot: Client, update: Message):
    if update.from_user.id not in Config.AUTH_USERS:
        return

    logger.info(f"Received message from user {update.from_user.id}")

    url = update.text
    youtube_dl_username = None
    youtube_dl_password = None
    file_name = None
    folder = f'./lk21/{update.from_user.id}/'

    # bypass logic removed - no lk21 usage

    # Proceed directly to youtube-dl/yt-dlp handling block

    if "|" in url:
        url_parts = url.split("|")
        if len(url_parts) == 2:
            url = url_parts[0].strip()
            file_name = url_parts[1].strip()
        elif len(url_parts) == 4:
            url = url_parts[0].strip()
            file_name = url_parts[1].strip()
            youtube_dl_username = url_parts[2].strip()
            youtube_dl_password = url_parts[3].strip()
        else:
            for entity in update.entities:
                if entity.type == "text_link":
                    url = entity.url
                elif entity.type == "url":
                    o = entity.offset
                    l = entity.length
                    url = url[o:o + l]
    else:
        for entity in update.entities:
            if entity.type == "text_link":
                url = entity.url
            elif entity.type == "url":
                o = entity.offset
                l = entity.length
                url = url[o:o + l]

    if not is_valid_url(url):
        await bot.send_message(
            chat_id=update.chat.id,
            text="Invalid or unsupported URL provided. Please send a valid HTTP/HTTPS URL.",
            reply_to_message_id=update.id)
        return

    command_to_exec = [
        "yt-dlp",
        "--no-warnings",
        "--youtube-skip-dash-manifest",
        "-j",
        url
    ]

    if Config.HTTP_PROXY != "":
        command_to_exec.extend(["--proxy", Config.HTTP_PROXY])

    if youtube_dl_username is not None:
        command_to_exec.extend(["--username", youtube_dl_username])
    if youtube_dl_password is not None:
        command_to_exec.extend(["--password", youtube_dl_password])

    try:
        process = await asyncio.create_subprocess_exec(
            *command_to_exec,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
    except Exception as e:
        logger.error(f"Error running yt-dlp process: {e}")
        await bot.send_message(
            chat_id=update.chat.id,
            text=f"Process error: {e}",
            reply_to_message_id=update.id
        )
        return

    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()

    if e_response and "nonnumeric port" not in e_response:
        error_message = e_response.replace(
            "please report this issue on https://yt-dl.org/bug . Make sure you are using the latest version; see  https://yt-dl.org/update  on how to update. Be sure to call youtube-dl with the --verbose flag and include its complete output.",
            "")
        if "This video is only available for registered users." in error_message:
            error_message += Translation.SET_CUSTOM_USERNAME_PASSWORD
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.NO_VOID_FORMAT_FOUND.format(str(error_message)),
            reply_to_message_id=update.id,
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True
        )
        return False

    # You can continue with rest of yt-dlp processing here if needed

