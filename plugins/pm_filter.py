import asyncio
import re
import ast
import math
from utils import get_shortlink
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from Script import script
import pyrogram
from database.connections_mdb import active_connection, all_connections, delete_connection, if_active, make_active, \
    make_inactive
from info import *
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from utils import get_size, is_subscribed, get_poster, temp, get_settings, save_group_settings, search_gagala
from database.users_chats_db import db
from database.ia_filterdb import Media, get_file_details, get_search_results
from database.filters_mdb import (
    del_all,
    find_filter,
    get_filters,
)
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
SPELL_CHECK = {}
FILTER_MODE = {}

@Client.on_message(filters.group & filters.text & filters.incoming)
async def give_filter(client, message):
    k = await manual_filters(client, message)
    if k == False:
        await auto_filter(client, message) 

@Client.on_message(filters.private & filters.text & filters.incoming)
async def pm_text(bot, message):
    content = message.text
    user = message.from_user.first_name
    user_id = message.from_user.id
    if content.startswith("/") or content.startswith("#"): return  # ignore commands and hashtags
    if user_id in ADMINS: return # ignore admins
    await message.reply_text("<b>ð If You Want Any Movie, Series Please Join Our Request Groups \n \n ð Request Group: [Click Here ð](https://t.me/+ZPpcbtCV204yYWU1)</b>")
    await bot.send_message(
        chat_id=LOG_CHANNEL,
        text=f"<b>#ðð_ððð\n\nNá´á´á´ : {user}\n\nID : {user_id}\n\nMá´ssá´É¢á´ : {content}</b>"
    )

@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    try:
        offset = int(offset)
    except:
        offset = 0
    search = BUTTONS.get(key)
    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
        return

    files, n_offset, total = await get_search_results(search, offset=offset, filter=True)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0

    if not files:
        return
    settings = await get_settings(query.message.chat.id)
    if settings['button']:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"[{get_size(file.file_size)}] {file.file_name}", 
                    url=await get_shortlink(f"https://telegram.dog/{temp.U_NAME}?start=files_{file.file_id}")
                ),
            ]
            for file in files
        ]
    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"[{get_size(file.file_size)}] {file.file_name}", 
                    url=await get_shortlink(f"https://telegram.dog/{temp.U_NAME}?start=files_{file.file_id}")
                ),
                InlineKeyboardButton(
                    text=f"[{get_size(file.file_size)}] {file.file_name}", 
                    url=await get_shortlink(f"https://telegram.dog/{temp.U_NAME}?start=files_{file.file_id}")
                ),
            ]
            for file in files
        ]
    try:
        if settings['auto_delete']:
            btn.insert(0, 
                [
                    InlineKeyboardButton(f'Info ð©', 'reqinfo'),
                    InlineKeyboardButton(f'Movie ð', 'minfo'),
                    InlineKeyboardButton(f'Series ð', 'sinfo')
                ]
            )

        else:
            btn.insert(0, 
                [
                    InlineKeyboardButton(f'Movie ð', 'minfo'),
                    InlineKeyboardButton(f'Series ð', 'sinfo')
                ]
            )
                
    except KeyError:
        grpid = await active_connection(str(message.from_user.id))
        await save_group_settings(grpid, 'auto_delete', True)
        settings = await get_settings(message.chat.id)
        if settings['auto_delete']:
            btn.insert(0, 
                [
                    InlineKeyboardButton(f'Info ð©', 'reqinfo'),
                    InlineKeyboardButton(f'Movie ð', 'minfo'),
                    InlineKeyboardButton(f'Series ð', 'sinfo')
                ]
            )

        else:
            btn.insert(0, 
                [
                    InlineKeyboardButton(f'Movie ð', 'minfo'),
                    InlineKeyboardButton(f'Series ð', 'sinfo')
                ]
            )

    if 0 < offset <= 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10
    if n_offset == 0:
        btn.append(
            [InlineKeyboardButton("â« ðððð", callback_data=f"next_{req}_{key}_{off_set}"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages")]
        )
    elif off_set is None:
        btn.append([InlineKeyboardButton("ðððð", callback_data="pages"), InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"), InlineKeyboardButton("ðððð âª", callback_data=f"next_{req}_{key}_{n_offset}")])
    else:
        btn.append(
            [
                InlineKeyboardButton("â« ðððð", callback_data=f"next_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"{math.ceil(int(offset)/10)+1} / {math.ceil(total/10)}", callback_data="pages"),
                InlineKeyboardButton("ðððð âª", callback_data=f"next_{req}_{key}_{n_offset}")
            ],
        )
    btn.insert(0, [
        InlineKeyboardButton("ð» How To Download ð»", url=f"https://t.me/RolexMoviesOX/55")
    ])
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()


@Client.on_callback_query(filters.regex(r"^spolling"))
async def advantage_spoll_choker(bot, query):
    _, user, movie_ = query.data.split('#')
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    if movie_ == "close_spellcheck":
        return await query.message.delete()
    movies = SPELL_CHECK.get(query.message.reply_to_message.id)
    if not movies:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    movie = movies[(int(movie_))]
    await query.answer(script.TOP_ALRT_MSG)
    k = await manual_filters(bot, query.message, text=movie)
    if k == False:
        files, offset, total_results = await get_search_results(movie, offset=0, filter=True)
        if files:
            k = (movie, files, offset, total_results)
            await auto_filter(bot, query, k)
        else:
            reqstr1 = query.from_user.id if query.from_user else 0
            reqstr = await bot.get_users(reqstr1)
            await bot.send_message(chat_id=LOG_CHANNEL, text=(script.NORSLTS.format(reqstr.id, reqstr.mention, movie)))
            k = await query.message.edit(script.MVE_NT_FND)
            await asyncio.sleep(10)
            await k.delete()

@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "gfiltersdeleteallconfirm":
        await del_allg(query.message, 'gfilters')
        await query.answer("Done !")
        return
    elif query.data == "gfiltersdeleteallcancel": 
        await query.message.reply_to_message.delete()
        await query.message.delete()
        await query.answer("Process Cancelled !")
        return
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Má´á´á´ sá´Êá´ I'á´ á´Êá´sá´É´á´ ÉªÉ´ Êá´á´Ê É¢Êá´á´á´!!", quote=True)
                    return await query.answer(MSG_ALRT)
            else:
                await query.message.edit_text(
                    "I'á´ É´á´á´ á´á´É´É´á´á´á´á´á´ á´á´ á´É´Ê É¢Êá´á´á´s!\nCÊá´á´á´ /connections á´Ê á´á´É´É´á´á´á´ á´á´ á´É´Ê É¢Êá´á´á´s",
                    quote=True
                )
                return await query.answer(MSG_ALRT)

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return await query.answer(MSG_ALRT)

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("Yá´á´ É´á´á´á´ á´á´ Êá´ GÊá´á´á´ Oá´¡É´á´Ê á´Ê á´É´ Aá´á´Ê Usá´Ê á´á´ á´á´ á´Êá´á´!", show_alert=True)
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("TÊá´á´'s É´á´á´ Òá´Ê Êá´á´!!", show_alert=True)
    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("DELETE", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("BACK", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"GÊá´á´á´ Ná´á´á´ : **{title}**\nGÊá´á´á´ ID : `{group_id}`",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return await query.answer(MSG_ALRT)
    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Cá´É´É´á´á´á´á´á´ á´á´ **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text('Sá´á´á´ á´ÊÊá´Ê á´á´á´á´ÊÊá´á´!!', parse_mode=enums.ParseMode.MARKDOWN)
        return await query.answer(MSG_ALRT)
    elif "disconnect" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"DÉªsá´á´É´É´á´á´á´á´á´ ÒÊá´á´ **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text(
                f"Sá´á´á´ á´ÊÊá´Ê á´á´á´á´ÊÊá´á´!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer(MSG_ALRT)
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Sá´á´á´á´ssÒá´ÊÊÊ á´á´Êá´á´á´á´ á´á´É´É´á´á´á´Éªá´É´ !"
            )
        else:
            await query.message.edit_text(
                f"Sá´á´á´ á´ÊÊá´Ê á´á´á´á´ÊÊá´á´!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer(MSG_ALRT)
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "TÊá´Êá´ á´Êá´ É´á´ á´á´á´Éªá´ á´ á´á´É´É´á´á´á´Éªá´É´s!! Cá´É´É´á´á´á´ á´á´ sá´á´á´ É¢Êá´á´á´s ÒÉªÊsá´.",
            )
            return await query.answer(MSG_ALRT)
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Yá´á´Ê á´á´É´É´á´á´á´á´á´ É¢Êá´á´á´ á´á´á´á´ÉªÊs ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
    if query.data.startswith("file"):
        clicked = query.from_user.id
        try:
            typed = query.message.reply_to_message.from_user.id
        except:
            typed = query.from_user.id
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('Ná´ sá´á´Ê ÒÉªÊá´ á´xÉªsá´.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"

        try:
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                await query.answer(url=f"https://telegram.dog/{temp.U_NAME}?start={ident}_{file_id}")
                return
            elif settings['botpm']:
                await query.answer(url=f"https://telegram.dog/{temp.U_NAME}?start={ident}_{file_id}")
                return
            else:
                await client.send_cached_media(
                    chat_id=query.from_user.id,
                    file_id=file_id,
                    caption=f_caption,
                    protect_content=True if ident == "filep" else False 
                )
                await query.answer('Check PM, I have sent files in pm', show_alert=True)
        except UserIsBlocked:
            await query.answer('You Are Blocked to use me !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://telegram.dog/{temp.U_NAME}?start={ident}_{file_id}")
        except Exception as e:
            await query.answer(url=f"https://telegram.dog/{temp.U_NAME}?start={ident}_{file_id}")
    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer("I Like Your Smartness, But Don't Be Oversmart Okay ð", show_alert=True)
            return
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"

        try:
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                if clicked == typed:
                    await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                    return
                else:
                    await query.answer(f"Há´Ê {query.from_user.first_name}, TÊÉªs Is Ná´á´ Yá´á´Ê Má´á´ Éªá´ Rá´Ç«á´á´sá´. Rá´Ç«á´á´sá´ Yá´á´Ê's !", show_alert=True)
            elif settings['botpm']:
                if clicked == typed:
                    await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                    return
                else:
                    await query.answer(f"Há´Ê {query.from_user.first_name}, TÊÉªs Is Ná´á´ Yá´á´Ê Má´á´ Éªá´ Rá´Ç«á´á´sá´. Rá´Ç«á´á´sá´ Yá´á´Ê's !", show_alert=True)
            else:
                if clicked == typed:
                    await client.send_cached_media(
                        chat_id=query.from_user.id,
                        file_id=file_id,
                        caption=f_caption,
                        protect_content=True if ident == "filep" else False,
                        reply_markup=InlineKeyboardMarkup(
                            [
                             [
                              InlineKeyboardButton('â¡MOVIÎS GáOUá®', url=f'https://t.me/+ZmoLctpXTo8yNjg9'),
                              InlineKeyboardButton('SÎáIÎS GáOUá®â¡', url=f'https://t.me/+68nCNDklgoZlODI1')
                           ],[
                              InlineKeyboardButton('ð¥ JOIÐ Uá®DÎTÎS CHÎÐÐÎL ð¥', url=CHNL_LNK)
                             ]
                            ]
                        )
                    )
                else:
                    await query.answer(f"Há´Ê {query.from_user.first_name}, TÊÉªs Is Ná´á´ Yá´á´Ê Má´á´ Éªá´ Rá´Ç«á´á´sá´. Rá´Ç«á´á´sá´ Yá´á´Ê's !", show_alert=True)
                await query.answer('CÊá´á´á´ PM, I Êá´á´ á´ sá´É´á´ ÒÉªÊá´s ÉªÉ´ PM', show_alert=True)
        except UserIsBlocked:
            await query.answer('UÉ´ÊÊá´á´á´ á´Êá´ Êá´á´ á´á´ÊÉ´ !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
        except Exception as e:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer("Já´ÉªÉ´ á´á´Ê Bá´á´á´-á´á´ á´Êá´É´É´á´Ê á´á´ÊÉ´! ð", show_alert=True)
            return
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('Ná´ sá´á´Ê ÒÉªÊá´ á´xÉªsá´.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption = f_caption
        if f_caption is None:
            f_caption = f"{title}"
        await query.answer()
        await client.send_cached_media(
            chat_id=query.from_user.id,
            file_id=file_id,
            caption=f_caption,
            protect_content=True if ident == 'checksubp' else False,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                  InlineKeyboardButton('Sá´á´á´á´Êá´ GÊá´á´á´', url=GRP_LNK),
                  InlineKeyboardButton('Uá´á´á´á´á´s CÊá´É´É´á´Ê', url=CHNL_LNK)
               ],[
                  InlineKeyboardButton("Bá´á´ Oá´¡É´á´Ê", url="t.me/MrperfectOffcial_bot")
                 ]
                ]
            )
        )
    elif query.data == "pages":
        await query.answer()

    elif query.data.startswith("opnsetgrp"):
        ident, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        st = await client.get_chat_member(grp_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and str(userid) not in ADMINS
        ):
            await query.answer("Yá´á´ Dá´É´'á´ Há´á´ á´ TÊá´ RÉªÉ¢Êá´s Tá´ Dá´ TÊÉªs !", show_alert=True)
            return
        title = query.message.chat.title
        settings = await get_settings(grp_id)
        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('FÉªÊá´á´Ê Bá´á´á´á´É´',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('SÉªÉ´É¢Êá´' if settings["button"] else 'Dá´á´ÊÊá´',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('FÉªÊá´ Sá´É´á´ Má´á´á´', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}'),
                    InlineKeyboardButton('Má´É´á´á´Ê Sá´á´Êá´' if settings["botpm"] else 'Aá´á´á´ Sá´É´á´',
                                         callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('PÊá´á´á´á´á´ Cá´É´á´á´É´á´',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('â OÉ´' if settings["file_secure"] else 'â OÒÒ',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Iá´á´Ê', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('â OÉ´' if settings["imdb"] else 'â OÒÒ',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Sá´á´ÊÊ CÊá´á´á´',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('â OÉ´' if settings["spell_check"] else 'â OÒÒ',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Wá´Êá´á´á´á´ MsÉ¢', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('â OÉ´' if settings["welcome"] else 'â OÒÒ',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Aá´á´á´-Dá´Êá´á´á´',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}'),
                    InlineKeyboardButton('10 MÉªÉ´s' if settings["auto_delete"] else 'â OÒÒ',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Aá´á´á´-FÉªÊá´á´Ê',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}'),
                    InlineKeyboardButton('â OÉ´' if settings["auto_ffilter"] else 'â OÒÒ',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_text(
                text=f"<b>CÊá´É´É¢á´ Yá´á´Ê Sá´á´á´ÉªÉ´É¢s Fá´Ê {title} As Yá´á´Ê WÉªsÊ â</b>",
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML
            )
            await query.message.edit_reply_markup(reply_markup)
        
    elif query.data.startswith("opnsetpm"):
        ident, grp_id = query.data.split("#")
        userid = query.from_user.id if query.from_user else None
        st = await client.get_chat_member(grp_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and str(userid) not in ADMINS
        ):
            await query.answer("Yá´á´ Dá´É´'á´ Há´á´ á´ TÊá´ RÉªÉ¢Êá´s Tá´ Dá´ TÊÉªs !", show_alert=True)
            return
        title = query.message.chat.title
        settings = await get_settings(grp_id)
        btn2 = [[
                 InlineKeyboardButton("CÊá´á´á´ PM", url=f"t.me/{temp.U_NAME}")
               ]]
        reply_markup = InlineKeyboardMarkup(btn2)
        await query.message.edit_text(f"<b>Yá´á´Ê sá´á´á´ÉªÉ´É¢s á´á´É´á´ Òá´Ê {title} Êá´s Êá´á´É´ sá´É´á´ á´á´ Êá´á´Ê PM</b>")
        await query.message.edit_reply_markup(reply_markup)
        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('FÉªÊá´á´Ê Bá´á´á´á´É´',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('SÉªÉ´É¢Êá´' if settings["button"] else 'Dá´á´ÊÊá´',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('FÉªÊá´ Sá´É´á´ Má´á´á´', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}'),
                    InlineKeyboardButton('Má´É´á´á´Ê Sá´á´Êá´' if settings["botpm"] else 'Aá´á´á´ Sá´É´á´',
                                         callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('PÊá´á´á´á´á´ Cá´É´á´á´É´á´',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('â OÉ´' if settings["file_secure"] else 'â OÒÒ',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Iá´á´Ê', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('â OÉ´' if settings["imdb"] else 'â OÒÒ',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Sá´á´ÊÊ CÊá´á´á´',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('â OÉ´' if settings["spell_check"] else 'â OÒÒ',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Wá´Êá´á´á´á´ MsÉ¢', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('â OÉ´' if settings["welcome"] else 'â OÒÒ',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Aá´á´á´-Dá´Êá´á´á´',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}'),
                    InlineKeyboardButton('10 MÉªÉ´s' if settings["auto_delete"] else 'â OÒÒ',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Aá´á´á´-FÉªÊá´á´Ê',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}'),
                    InlineKeyboardButton('â OÉ´' if settings["auto_ffilter"] else 'â OÒÒ',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await client.send_message(
                chat_id=userid,
                text=f"<b>CÊá´É´É¢á´ Yá´á´Ê Sá´á´á´ÉªÉ´É¢s Fá´Ê {title} As Yá´á´Ê WÉªsÊ â</b>",
                reply_markup=reply_markup,
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML,
                reply_to_message_id=query.message.id
            )

    elif query.data.startswith("show_option"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("UÉ´á´á´ á´ÉªÊá´ÊÊá´", callback_data=f"unavailable#{from_user}"),
                InlineKeyboardButton("Uá´Êá´á´á´á´á´", callback_data=f"uploaded#{from_user}")
             ],[
                InlineKeyboardButton("AÊÊá´á´á´Ê Aá´ á´ÉªÊá´ÊÊá´", callback_data=f"already_available#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton("VÉªá´á´¡ Sá´á´á´á´s", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Há´Êá´ á´Êá´ á´Êá´ á´á´á´Éªá´É´s !")
        else:
            await query.answer("Yá´á´ á´á´É´'á´ Êá´á´ á´ sá´ÒÒÉªá´Éªá´É´á´ ÊÉªÉ¢á´s á´á´ á´á´ á´ÊÉªs !", show_alert=True)
        
    elif query.data.startswith("unavailable"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("â ï¸ UÉ´á´á´ á´ÉªÊá´ÊÊá´ â ï¸", callback_data=f"unalert#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton("VÉªá´á´¡ Sá´á´á´á´s", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sá´á´ á´á´ UÉ´á´á´ á´ÉªÊá´ÊÊá´ !")
            try:
                await client.send_message(chat_id=int(from_user), text=f"<b>Há´Ê {user.mention}, Sá´ÊÊÊ Yá´á´Ê Êá´á´Ì¨á´á´sá´ Éªs á´É´á´á´ á´ÉªÊá´ÊÊá´. Sá´ á´á´Ê á´á´á´á´Êá´á´á´Ês á´á´É´'á´ á´á´Êá´á´á´ Éªá´.</b>", reply_markup=InlineKeyboardMarkup(btn2))
            except UserIsBlocked:
                await client.send_message(chat_id=int(SUPPORT_CHAT_ID), text=f"<b>Há´Ê {user.mention}, Sá´ÊÊÊ Yá´á´Ê Êá´á´Ì¨á´á´sá´ Éªs á´É´á´á´ á´ÉªÊá´ÊÊá´. Sá´ á´á´Ê á´á´á´á´Êá´á´á´Ês á´á´É´'á´ á´á´Êá´á´á´ Éªá´.\n\nNá´á´á´: TÊÉªs á´á´ssá´É¢á´ Éªs sá´É´á´ á´á´ á´ÊÉªs É¢Êá´á´á´ Êá´á´á´á´sá´ Êá´á´'á´ á´ ÊÊá´á´á´á´á´ á´Êá´ Êá´á´. Tá´ sá´É´á´ á´ÊÉªs á´á´ssá´É¢á´ á´á´ Êá´á´Ê PM, Má´sá´ á´É´ÊÊá´á´á´ á´Êá´ Êá´á´.</b>", reply_markup=InlineKeyboardMarkup(btn2))
        else:
            await query.answer("Yá´á´ á´á´É´'á´ Êá´á´ á´ sá´ÒÒÉªá´Éªá´É´á´ ÊÉªÉ¢á´s á´á´ á´á´ á´ÊÉªs !", show_alert=True)

    elif query.data.startswith("uploaded"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("â Uá´Êá´á´á´á´á´ â", callback_data=f"upalert#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton("VÉªá´á´¡ Sá´á´á´á´s", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sá´á´ á´á´ Uá´Êá´á´á´á´á´ !")
            try:
                await client.send_message(chat_id=int(from_user), text=f"<b>Há´Ê {user.mention}, Yá´á´Ê Êá´á´Ì¨á´á´sá´ Êá´s Êá´á´É´ á´á´Êá´á´á´á´á´ ÊÊ á´á´Ê á´á´á´á´Êá´á´á´Ês. KÉªÉ´á´ÊÊ sá´á´Êá´Ê á´É¢á´ÉªÉ´.</b>", reply_markup=InlineKeyboardMarkup(btn2))
            except UserIsBlocked:
                await client.send_message(chat_id=int(SUPPORT_CHAT_ID), text=f"<b>Há´Ê {user.mention}, Yá´á´Ê Êá´á´Ì¨á´á´sá´ Êá´s Êá´á´É´ á´á´Êá´á´á´á´á´ ÊÊ á´á´Ê á´á´á´á´Êá´á´á´Ês. KÉªÉ´á´ÊÊ sá´á´Êá´Ê á´É¢á´ÉªÉ´.\n\nNá´á´á´: TÊÉªs á´á´ssá´É¢á´ Éªs sá´É´á´ á´á´ á´ÊÉªs É¢Êá´á´á´ Êá´á´á´á´sá´ Êá´á´'á´ á´ ÊÊá´á´á´á´á´ á´Êá´ Êá´á´. Tá´ sá´É´á´ á´ÊÉªs á´á´ssá´É¢á´ á´á´ Êá´á´Ê PM, Má´sá´ á´É´ÊÊá´á´á´ á´Êá´ Êá´á´.</b>", reply_markup=InlineKeyboardMarkup(btn2))
        else:
            await query.answer("Yá´á´ á´á´É´'á´ Êá´á´ á´ sá´ÒÒÉªá´Éªá´É´á´ ÊÉªÉ¢á´s á´á´ á´á´ á´ÊÉªs !", show_alert=True)

    elif query.data.startswith("already_available"):
        ident, from_user = query.data.split("#")
        btn = [[
                InlineKeyboardButton("ð¢ AÊÊá´á´á´Ê Aá´ á´ÉªÊá´ÊÊá´ ð¢", callback_data=f"alalert#{from_user}")
              ]]
        btn2 = [[
                 InlineKeyboardButton("VÉªá´á´¡ Sá´á´á´á´s", url=f"{query.message.link}")
               ]]
        if query.from_user.id in ADMINS:
            user = await client.get_users(from_user)
            reply_markup = InlineKeyboardMarkup(btn)
            content = query.message.text
            await query.message.edit_text(f"<b><strike>{content}</strike></b>")
            await query.message.edit_reply_markup(reply_markup)
            await query.answer("Sá´á´ á´á´ AÊÊá´á´á´Ê Aá´ á´ÉªÊá´ÊÊá´ !")
            try:
                await client.send_message(chat_id=int(from_user), text=f"<b>Há´Ê {user.mention}, Yá´á´Ê Êá´á´Ì¨á´á´sá´ Éªs á´ÊÊá´á´á´Ê á´á´ á´ÉªÊá´ÊÊá´ á´É´ á´á´Ê Êá´á´'s á´á´á´á´Êá´sá´. KÉªÉ´á´ÊÊ sá´á´Êá´Ê á´É¢á´ÉªÉ´.</b>", reply_markup=InlineKeyboardMarkup(btn2))
            except UserIsBlocked:
                await client.send_message(chat_id=int(SUPPORT_CHAT_ID), text=f"<b>Há´Ê {user.mention}, Yá´á´Ê Êá´á´Ì¨á´á´sá´ Éªs á´ÊÊá´á´á´Ê á´á´ á´ÉªÊá´ÊÊá´ á´É´ á´á´Ê Êá´á´'s á´á´á´á´Êá´sá´. KÉªÉ´á´ÊÊ sá´á´Êá´Ê á´É¢á´ÉªÉ´.\n\nNá´á´á´: TÊÉªs á´á´ssá´É¢á´ Éªs sá´É´á´ á´á´ á´ÊÉªs É¢Êá´á´á´ Êá´á´á´á´sá´ Êá´á´'á´ á´ ÊÊá´á´á´á´á´ á´Êá´ Êá´á´. Tá´ sá´É´á´ á´ÊÉªs á´á´ssá´É¢á´ á´á´ Êá´á´Ê PM, Má´sá´ á´É´ÊÊá´á´á´ á´Êá´ Êá´á´.</b>", reply_markup=InlineKeyboardMarkup(btn2))
        else:
            await query.answer("Yá´á´ á´á´É´'á´ Êá´á´ á´ sá´ÒÒÉªá´Éªá´É´á´ ÊÉªÉ¢á´s á´á´ á´á´ á´ÊÉªs !", show_alert=True)

    elif query.data.startswith("alalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Há´Ê {user.first_name}, Your Request Is Already Available, Please Check Your Spelling And Follow [Request Tipsâ](https://t.me/TVSeriesCW/1378)", show_alert=True)
        else:
            await query.answer("Yá´á´ á´á´É´'á´ Êá´á´ á´ sá´ÒÒÉªá´Éªá´É´á´ ÊÉªÉ¢á´s á´á´ á´á´ á´ÊÉªs !", show_alert=True)

    elif query.data.startswith("upalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Há´Ê {user.first_name}, Your Request Is Uploadedâ¡, Type Again In Request Group", show_alert=True)
        else:
            await query.answer("Yá´á´ á´á´É´'á´ Êá´á´ á´ sá´ÒÒÉªá´Éªá´É´á´ ÊÉªÉ¢á´s á´á´ á´á´ á´ÊÉªs !", show_alert=True)
        
    elif query.data.startswith("unalert"):
        ident, from_user = query.data.split("#")
        if int(query.from_user.id) == int(from_user):
            user = await client.get_users(from_user)
            await query.answer(f"Hey {user.first_name}, Your Movie/Series Not Released Digitally/OTT â", show_alert=True)
        else:
            await query.answer("Yá´á´ á´á´É´'á´ Êá´á´ á´ sá´ÒÒÉªá´Éªá´É´á´ ÊÉªÉ¢á´s á´á´ á´á´ á´ÊÉªs !", show_alert=True)

    elif query.data == "reqinfo":
        await query.answer(text=script.REQINFO, show_alert=True)

    elif query.data == "minfo":
        await query.answer(text=script.MINFO, show_alert=True)

    elif query.data == "sinfo":
        await query.answer(text=script.SINFO, show_alert=True)

    elif query.data == "start":
        buttons = [[
                    InlineKeyboardButton('â á´á´á´ á´á´ á´á´ Êá´á´Ê É¢Êá´á´á´ â', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
        ], [
            InlineKeyboardButton('ð» á´ÊÉªá´á´ Êá´Êá´ á´á´ á´Êá´á´á´á´ á´É´á´ ÊÉªá´á´ á´ÊÉªs ð»', callback_data='source')
        ], [
            InlineKeyboardButton('á´á´á´ á´Êá´á´á´Ê ð', url='https://t.me/JonSnow11'),
            InlineKeyboardButton('á´Êá´á´á´ ð', callback_data='about')
                  ]]
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer(MSG_ALRT)

    elif query.data == "filters":
        buttons = [[
            InlineKeyboardButton('Má´É´á´á´Ê FIÊá´á´Ê', callback_data='manuelfilter'),
            InlineKeyboardButton('Aá´á´á´ FIÊá´á´Ê', callback_data='autofilter')
        ],[
            InlineKeyboardButton('â¸ Bá´á´á´', callback_data='help'),
            InlineKeyboardButton('GÊá´Êá´Ê FÉªÊá´á´Ês', callback_data='global_filters')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.HELP_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "global_filters":
        buttons = [[
            InlineKeyboardButton('â¸ Bá´á´á´', callback_data='filters')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.GFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    
    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('FIÊá´á´Ês', callback_data='filters'),
            InlineKeyboardButton('FÉªÊá´ Sá´á´Êá´', callback_data='store_file')
        ], [
            InlineKeyboardButton('Cá´É´É´á´á´á´Éªá´É´', callback_data='coct'),
            InlineKeyboardButton('Exá´Êá´ Má´á´s', callback_data='extra')
        ], [
            InlineKeyboardButton('Há´á´á´', callback_data='start'),
            InlineKeyboardButton('Sá´á´á´á´s', callback_data='stats')
        ]]
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.HELP_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "about":
        buttons = [[
            InlineKeyboardButton('Sá´á´á´á´Êá´ GÊá´á´á´', url=GRP_LNK),
            InlineKeyboardButton('Sá´á´Êá´á´ Cá´á´á´', callback_data='source')
        ],[
            InlineKeyboardButton('Há´á´á´', callback_data='start'),
            InlineKeyboardButton('CÊá´sá´', callback_data='close_data')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "source":
        buttons = [[
            InlineKeyboardButton('â¸ Bá´á´á´', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.SOURCE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "manuelfilter":
        buttons = [[
            InlineKeyboardButton('â¸ Bá´á´á´', callback_data='filters'),
            InlineKeyboardButton('Bá´á´á´á´É´s', callback_data='button')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.MANUELFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "button":
        buttons = [[
            InlineKeyboardButton('â¸ Bá´á´á´', callback_data='manuelfilter')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.BUTTON_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "autofilter":
        buttons = [[
            InlineKeyboardButton('â¸ Bá´á´á´', callback_data='filters')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.AUTOFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "coct":
        buttons = [[
            InlineKeyboardButton('â¸ Bá´á´á´', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CONNECTION_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "extra":
        buttons = [[
            InlineKeyboardButton('â¸ Bá´á´á´', callback_data='help'),
            InlineKeyboardButton('Aá´á´ÉªÉ´', callback_data='admin')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.EXTRAMOD_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    
    elif query.data == "store_file":
        buttons = [[
            InlineKeyboardButton('â¸ Bá´á´á´', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.FILE_STORE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    
    elif query.data == "admin":
        buttons = [[
            InlineKeyboardButton('â¸ Bá´á´á´', callback_data='extra')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ADMIN_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "stats":
        buttons = [[
            InlineKeyboardButton('â¸ Bá´á´á´', callback_data='help'),
            InlineKeyboardButton('â² Rá´ÒÊá´sÊ', callback_data='rfrsh')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "rfrsh":
        await query.answer("Fetching MongoDb DataBase")
        buttons = [[
            InlineKeyboardButton('â¸ Bá´á´á´', callback_data='help'),
            InlineKeyboardButton('â² Rá´ÒÊá´sÊ', callback_data='rfrsh')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    elif query.data == "owner_info":
            btn = [[
                    InlineKeyboardButton("â¸ Bá´á´á´", callback_data="start"),
                    InlineKeyboardButton("Cá´É´á´á´á´á´", url="t.me/MrperfectOffcial_bot")
                  ]]
            reply_markup = InlineKeyboardMarkup(btn)
            await query.message.edit_text(
                text=(script.OWNER_INFO),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )

    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        grpid = await active_connection(str(query.from_user.id))

        if str(grp_id) != str(grpid):
            await query.message.edit("Yá´á´Ê Aá´á´Éªá´ á´ Cá´É´É´á´á´á´Éªá´É´ Há´s Bá´á´É´ CÊá´É´É¢á´á´. Gá´ Tá´ /connections á´É´á´ á´Êá´É´É¢á´ Êá´á´Ê á´á´á´Éªá´ á´ á´á´É´É´á´á´á´Éªá´É´.")
            return await query.answer(MSG_ALRT)

        if status == "True":
            await save_group_settings(grpid, set_type, False)
        else:
            await save_group_settings(grpid, set_type, True)

        settings = await get_settings(grpid)

        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('FÉªÊá´á´Ê Bá´á´á´á´É´',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('SÉªÉ´É¢Êá´' if settings["button"] else 'Dá´á´ÊÊá´',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('FÉªÊá´ Sá´É´á´ Má´á´á´', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}'),
                    InlineKeyboardButton('Má´É´á´á´Ê Sá´á´Êá´' if settings["botpm"] else 'Aá´á´á´ Sá´É´á´',
                                         callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('PÊá´á´á´á´á´ Cá´É´á´á´É´á´',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('â OÉ´' if settings["file_secure"] else 'â OÒÒ',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Iá´á´Ê', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('â OÉ´' if settings["imdb"] else 'â OÒÒ',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Sá´á´ÊÊ CÊá´á´á´',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('â OÉ´' if settings["spell_check"] else 'â OÒÒ',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Wá´Êá´á´á´á´ MsÉ¢', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('â OÉ´' if settings["welcome"] else 'â OÒÒ',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Aá´á´á´-Dá´Êá´á´á´',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}'),
                    InlineKeyboardButton('10 MÉªÉ´s' if settings["auto_delete"] else 'â OÒÒ',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Aá´á´á´-FÉªÊá´á´Ê',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}'),
                    InlineKeyboardButton('â OÉ´' if settings["auto_ffilter"] else 'â OÒÒ',
                                         callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{str(grp_id)}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_reply_markup(reply_markup)
    await query.answer(MSG_ALRT)

    
async def auto_filter(client, msg, spoll=False):
    reqstr1 = msg.from_user.id if msg.from_user else 0
    reqstr = await client.get_users(reqstr1)
    if not spoll:
        message = msg
        settings = await get_settings(message.chat.id)
        if message.text.startswith("/"): return  # ignore commands
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if len(message.text) < 100:
            search = message.text
            files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)
            if not files:
                if settings["spell_check"]:
                    return await advantage_spell_chok(client, msg)
                else:
                    await client.send_message(chat_id=LOG_CHANNEL, text=(script.NORSLTS.format(reqstr.id, reqstr.mention, search)))
                    return
        else:
            return
    else:
        settings = await get_settings(msg.message.chat.id)
        message = msg.message.reply_to_message  # msg will be callback query
        search, files, offset, total_results = spoll
    pre = 'filep' if settings['file_secure'] else 'file'
    if settings["button"]:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"[{get_size(file.file_size)}] {file.file_name}", 
                    url=await get_shortlink(f"https://telegram.dog/{temp.U_NAME}?start=files_{file.file_id}")
                ),
            ]
            for file in files
        ]
    else:
        btn = [
            [
                InlineKeyboardButton(
                    text=f"[{get_size(file.file_size)}] {file.file_name}", 
                    url=await get_shortlink(f"https://telegram.dog/{temp.U_NAME}?start=files_{file.file_id}")
                ),
                InlineKeyboardButton(
                    text=f"[{get_size(file.file_size)}] {file.file_name}", 
                    url=await get_shortlink(f"https://telegram.dog/{temp.U_NAME}?start=files_{file.file_id}")
                ),
            ]
            for file in files
        ]

    try:
        if settings['auto_delete']:
            btn.insert(0, 
                [
                    InlineKeyboardButton(f'Info ð©', 'reqinfo'),
                    InlineKeyboardButton(f'Movie ð', 'minfo'),
                    InlineKeyboardButton(f'Series ð', 'sinfo')
                ]
            )

        else:
            btn.insert(0, 
                [
                    InlineKeyboardButton(f'Movie ð', 'minfo'),
                    InlineKeyboardButton(f'Series ð', 'sinfo')
                ]
            )
                
    except KeyError:
        grpid = await active_connection(str(message.from_user.id))
        await save_group_settings(grpid, 'auto_delete', True)
        settings = await get_settings(message.chat.id)
        if settings['auto_delete']:
            btn.insert(0, 
                [
                    InlineKeyboardButton(f'Info ð©', 'reqinfo'),
                    InlineKeyboardButton(f'Movie ð', 'minfo'),
                    InlineKeyboardButton(f'Series ð', 'sinfo')
                ]
            )

        else:
            btn.insert(0, 
                [
                    InlineKeyboardButton(f'Movie ð', 'minfo'),
                    InlineKeyboardButton(f'Series ð', 'sinfo')
                ]
            )

    btn.insert(0, [
        InlineKeyboardButton("â¼ï¸ How To Download âï¸", url=f"t.me/RolexMoviesOX/55")
    ])

    if offset != "":
        key = f"{message.chat.id}-{message.id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        btn.append(
            [InlineKeyboardButton("ðððð", callback_data="pages"), InlineKeyboardButton(text=f"1/{math.ceil(int(total_results)/10)}",callback_data="pages"), InlineKeyboardButton(text="ðððð âª",callback_data=f"next_{req}_{key}_{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton(text="ðð ðððð ððððð ððððððððð",callback_data="pages")]
        )
    imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    TEMPLATE = settings['template']
    if imdb:
        cap = TEMPLATE.format(
            query=search,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
    else:
        cap = f"<b><i> Hey {message.from_user.mention},âYour Search Results</b> â{search}âðð» </i>"
    if imdb and imdb.get('poster'):
        try:
            if message.chat.id == SUPPORT_CHAT_ID:
                await message.reply_text(f"<b>Há´Ê {message.from_user.mention}, {str(total_results)} Êá´sá´Êá´s á´Êá´ Òá´á´É´á´ ÉªÉ´ á´Ê á´á´á´á´Êá´sá´ Òá´Ê Êá´á´Ê á´Ì¨á´á´ÊÊ {search}. KÉªÉ´á´ÊÊ á´sá´ ÉªÉ´ÊÉªÉ´á´ sá´á´Êá´Ê á´Ê á´á´á´á´ á´ É¢Êá´á´á´ á´É´á´ á´á´á´ á´á´ á´s á´á´á´ÉªÉ´ á´á´ É¢á´á´ á´á´á´ Éªá´ ÒÉªÊá´s. TÊÉªs Éªs á´ sá´á´á´á´Êá´ É¢Êá´á´á´ sá´ á´Êá´á´ Êá´á´ á´á´É´'á´ É¢á´á´ ÒÉªÊá´s ÒÊá´á´ Êá´Êá´...</b>")
            else:
                hehe = await message.reply_photo(photo=imdb.get('poster'), caption=cap[:1024], reply_markup=InlineKeyboardMarkup(btn))
                try:
                    if settings['auto_delete']:
                        await asyncio.sleep(SELF_DELETE_SECONDS)
                        await hehe.delete()
                        await message.delete()
                except KeyError:
                    grpid = await active_connection(str(message.from_user.id))
                    await save_group_settings(grpid, 'auto_delete', True)
                    settings = await get_settings(message.chat.id)
                    if settings['auto_delete']:
                        await asyncio.sleep(SELF_DELETE_SECONDS)
                        await hehe.delete()
                        await message.delete()
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            if message.chat.id == SUPPORT_CHAT_ID:
                await message.reply_text(f"<b>Há´Ê {message.from_user.mention}, {str(total_results)} Êá´sá´Êá´s á´Êá´ Òá´á´É´á´ ÉªÉ´ á´Ê á´á´á´á´Êá´sá´ Òá´Ê Êá´á´Ê á´Ì¨á´á´ÊÊ {search}. KÉªÉ´á´ÊÊ á´sá´ ÉªÉ´ÊÉªÉ´á´ sá´á´Êá´Ê á´Ê á´á´á´á´ á´ É¢Êá´á´á´ á´É´á´ á´á´á´ á´á´ á´s á´á´á´ÉªÉ´ á´á´ É¢á´á´ á´á´á´ Éªá´ ÒÉªÊá´s. TÊÉªs Éªs á´ sá´á´á´á´Êá´ É¢Êá´á´á´ sá´ á´Êá´á´ Êá´á´ á´á´É´'á´ É¢á´á´ ÒÉªÊá´s ÒÊá´á´ Êá´Êá´...</b>")
            else:
                pic = imdb.get('poster')
                poster = pic.replace('.jpg', "._V1_UX360.jpg")
                hmm = await message.reply_photo(photo=poster, caption=cap[:1024], reply_markup=InlineKeyboardMarkup(btn))
                try:
                    if settings['auto_delete']:
                        await asyncio.sleep(SELF_DELETE_SECONDS)
                        await hmm.delete()
                        await message.delete()
                except KeyError:
                    grpid = await active_connection(str(message.from_user.id))
                    await save_group_settings(grpid, 'auto_delete', True)
                    settings = await get_settings(message.chat.id)
                    if settings['auto_delete']:
                        await asyncio.sleep(SELF_DELETE_SECONDS)
                        await hmm.delete()
                        await message.delete()
        except Exception as e:
            if message.chat.id == SUPPORT_CHAT_ID:
                await message.reply_text(f"<b>Há´Ê {message.from_user.mention}, {str(total_results)} Êá´sá´Êá´s á´Êá´ Òá´á´É´á´ ÉªÉ´ á´Ê á´á´á´á´Êá´sá´ Òá´Ê Êá´á´Ê á´Ì¨á´á´ÊÊ {search}. KÉªÉ´á´ÊÊ á´sá´ ÉªÉ´ÊÉªÉ´á´ sá´á´Êá´Ê á´Ê á´á´á´á´ á´ É¢Êá´á´á´ á´É´á´ á´á´á´ á´á´ á´s á´á´á´ÉªÉ´ á´á´ É¢á´á´ á´á´á´ Éªá´ ÒÉªÊá´s. TÊÉªs Éªs á´ sá´á´á´á´Êá´ É¢Êá´á´á´ sá´ á´Êá´á´ Êá´á´ á´á´É´'á´ É¢á´á´ ÒÉªÊá´s ÒÊá´á´ Êá´Êá´...</b>")
            else:
                logger.exception(e)
                fek = await message.reply_photo(photo=NOR_IMG, caption=cap, reply_markup=InlineKeyboardMarkup(btn))
                try:
                    if settings['auto_delete']:
                        await asyncio.sleep(SELF_DELETE_SECONDS)
                        await fek.delete()
                        await message.delete()
                except KeyError:
                    grpid = await active_connection(str(message.from_user.id))
                    await save_group_settings(grpid, 'auto_delete', True)
                    settings = await get_settings(message.chat.id)
                    if settings['auto_delete']:
                        await asyncio.sleep(SELF_DELETE_SECONDS)
                        await fek.delete()
                        await message.delete()
    else:
        if message.chat.id == SUPPORT_CHAT_ID:
            await message.reply_text(f"<b>Há´Ê {message.from_user.mention}, {str(total_results)} Êá´sá´Êá´s á´Êá´ Òá´á´É´á´ ÉªÉ´ á´Ê á´á´á´á´Êá´sá´ Òá´Ê Êá´á´Ê á´Ì¨á´á´ÊÊ {search}. KÉªÉ´á´ÊÊ á´sá´ ÉªÉ´ÊÉªÉ´á´ sá´á´Êá´Ê á´Ê á´á´á´á´ á´ É¢Êá´á´á´ á´É´á´ á´á´á´ á´á´ á´s á´á´á´ÉªÉ´ á´á´ É¢á´á´ á´á´á´ Éªá´ ÒÉªÊá´s. TÊÉªs Éªs á´ sá´á´á´á´Êá´ É¢Êá´á´á´ sá´ á´Êá´á´ Êá´á´ á´á´É´'á´ É¢á´á´ ÒÉªÊá´s ÒÊá´á´ Êá´Êá´...</b>")
        else:
            fuk = await message.reply_photo(photo=NOR_IMG, caption=cap, reply_markup=InlineKeyboardMarkup(btn))
            try:
                if settings['auto_delete']:
                    await asyncio.sleep(SELF_DELETE_SECONDS)
                    await fuk.delete()
                    await message.delete()
            except KeyError:
                grpid = await active_connection(str(message.from_user.id))
                await save_group_settings(grpid, 'auto_delete', True)
                settings = await get_settings(message.chat.id)
                if settings['auto_delete']:
                    await asyncio.sleep(SELF_DELETE_SECONDS)
                    await fuk.delete()
                    await message.delete()
    if spoll:
        await msg.message.delete()


async def advantage_spell_chok(client, msg):
    mv_rqst = msg.text
    reqstr1 = msg.from_user.id if msg.from_user else 0
    reqstr = await client.get_users(reqstr1)
    settings = await get_settings(msg.chat.id)
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)",
        "", msg.text, flags=re.IGNORECASE)  # plis contribute some common words
    RQST = query.strip()
    query = query.strip() + " movie"
    g_s = await search_gagala(query)
    g_s += await search_gagala(msg.text)
    gs_parsed = []
    if not g_s:
        await client.send_message(chat_id=LOG_CHANNEL, text=(script.NORSLTS.format(reqstr.id, reqstr.mention, mv_rqst)))
        k = await msg.reply(script.I_CUDNT.format(RQST))
        await asyncio.sleep(8)
        await k.delete()
        return
    regex = re.compile(r".*(imdb|wikipedia).*", re.IGNORECASE)  # look for imdb / wiki results
    gs = list(filter(regex.match, g_s))
    gs_parsed = [re.sub(
        r'\b(\-([a-zA-Z-\s])\-\simdb|(\-\s)?imdb|(\-\s)?wikipedia|\(|\)|\-|reviews|full|all|episode(s)?|film|movie|series)',
        '', i, flags=re.IGNORECASE) for i in gs]
    if not gs_parsed:
        reg = re.compile(r"watch(\s[a-zA-Z0-9_\s\-\(\)]*)*\|.*",
                         re.IGNORECASE)  # match something like Watch Niram | Amazon Prime
        for mv in g_s:
            match = reg.match(mv)
            if match:
                gs_parsed.append(match.group(1))
    user = msg.from_user.id if msg.from_user else 0
    movielist = []
    gs_parsed = list(dict.fromkeys(gs_parsed))  # removing duplicates https://stackoverflow.com/a/7961425
    if len(gs_parsed) > 3:
        gs_parsed = gs_parsed[:3]
    if gs_parsed:
        for mov in gs_parsed:
            imdb_s = await get_poster(mov.strip(), bulk=True)  # searching each keyword in imdb
            if imdb_s:
                movielist += [movie.get('title') for movie in imdb_s]
    movielist += [(re.sub(r'(\-|\(|\)|_)', '', i, flags=re.IGNORECASE)).strip() for i in gs_parsed]
    movielist = list(dict.fromkeys(movielist))  # removing duplicates
    if not movielist:
        await client.send_message(chat_id=LOG_CHANNEL, text=(script.NORSLTS.format(reqstr.id, reqstr.mention, mv_rqst)))
        k = await msg.reply(script.I_CUD_NT.format(RQST))
        await asyncio.sleep(8)
        await k.delete()
        return
    SPELL_CHECK[msg.id] = movielist
    btn = [[
        InlineKeyboardButton(
            text=movie.strip(),
            callback_data=f"spolling#{user}#{k}",
        )
    ] for k, movie in enumerate(movielist)]
    btn.append([InlineKeyboardButton(text="Close", callback_data=f'spolling#{user}#close_spellcheck')])
    spell_check_del = await msg.reply_photo(
        photo=(SPELL_IMG),
        caption=(script.CUDNT_FND.format(RQST)),
        reply_markup=InlineKeyboardMarkup(btn)
    )
    try:
        if settings['auto_delete']:
            await asyncio.sleep(SELF_DELETE_SECONDS)
            await spell_check_del.delete()
    except KeyError:
            grpid = await active_connection(str(message.from_user.id))
            await save_group_settings(grpid, 'auto_delete', True)
            settings = await get_settings(message.chat.id)
            if settings['auto_delete']:
                await asyncio.sleep(SELF_DELETE_SECONDS)
                await spell_check_del.delete()


async def manual_filters(client, message, text=False):
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            await client.send_message(
                                group_id, 
                                reply_text, 
                                disable_web_page_preview=True,
                                reply_to_message_id=reply_id)
                        else:
                            button = eval(btn)
                            await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )
                    elif btn == "[]":
                        await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )
                    else:
                        button = eval(btn)
                        await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False
   
   
