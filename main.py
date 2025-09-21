from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import httpx
import json
import asyncio
import astrbot.api.message_components as Comp

@register("asbot_plugin_furry-API", "furryhm", "调用趣绮梦云黑API查询用户的插件", "2.3.0")
class QimengYunheiPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    @filter.command("云黑", alias={"云黑查询", "查云黑"})
    async def query_yunhei(self, event: AstrMessageEvent, user_id: str = ""):
        """
        /云黑@某人 或 /云黑 QQ 或 /云黑查询 QQ
        """
        
        # 解析目标用户ID
        self_id = event.get_self_id()
        target_id = next(
            (
                str(seg.qq)
                for seg in event.get_messages()
                if isinstance(seg, Comp.At) and str(seg.qq) != self_id
            ),
            None,
        )
        
        # 如果没有@用户，则使用传入的user_id参数或查询自己
        if not target_id:
            target_id = (
                user_id
                if user_id and str(user_id) != self_id
                else event.get_sender_id()
            )
            
        # 确保最终使用的user_id是target_id
        final_user_id = target_id

        # 检查API Key是否配置
        api_key = self.config.get("api_key", "")
        if not api_key:
            yield event.plain_result("请先在插件配置中填写申请的API Key")

        # 构造API请求URL
        api_url = f"https://fz.qimeng.fun/OpenAPI/all_f.php?id={final_user_id}&key={api_key}"

        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                # 请求云黑信息API
                yunhei_response = await client.get(api_url, timeout=10)
                
                # 处理云黑查询结果
                if isinstance(yunhei_response, Exception):
                    yield event.plain_result(f"查询失败：网络错误（{str(yunhei_response)}）")
                    return
                    
                yunhei_response.raise_for_status()
                
                # 检查响应内容是否为空
                if not yunhei_response.text.strip():
                    yield event.plain_result(f"查询失败：API返回空响应 (用户ID: {final_user_id})")
                    return
                    
                # 尝试解析JSON
                try:
                    data = yunhei_response.json()
                except json.JSONDecodeError as e:
                    yield event.plain_result(f"查询失败：API返回数据格式错误 ({str(e)})")
                    logger.error(f"JSON解析错误: {e}, 响应内容: {yunhei_response.text}")
                    return

            # 解析返回数据（按API示例结构处理）
            if not data.get("info"):
                yield event.plain_result("未查询到该用户的信息")
                
            # 提取核心信息（处理嵌套结构）
            info_list = data.get("info", [])
            if len(info_list) < 3:
                yield event.plain_result("查询失败：API返回数据格式不完整")
            user_info = info_list[0]  # 用户基础信息
            stats_info = info_list[1]  # 发送统计信息
            yunhei_info = info_list[2]  # 云黑记录信息

            # 辅助函数用于判断布尔值
            def is_true(value):
                return str(value).lower() == 'true' if value is not None else False

            # 提取用户信息
            user = user_info.get('user', '未知')
            tel_bound = '是' if is_true(user_info.get('tel')) else '否'
            wechat_bound = '是' if is_true(user_info.get('wx')) else '否'
            alipay_bound = '是' if is_true(user_info.get('zfb')) else '否'
            realname_auth = '是' if is_true(user_info.get('shiming')) else '否'
            
            # 提取发送统计
            group_count = stats_info.get('group_num', '未知')
            monthly_active = stats_info.get('m_send_num', '未知')
            total_send = stats_info.get('send_num', '未知')
            first_send = stats_info.get('first_send', '无记录')
            last_send = stats_info.get('last_send', '无记录')
            
            # 提取云黑记录
            yunhei_status = '是' if is_true(yunhei_info.get('yh')) else '否'
            yunhei_type = yunhei_info.get('type', 'none') if yunhei_info.get('type') else '无'
            
            # 为云黑类型添加中文翻译
            type_translations = {
                'none': '无违规',
                'yunhei': '云黑'
            }
            yunhei_type = type_translations.get(yunhei_type, yunhei_type)
            
            yunhei_reason = yunhei_info.get('note', '无说明') if yunhei_info.get('note') else '无说明'
            yunhei_admin = yunhei_info.get('admin', '未知') if yunhei_info.get('admin') else '未知'
            yunhei_level = yunhei_info.get('level', '无') if yunhei_info.get('level') else '无'
            yunhei_date = yunhei_info.get('date', '无记录') if yunhei_info.get('date') else '无记录'
            
            # 使用 AstrBot API 获取用户信息和头像
            qq_name = user  # 默认使用QQ号作为名称
            avatar_url = f"https://q4.qlogo.cn/headimg_dl?dst_uin={final_user_id}&spec=640"
            
            try:
                # 尝试通过 AstrBot API 获取用户信息（参考Box插件实现方式）
                stranger_info = await event.bot.get_stranger_info(user_id=int(final_user_id))
                if stranger_info and 'nickname' in stranger_info and stranger_info['nickname']:
                    qq_name = stranger_info['nickname']
                elif stranger_info and 'name' in stranger_info and stranger_info['name']:
                    qq_name = stranger_info['name']
            except Exception as e:
                logger.warning(f"无法通过 AstrBot API 获取用户信息: {e}")
                # 回退到默认名称（QQ号）
            
            # 格式化输出结果 - 按照头像、名字、QQ号的顺序
            result = f"""【{qq_name}的信息档案】
名称：{qq_name}
QQ 号：{user}
🔗 关联信息绑定状态
手机号绑定：{tel_bound}
微信绑定：{wechat_bound}
支付宝绑定：{alipay_bound}
实名认证：{realname_auth}
📊 发送行为统计
加群数：{group_count} 个
月活数量：{monthly_active}
累计发送次数：{total_send} 次
首次发送时间：{first_send}
末次发送时间：{last_send}
🔍 云黑记录查询
是否云黑：{yunhei_status}
类型：{yunhei_type}
原因：{yunhei_reason}
上黑管理：{yunhei_admin}
云黑等级：{yunhei_level}
记录日期：{yunhei_date}"""

            # 如果有头像URL，则将头像和文本合并成一条消息发送（使用file参数）
            if avatar_url:
                try:
                    # 合并头像和文本为一条消息（使用file参数）
                    message_chain = [
                        Comp.Image(file=avatar_url),
                        Comp.Plain(text=result)
                    ]
                    yield event.chain_result(message_chain)
                except Exception as e:
                    logger.error(f"发送头像和文本失败: {e}")
                    # 如果合并发送失败，则分别发送
                    yield event.image_result(avatar_url)
                    yield event.plain_result(result)
            else:
                # 没有头像则只发送文本结果
                yield event.plain_result(result)

        except httpx.RequestError as e:
            yield event.plain_result(f"查询失败：网络错误（{str(e)}）")
        except (KeyError, IndexError) as e:
            yield event.plain_result(f"查询失败：数据解析错误（{str(e)}）")
        except Exception as e:
            yield event.plain_result(f"查询失败：{str(e)}")