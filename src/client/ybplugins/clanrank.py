'''
查询公会排名
'''

import re
import copy
import time
import json
import asyncio
import requests
from typing import Any, Dict, Union

from aiocqhttp.api import Api
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from quart import Quart
from random import randint


class clanrank:
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
        self.api = 'https://service-kjcbcnmw-1254119946.gz.apigw.tencentcs.com'
        self.header = {
            'Host': 'service-kjcbcnmw-1254119946.gz.apigw.tencentcs.com',
            'Content-Type': 'application/json',
            'Connection': 'keep-alive',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36',
            'DNT': '1',
            'Origin': 'https://kengxxiao.github.io',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://kengxxiao.github.io/Kyouka/',
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
            r"^(设置会名) *(?:[\:：](.*))?$",
            r"^(查询公会|查询会长) *(-?\d+)? *(?:[\:：](.*))?$",
            r"^(查询排名|查询分数) *(-?\d+)? *(?:[\:：](\d+))?$",
            r"^(查询本会|查询档线) *(-?\d+)?$",
            r"^(历史数据) *$",
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

        if cmd == '设置会名':
            if ctx['message_type'] == 'group':
                gid = sender_qqid
                gid = int(gid)
                minfo = await self.cqapi.get_group_member_info(
                    group_id=ctx['group_id'], user_id=gid)
                role = minfo.get('role') or None
                if role != 'owner' and role != 'admin' and gid not in self.admin_list:
                    return '只有群主或管理员可设置会名'
                self.clan[ctx['group_id']] = str(match.group(2))
                msg = f"[CQ:at,qq={gid}],公会名已设置为：" + str(match.group(2))
                return msg
        elif cmd == '查询本会':
            if ctx['message_type'] == 'group':
                if ctx['group_id'] not in self.clan:
                    return '本群未设置会名'
                else:
                    cname = str(self.clan[ctx['group_id']])
                    tindex = (int(match.group(2))-1) if match.group(
                        2) is not None else 0
                    r = requests.get(
                        str(self.api + '/default'), headers=self.header)
                    rget = r.json()
                    self.time = copy.deepcopy(rget['history'])
                    if tindex >= len(self.time) or tindex < 0:
                        return '请输入合法的时间序号'
                    r = requests.post(str(self.api + '/name/0'), data=json.dumps(
                        {"history": int(self.time[tindex]), "clanName": str(cname)}), headers=self.header)
                    rget = r.json()
                    msg = ''
                    for i in rget['data']:
                        msg += str(i['clan_name'])
                        msg += ':\n排名 '
                        msg += str(i['rank'])
                        msg += '\n分数 '
                        msg += str(i['damage'])
                        msg += '\n会长 '
                        msg += str(i['leader_name'])
                        msg += '\n\n'
                    msg += '数据获取时间：'
                    msg += str(time.strftime("%Y-%m-%d %H:%M:%S",
                                             time.localtime(self.time[0])))
                    return msg
        elif cmd == '查询档线':
            if ctx['message_type'] == 'group':
                tindex = (int(match.group(2))-1) if match.group(
                    2) is not None else 0
                r = requests.get(
                    str(self.api + '/default'), headers=self.header)
                rget = r.json()
                self.time = copy.deepcopy(rget['history'])
                if tindex >= len(self.time) or tindex < 0:
                    return '请输入合法的时间序号'
                r = requests.post(str(self.api + '/line'), data=json.dumps(
                    {"history": int(self.time[tindex])}), headers=self.header)
                rget = r.json()
                msg = ''
                for i in rget['data']:
                    msg += str(i['clan_name'])
                    msg += ': \n'
                    msg += str(i['damage']).ljust(10, ' ')
                    msg += ' 排名'
                    msg += str(i['rank'])
                    msg += '\n'
                msg += '\n'
                msg += '数据获取时间：'
                msg += str(time.strftime("%Y-%m-%d %H:%M:%S",
                                         time.localtime(self.time[0])))
                return msg
        elif cmd == '历史数据':
            if ctx['message_type'] == 'group':
                r = requests.get(
                    str(self.api + '/default'), headers=self.header)
                rget = r.json()
                self.time = copy.deepcopy(rget['history'])
                msg = ''
                for i in range(len(self.time)):
                    msg += str(i+1) + ' : '
                    msg += str(time.strftime("%Y-%m-%d %H:%M:%S",
                                             time.localtime(self.time[i])))
                    msg += '\n'
                msg += '\n使用 命令+时间序号 获取指定时间的数据'
                return msg
        elif cmd == '查询公会':
            cname = str(match.group(3))
            tindex = (int(match.group(2))-1) if match.group(
                2) is not None else 0
            r = requests.get(
                str(self.api + '/default'), headers=self.header)
            rget = r.json()
            self.time = copy.deepcopy(rget['history'])
            if tindex >= len(self.time) or tindex < 0:
                return '请输入合法的时间序号'
            r = requests.post(str(self.api + '/name/0'), data=json.dumps(
                {"history": int(self.time[tindex]), "clanName": str(cname)}), headers=self.header)
            rget = r.json()
            msg = ''
            for i in rget['data']:
                msg += str(i['clan_name'])
                msg += ':\n排名 '
                msg += str(i['rank'])
                msg += '\n分数 '
                msg += str(i['damage'])
                msg += '\n会长 '
                msg += str(i['leader_name'])
                msg += '\n\n'
            msg += '数据获取时间：'
            msg += str(time.strftime("%Y-%m-%d %H:%M:%S",
                                     time.localtime(self.time[0])))
            return msg
        elif cmd == '查询会长':
            lname = str(match.group(3))
            tindex = (int(match.group(2))-1) if match.group(
                2) is not None else 0
            r = requests.get(
                str(self.api + '/default'), headers=self.header)
            rget = r.json()
            self.time = copy.deepcopy(rget['history'])
            if tindex >= len(self.time) or tindex < 0:
                return '请输入合法的时间序号'
            r = requests.post(str(self.api + '/leader/0'), data=json.dumps(
                {"history": int(self.time[tindex]), "leaderName": str(lname)}), headers=self.header)
            rget = r.json()
            msg = ''
            for i in rget['data']:
                msg += str(i['clan_name'])
                msg += ':\n排名 '
                msg += str(i['rank'])
                msg += '\n分数 '
                msg += str(i['damage'])
                msg += '\n会长 '
                msg += str(i['leader_name'])
                msg += '\n\n'
            msg += '数据获取时间：'
            msg += str(time.strftime("%Y-%m-%d %H:%M:%S",
                                     time.localtime(self.time[0])))
            return msg
        elif cmd == '查询排名':
            rname = int(match.group(3)) if match.group(
                3) is not None else 0
            tindex = (int(match.group(2))-1) if match.group(
                2) is not None else 0
            r = requests.get(
                str(self.api + '/default'), headers=self.header)
            rget = r.json()
            self.time = copy.deepcopy(rget['history'])
            if tindex >= len(self.time) or tindex < 0:
                return '请输入合法的时间序号'
            r = requests.post(str(self.api + '/rank/' + str(rname)), data=json.dumps(
                {"history": int(self.time[tindex])}), headers=self.header)
            rget = r.json()
            msg = ''
            for i in rget['data']:
                msg += str(i['clan_name'])
                msg += ':\n排名 '
                msg += str(i['rank'])
                msg += '\n分数 '
                msg += str(i['damage'])
                msg += '\n会长 '
                msg += str(i['leader_name'])
                msg += '\n\n'
            msg += '数据获取时间：'
            msg += str(time.strftime("%Y-%m-%d %H:%M:%S",
                                     time.localtime(self.time[0])))
            return msg
        elif cmd == '查询分数':
            sname = int(match.group(3)) if match.group(
                3) is not None else 0
            tindex = (int(match.group(2))-1) if match.group(
                2) is not None else 0
            r = requests.get(
                str(self.api + '/default'), headers=self.header)
            rget = r.json()
            self.time = copy.deepcopy(rget['history'])
            if tindex >= len(self.time) or tindex < 0:
                return '请输入合法的时间序号'
            r = requests.post(str(self.api + '/score/' + str(sname)), data=json.dumps(
                {"history": int(self.time[tindex])}), headers=self.header)
            rget = r.json()
            msg = ''
            for i in rget['data']:
                msg += str(i['clan_name'])
                msg += ':\n排名 '
                msg += str(i['rank'])
                msg += '\n分数 '
                msg += str(i['damage'])
                msg += '\n会长 '
                msg += str(i['leader_name'])
                msg += '\n\n'
            msg += '数据获取时间：'
            msg += str(time.strftime("%Y-%m-%d %H:%M:%S",
                                     time.localtime(self.time[0])))
            return msg

        # 返回布尔值：是否阻止后续插件（返回None视作False）
        return False
