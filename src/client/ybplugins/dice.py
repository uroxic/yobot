'''
[.r] 掷骰子
[.r 3d12] 掷3次12面骰子
'''

import re
import copy
import json
import asyncio
from typing import Any, Dict, Union

from aiocqhttp.api import Api
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from quart import Quart
from random import randint


class Dice:
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

        # # 注册定时任务，详见apscheduler文档
        # @scheduler.scheduled_job('cron', hour=8)
        # async def good_morning():
        #     await self.api.send_group_msg(group_id=123456, message='早上好')

        # # 注册web路由，详见flask与quart文档
        # @app.route('/is-bot-running', methods=['GET'])
        # async def check_bot():
        #     return 'yes, bot is running'

    async def do_dice(self, sender_qqid, num, min_, max_, opr, offset, TIP="的掷骰结果是："):
        if num == 0:
            return '咦？我骰子呢？'
        min_, max_ = min(min_, max_), max(min_, max_)
        rolls = list(map(lambda _: random.randint(min_, max_), range(num)))
        sum_ = sum(rolls)
        rolls_str = '+'.join(map(lambda x: str(x), rolls))
        if len(rolls_str) > 100:
            rolls_str = str(sum_)
        res = sum_ + opr * offset
        msg = [
            f"[CQ:at,qq={sender_qqid}]",
            f'{TIP}\n', str(num) if num > 1 else '', 'D',
            f'{min_}~' if min_ != 1 else '', str(max_),
            (' +-'[opr] + str(offset)) if offset else '',
            '=', rolls_str, (' +-'[opr] + str(offset)) if offset else '',
            f'={res}' if offset or num > 1 else '',
        ]
        msg = ''.join(msg)
        return msg

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
            r'^\.r\s*((?P<num>\d{0,2})d((?P<min>\d{1,4})~)?(?P<max>\d{0,4})((?P<opr>[+-])(?P<offset>\d{0,5}))?)?\b',
            #r"^(查询公会|查询会长) *(-?\d+)? *(?:[\:：](.*))?$",
            #r"^(查询排名|查询分数) *(-?\d+)? *(?:[\:：](\d+))?$",
            #r"^(查询本会|查询档线) *(-?\d+)?$",
            #r"^(历史数据) *$",
            #r"^(预计伤害) *(-?\d+)([Ww万Kk千])? *(?:\[CQ:at,qq=(\d+)\])? *$",
            #r"^(送钻) *(-?\d+)([Ww万Kk千])? *$"
        ]
        match = None
        for r in regex:
            match = re.match(r, msg)
            if match is not None:
                break
        if match is None:
            return
        else:
            num, min_, max_, opr, offset = 1, 1, 100, 1, 0
            if match.group('num'):
                num = int(match.group('num'))
            if match.group('min'):
                min_ = int(match.group('min'))
            if match.group('max'):
                max_ = int(match.group('max'))
            if match.group('opr'):
                opr = -1 if match.group('opr') == '-' else 1
            if match.group('offset'):
                offset = int(match.group('offset'))
            return self.do_dice(sender_qqid, num, min_, max_, opr, offset)

        # 返回布尔值：是否阻止后续插件（返回None视作False）
        return False
