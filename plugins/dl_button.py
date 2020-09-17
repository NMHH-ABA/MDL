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
from helper_funcs.display_progress import progress_for_pyrogram, humanbytes, TimeFormatter
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
# https://stackoverflow.com/a/37631799/4723940
from PIL import Image

from urllib.request import urlopen
from urllib.request import urlretrieve
import random


async def ddl_call_back(bot, update):
    shomar = random.randint(1, 10000)
    logger.info(update)
    cb_data = update.data
    if "=" in cb_data:
        tg_send_type,vttype,clipid = cb_data.split("=")
        thumb_image_path = Config.DOWNLOAD_LOCATION + \
                           "/" + str(shomar) + ".jpg"
        if vttype ==  "clip":
            youtube_dl_url = "https://d2rwmwucnr0d10.cloudfront.net/videoClips/" + clipid + ".mp4"
            link = "https://dak1vd5vmi7x6.cloudfront.net/api/v1/publicrole/showmodule/videoclipdetails?id=" + clipid
            f = urlopen(link)
            myfile = f.read()
            jconv = json.loads(myfile)
            details = jconv["details"]
            description = "@BachehayeManoto\n" + details["videoclipDescription"]
            videoCliplandscapeImgIxUrl = details["videoCliplandscapeImgIxUrl"]
            custom_file_name = "@BachehayeManoto " + details["videoclipTitle"] + ".mp4"
            try:
                urlretrieve(videoCliplandscapeImgIxUrl,
                            thumb_image_path)
            except:
                pass
        if vttype ==  "video":
            link = "https://dak1vd5vmi7x6.cloudfront.net/api/v1/publicrole/showmodule/episodedetails?id=" + clipid
            f = urlopen(link)
            myfile = f.read()
            jconv = json.loads(myfile)
            details = jconv["details"]
            description = "@BachehayeManoto\n" + details["episodeShareDescription"]
            videoCliplandscapeImgIxUrl = details["episodelandscapeImgIxUrl"]
            custom_file_name = "@BachehayeManoto " + details["formattedEpisodeTitle"] + ".mp4"
            youtube_dl_url = details["videoDownloadUrl"]
            try:
                urlretrieve(videoCliplandscapeImgIxUrl,
                            thumb_image_path)
            except:
                pass
        if vttype ==  "news":
            link = "https://dr905zevbmkvz.cloudfront.net/api/v1/publicrole/newsmodule/banner"
            f = urlopen(link)
            myfile = f.read()
            jconv = json.loads(myfile)
            details = jconv["details"]
            description = "@BachehayeManoto\n" + details["headline"] + details["strapline1"]
            custom_file_name = "@BachehayeManoto " + details["headline"] + " " + details["strapline1"] + ".mp4"
            videoCliplandscapeImgIxUrl = details["landscapeImgIxUrl"]

            link2 = "https://dak1vd5vmi7x6.cloudfront.net/api/v1/publicrole/newsmodule/newsvideo"
            f2 = urlopen(link2)
            myfile2 = f2.read()
            jconv2 = json.loads(myfile2)
            details2 = jconv2["details"]
            youtube_dl_url = details2["videoDownloadUrl"]
            try:
                urlretrieve(videoCliplandscapeImgIxUrl,
                            thumb_image_path)
            except:
                pass
        if vttype == "newsclip":
            youtube_dl_url = "https://d2rwmwucnr0d10.cloudfront.net/news/" + clipid + ".mp4"
            link = "https://dr905zevbmkvz.cloudfront.net/api/v1/publicrole/newsmodule/details?id=" + clipid
            f = urlopen(link)
            myfile = f.read()
            jconv = json.loads(myfile)
            details = jconv["details"]
            authorName = details["authorName"]
            shortDescription = details["shortDescription"]
            newsContent = details["newsContent"]
            description = "@BachehayeManoto\n" + "<b>" + authorName + "</b>" + "\n" + shortDescription + newsContent
            if len(description) > 1024:
                description = "@BachehayeManoto\n" + "*" + authorName + "*" + shortDescription
            videoCliplandscapeImgIxUrl = details["landscapeImgIxUrl"]
            custom_file_name = "@BachehayeManoto " + details["newsTitle"] + ".mp4"
            try:
                urlretrieve(videoCliplandscapeImgIxUrl,
                            thumb_image_path)
            except:
                pass
        youtube_dl_format = "0"
        youtube_dl_ext = "mp4"
        start = datetime.now()
        await bot.edit_message_text(
            text="در حال دانلود ...",
            chat_id=update.message.chat.id,
            message_id=update.message.message_id
        )
        tmp_directory_for_each_user = Config.DOWNLOAD_LOCATION + "/" + str(shomar)
        if not os.path.isdir(tmp_directory_for_each_user):
            os.makedirs(tmp_directory_for_each_user)
        download_directory = tmp_directory_for_each_user + "/" + custom_file_name
        command_to_exec = []
        async with aiohttp.ClientSession() as session:
            c_time = time.time()
            try:
                await download_coroutine(
                    bot,
                    session,
                    youtube_dl_url,
                    download_directory,
                    update.message.chat.id,
                    update.message.message_id,
                    c_time
                )
            except asyncio.TimeOutError:
                await bot.edit_message_text(
                    text=Translation.SLOW_URL_DECED,
                    chat_id=update.message.chat.id,
                    message_id=update.message.message_id
                )
                return False
        if os.path.exists(download_directory):
            end_one = datetime.now()
            await bot.edit_message_text(
                text="در حال آپلود ...",
                chat_id=update.message.chat.id,
                message_id=update.message.message_id
            )
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
                    text=Translation.RCHD_TG_API_LIMIT,
                    message_id=update.message.message_id
                )
            else:
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
                if tg_send_type == "file":
                    await bot.send_document(
                        chat_id=update.message.chat.id,
                        document=download_directory,
                        thumb=thumb_image_path,
                        caption=description,
                        # reply_markup=reply_markup,
                        reply_to_message_id=update.message.message_id,
                        parse_mode="HTML",
                        progress=progress_for_pyrogram,
                        progress_args=(
                            "درحال آپلود ...",
                            update.message,
                            start_time
                        )
                    )
                elif tg_send_type == "video":
                    await bot.send_video(
                        chat_id=update.message.chat.id,
                        video=download_directory,
                        caption=description,
                        duration=duration,
                        width=width,
                        height=height,
                        supports_streaming=True,
                        # reply_markup=reply_markup,
                        thumb=thumb_image_path,
                        reply_to_message_id=update.message.message_id,
                        parse_mode="HTML",
                        progress=progress_for_pyrogram,
                        progress_args=(
                            "درحال آپلود ...",
                            update.message,
                            start_time
                        )
                    )
                else:
                    logger.info("Did this happen? :\\")
                end_two = datetime.now()
                try:
                    os.remove(download_directory)
                    os.remove(thumb_image_path)
                except:
                    pass
                time_taken_for_download = (end_one - start).seconds
                time_taken_for_upload = (end_two - end_one).seconds
                await bot.edit_message_text(
                    text="Downloaded in {} seconds. \nUploaded in {} seconds.".format(time_taken_for_download,time_taken_for_upload),
                    chat_id=update.message.chat.id,
                    message_id=update.message.message_id,
                    disable_web_page_preview=True
                )
        else:
            await bot.edit_message_text(
                text=Translation.NO_VOID_FORMAT_FOUND.format("Incorrect Link"),
                chat_id=update.message.chat.id,
                message_id=update.message.message_id,
                disable_web_page_preview=True
            )
    if "+" in cb_data:
        tg_send_type, youtube_dl_format, youtube_dl_ext = cb_data.split("+")
        thumb_image_path = Config.DOWNLOAD_LOCATION + \
                           "/" + str(update.from_user.id) + ".jpg"
        youtube_dl_url = update.message.reply_to_message.text
        custom_file_name = os.path.basename(youtube_dl_url)
        if "|" in youtube_dl_url:
            url_parts = youtube_dl_url.split("|")
            if len(url_parts) == 2:
                youtube_dl_url = url_parts[0]
                custom_file_name = url_parts[1]
            else:
                for entity in update.message.reply_to_message.entities:
                    if entity.type == "text_link":
                        youtube_dl_url = entity.url
                    elif entity.type == "url":
                        o = entity.offset
                        l = entity.length
                        youtube_dl_url = youtube_dl_url[o:o + l]
            if youtube_dl_url is not None:
                youtube_dl_url = youtube_dl_url.strip()
            if custom_file_name is not None:
                custom_file_name = custom_file_name.strip()
            # https://stackoverflow.com/a/761825/4723940
            logger.info(youtube_dl_url)
            logger.info(custom_file_name)
        else:
            for entity in update.message.reply_to_message.entities:
                if entity.type == "text_link":
                    youtube_dl_url = entity.url
                elif entity.type == "url":
                    o = entity.offset
                    l = entity.length
                    youtube_dl_url = youtube_dl_url[o:o + l]
        description = "@BachehayeManoto"
        custom_file_name = custom_file_name + ".mp4"
        if "FullHD" in custom_file_name:
            description = "@BachehayeManoto FullHD"
        if "HD" in custom_file_name:
            description = "@BachehayeManoto HD"
        if "Mobile" in custom_file_name:
            description = "@BachehayeManoto\nنسخه کم حجم مناسب موبایل"
        start = datetime.now()
        await bot.edit_message_text(
            text=Translation.DOWNLOAD_START,
            chat_id=update.message.chat.id,
            message_id=update.message.message_id
        )
        tmp_directory_for_each_user = Config.DOWNLOAD_LOCATION + "/" + str(update.from_user.id)
        if not os.path.isdir(tmp_directory_for_each_user):
            os.makedirs(tmp_directory_for_each_user)
        download_directory = tmp_directory_for_each_user + "/" + custom_file_name
        command_to_exec = []
        async with aiohttp.ClientSession() as session:
            c_time = time.time()
            try:
                await download_coroutine(
                    bot,
                    session,
                    youtube_dl_url,
                    download_directory,
                    update.message.chat.id,
                    update.message.message_id,
                    c_time
                )
            except asyncio.TimeOutError:
                await bot.edit_message_text(
                    text=Translation.SLOW_URL_DECED,
                    chat_id=update.message.chat.id,
                    message_id=update.message.message_id
                )
                return False
        if os.path.exists(download_directory):
            end_one = datetime.now()
            await bot.edit_message_text(
                text=Translation.UPLOAD_START,
                chat_id=update.message.chat.id,
                message_id=update.message.message_id
            )
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
                    text=Translation.RCHD_TG_API_LIMIT,
                    message_id=update.message.message_id
                )
            else:
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
                try:
                    os.remove(download_directory)
                    os.remove(thumb_image_path)
                except:
                    pass
                time_taken_for_download = (end_one - start).seconds
                time_taken_for_upload = (end_two - end_one).seconds
                await bot.edit_message_text(
                    text=Translation.AFTER_SUCCESSFUL_UPLOAD_MSG_WITH_TS.format(time_taken_for_download,
                                                                                time_taken_for_upload),
                    chat_id=update.message.chat.id,
                    message_id=update.message.message_id,
                    disable_web_page_preview=True
                )
        else:
            await bot.edit_message_text(
                text=Translation.NO_VOID_FORMAT_FOUND.format("Incorrect Link"),
                chat_id=update.message.chat.id,
                message_id=update.message.message_id,
                disable_web_page_preview=True
            )


async def download_coroutine(bot, session, url, file_name, chat_id, message_id, start):
    downloaded = 0
    display_message = ""
    async with session.get(url, timeout=Config.PROCESS_MAX_TIMEOUT) as response:
        total_length = int(response.headers["Content-Length"])
        content_type = response.headers["Content-Type"]
        if "text" in content_type and total_length < 500:
            return await response.release()
        await bot.edit_message_text(
            chat_id,
            message_id,
            text="""درحال دانلود ...
File Size: {}""".format(humanbytes(total_length))
        )
        with open(file_name, "wb") as f_handle:
            while True:
                chunk = await response.content.read(Config.CHUNK_SIZE)
                if not chunk:
                    break
                f_handle.write(chunk)
                downloaded += Config.CHUNK_SIZE
                now = time.time()
                diff = now - start
                if round(diff % 5.00) == 0 or downloaded == total_length:
                    percentage = downloaded * 100 / total_length
                    speed = downloaded / diff
                    elapsed_time = round(diff) * 1000
                    time_to_completion = round(
                        (total_length - downloaded) / speed) * 1000
                    estimated_total_time = elapsed_time + time_to_completion
                    try:
                        current_message = """**در حال دانلود ...**
File Size: {}
Downloaded: {}
ETA: {}""".format(
    humanbytes(total_length),
    humanbytes(downloaded),
    TimeFormatter(estimated_total_time)
)
                        if current_message != display_message:
                            await bot.edit_message_text(
                                chat_id,
                                message_id,
                                text=current_message
                            )
                            display_message = current_message
                    except Exception as e:
                        logger.info(str(e))
                        pass
        return await response.release()
