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

@pyrogram.Client.on_message(pyrogram.Filters.regex(pattern=".*convert.*"))
async def echo(bot, update):
    cb_data = update.text
    # youtube_dl extractors
    convert, youtube_dl_url, custom_file_name = cb_data.split("|")
    await bot.send_message(
        text=Translation.DOWNLOAD_START,
        chat_id=update.chat.id,
        reply_to_message_id=update.message_id,
    )
    tg_send_type = "file"
    description = "@BachehayeManoto\nنسخه کم حجم مناسب موبایل"
    tmp_directory_for_each_user = Config.DOWNLOAD_LOCATION + "/" + str(update.from_user.id)
    if not os.path.isdir(tmp_directory_for_each_user):
        os.makedirs(tmp_directory_for_each_user)
    download_directory = tmp_directory_for_each_user + "/" + custom_file_name
    upload_directory = tmp_directory_for_each_user + "/upload/" + custom_file_name
    command_to_exec = []
    command_to_exec = [
        "youtube-dl",
        "-c",
        "--max-filesize", str(Config.TG_MAX_FILE_SIZE),
        "--embed-subs",
        "-f", "best[height=720]",
        "--hls-prefer-ffmpeg", youtube_dl_url,
        "-o", download_directory
    ]
    command_to_exec.append("--no-warnings")
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
        #logger.info(t_response)
        end_one = datetime.now()
        time_taken_for_download = (end_one - start).seconds
        file_size = Config.TG_MAX_FILE_SIZE + 1
        try:
            file_size = os.stat(download_directory).st_size
        except :
            pass
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
            command_to_exec = []
            command_to_exec = [
                "ffmpeg",
                "-i", download_directory,
                #"-preset", "slow",
                #"-codec:a", "libfdk_aac",
                #"-b:a", "128k",
                #"-codec:v", "libx264",
                #"-pix_fmt", "yuv420p",
                #"-b:v", "250k",
                #"-minrate","200k",
                #"-minrate", "200k",
                #"-bufsize", "500k",
                #"-vf", "scale=-1:180",
                "-s","320x180",
                "-c:a","copy",
                upload_directory
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
            if t_response:
                start_time = time.time()
                # try to upload file
                if tg_send_type == "file":
                    await bot.send_document(
                        chat_id=update.chat.id,
                        document=upload_directory,
                        #thumb=thumb_image_path,
                        caption=description,
                        parse_mode="HTML",
                        # reply_markup=reply_markup,
                        reply_to_message_id=update.message_id,
                        progress=progress_for_pyrogram,
                        progress_args=(
                            Translation.UPLOAD_START,
                            update,
                            start_time
                        )
                    )
                else:
                    logger.info("Did this happen? :\\")
                end_two = datetime.now()
                time_taken_for_upload = (end_two - end_one).seconds
                try:
                    shutil.rmtree(tmp_directory_for_each_user)
                except:
                    pass
                await bot.edit_message_text(
                    text=Translation.AFTER_SUCCESSFUL_UPLOAD_MSG_WITH_TS.format(time_taken_for_download,
                                                                                time_taken_for_upload),
                    chat_id=update.chat.id,
                    message_id=update.message_id + 1,
                    disable_web_page_preview=True
                )
