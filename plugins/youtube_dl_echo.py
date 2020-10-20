#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K

# the logging things
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import asyncio
import json
import math
import os
import time
import shutil
from datetime import datetime

# the secret configuration specific things
if bool(os.environ.get("WEBHOOK", False)):
    from sample_config import Config
else:
    from config import Config

# the Strings used for this "thing"
from translation import Translation

import pyrogram
logging.getLogger("pyrogram").setLevel(logging.WARNING)

from helper_funcs.chat_base import TRChatBase
from helper_funcs.help_uploadbot import DownLoadFile
from helper_funcs.display_progress import progress_for_pyrogram, humanbytes
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
# https://stackoverflow.com/a/37631799/4723940
from PIL import Image
from helper_funcs.help_Nekmo_ffmpeg import generate_screen_shots

import random
from urllib.parse import unquote

@pyrogram.Client.on_message(pyrogram.Filters.regex(pattern=".*http.*"))
async def echo(bot, update):
    TRChatBase(update.from_user.id, update.text, "/echo")
    logger.info(update.from_user)
    url = update.text
    url = unquote(url)
    if "/ویدیو/" in url:
        inline_keyboard = []
        inline_keyboard.append([
            pyrogram.InlineKeyboardButton(
                "360P",
                callback_data=("360P").encode("UTF-8")
            ),
            pyrogram.InlineKeyboardButton(
                "480P",
                callback_data=("480P").encode("UTF-8")
            ),
            pyrogram.InlineKeyboardButton(
                "720P",
                callback_data=("720P").encode("UTF-8")
            ),
            pyrogram.InlineKeyboardButton(
                "1080P",
                callback_data=("1080P").encode("UTF-8")
            )
        ])
        reply_markup = pyrogram.InlineKeyboardMarkup(inline_keyboard)
        await bot.send_message(
            chat_id=update.chat.id,
            text=Translation.FORMAT_SELECTION.format(""),
            reply_markup=reply_markup,
            parse_mode="html",
            reply_to_message_id=update.message_id
        )
    else:
        await bot.send_message(
            text="لینک ارسالی اشتباه هست",
            chat_id=update.chat.id,
            reply_to_message_id=update.message_id
        )
