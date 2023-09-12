import time

import requests
import re
import json
import asyncio
import aiohttp
import random
import xml.etree.ElementTree as ET
import pandas as pd

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
}
finish_num = 0
all_dm_dict = {}
top20_pending = {}


async def fetch_cid(session, url):
    async with session.get(url, headers=headers) as response:
        return json.loads(await response.text())['data'][0]['cid']


def callback(finish_num):
    print(f'当前进度：{finish_num} / 300 , 请稍后。。。')


async def fetch_dm(session, bvid, lock):
    global finish_num, all_dm_dict, top20_pending
    await asyncio.sleep(round(random.uniform(0, 2), 2))
    try:
        cid = await fetch_cid(session,f'https://api.bilibili.com/x/player/pagelist?bvid={bvid}&jsonp=jsonp')
    except:
        raise Exception('您的请求过于频繁，请稍后重试')
    url = f'https://api.bilibili.com/x/v1/dm/list.so?oid={cid}'
    dm_dict = {}
    try:
        await asyncio.sleep(round(random.uniform(0, 2), 2))
        async with session.get(url, headers=headers) as response:
            response.encoding = 'utf-8'
            xml_str = await response.text()

        root = ET.ElementTree(ET.fromstring(xml_str)).getroot()
        for d in root.findall('d'):
            if d.text in dm_dict:
                dm_dict[d.text] += 1
            else:
                dm_dict[d.text] = 1
    except:
        pass
    try:
        await lock.acquire()
        for (k, v) in dm_dict.items():
            if k in all_dm_dict:
                all_dm_dict[k] += v
            else:
                all_dm_dict[k] = v
    except:
        pass
    finally:
        lock.release()
    dm_dict = sorted(dm_dict.items(), key=lambda x: x[1], reverse=True)[:40] if len(dm_dict) > 40 else list(
        dm_dict.items())
    try:
        await lock.acquire()
        for (k, v) in dm_dict:
            if k in top20_pending:
                top20_pending[k] += v
            else:
                top20_pending[k] = v
        finish_num += 1
        callback(finish_num)
    except:
        pass
    finally:
        lock.release()


def get_bvid_list(keyword):
    bvid_list = []
    pre_list_url = 'https://api.bilibili.com/x/web-interface/wbi/search/type?'
    cookies = {}
    try:
        cookies = requests.get(url='https://www.bilibili.com/', headers=headers).cookies.get_dict()
    except:
        raise Exception('请求失败，请检查网络')
    for i in range(15):
        list_url = pre_list_url + f'page={i + 1}&keyword={keyword}&search_type=video'
        try:
            bvid_list.extend(re.findall(r"\"bvid\":\"(\w+?)\"",
                                        requests.get(url=list_url, headers=headers, cookies=cookies).text))
            if len(bvid_list) >= 300:
                print(f'已获取全部bvid，开始下一步操作')
                break
            else:
                print(f'正在获取bvid，已爬取{i + 1}次，剩余{15 - i - 1}次，请稍后。。。')
            time.sleep(round(random.uniform(0, 2.0), 2))
        except:
            raise Exception('无效的cookie，您的IP有可能被封禁，请更换IP后重试')
    return bvid_list


def get_keyword():
    return str(input('请输入要查找的关键字: ').encode('utf-8')).upper()[2:-1].replace('\\X', '%')


async def main(kw):
    lock = asyncio.Lock()
    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*[asyncio.ensure_future(fetch_dm(session, bvid, lock)) for bvid in get_bvid_list(kw)])
if __name__ == '__main__':
    kw = get_keyword()

    asyncio.run(main(kw))

    print('爬取完成 ! \n\n正在生成统计结果。。。')
    top20 = sorted(top20_pending.items(), key=lambda x: x[1], reverse=True)[:20]
    print('统计结果如下:')
    with open('top20.txt', 'w', encoding='utf-8') as f:
        for index, (content, count) in enumerate(top20):
            try:
                f.write(content + ' ' + str(count) + '\n')
                print(f"Top {index + 1} :{content} , count :{all_dm_dict[content]}")
            except:
                pass

    df = pd.DataFrame([{'danmu': k, 'count': v} for k, v in all_dm_dict.items()])
    df.to_excel('all_dm.xlsx', index=False)
    print('Excel表格导入完成')
