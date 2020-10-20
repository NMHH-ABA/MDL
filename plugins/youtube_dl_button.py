#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K

# the logging things
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import asyncio
import aiohttp
import json
import math
import os
import shutil
import time
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
from helper_funcs.display_progress import progress_for_pyrogram, humanbytes
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
# https://stackoverflow.com/a/37631799/4723940
from PIL import Image
from helper_funcs.help_Nekmo_ffmpeg import generate_screen_shots

from helper_funcs.display_progress import progress_for_pyrogram, humanbytes, TimeFormatter

from bs4 import BeautifulSoup
import requests
from urllib.request import urlopen
from urllib.request import urlretrieve
import random

async def youtube_dl_call_back(bot, update):
    shomar = random.randint(1, 10000)
    cb_data = update.data
    if "360P" in cb_data:
        youtube_dl_format = "best[height=360]"
    if "480P" in cb_data:
        youtube_dl_format = "best[height=480]"
    if "720P" in cb_data:
        youtube_dl_format = "best[height=720]"
    if "1080P" in cb_data:
        youtube_dl_format = "best[height=1080]"
    thumb_image_path = Config.DOWNLOAD_LOCATION + \
                       "/" + str(shomar) + ".jpg"
    intlurl = update.message.reply_to_message.text
    await bot.edit_message_text(
        text=Translation.DOWNLOAD_START,
        chat_id=update.message.chat.id,
        message_id=update.message.message_id
    )
    page = requests.get(intlurl)
    soup = BeautifulSoup(page.content, 'html.parser')
    soupstr = str(soup)
    if "clvod" in soupstr:
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

    if "https://embed.kwikmotion.com" in soupstr:
        first = soup.find(class_="main-container container-fluid")
        second = str(first.find(class_="region region-content"))
        # print(second)
        one = second.find("src=")
        two = second.find("?autoplay")
        three = second[one + 5:two]
        page2 = requests.get(three)
        soup2 = BeautifulSoup(page2.content, 'html.parser')
        output2 = str(soup2)
        G = output2.find("hls: ")
        H = output2.find("dash: ")
        youtube_dl_url = output2[G + 6:H - 20]
        J = output2.find("poster: ")
        K = output2.find("tracks: [")
        IMG = output2[J + 9:K - 20]
        M = output2.find('og:image"/><meta content=')
        N = output2.find('property="og:title')
        custom_file_name = output2[M + 27:N - 2]
    try:
        urlretrieve(IMG,
                    thumb_image_path)
    except:
        pass
    if "mp4/playlist.m3u8" in youtube_dl_url:
        await bot.edit_message_text(
            text="متاسفانه امکان دانلود این ویدیو وجود ندارد",
            chat_id=update.message.chat.id,
            message_id=update.message.message_id
        )
    if "smil/playlist.m3u8" in youtube_dl_url:
        tg_send_type = "video"
        description = custom_file_name
        custom_file_name = custom_file_name + ".mp4"
        tmp_directory_for_each_user = Config.DOWNLOAD_LOCATION + "/" + str(shomar)
        if not os.path.isdir(tmp_directory_for_each_user):
            os.makedirs(tmp_directory_for_each_user)
        download_directory = tmp_directory_for_each_user + "/" + custom_file_name
        command_to_exec = []
        command_to_exec = [
            "youtube-dl",
            "-c",
            "--max-filesize", str(Config.TG_MAX_FILE_SIZE),
            "-f", youtube_dl_format,
            "--hls-prefer-ffmpeg", youtube_dl_url,
            "-o", download_directory
        ]
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
                chat_id=update.message.chat.id,
                message_id=update.message.message_id,
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
                    chat_id=update.message.chat.id,
                    text=Translation.RCHD_TG_API_LIMIT.format(time_taken_for_download, humanbytes(file_size)),
                    message_id=update.message.message_id
                )
            else:
                is_w_f = False
                await bot.edit_message_text(
                    text=Translation.UPLOAD_START,
                    chat_id=update.message.chat.id,
                    message_id=update.message.message_id
                )
                # get the correct width, height, and duration for videos greater than 10MB
                # ref: message from @BotSupport
                width = 0
                height = 0
                duration = 0
                if tg_send_type != "file":
                    metadata = extractMetadata(createParser(download_directory))
                    if metadata is not None:
                        if metadata.has("duration"):
                            duration = metadata.get('duration').seconds
                # get the correct width, height, and duration for videos greater than 10MB
                if os.path.exists(thumb_image_path):
                    width = 0
                    height = 0
                    metadata = extractMetadata(createParser(thumb_image_path))
                    if metadata.has("width"):
                        width = metadata.get("width")
                    if metadata.has("height"):
                        height = metadata.get("height")
                    if tg_send_type == "vm":
                        height = width
                    # resize image
                    # ref: https://t.me/PyrogramChat/44663
                    # https://stackoverflow.com/a/21669827/4723940
                    Image.open(thumb_image_path).convert(
                        "RGB").save(thumb_image_path)
                    img = Image.open(thumb_image_path)
                    # https://stackoverflow.com/a/37631799/4723940
                    # img.thumbnail((90, 90))
                    if tg_send_type == "file":
                        img.resize((320, height))
                    else:
                        img.resize((90, height))
                    img.save(thumb_image_path, "JPEG")
                    # https://pillow.readthedocs.io/en/3.1.x/reference/Image.html#create-thumbnails
                else:
                    thumb_image_path = None
                start_time = time.time()
                # try to upload file
                if tg_send_type == "audio":
                    await bot.send_audio(
                        chat_id=update.message.chat.id,
                        audio=download_directory,
                        caption=description,
                        parse_mode="HTML",
                        duration=duration,
                        # performer=response_json["uploader"],
                        # title=response_json["title"],
                        # reply_markup=reply_markup,
                        thumb=thumb_image_path,
                        reply_to_message_id=update.message.reply_to_message.message_id,
                        progress=progress_for_pyrogram,
                        progress_args=(
                            Translation.UPLOAD_START,
                            update.message,
                            start_time
                        )
                    )
                elif tg_send_type == "file":
                    await bot.send_document(
                        chat_id=update.message.chat.id,
                        document=download_directory,
                        thumb=thumb_image_path,
                        caption=description,
                        parse_mode="HTML",
                        # reply_markup=reply_markup,
                        reply_to_message_id=update.message.reply_to_message.message_id,
                        progress=progress_for_pyrogram,
                        progress_args=(
                            Translation.UPLOAD_START,
                            update.message,
                            start_time
                        )
                    )
                elif tg_send_type == "vm":
                    await bot.send_video_note(
                        chat_id=update.message.chat.id,
                        video_note=download_directory,
                        duration=duration,
                        length=width,
                        thumb=thumb_image_path,
                        reply_to_message_id=update.message.reply_to_message.message_id,
                        progress=progress_for_pyrogram,
                        progress_args=(
                            Translation.UPLOAD_START,
                            update.message,
                            start_time
                        )
                    )
                elif tg_send_type == "video":
                    await bot.send_video(
                        chat_id=update.message.chat.id,
                        video=download_directory,
                        #caption=description,
                        parse_mode="HTML",
                        duration=duration,
                        width=width,
                        height=height,
                        supports_streaming=True,
                        # reply_markup=reply_markup,
                        thumb=thumb_image_path,
                        reply_to_message_id=update.message.reply_to_message.message_id,
                        progress=progress_for_pyrogram,
                        progress_args=(
                            Translation.UPLOAD_START,
                            update.message,
                            start_time
                        )
                    )
                else:
                    logger.info("Did this happen? :\\")
                end_two = datetime.now()
                time_taken_for_upload = (end_two - end_one).seconds
                try:
                    shutil.rmtree(tmp_directory_for_each_user)
                    os.remove(thumb_image_path)
                except:
                    pass
                await bot.edit_message_text(
                    text=Translation.AFTER_SUCCESSFUL_UPLOAD_MSG_WITH_TS.format(time_taken_for_download,
                                                                                time_taken_for_upload),
                    chat_id=update.message.chat.id,
                    message_id=update.message.message_id,
                    disable_web_page_preview=True
                )
    else:
        await bot.edit_message_text(
            text="لینک ارسالی اشتباه هست",
            chat_id=update.message.chat.id,
            message_id=update.message.message_id
        )
