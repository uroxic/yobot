'''
无损音乐搜索 数据来自acgjc.com
'''

import re
import copy
import time
import json
import asyncio
import requests
from urllib.parse import quote
from typing import Any, Dict, Union

from aiocqhttp.api import Api
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from quart import Quart
from random import randint


class Flac:
    def __init__(self,
                 glo_setting: Dict[str, Any],
                 scheduler: AsyncIOScheduler,
                 app: Quart,
                 bot_api: Api,
                 *args, **kwargs):
        '''
        初始化，只在启动时执行一次

        参数：
            glo_setting 包含所有设置项，具体见default_config.json
            bot_api 是调用机器人API的接口，具体见<https://python-aiocqhttp.cqp.moe/>
            scheduler 是与机器人一同启动的AsyncIOScheduler实例
            app 是机器人后台Quart服务器实例
        '''
        # 注意：这个类加载时，asyncio事件循环尚未启动，且bot_api没有连接
        # 此时不要调用bot_api
        # 此时没有running_loop，不要直接使用await，请使用asyncio.ensure_future并指定loop=asyncio.get_event_loop()

        # 如果需要启用，请注释掉下面一行
        # return

        # 这是来自yobot_config.json的设置，如果需要增加设置项，请修改default_config.json文件
        self.setting = glo_setting
        self.admin_list = copy.deepcopy(self.setting["super-admin"])

        # 这是cqhttp的api，详见cqhttp文档
        self.cqapi = bot_api
        self.clan = {}
        self.time = []
        self.api = 'http://mtage.top:8099/acg-music/search'
        self.header = {
            'Content-Type': 'application/json',
            'Connection': 'keep-alive',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36',
            'DNT': '1',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }

        # # 注册定时任务，详见apscheduler文档
        # @scheduler.scheduled_job('cron', hour=8)
        # async def good_morning():
        #     await self.api.send_group_msg(group_id=123456, message='早上好')

        # # 注册web路由，详见flask与quart文档
        # @app.route('/is-bot-running', methods=['GET'])
        # async def check_bot():
        #     return 'yes, bot is running'

    async def execute_async(self, ctx: Dict[str, Any]) -> Union[None, bool, str]:
        '''
        每次bot接收有效消息时触发

        参数ctx 具体格式见：https://cqhttp.cc/docs/#/Post
        '''
        # 注意：这是一个异步函数，禁止使用阻塞操作（比如requests）

        # 如果需要使用，请注释掉下面一行
        # return

        msg = ctx['raw_message']
        sender_qqid = ctx["user_id"]
        regex = [
            r"^(搜无损) *(\S*)?$",
            #r"^(查询公会|查询会长) *(-?\d+)? *(?:[\:：](.*))?$",
            #r"^(查询排名|查询分数) *(-?\d+)? *(?:[\:：](\d+))?$",
            #r"^(查询本会|查询档线) *(-?\d+)?$",
            #r"^(历史数据) *$",
            #r"^(预计伤害) *(-?\d+)([Ww万Kk千])? *(?:\[CQ:at,qq=(\d+)\])? *$"
            #r"^(送钻) *(-?\d+)([Ww万Kk千])? *$"
        ]
        match = None
        for r in regex:
            match = re.match(r, msg)
            if match is not None:
                break
        if match is None:
            return
        cmd = match.group(1)

        if cmd == '搜无损':
            if ctx['message_type'] == 'private':
                msg = ''
            else:
                msg = f"[CQ:at,qq={ctx['user_id']}]\n"
            keyword = str(match.group(2)) if match.group(
                2) is not None else ''
            resp = requests.get('http://mtage.top:8099/acg-music/search',
                                params={'title-keyword': keyword}, headers=self.header)
            res = resp.json()
            if res['success'] is False:
                msg += f'查询失败 请至acgjc官网查询 www.acgjc.com/?s={quote(keyword)}'
                return msg

            music_list = res['result']['content']
            music_list = music_list[:min(5, len(music_list))]

            details = [" ".join([
                f"{ele['title']}",
                f"{ele['downloadLink']}",
                f"密码：{ele['downloadPass']}" if ele['downloadPass'] else ""
            ]) for ele in music_list]

            msg_list = [
                f"共 {res['result']['totalElements']} 条结果" if len(
                    music_list) > 0 else '没有任何结果',
                *details,
            ]

            msg += '\n'.join(msg_list)
            msg += '\n\n数据来自 www.acgjc.com\n',
            msg += f'更多结果可见 www.acgjc.com/?s={quote(keyword)}'
            return msg

        # 返回布尔值：是否阻止后续插件（返回None视作False）
        return False
