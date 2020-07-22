'''
出道功能
重启清空所有出道记录
'''

import re
import copy
import asyncio
from typing import Any, Dict, Union

from aiocqhttp.api import Api
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from quart import Quart
from random import randint


class Debut:
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
        self.api = bot_api
        self.debut = {}
        self.debut1 = ['听说女装出道比较好呢~', '听说你想和望酱一起五万円一次?', '这是要转投ll还是cgss呢?']
        self.debut2 = ['多次出道?已为您买好机票', '会长的决定权也是很重要的!', '不考虑改个名吗?']
        self.debut3 = ['']

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
            #r"^(取消出道) *(\S*)?$",
            r"^(毕业|删除出道记录|添加出道管理员|删除出道管理员) *(?:\[CQ:at,qq=(\d+)\])? *$",
            r"^(申请出道|查看出道记录|清空出道记录) *$"
            #r"^(充值) *(-?\d+)([Ww万Kk千])? *(?:\[CQ:at,qq=(\d+)\])? *$",
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

        if cmd == '申请出道':
            if ctx['message_type'] == 'group':
                if ctx['group_id'] not in self.debut:
                    self.debut[ctx['group_id']] = {}
                if ctx['sender']['card'] not in self.debut[ctx['group_id']]:
                    self.debut[ctx['group_id']][ctx['user_id']] = ['', 0, 0]
                    self.debut[ctx['group_id']][ctx['user_id']
                                                ][0] = ctx['sender']['card']
                    self.debut[ctx['group_id']][ctx['user_id']][1] += 1
                    msg = "同意" + f"[CQ:at,qq={ctx['user_id']}]" + \
                        '的出道申请\n'
                    msg += self.debut1[randint(0, len(self.debut1)-1)]
                    return msg
                else:
                    self.debut[ctx['group_id']][ctx['user_id']
                                                ][0] = ctx['sender']['card']
                    self.debut[ctx['group_id']][ctx['user_id']][1] += 1
                    msg = "同意" + f"[CQ:at,qq={ctx['user_id']}]" + \
                        '的第' + str(self.debut[ctx['group_id']]
                                   [ctx['user_id']][1]) + '次出道申请\n'
                    msg += self.debut2[randint(0, len(self.debut2)-1)]
                    return msg
        elif cmd == '查看出道记录':
            if ctx['message_type'] == 'group':
                if ctx['group_id'] not in self.debut:
                    return '本群无人出道'
                else:
                    key = self.debut[ctx['group_id']].keys()
                    msg = ''
                    for i in key:
                        msg += str(self.debut[ctx['group_id']][i][0]) + ': 出道 ' + \
                            str(self.debut[ctx['group_id']][i][1]) + ' 次,毕业 ' + \
                            str(self.debut[ctx['group_id']][i][2]) + ' 次\n'
                    msg += '总计 ' + \
                        str(len(self.debut[ctx['group_id']])) + ' 人出道'
                    return msg
        elif cmd == '清空出道记录':
            if ctx['message_type'] == 'group':
                if ctx['user_id'] in self.admin_list:
                    if ctx['group_id'] not in self.debut:
                        return '本群无人出道'
                    else:
                        del self.debut[ctx['group_id']]
                        return '已清空出道记录'
                else:
                    return f"[CQ:at,qq={ctx['user_id']}],您无权清空出道记录"
        elif cmd == '毕业':
            if ctx['message_type'] == 'group':
                if ctx['user_id'] in self.admin_list:
                    gid = match.group(2) if match.group(
                        2) is not None else sender_qqid
                    gid = int(gid)
                    if ctx['group_id'] not in self.debut:
                        return '本群无人出道'
                    elif gid not in self.debut[ctx['group_id']]:
                        return '此成员从未出道,无法毕业'
                    elif self.debut[ctx['group_id']][gid][2] >= self.debut[ctx['group_id']][gid][1]:
                        return '此成员当前未出道,无法毕业'
                    else:
                        self.debut[ctx['group_id']][gid][2] += 1
                        return f"[CQ:at,qq={gid}]已毕业"
                else:
                    return f"[CQ:at,qq={ctx['user_id']}],管理员的决定权也是很重要的!"
        elif cmd == '删除出道记录':
            if ctx['message_type'] == 'group':
                if ctx['user_id'] in self.admin_list:
                    gid = match.group(2) if match.group(
                        2) is not None else sender_qqid
                    gid = int(gid)
                    if ctx['group_id'] not in self.debut:
                        return '本群无人出道'
                    elif gid not in self.debut[ctx['group_id']]:
                        return '此成员无出道记录'
                    else:
                        del self.debut[ctx['group_id']][gid]
                        return f"已删除[CQ:at,qq={gid}]的出道记录"
                else:
                    return f"[CQ:at,qq={ctx['user_id']}],管理员的决定权也是很重要的!"
        elif cmd == '添加出道管理员':
            if ctx['message_type'] == 'group':
                if ctx['user_id'] in self.setting["super-admin"] or ctx['sender']['role'] == 'owner':
                    gid = match.group(2) if match.group(
                        2) is not None else sender_qqid
                    gid = int(gid)
                    if gid in self.admin_list:
                        return '已存在此管理员'
                    else:
                        self.admin_list.append(gid)
                        return f"已将[CQ:at,qq={gid}]添加为出道管理员"
                else:
                    return f"[CQ:at,qq={ctx['user_id']}],怎么,想篡位?"
        elif cmd == '删除出道管理员':
            if ctx['message_type'] == 'group':
                if ctx['user_id'] in self.setting["super-admin"] or ctx['sender']['role'] == 'owner':
                    gid = match.group(2) if match.group(
                        2) is not None else sender_qqid
                    gid = int(gid)
                    if gid not in self.admin_list:
                        return '不存在此管理员'
                    elif gid in self.setting["super-admin"] or gid == ctx['user_id']:
                        return '无法删除此管理员'
                    else:
                        del self.admin_list[self.admin_list.index(gid)]
                        return f"已将出道管理员[CQ:at,qq={gid}]删除"
                else:
                    return f"[CQ:at,qq={ctx['user_id']}],怎么,想篡位?"

        # 返回布尔值：是否阻止后续插件（返回None视作False）
        return False
