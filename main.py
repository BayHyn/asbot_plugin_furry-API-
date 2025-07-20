import requests
from astrbot import Plugin, on_command, Message

class QimengYunheiPlugin(Plugin):
    # 配置项：需填写申请的API Key（在插件配置文件中设置）
    config = {
        "api_key": ""  # 用户需替换为自己申请的key
    }

    # 命令触发：用户发送 "云黑查询 ID" 时触发
    @on_command("云黑查询", aliases=["查询云黑"], usage="云黑查询 <用户ID>")
    async def query_yunhei(self, ctx: Message):
        # 获取用户输入的ID
        user_id = ctx.get_args().strip()
        if not user_id:
            return await ctx.reply("请输入查询的用户ID，格式：云黑查询 <ID>")

        # 检查API Key是否配置
        api_key = self.config.get("api_key")
        if not api_key:
            return await ctx.reply("请先在插件配置中填写申请的API Key")

        # 构造API请求URL
        api_url = f"https://fz.qimeng.fun/OpenAPI/all_f.php?id={user_id}&key={api_key}"

        try:
            # 发送请求（添加超时控制，防止阻塞）
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()  # 检查HTTP错误状态码
            data = response.json()

            # 解析返回数据（按API示例结构处理）
            if not data.get("info"):
                return await ctx.reply("未查询到该用户的信息")

            # 提取核心信息（处理嵌套结构）
            info_list = data["info"][0]["info"]
            user_info = info_list[0]  # 用户基础信息
            stats_info = info_list[1]  # 发送统计信息
            yunhei_info = info_list[2]  # 云黑记录信息

            # 格式化输出结果
            result = [
                f"📌 用户ID：{user_info.get('user', '未知')}",
                "\n📱 关联信息：",
                f"- 手机号绑定：{'是' if user_info.get('tel') == 'true' else '否'}",
                f"- 微信绑定：{'是' if user_info.get('wx') == 'true' else '否'}",
                f"- 支付宝绑定：{'是' if user_info.get('zfb') == 'true' else '否'}",
                f"- 实名认证：{'是' if user_info.get('shiming') == 'true' else '否'}",
                "\n📊 发送统计：",
                f"- 加群数：{stats_info.get('group_num', '未知')}",
                f"- 月活数量：{stats_info.get('m_send_num', '未知')}",
                f"- 累计发送：{stats_info.get('send_num', '未知')}",
                f"- 首次发送：{stats_info.get('first_send', '无记录')}",
                f"- 末次发送：{stats_info.get('last_send', '无记录')}",
                "\n🔍 云黑记录：",
                f"- 是否云黑：{'是' if yunhei_info.get('yh') == 'true' else '否'}",
                f"- 类型：{yunhei_info.get('type', 'none')}",
                f"- 原因：{yunhei_info.get('note', '无说明')}",
                f"- 上黑管理：{yunhei_info.get('admin', '未知')}",
                f"- 云黑等级：{yunhei_info.get('level', '无')}",
                f"- 记录日期：{yunhei_info.get('date', '无记录')}"
            ]

            await ctx.reply("\n".join(result))

        except requests.exceptions.RequestException as e:
            await ctx.reply(f"查询失败：网络错误（{str(e)}）")
        except (KeyError, IndexError) as e:
            await ctx.reply(f"查询失败：数据解析错误（{str(e)}）")
        except Exception as e:
            await ctx.reply(f"查询失败：{str(e)}")

    # 插件元信息
    def __init__(self):
        super().__init__()
        self.name = "趣绮梦云黑查询"
        self.version = "1.0.0"
        self.description = "查询用户的云黑记录及关联信息（需申请API Key）"
        self.author = "furryHM"