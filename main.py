from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import httpx
import json

@register("asbot_plugin_furry-API", "furryhm", "调用趣绮梦云黑API查询用户的插件", "1.0.0")
class QimengYunheiPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

    @filter.command("云黑查询", "查询用户云黑信息")
    async def query_yunhei(self, event: AstrMessageEvent, user_id: str = ""):
        # 获取用户输入的ID
        if not user_id:
            yield event.plain_result("请输入查询的用户ID，格式：云黑查询 <ID>")

        # 检查API Key是否配置
        api_key = self.config.get("api_key", "")
        if not api_key:
            yield event.plain_result("请先在插件配置中填写申请的API Key")

        # 构造API请求URL
        api_url = f"https://fz.qimeng.fun/OpenAPI/all_f.php?id={user_id}&key={api_key}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(api_url, timeout=10)
                response.raise_for_status()
                
                # 检查响应内容是否为空
                if not response.text.strip():
                    yield event.plain_result("查询失败：API返回空响应")
                    return
                    
                # 尝试解析JSON
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    yield event.plain_result(f"查询失败：API返回数据格式错误 ({str(e)})")
                    logger.error(f"JSON解析错误: {e}, 响应内容: {response.text}")
                    return

            # 解析返回数据（按API示例结构处理）
            if not data.get("info"):
                yield event.plain_result("未查询到该用户的信息")
                
            # 提取核心信息（处理嵌套结构）
            info_list = data.get("info", [{}])[0].get("info", [])
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
            yunhei_type = yunhei_info.get('type', 'none')
            yunhei_reason = yunhei_info.get('note', '无说明')
            yunhei_admin = yunhei_info.get('admin', '未知')
            yunhei_level = yunhei_info.get('level', '无')
            yunhei_date = yunhei_info.get('date', '无记录')
            
            # 格式化输出结果
            result = f"""📌 用户ID：{user}
\n📱 关联信息：
- 手机号绑定：{tel_bound}
- 微信绑定：{wechat_bound}
- 支付宝绑定：{alipay_bound}
- 实名认证：{realname_auth}
\n📊 发送统计：
- 加群数：{group_count}
- 月活数量：{monthly_active}
- 累计发送：{total_send}
- 首次发送：{first_send}
- 末次发送：{last_send}
\n🔍 云黑记录：
- 是否云黑：{yunhei_status}
- 类型：{yunhei_type}
- 原因：{yunhei_reason}
- 上黑管理：{yunhei_admin}
- 云黑等级：{yunhei_level}
- 记录日期：{yunhei_date}"""

            yield event.plain_result(result)

        except httpx.RequestError as e:
            yield event.plain_result(f"查询失败：网络错误（{str(e)}）")
        except (KeyError, IndexError) as e:
            yield event.plain_result(f"查询失败：数据解析错误（{str(e)}）")
        except Exception as e:
            yield event.plain_result(f"查询失败：{str(e)}")
