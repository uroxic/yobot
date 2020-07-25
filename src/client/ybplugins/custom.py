'''
自定义功能：

在这里可以编写自定义的功能，
编写完毕后记得 git commit，

这个模块只是为了快速编写小功能，如果想编写完整插件可以使用：
https://github.com/richardchien/python-aiocqhttp
或者
https://github.com/richardchien/nonebot

关于PR：
如果基于此文件的PR，请在此目录下新建一个`.py`文件，并修改类名
然后在`yobot.py`中添加`import`（这一步可以交给仓库管理者做）
'''

import re
import os
import json
import asyncio
from typing import Any, Dict, Union

from aiocqhttp.api import Api
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from quart import Quart
from random import randint


class Custom:
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
        self.admin_list = self.setting["super-admin"]
        self.novel_file = open(os.path.join(
            self.setting["dirname"], "novel.json"), "rt", encoding="utf-8")
        self.novel = json.load(self.novel_file)
        self.novel_list = list(self.novel.keys())
        self.sheet_file = open(os.path.join(
            self.setting["dirname"], "sheet.json"), "rt", encoding="utf-8")
        self.sheet = json.load(self.sheet_file)
        self.sheet_list = list(self.sheet.keys())
        self.pot = {}
        self.potmbr = {}

        # 这是cqhttp的api，详见cqhttp文档
        self.api = bot_api

        # # 注册定时任务，详见apscheduler文档
        # @scheduler.scheduled_job('cron', hour=8)
        # async def good_morning():
        #     await self.api.send_group_msg(group_id=123456, message='早上好')

        # # 注册web路由，详见flask与quart文档
        # @app.route('/is-bot-running', methods=['GET'])
        # async def check_bot():
        #     return 'yes, bot is running'

    def fuzzyfinder(self, user_input, collection):
        suggestions1 = []
        pattern = '.*?'.join(user_input)    # Converts 'djm' to 'd.*?j.*?m'
        regex1 = re.compile(pattern)         # Compiles a regex.
        for item in collection:
            # Checks if the current item matches the regex.
            match = regex1.search(item)
            if match:
                suggestions1.append((len(match.group()), match.start(), item))
        temp1 = [x for _, _, x in sorted(suggestions1)]
        suggestions2 = []
        pattern = '|'.join(user_input)    # Converts 'djm' to 'd.*?j.*?m'
        regex2 = re.compile(pattern)         # Compiles a regex.
        for item in collection:
            # Checks if the current item matches the regex.
            match = regex2.search(item)
            if match and item not in temp1:
                suggestions2.append(
                    (len(regex2.findall(item)), match.start(), item))
        temp2 = [x for _, _, x in sorted(suggestions2)]
        if len(temp1):
            temp = temp1 + temp2[:5]
        else:
            temp = temp2[:10]
        return temp

    async def execute_async(self, ctx: Dict[str, Any]) -> Union[None, bool, str]:
        '''
        每次bot接收有效消息时触发

        参数ctx 具体格式见：https://cqhttp.cc/docs/#/Post
        '''
        # 注意：这是一个异步函数，禁止使用阻塞操作（比如requests）

        # 如果需要使用，请注释掉下面一行
        # return

        cmd = ctx['raw_message']
        if cmd == 'box登记':
            if ctx['message_type'] == 'group':
                # 调用api发送消息，详见cqhttp文档
                await self.api.send_group_msg(
                    group_id=ctx['group_id'], message='https://wj.qq.com/s2/6637810/dece/')

                # 返回字符串：发送消息并阻止后续插件
                return '若链接失效请通知管理员'
            if ctx['message_type'] == 'private':
                # 调用api发送消息，详见cqhttp文档
                await self.api.send_private_msg(
                    user_id=ctx['user_id'], message='https://wj.qq.com/s2/6637810/dece/')

                # 返回字符串：发送消息并阻止后续插件
                return '若链接失效请通知管理员'
        if cmd == '排刀表':
            if ctx['message_type'] == 'group':
                # 调用api发送消息，详见cqhttp文档
                await self.api.send_group_msg(
                    group_id=ctx['group_id'], message='https://docs.qq.com/sheet/DY1VSblJDQ0Vqbnhr')

                # 返回字符串：发送消息并阻止后续插件
                return '若链接失效请通知管理员'
            if ctx['message_type'] == 'private':
                # 调用api发送消息，详见cqhttp文档
                await self.api.send_private_msg(
                    user_id=ctx['user_id'], message='https://docs.qq.com/sheet/DY1VSblJDQ0Vqbnhr')

                # 返回字符串：发送消息并阻止后续插件
                return '若链接失效请通知管理员'
        if cmd[:5] == '来份轻小说' or cmd == '来点轻小说':
            match = re.match(r'^(来份轻小说|来点轻小说) *(?:[\:：](.*))?$', cmd)
            if ctx['message_type'] == 'private':
                msg = ''
            else:
                msg = f"[CQ:at,qq={ctx['user_id']}]\n"
            if match.group(2) is None:
                index = self.novel_list[randint(0, len(self.novel_list)-1)]
            elif str(match.group(2)) in self.novel_list:
                index = str(match.group(2))
            else:
                slist = self.fuzzyfinder(str(match.group(2)), self.novel_list)
                if len(slist):
                    msg += '您要找的可能是：\n\n'
                    for index in slist:
                        msg += str(index + ': \n' + self.novel[index] + '\n')
                    msg += '\n链接需要科学地打开，若链接失效请通知管理员'
                    msg += '\n若提示密钥无效，请检查链接是否有多余的后缀，或直接复制链接至浏览器打开'
                else:
                    msg += '未在列表中找到此小说'
                return msg
            msg += str(index + ': \n' + self.novel[index] + '\n')
            msg += '\n链接需要科学地打开，若链接失效请通知管理员'
            msg += '\n若提示密钥无效，请检查链接是否有多余的后缀，或直接复制链接至浏览器打开'
            return msg
        if cmd == '轻小说目录':
            if ctx['message_type'] == 'private':
                msg = ''
            else:
                msg = f"[CQ:at,qq={ctx['user_id']}]"
            for i in self.novel_list:
                msg += '\n' + str(i)
            return msg
        if cmd[:5] == '来份琴谱' or cmd == '来点琴谱':
            match = re.match(r'^(来份琴谱|来点琴谱) *(?:[\:：](.*))?$', cmd)
            if ctx['message_type'] == 'private':
                msg = ''
            else:
                msg = f"[CQ:at,qq={ctx['user_id']}]\n"
            if match.group(2) is None:
                index = self.sheet_list[randint(0, len(self.sheet_list)-1)]
            elif str(match.group(2)) in self.sheet_list:
                index = str(match.group(2))
            else:
                slist = self.fuzzyfinder(str(match.group(2)), self.sheet_list)
                if len(slist):
                    msg += '您要找的可能是：\n\n'
                    for index in slist:
                        msg += str(index + ': \n' + self.sheet[index] + '\n')
                    msg += '\n链接需要科学地打开，若链接失效请通知管理员'
                    msg += '\n若提示密钥无效，请检查链接是否有多余的后缀，或直接复制链接至浏览器打开'
                else:
                    msg += '未在列表中找到此小说'
                return msg
            msg += str(index + ': \n' + self.sheet[index] + '\n')
            msg += '\n链接需要科学地打开，若链接失效请通知管理员'
            msg += '\n若提示密钥无效，请检查链接是否有多余的后缀，或直接复制链接至浏览器打开'
            return msg
        if cmd == '琴谱目录':
            if ctx['message_type'] == 'private':
                msg = ''
            else:
                msg = f"[CQ:at,qq={ctx['user_id']}]"
            for i in self.sheet_list:
                msg += '\n' + str(i)
            return msg
        if cmd[:2] == '约锅':
            if ctx['message_type'] == 'group':
                match = re.match(r"^(约锅) *(\S*)?$", cmd)
                msg = f"[CQ:at,qq={ctx['user_id']}]\n"
                if match.group(2) is None or str(match.group(2)) == '' or str(match.group(2)) == '?' or str(match.group(2)) == '？':
                    if len(self.pot) == 0:
                        msg += '当前无人约锅'
                    else:
                        loclist = list(self.pot.keys())
                        for i in loclist:
                            msg += '\n' + str(i) + ':\n'
                            potlist = list(self.pot[i].keys())
                            for j in potlist:
                                msg += str(self.pot[i][j]) + '\n'
                    msg += '\n请输入约锅+地点加入约锅'
                else:
                    if ctx['user_id'] not in self.potmbr:
                        location = str(match.group(2))
                        minfo = await self.api.get_group_member_info(
                            group_id=ctx['group_id'], user_id=ctx['user_id'])
                        self.potmbr[ctx['user_id']] = location
                        if location in self.pot:
                            self.pot[location][ctx['user_id']] = minfo.get(
                                'card') or minfo['nickname']
                        else:
                            self.pot[location] = {}
                            self.pot[location][ctx['user_id']] = minfo.get(
                                'card') or minfo['nickname']
                        msg += '成功加入' + str(location) + '的约锅'
                    else:
                        msg += '您已约过锅'
            return msg
        if cmd == '咕咕':
            if ctx['message_type'] == 'group':
                msg = f"[CQ:at,qq={ctx['user_id']}]\n"
                if ctx['user_id'] not in self.potmbr:
                    msg += '您当前未约锅'
                else:
                    msg += '成功咕咕' + str(self.potmbr[ctx['user_id']]) + '的约锅'
                    del self.pot[self.potmbr[ctx['user_id']]][ctx['user_id']]
                    potlist = list(
                        self.pot[self.potmbr[ctx['user_id']]].keys())
                    if len(potlist):
                        msg += '\n请以下成员注意'
                        for i in potlist:
                            msg += f"\n[CQ:at,qq={i}]"
                    else:
                        del self.pot[self.potmbr[ctx['user_id']]]
                    del self.potmbr[ctx['user_id']]
            return msg
        if cmd == '走起':
            if ctx['message_type'] == 'group':
                msg = f"[CQ:at,qq={ctx['user_id']}]\n"
                if ctx['user_id'] not in self.potmbr:
                    msg += '您当前未约锅'
                else:
                    msg += str(self.potmbr[ctx['user_id']]) + '的约锅已开始'
                    del self.pot[self.potmbr[ctx['user_id']]][ctx['user_id']]
                    potlist = list(
                        self.pot[self.potmbr[ctx['user_id']]].keys())
                    if len(potlist):
                        msg += '\n请以下成员注意'
                        for i in potlist:
                            msg += f"\n[CQ:at,qq={i}]"
                            del self.potmbr[i]
                    del self.pot[self.potmbr[ctx['user_id']]]
                    del self.potmbr[ctx['user_id']]
            return msg
            # 返回布尔值：是否阻止后续插件（返回None视作False）
        return False
