import os
import time

import requests
import re
import json
import asyncio
import aiohttp
import aiofiles
import random
import xml.etree.ElementTree as ET

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
}
bvid_list = []
finish_num = 0

async def fetch_cid(url):
    global headers
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            return json.loads(await response.text())['data'][0]['cid']


async def write_to_file(filename, data):
    async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
        for item in data:
            await f.write(item + '\n')


async def fetch_dm(bvid, lock):
    global headers,finish_num
    await asyncio.sleep(round(random.uniform(0, 5), 2))
    cid = await fetch_cid(f'https://api.bilibili.com/x/player/pagelist?bvid={bvid}&jsonp=jsonp')
    url = f'https://api.bilibili.com/x/v1/dm/list.so?oid={cid}'
    dm_list = []
    fn = os.path.join('./dm', f'dm_{cid}.txt')
    if not os.path.exists(fn):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                response.encoding = 'utf-8'
                tree = ET.ElementTree(ET.fromstring(await response.text()))
                root = tree.getroot()
                for d in root.findall('d'):
                    dm_list.append(d.text)
        await write_to_file(fn, dm_list)
    await lock.acquire()
    try:
        finish_num = finish_num + 1
    finally:
        lock.release()
    await callback(lock)


async def callback(lock):
    global finish_num
    await lock.acquire()
    try:
        print(f'当前进度：{finish_num} / 300 , 请稍后。。。')
    finally:
        lock.release()


async def main():
    global bvid_list
    lock = asyncio.Lock()
    await asyncio.sleep(round(random.uniform(0.0, 4.0), 2))
    await asyncio.gather(*[fetch_dm(bvid, lock) for bvid in bvid_list])


def get_bvid_list(keyword, readable):
    global headers
    fn = './' + readable + '_bvid_list.txt'
    bvid_list = []

    if os.path.exists(fn):
        print('检测到缓存，为您从本地加载。。。')
        with open(fn, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                bvid_list.append(line)

        print('加载成功！')
        return bvid_list
    else:
        print('未检测到缓存，为您从b站加载，总共需要爬取15次')
        pre_list_url = 'https://api.bilibili.com/x/web-interface/wbi/search/type?'
        try:
            cookies = requests.get(url='https://www.bilibili.com/', headers=headers).cookies.get_dict()
        except:
            pass
        for i in range(15):
            list_url = pre_list_url + f'page={i + 1}&keyword={keyword}&search_type=video'
            bvid_list.extend(re.findall(r"\"bvid\":\"(\w+?)\"",
                                        requests.get(url=list_url, headers=headers, cookies=cookies).text))
            if len(bvid_list) >= 300:
                print(f'已获取全部bvid，开始下一步操作')
                break
            else:
                print(f'正在获取bvid，已爬取{i + 1}次，剩余{15 - i - 1}次，请稍后。。。')
                time.sleep(round(random.uniform(0.5, 3.0), 2))
        with open(fn, 'w', newline='', encoding='utf-8') as f:
            for item in bvid_list:
                f.write(item + '\n')
        return bvid_list


if __name__ == '__main__':
    kw = input('请输入要查找的关键字: ')
    while not kw:
        files = os.listdir(os.getcwd())
        for file in files:
            if os.path.isfile(file):
                try:
                    kw = re.search(r'(\w+)_bvid', file).group(1)
                except:
                    pass
        if not kw:
            kw = input('未搜索到缓存，请手动输入关键字： ')
    keyword = str(kw.encode('utf-8')).upper()[2:-1].replace('\\X', '%')
    bvid_list = get_bvid_list(keyword, kw)
    asyncio.run(main())
