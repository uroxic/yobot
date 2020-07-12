'''
合刀功能
重启清空合刀列表
'''

import re
import copy
import asyncio
from typing import Any, Dict, Union

from aiocqhttp.api import Api
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from quart import Quart
from random import randint


class cooperate:
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
        self.cooperate = {}

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
            r"^(设置刀型) *(\S+) *(?:\[CQ:at,qq=(\d+)\])? *$",
            r"^(申请合刀|取消合刀|进入合刀|完成合刀|添加合刀管理员|删除合刀管理员) *(?:\[CQ:at,qq=(\d+)\])? *$",
            r"^(查看合刀列表|清空合刀列表) *$",
            r"^(预计伤害) *(-?\d+)([Ww万Kk千])? *(?:\[CQ:at,qq=(\d+)\])? *$"
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

        if cmd == '查看合刀列表':
            if ctx['message_type'] == 'group':
                if ctx['group_id'] not in self.cooperate:
                    return '合刀列表为空'
                else:
                    key = self.cooperate[ctx['group_id']].keys()
                    msg = ''
                    for i in key:
                        msg += str(self.cooperate[ctx['group_id']][i][0]) + '(' + str(
                            self.cooperate[ctx['group_id']][i][4]) + ')' + ':  '
                        if self.cooperate[ctx['group_id']][i][3] == 1:
                            msg += '已完成'
                        elif self.cooperate[ctx['group_id']][i][2] != None:
                            msg += '预计' + \
                                str(self.cooperate[ctx['group_id']][i][2])
                        elif self.cooperate[ctx['group_id']][i][1] == 1:
                            msg += '已进入'
                        else:
                            msg += '未进入'
                        msg += '\n'
                    msg += '总计 ' + \
                        str(len(self.cooperate[ctx['group_id']])) + ' 人'
                    return msg
        elif cmd == '清空合刀列表':
            if ctx['message_type'] == 'group':
                if ctx['user_id'] in self.admin_list:
                    if ctx['group_id'] not in self.cooperate:
                        return '合刀列表为空'
                    else:
                        del self.cooperate[ctx['group_id']]
                        return '已清空合刀列表'
                else:
                    return f"[CQ:at,qq={ctx['user_id']}],您无权清空合刀列表"
        elif cmd == '申请合刀':
            if ctx['message_type'] == 'group':
                gid = match.group(2) if match.group(
                    2) is not None else sender_qqid
                gid = int(gid)
                if ctx['group_id'] not in self.cooperate:
                    self.cooperate[ctx['group_id']] = {}
                if gid not in self.cooperate[ctx['group_id']]:
                    self.cooperate[ctx['group_id']][gid] = [
                        '', 0, None, 0, '未知']
                    minfo = await self.api.get_group_member_info(
                        group_id=ctx['group_id'], user_id=gid)
                    self.cooperate[ctx['group_id']][gid][0] = minfo.get(
                        'card') or minfo['nickname']
                    msg = f"已将[CQ:at,qq={gid}]加入合刀列表"
                    return msg
                else:
                    msg = '此成员已在合刀列表中'
                    return msg
        elif cmd == '取消合刀':
            if ctx['message_type'] == 'group':
                gid = match.group(2) if match.group(
                    2) is not None else sender_qqid
                gid = int(gid)
                if ctx['group_id'] not in self.cooperate:
                    return '合刀列表为空'
                elif gid not in self.cooperate[ctx['group_id']]:
                    return '此成员未在合刀列表中'
                elif self.cooperate[ctx['group_id']][gid][1] != 0 and ctx['user_id'] not in self.admin_list:
                    return '此成员已进入战斗,须由管理员取消合刀'
                else:
                    del self.cooperate[ctx['group_id']][gid]
                    return f"已取消[CQ:at,qq={gid}]合刀"
        elif cmd == '进入合刀':
            if ctx['message_type'] == 'group':
                gid = match.group(2) if match.group(
                    2) is not None else sender_qqid
                gid = int(gid)
                if ctx['group_id'] not in self.cooperate:
                    return '合刀列表为空'
                if gid not in self.cooperate[ctx['group_id']]:
                    return '此成员未在合刀列表中'
                if self.cooperate[ctx['group_id']][gid][1] == 0:
                    self.cooperate[ctx['group_id']][gid][1] = 1
                    msg = f"[CQ:at,qq={gid}]已进入合刀"
                    return msg
                else:
                    msg = '此成员已进入合刀'
                    return msg
        elif cmd == '预计伤害':
            if ctx['message_type'] == 'group':
                gid = match.group(4) if match.group(
                    4) is not None else sender_qqid
                gid = int(gid)
                if ctx['group_id'] not in self.cooperate:
                    return '合刀列表为空'
                if gid not in self.cooperate[ctx['group_id']]:
                    return '此成员未在合刀列表中'
                unit = {
                    'W': 10000,
                    'w': 10000,
                    '万': 10000,
                    'k': 1000,
                    'K': 1000,
                    '千': 1000,
                }.get(match.group(3), 1)
                damage = int(match.group(2)) * unit
                damage = int(damage/10000+0.5)
                self.cooperate[ctx['group_id']][gid][2] = str(damage) + 'w'
                return f"[CQ:at,qq={gid}]预计伤害为{self.cooperate[ctx['group_id']][gid][2]}"
        elif cmd == '完成合刀':
            if ctx['message_type'] == 'group':
                gid = match.group(2) if match.group(
                    2) is not None else sender_qqid
                gid = int(gid)
                if ctx['group_id'] not in self.cooperate:
                    return '合刀列表为空'
                if gid not in self.cooperate[ctx['group_id']]:
                    return '此成员未在合刀列表中'
                if self.cooperate[ctx['group_id']][gid][3] == 0:
                    self.cooperate[ctx['group_id']][gid][3] = 1
                    msg = f"[CQ:at,qq={gid}]已完成合刀"
                    return msg
                else:
                    msg = '此成员已完成合刀'
                    return msg
        elif cmd == '设置刀型':
            if ctx['message_type'] == 'group':
                gid = match.group(3) if match.group(
                    3) is not None else sender_qqid
                gid = int(gid)
                if ctx['group_id'] not in self.cooperate:
                    return '合刀列表为空'
                if gid not in self.cooperate[ctx['group_id']]:
                    return '此成员未在合刀列表中'
                self.cooperate[ctx['group_id']][gid][4] = match.group(2)
                msg = f"[CQ:at,qq={gid}]的刀型已设置为：" + str(match.group(2))
                return msg
        elif cmd == '添加合刀管理员':
            if ctx['message_type'] == 'group':
                if ctx['user_id'] in self.setting["super-admin"] or ctx['sender']['role'] == 'owner':
                    gid = match.group(2) if match.group(
                        2) is not None else sender_qqid
                    gid = int(gid)
                    if gid in self.admin_list:
                        return '已存在此管理员'
                    else:
                        self.admin_list.append(gid)
                        return f"已将[CQ:at,qq={gid}]添加为合刀管理员"
                else:
                    return f"[CQ:at,qq={ctx['user_id']}],怎么,想篡位?"
        elif cmd == '删除合刀管理员':
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
                        return f"已将合刀管理员[CQ:at,qq={gid}]删除"
                else:
                    return f"[CQ:at,qq={ctx['user_id']}],怎么,想篡位?"

        # 返回布尔值：是否阻止后续插件（返回None视作False）
        return False
