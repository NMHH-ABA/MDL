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
from bs4 import BeautifulSoup
import requests

@pyrogram.Client.on_message(pyrogram.Filters.regex(pattern=".*http.*"))
async def echo(bot, update):
    TRChatBase(update.from_user.id, update.text, "/echo")
    logger.info(update.from_user)
    url = update.text
    shomar = random.randint(1, 10000)
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    first = soup.find(class_="main-container container-fluid")
    second = first.find(class_="region region-content")
    desc = second.find(class_="field field-name-title field-type-ds field-label-hidden")
    custom_file_name = desc.find(class_="field-item even").get_text()
    output = str(second)
    A = output.find("https://clvod")
    B = output.find("m3u8")
    youtube_dl_url = output[A:B + 4]
    D = output.find("https://embed")
    E = output.find(".jpg")
    IMG = output[D:E + 4]
    try:
        urlretrieve(IMG,
                    thumb_image_path)
    except:
        pass
    if ".mp4/playlist.m3u8" in youtube_dl_url:
        await bot.send_message(
            text="امکان دانلود این ویدیو وجود ندارد",
            chat_id=update.chat.id,
            reply_to_message_id=update.message_id,
        )
    if ".smil/playlist.m3u8" in youtube_dl_url:
        await bot.send_message(
            text=Translation.DOWNLOAD_START,
            chat_id=update.chat.id,
            reply_to_message_id=update.message_id,
        )
        description = custom_file_name
        custom_file_name = custom_file_name + ".mp4"
        tmp_directory_for_each_user = Config.DOWNLOAD_LOCATION + "/" + str(shomar)
        if not os.path.isdir(tmp_directory_for_each_user):
            os.makedirs(tmp_directory_for_each_user)
        download_directory = tmp_directory_for_each_user + "/" + custom_file_name
        command_to_exec = []
        # command_to_exec = ["youtube-dl", "-f", youtube_dl_format, "--hls-prefer-ffmpeg", "--recode-video", "mp4", "-k", youtube_dl_url, "-o", download_directory]
        command_to_exec = [
            "youtube-dl",
            "-c",
            "--max-filesize", str(Config.TG_MAX_FILE_SIZE),
            "-f", "best[height=1080]",
            "--hls-prefer-ffmpeg", youtube_dl_url,
            "-o", download_directory
        ]
        command_to_exec.append("--no-warnings")
        # command_to_exec.append("--quiet")
        logger.info(command_to_exec)
        start = datetime.now()
        process = await asyncio.create_subprocess_exec(
            *command_to_exec,
            # stdout must a pipe to be accessible as process.stdout
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        # Wait for the subprocess to finish
        stdout, stderr = await process.communicate()
        e_response = stderr.decode().strip()
        t_response = stdout.decode().strip()
        logger.info(e_response)
        logger.info(t_response)
        ad_string_to_replace = "please report this issue on https://yt-dl.org/bug . Make sure you are using the latest version; see  https://yt-dl.org/update  on how to update. Be sure to call youtube-dl with the --verbose flag and include its complete output."
        if e_response and ad_string_to_replace in e_response:
            error_message = e_response.replace(ad_string_to_replace, "")
            await bot.edit_message_text(
                chat_id=update.chat.id,
                message_id=update.message_id + 1,
                text=error_message
            )
            return False
        if t_response:
            # logger.info(t_response)
            end_one = datetime.now()
            time_taken_for_download = (end_one - start).seconds
            file_size = Config.TG_MAX_FILE_SIZE + 1
            try:
                file_size = os.stat(download_directory).st_size
            except FileNotFoundError as exc:
                download_directory = os.path.splitext(download_directory)[0] + "." + "mkv"
                # https://stackoverflow.com/a/678242/4723940
                file_size = os.stat(download_directory).st_size
            if file_size > Config.TG_MAX_FILE_SIZE:
                await bot.edit_message_text(
                    chat_id=update.chat.id,
                    text=Translation.RCHD_TG_API_LIMIT.format(time_taken_for_download, humanbytes(file_size)),
                    message_id=update.message_id + 1
                )
            else:
                await bot.edit_message_text(
                    text=Translation.UPLOAD_START,
                    chat_id=update.chat.id,
                    message_id=update.message_id + 1
                )
                # get the correct width, height, and duration for videos greater than 10MB
                width = 0
                height = 0
                duration = 0
                metadata = extractMetadata(createParser(download_directory))
                if metadata is not None:
                    if metadata.has("duration"):
                        duration = metadata.get('duration').seconds
                start_time = time.time()
                # try to upload file
                await bot.send_video(
                    chat_id=update.chat.id,
                    video=download_directory,
                    caption=description,
                    parse_mode="HTML",
                    duration=duration,
                    width=320,
                    height=90,
                    supports_streaming=True,
                    # reply_markup=reply_markup,
                    thumb=thumb_image_path,
                    reply_to_message_id=update.message_id + 1,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Translation.UPLOAD_START,
                        update,
                        start_time
                    )
                )
                end_two = datetime.now()
                time_taken_for_upload = (end_two - end_one).seconds
                try:
                    shutil.rmtree(tmp_directory_for_each_user)
                except:
                    pass
                await bot.edit_message_text(
                    text="Downloaded in {} seconds. \nUploaded in {} seconds.".format(time_taken_for_download,
                                                                                      time_taken_for_upload),
                    chat_id=update.chat.id,
                    message_id=update.message_id + 1,
                    disable_web_page_preview=True
                )
