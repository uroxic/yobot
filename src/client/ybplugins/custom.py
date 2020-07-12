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
        if cmd == '申请出道':
            if ctx['message_type'] == 'group':
                if ctx['group_id'] not in self.debut:
                    self.debut[ctx['group_id']] = {}
                if ctx['sender']['card'] not in self.debut[ctx['group_id']]:
                    self.debut[ctx['group_id']][ctx['sender']['card']] = 1
                    msg = "同意" + f"[CQ:at,qq={ctx['user_id']}]" + \
                        '的出道申请\n'
                    msg += self.debut1[randint(0, len(self.debut1)-1)]
                    return msg
                else:
                    self.debut[ctx['group_id']][ctx['sender']['card']] += 1
                    msg = "同意" + f"[CQ:at,qq={ctx['user_id']}]" + \
                        '的第' + str(self.debut[ctx['group_id']]
                                   [ctx['sender']['card']]) + '次出道申请\n'
                    msg += self.debut2[randint(0, len(self.debut2)-1)]
                    return msg
        if cmd == '查看出道记录':
            if ctx['message_type'] == 'group':
                if ctx['group_id'] not in self.debut:
                    return '本群无人出道'
                else:
                    key = self.debut[ctx['group_id']].keys()
                    msg = ''
                    for i in key:
                        msg += str(i) + ': 出道 ' + \
                            str(self.debut[ctx['group_id']][i]) + ' 次\n'
                    msg += '总计 ' + \
                        str(len(self.debut[ctx['group_id']])) + ' 人出道'
                    return msg
        if cmd == '清空出道记录':
            if ctx['message_type'] == 'group':
                if ctx['user_id'] in self.admin_list or ctx['sender']['role'] == 'owner' or ctx['sender']['role'] == 'admin':
                    if ctx['group_id'] not in self.debut:
                        return '本群无人出道'
                    else:
                        del self.debut[ctx['group_id']]
                        return '已清空出道记录'
                else:
                    return f"[CQ:at,qq={ctx['user_id']}],您无权清空出道记录"

        # 返回布尔值：是否阻止后续插件（返回None视作False）
        return False
