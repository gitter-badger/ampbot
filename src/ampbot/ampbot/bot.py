#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Bot.py"""
#own
from Lib.ampbot import Parse, Answers, Logger
from Lib.Spotify import Search, Playlist, Releases
from Lib.Config import Parser

#packages
from telegram.ext import *
from telegram.error import Unauthorized, NetworkError
from telegram.ext.dispatcher import run_async
from telegram import InlineQueryResultArticle, InlineQueryResultAudio, InputTextMessageContent, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, MessageEntity
from uuid import uuid4

import re
from pprint import pprint
from emoji import emojize
import arrow
import logging
#from apscheduler.schedulers.background import BackgroundScheduler
#import spotipy

#import requests
#import arrow
#from tld import get_tld
#import configparser
#import datetime
#import pytz
#import time
#import re
#import math
#import validators
#import threading
#import ftfy
#from tabulate import tabulate
#from pprint import pprint

ISSUES = range(1)
lastUpdate = None
scheduler = None
config = None
tgBot = None
clientId = None
clientSecret = None

logger = Logger.ConfigureLogging()

@run_async
def start(bot, update):
    bot.sendMessage(update.message.chat_id, Answers.Start(), parse_mode=ParseMode.MARKDOWN)
    logger.info('START: {0}({1})'.format(update.message.from_user.username, update.message.from_user.id))

@run_async
def settings(bot, update):
    bot.sendMessage(update.message.chat_id, Answers.Settings())
    logger.info('SETTINGS: {0}({1})'.format(update.message.from_user.username, update.message.from_user.id))

@run_async
def help(bot, update):
    bot.sendMessage(update.message.chat_id, Answers.Help())
    logger.info('HELP: {0}({1})'.format(update.message.from_user.username, update.message.from_user.id))

@run_async
def test(bot, update):
    print(str(update))
    bot.sendMessage(update.message.chat_id, Answers.Test())
    logger.info('TEST: {0}({1})'.format(update.message.from_user.username, update.message.from_user.id))

@run_async
def rate(bot, update):
    bot.sendMessage(
        update.message.chat_id,
        Answers.Rate('{0}={1}'.format(config.production.bot.rateLink, config.production.bot.username)),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Rate now', url='{0}={1}'.format(config.production.bot.rateLink, config.production.bot.username))]]),
        parse_mode=ParseMode.MARKDOWN)
    logger.info('RATE: {0}({1})'.format(update.message.from_user.username, update.message.from_user.id))

@run_async
def group(bot, update):
    bot.sendMessage(
        update.message.chat_id,
        Answers.Group(config.production.bot.groupLink),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Join now', url=config.production.bot.groupLink)]]),
        parse_mode=ParseMode.MARKDOWN)
    logger.info('GROUP: {0}({1})'.format(update.message.from_user.username, update.message.from_user.id))

@run_async
def issue(bot, update):
    logger.info('ISSUE: {0}({1}): {2}'.format(update.message.from_user.username, update.message.from_user.id, update.message.text))
    bot.sendMessage(update.message.chat_id, Answers.Issue())
    return ISSUES

@run_async
def sendToAdmin(bot, update):
    logger.info('sendToAdmin: {0}({1}): {2}'.format(update.message.from_user.username, update.message.from_user.id, update.message.text))
    bot.forwardMessage(8139296, update.message.chat_id, update.message.message_id)
    bot.sendMessage(update.message.chat_id, Answers.SendToAdmin())
    return ConversationHandler.END

@run_async
def channel(bot, update):
    bot.sendMessage(update.message.chat_id, Answers.Channel())
    logger.info('CHANNEL: {0}({1})'.format(update.message.from_user.username, update.message.from_user.id))

@run_async
def playlist(bot, update):
    bot.sendMessage(
        update.message.chat_id,
        Answers.Playlist(config.production.spotify.playlistUri, config.production.spotify.playlistFullId),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Join now', url=config.production.spotify.playlistUri)]]),
        parse_mode=ParseMode.MARKDOWN)
    logger.info('PLAYLIST: {0}({1})'.format(update.message.from_user.username, update.message.from_user.id))
    
@run_async
def default(bot, update):
    logger.info('DEFAULT: {0}({1}): {2}'.format(update.message.from_user.username, update.message.from_user.id, update.message.text))
    if update.message.from_user.id == 8139296:
        if update.message.reply_to_message:
            bot.sendMessage(update.message.reply_to_message.forward_from.id, update.message.text, reply_to_message_id=update.message.reply_to_message.message_id-1)
    else:
        bot.sendMessage(update.message.chat_id, Answers.Default())


def inline(bot, update):
    query = update.inline_query.query
    inline = list()
    if len(query) > 0:
        if query == 'new albums':
            releases = list()
            message = ''
            local = arrow.utcnow().to('Europe/Berlin')
            newReleases = Releases.newReleases(config, 'DE')
            if len(newReleases['albums']['items']) > 0:
                message += 'New Releases {0}\n\n'.format(local.format('YYYY-MM-DD HH:mm'))
                count = 1
                for album in newReleases['albums']['items']:
                    message += '{0}. [{1}]({2}) by {3}\n'.format(count, album['name'], album['external_urls']['spotify'], album['artists'][0]['name'])
                    releases.append(
                        InlineQueryResultArticle(
                            id=uuid4(),
                            title=Parse.AlbumReleaseInlineTitle(count, album),
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Go to Spotify', url=Parse.AlbumUrl(album))]]),
                            input_message_content=InputTextMessageContent(Parse.AlbumReleaseInlineInputMessage(album), ParseMode.MARKDOWN, False),
                            description=Parse.AlbumInlineDescription(album),
                            thumb_url=Parse.AlbumThumbUrl(album),
                            thumb_width=640,
                            thumb_height=640
                        )
                    )
                    count += 1

                inline.append(
                        InlineQueryResultArticle(
                            id=uuid4(),
                            title='New Releases {0}\n\n'.format(local.format('YYYY-MM-DD HH:mm')),
                            reply_markup=None,
                            input_message_content=InputTextMessageContent(message, ParseMode.MARKDOWN, True)
                        )
                    )
                for release in releases:
                    inline.append(release)
        else:
            results = Search.getResults(query, config)
            if len(results['tracks']['items']) > 0:
                for track in results['tracks']['items']:
                    if Parse.TrackPreviewUrl(track) != None:
                        inline.append(
                            InlineQueryResultAudio(
                                id='spotify:track:{0}'.format(track['id']), #uuid4(),
                                audio_url=Parse.TrackPreviewUrl(track),
                                performer=Parse.TrackArtists(track),
                                title=Parse.TrackInlineTitle(track),
                                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Go to Spotify', url=Parse.TrackUrl(track))]]),
                                input_message_content=InputTextMessageContent(Parse.TrackInlineInputMessage(track), ParseMode.MARKDOWN, False)
                            )
                        )
                    else:
                        inline.append(
                        InlineQueryResultArticle(
                            id='spotify:track:{0}'.format(track['id']), #uuid4(),
                            title=Parse.TrackInlineTitleWithOutPreview(track),
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Go to Spotify', url=Parse.TrackUrl(track))]]),
                            input_message_content=InputTextMessageContent(Parse.TrackInlineInputMessage(track), ParseMode.MARKDOWN, False),
                            description=Parse.TrackInlineDescriptionWithOutPreview(track),
                            url=Parse.TrackUrl(track),
                            hide_url=True,
                            thumb_url=Parse.TrackThumbUrl(track),
                            thumb_width=640,
                            thumb_height=640
                        )
                    )                
            if len(results['artists']['items']) > 0:
                for artist in results['artists']['items']:
                    inline.append(
                        InlineQueryResultArticle(
                            id=uuid4(),
                            title=Parse.ArtistInlineTitle(artist),
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Go to Spotify', url=Parse.ArtistUrl(artist))]]),
                            input_message_content=InputTextMessageContent(Parse.ArtistInlineInputMessage(artist), ParseMode.MARKDOWN, False),
                            description=Parse.ArtistInlineDescription(artist),
                            thumb_url=Parse.ArtistThumbUrl(artist),
                            thumb_width=640,
                            thumb_height=640
                        )
                    )
            if len(results['albums']['items']) > 0:
                for album in results['albums']['items']:
                    inline.append(
                        InlineQueryResultArticle(
                            id=uuid4(),
                            title=Parse.AlbumInlineTitle(album),
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Go to Spotify', url=Parse.AlbumUrl(album))]]),
                            input_message_content=InputTextMessageContent(Parse.AlbumInlineInputMessage(album), ParseMode.MARKDOWN, False),
                            description=Parse.AlbumInlineDescription(album),
                            thumb_url=Parse.AlbumThumbUrl(album),
                            thumb_width=640,
                            thumb_height=640
                        )
                    )
            if len(results['playlists']['items']) > 0:
                for playlist in results['playlists']['items']:
                    inline.append(
                        InlineQueryResultArticle(
                            id=uuid4(),
                            title=Parse.PlaylistInlineTitle(playlist),
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Go to Spotify', url=Parse.PlaylistUrl(playlist))]]),
                            input_message_content=InputTextMessageContent(Parse.PlaylistInlineInputMessage(playlist), ParseMode.MARKDOWN, False),
                            description=Parse.PlaylistInlineDescription(playlist),
                            thumb_url=Parse.PlaylistThumbUrl(playlist),
                            thumb_width=640,
                            thumb_height=640
                        )
                    )
        bot.answerInlineQuery(update.inline_query.id, inline)
        logger.info('INLINE: {0}({1}): {2}'.format(update.inline_query.from_user.username, update.inline_query.from_user.id, update.inline_query.query))

@run_async
def callback(bot, update):
    query = update.callback_query
    logger.info('CALLBACK: {0}({1})'.format(update.message.from_user.username, update.message.from_user.id))

@run_async
def chosen(bot, update):
    id = update.chosen_inline_result.result_id
    username = update.chosen_inline_result.from_user.first_name
    #logger.info('CHOSEN: {0}({1})'.format(update.chosen_inline_result.from_user.username, update.chosen_inline_result.from_user.id))
    if 'spotify:track:' in id:
        if Playlist.addTrack(id, config):
            Playlist.updatePlaylistName(update.chosen_inline_result.from_user.first_name, config)

@run_async
def new(bot, update):
    message = ''
    local = arrow.utcnow().to('Europe/Berlin')
    newReleases = Releases.newReleases(config, 'DE')
    if len(newReleases['albums']['items']) > 0:
        message += 'New Releases {0}\n\n'.format(local.format('YYYY-MM-DD HH:mm'))
        count = 1
        for album in newReleases['albums']['items']:
            message += '{0}. [{1}]({2}) by {3}\n'.format(count, album['name'], album['external_urls']['spotify'], album['artists'][0]['name'])
            count += 1
    bot.sendMessage(update.message.chat_id, message, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    logger.info('NEW: {0}({1})'.format(update.message.from_user.username, update.message.from_user.id))

@run_async
def add(bot, update, args, user_data, chat_data):
    if len(args) > 0:
        if 'spotify:track:' in args[0]:
            Playlist.addTrack(args[0], config)
            Playlist.updatePlaylistName(update.message.from_user.first_name, config)
        if 'https://open.spotify.com/track/' in args[0]:
            Playlist.addTrack(args[0].replace("https://open.spotify.com/track/", "spotify:track:"), config)
            Playlist.updatePlaylistName(update.message.from_user.first_name, config)
    else:
        if update.message.reply_to_message != None:
            matches = re.findall(r"spotify:track:[^\s]+", update.message.reply_to_message.text)
            if len(matches) > 0:
                for match in matches:
                    if 'spotify:track:' in match:
                        Playlist.addTrack(match, config)
                        Playlist.updatePlaylistName(update.message.from_user.first_name, config)
            for entity in update.message.reply_to_message.entities:
                if entity.type == MessageEntity.TEXT_LINK:
                    if 'https://open.spotify.com/track/' in entity.url:
                        Playlist.addTrack(entity.url.replace("https://open.spotify.com/track/", "spotify:track:"), config)
                        Playlist.updatePlaylistName(update.message.from_user.first_name, config)
    

@run_async
def cancel(bot, update):
    user = update.message.from_user
    update.message.reply_text('action canceled')
    logger.info('CANCEL: {0}({1})'.format(update.message.from_user.username, update.message.from_user.id))
    return ConversationHandler.END
    
        
@run_async
def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))   

def main():
    global config
    global tgBot
    global scheduler
    global lastUpdate
    withoutErrors = True
    config = Parser.parse_ini('ampbot.ini')

    logger.info('@ampbot started')
    
    updater = Updater(config.production.bot.token, workers=10)
    tgBot = updater.bot

    while withoutErrors:
        try:
            dp = updater.dispatcher
            dp.add_handler(CommandHandler("start", start))
            dp.add_handler(CommandHandler("settings", settings))
            dp.add_handler(CommandHandler("help", help))
            dp.add_handler(CommandHandler("rate", rate))
            dp.add_handler(CommandHandler("test", test))
            dp.add_handler(CommandHandler("group", group))
            dp.add_handler(CommandHandler("channel", channel))
            dp.add_handler(CommandHandler("playlist", playlist))
            dp.add_handler(CommandHandler("new", new))
            dp.add_handler(CommandHandler("add", add, pass_user_data=True, pass_chat_data=True, pass_args=True))
            dp.add_handler(CallbackQueryHandler(callback))
            dp.add_handler(InlineQueryHandler(inline))
            dp.add_handler(ChosenInlineResultHandler(chosen))

            conversation = ConversationHandler(
                entry_points=[CommandHandler('issues', issue)],
                states={
                    ISSUES: [MessageHandler(Filters.text, sendToAdmin)]
                },
                fallbacks=[CommandHandler('cancel', cancel)]
            )
            dp.add_handler(conversation)
            dp.add_handler(MessageHandler(None, default))

            dp.add_error_handler(error)
        
            updater.start_polling()
            updater.idle()
        except NetworkError:
            time.sleep(5)
        except Unauthorized:
            updater.last_update_id = updater.last_update_id + 1
        except:
            withoutErrors = False 

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(sys.stderr + '\nExiting by user request.\n')
        sys.exit(0)