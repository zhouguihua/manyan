#!/user/bin/env python
# -*- coding:utf-8 -*-
# 作者：周桂华
# 开发时间: 2021/8/2 21:18

from settings import UA_LIST
import random
import requests
from requests.exceptions import RequestException
import time
import re
import os
import json
from multiprocessing import Pool


class MaoYanSpider(object):
    """
    https://maoyan.com/board
    """

    def __init__(self):
        self.headers = {"User-Agent": random.choice(UA_LIST)}

    def parse_html(self, text):
        # 提取电影名，排行，主演，上映时间, 链接, 电影宣传图, 评分
        regex_compile = re.compile(
            '<dd>.*?board-index.*?>(.*?)</i>.*?data-src="(.*?)"'
            + '.*?name.*?a.*?>(.*?)</a>.*?star.*?主演：(.*?)</p>'
            + '.*?releasetime.*?上映时间：(.*?)</p>.*?integer.*?>(.*?)</i>'
            + '.*?fraction.*?>(.*?)</i>.*?</dd>', re.S)
        results = regex_compile.findall(text)
        for res in results:
            yield {
                "排名": res[0],
                "电影海报": res[1],
                "电影名": res[2],
                "主演": res[3].strip(),
                "上映时间": res[4],
                "评分": res[5] + res[6]
            }

    def get_one_page(self, url, retry_count=0):
        try:
            resp = requests.get(url, headers=self.headers, timeout=30)
            # print("url:{},请求头信息{}".format(url, resp.request.headers))
            resp.raise_for_status()
        except RequestException as e1:
            print("url: {} ,  报错：{}".format(url, e1))
            time.sleep(1.5)
            retry_count += 1
            if min(retry_count, 3) < 3:
                print("url：{}, 第{}次重试".format(url, retry_count))
                self.get_one_page(url, retry_count)
            else:
                print("url：{}, 超过最大重试次数".format(url))
        else:
            if "猫眼验证中心" not in resp.text:
                return resp.text
            else:
                time.sleep(5)
                retry_count += 1
                print("url:{}出现验证".format(url))
                self.get_one_page(url, retry_count)

    def write_to_file(self, item):
        with open(os.path.join(os.getcwd(), "output/1.json"), mode="a+", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    def run(self, page):
        print("开始抓取第{}页......".format(page))
        url = "https://maoyan.com/board/4?offset={}"
        res = self.get_one_page(url.format(page))
        if res:
            items = self.parse_html(res)
            for item in items:
                self.write_to_file(item)


if __name__ == '__main__':
    if not os.path.exists(os.path.join(os.getcwd(), "output")):
        os.makedirs(os.path.join(os.getcwd(), "output"))
    print("------开始抓取猫眼排行榜------")
    start_time = time.perf_counter()
    pool = Pool()
    for i in range(10):
        pool.apply_async(MaoYanSpider().run, args=(i*10, ))
    pool.close()
    pool.join()
    print("------抓取猫眼排行榜结束----")
    print("耗时{:.2f}秒".format(time.perf_counter() - start_time))

