import logging
import asyncio
import requests
import json
import datetime
import os
from config import *
from aiogram import Bot, Dispatcher, executor, types


logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


# @dp.message_handler(commands=['subscribe'])
# async def subscribe(message: types.Message):
#     await message.answer("Вы успешно подписались на рассылку!\nЖдите, скоро выйдут новые обзоры и вы узнаете о них первыми =)")


# @dp.message_handler(commands=['unsubscribe'])
# async def unsubscribe(message: types.Message):
#     await message.answer("Вы успешно отписаны от рассылки.")


def get_posts():
    try:
        url = f"https://api.vk.com/method/wall.get?v=5.131&access_token={APP_TOKEN}&scope=photos,audio&owner_id={TARGET_ID}"
        response = requests.get(url).json()

        result = []
        items = response['response']['items']

        for i in range(0, len(items)):
            item = items[i]

            if isStored(item['hash']):
                continue

            for attachment in item['attachments']:
                if attachment['type'] == 'photo':
                    photo = get_highest_quality_photo(attachment['photo']['sizes'])

            store(item['hash'])

            if len(result) < i + 1:
                result.append({})

            result[i]['photo'] = photo

        return result
    except:
        log('Error while getting posts', 'get_posts')


def get_highest_quality_photo(sizes):
    try:
        max_height = 0
        index = 0

        for j in range(0, len(sizes)):
            if sizes[j]['height'] > max_height:
                max_height = sizes[j]['height']
                index = j

        return sizes[index]['url']
    except:
        log('Error while getting the highest quality photo',
            'get_highest_quality_photo')
        return ''


def get_video(story):
    try:
        index = list(story['video']['files'].keys())[0]
        video = story['video']['files'][index]
        return video
    except:
        log('Error while getting video from story', 'get_video')
        return ''


def log(text, place):
    try:
        with open('logs.txt', 'a') as logs:
            logs.write(str(datetime.datetime.now()) +
                       "  :  " + text + " in " + place + "\n")

        logs.close()
    except:
        print('APOCALYPSE BEGINS...')


def store(data):
    try:
        if not os.path.exists(os.path.abspath(os.curdir) + '\hashes.txt'):
            storage = open("hashes.txt", "x")
            storage.close()

        with open('hashes.txt', 'a+') as storage:
            storage.write(str(data) + "\n")

        storage.close()
    except:
        log('Error while storing data', 'store')


def isStored(data):
    try:
        if not os.path.exists(os.path.abspath(os.curdir) + '\hashes.txt'):
            storage = open("hashes.txt", "x")

        with open('hashes.txt', 'r+') as storage:
            for line in storage:
                if line == str(data) + "\n":
                    return True

            return False
    except:
        log('Error while verifying that data is stored', 'isStored')


def isTarget(id):
    return str(id) == TARGET_ID


def get_stories():
    try:
        url = f"https://api.vk.com/method/stories.get?v=5.131&access_token={APP_TOKEN}&scope=stories,offline"
        response = requests.get(url).json()

        result = []
        items = response['response']['items']

        for i in range(0, response['response']['count']):
            item = items[i]

            if not isTarget(item['stories'][0]['owner_id']):
                continue

            for j in range(0, len(item['stories'])):
                if isStored(item['stories'][j]['id']):
                    continue

                store(item['stories'][j]['id'])
                
                photo = video = ''
                story = item['stories'][j]

                if story['type'] == 'photo':
                    photo = get_highest_quality_photo(story['photo']['sizes'])

                if story['type'] == 'video':
                    video = get_video(story)

                if len(result) < j + 1:
                    result.append({})

                result[j]['photo'] = photo
                result[j]['video'] = video

        return result
    except:
        log('Error while getting stories', 'get_stories')
        return []


async def scheduled(wait_for):
    while True:
        await asyncio.sleep(wait_for)

        try:
            posts = get_posts()
            stories = get_stories()

            for post in posts:
                await bot.send_photo(CHAT_ID, post['photo'])

            for story in stories:
                if 'video' in story:
                    await bot.send_video(CHAT_ID, story['video'])
                elif 'photo' in story:
                    await bot.send_video(CHAT_ID, story['video'])
        except:
            log('Something went wrong! Error...', 'scheduled')
            print('Error...')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled(10))
    executor.start_polling(dp, skip_updates=True)
