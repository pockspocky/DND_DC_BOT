"""
D&D场景描述生成器
使用Google Gemini API生成适合DM朗读的场景描述
"""
import logging
import os
from typing import Optional
from google import genai

logger = logging.getLogger(__name__)

class SceneGenerator:
    """场景描述生成器"""
    
    def __init__(self):
        # 设置API密钥
        os.environ['GEMINI_API_KEY'] = "AIzaSyATI4q2fKp0euRcN4jIYtbJrhJyW6GPUck"
        self.client = genai.Client()
        # 使用Gemini Flash模型
        self.model = "gemini-2.5-flash"
    
    async def generate_scene_description(
        self, 
        english_prompt: str, 
        length: int = 100,
        style: str = "描述性"
    ) -> Optional[str]:
        """
        生成场景描述
        
        Args:
            english_prompt: 英文描述提示
            length: 目标长度（字符数）
            style: 描述风格（支持任意风格词汇，如：描述性、神秘、恐怖、浪漫、幽默等）
            
        Returns:
            生成的中文场景描述
        """
        try:
            # 先尝试调用真实API
            try:
                # 构建系统提示
                system_prompt = self._build_system_prompt(length, style)
                
                # 构建完整提示（Gemini不需要分开system和user消息）
                full_prompt = f"""
{system_prompt}

请根据以下英文描述生成一段适合DM朗读的中文场景描述：

{english_prompt}

要求：
- 大约{length}字左右
- 风格：{style}
- 适合口语化朗读
- 营造沉浸感
- 不要包含具体的游戏规则或数值
"""
                
                # 使用Gemini API调用
                completion = self.client.models.generate_content(
                    model=self.model,
                    contents=full_prompt
                )
                
                response = completion.text
                if response:
                    # 清理响应，移除可能的格式标记
                    response = response.strip()
                    # 移除可能的引号
                    if response.startswith('"') and response.endswith('"'):
                        response = response[1:-1]
                    
                    logger.info(f"生成场景描述成功，长度: {len(response)}字")
                    return response
                
            except Exception as api_error:
                logger.warning(f"API调用失败，使用演示模式: {api_error}")
                # 如果API调用失败，返回演示内容
                return self._generate_demo_description(english_prompt, length, style)
            
            return None
            
        except Exception as e:
            logger.error(f"生成场景描述失败: {e}")
            return None
    
    def _build_system_prompt(self, length: int, style: str) -> str:
        """构建系统提示"""
        # 预定义风格的详细说明
        predefined_styles = {
            "描述性": "使用丰富的形容词和感官描述，让玩家能够想象出生动的画面",
            "戏剧性": "使用戏剧化的语言，增强情感冲击力，让场景更加引人入胜",
            "神秘": "营造神秘氛围，使用含蓄的描述和暗示，让玩家产生好奇心",
            "紧张": "使用紧迫的语言和短句，营造紧张刺激的氛围",
            "恐怖": "营造恐怖氛围，使用令人不安的描述和暗示，让玩家感到紧张和恐惧",
            "浪漫": "使用优美的语言和诗意的描述，营造浪漫温馨的氛围",
            "幽默": "使用轻松幽默的语言，带有一些有趣的细节和描述",
            "史诗": "使用宏伟壮阔的语言，展现史诗般的场面和氛围",
            "温馨": "使用温暖亲切的语言，营造舒适安全的氛围",
            "冒险": "使用充满活力的语言，强调探索和发现的刺激感"
        }
        
        # 如果是预定义风格，使用详细说明；否则直接使用用户输入作为风格指导
        if style in predefined_styles:
            style_instruction = predefined_styles[style]
        else:
            # 自定义风格，让AI根据风格词汇灵活发挥
            style_instruction = f"采用'{style}'的风格特点，根据这个风格词汇来调整语言风格、词汇选择和氛围营造"
        
        return f"""你是一个专业的龙与地下城（D&D）地下城主（DM）助手。你的任务是根据英文描述生成适合DM朗读的中文场景描述。

要求：
1. 文本长度控制在{length}字左右（可以上下浮动20%）
2. 风格：{style_instruction}
3. 语言特点：
   - 口语化，适合朗读
   - 富有画面感
   - 避免过于书面化的表达
   - 营造沉浸感
4. 内容特点：
   - 专注于环境、氛围、感官体验
   - 不包含具体的游戏机制或数值
   - 为玩家的行动留出空间
   - 适合fantasy奇幻设定

请直接输出描述文本，不要加任何前缀或后缀。"""
    
    def get_suggested_styles(self) -> list:
        """获取建议的描述风格（用户也可以输入自定义风格）"""
        return ["描述性", "戏剧性", "神秘", "紧张", "恐怖", "浪漫", "幽默", "史诗", "温馨", "冒险"]
    
    def _generate_demo_description(self, english_prompt: str, length: int, style: str) -> str:
        """生成演示场景描述（当API不可用时使用）"""
        # 基于输入生成合适的演示内容
        demo_descriptions = {
            "描述性": {
                "default": "夜幕降临在这片古老的森林中，月光透过茂密的树冠洒下斑驳的银辉。远处，几团神秘的蓝绿色光芒在树丛间若隐若现，仿佛精灵在暗中窃窃私语。空气中弥漫着潮湿的泥土气息和青草的清香，偶尔传来一声不明野兽的低吼声，让人不禁心生戒备。"
            },
            "戏剧性": {
                "default": "黑暗如潮水般吞噬着森林！诡异的光芒在树林深处闪烁，仿佛来自异世界的召唤！每一缕月光都透露着不祥的预兆，每一声风响都可能是危险的先兆！冒险者们，你们是否有勇气踏入这片被诅咒的土地？"
            },
            "神秘": {
                "default": "森林中隐藏着不为人知的秘密...那些飘忽的光芒似乎在暗示着什么，或许是古老的魔法，或许是失落的灵魂。树木的阴影中似乎有什么在窥视着，但当你仔细观察时，却什么也看不到。这片森林保守着它的秘密，等待着勇敢者去揭开真相。"
            },
            "紧张": {
                "default": "危险！树影中有什么在移动！那些诡异的光芒越来越近，时间不多了！你们必须立刻做出决定：是前进还是后退？每一步都可能踏入陷阱！保持警惕，准备战斗！"
            },
            "恐怖": {
                "default": "阴冷的恐惧感爬上脊背...森林中传来令人不安的声音，仿佛有什么邪恶的存在在黑暗中窥视着。枯败的树枝在风中发出如同哀嚎般的声响，地面上散落着不知名的骨头。这里的空气充满了死亡的气息，每一步都可能踏入未知的恐怖。"
            },
            "浪漫": {
                "default": "月光如水银般洒在森林中，为这片静谧的土地披上了一层梦幻的银纱。微风轻抚着树叶，奏响了大自然的夜曲。远处传来夜莺的歌声，与潺潺的溪水声交织成一曲优美的小夜曲。这里的一切都显得如此温柔而浪漫，仿佛是诗人笔下的仙境。"
            },
            "幽默": {
                "default": "这片森林看起来颇有些'个性'，树木们似乎在摆出各种奇怪的姿势，仿佛在参加一场'最佳造型'比赛。一只松鼠正端坐在树枝上，用一种颇为严肃的表情审视着你们，仿佛在说'又是一群迷路的冒险者'。就连那些神秘的光芒都显得有些俏皮，时亮时暗，像是在和你们玩捉迷藏。"
            },
            "史诗": {
                "default": "这里，曾经是古老传说的起源之地！巍峨的古树见证了无数英雄的崛起与陨落，每一片叶子都承载着传奇的记忆。那些在林间闪烁的光芒，正是远古魔法的余韵，诉说着这片土地曾经的辉煌。站在这里，你们仿佛能听到历史的回声，感受到命运的召唤。"
            },
            "温馨": {
                "default": "这片森林就像一个温暖的家，古老的橡树张开它粗壮的臂膀，为所有生灵提供庇护。林间的小径被柔软的苔藓覆盖，踩上去舒适而安静。不时有小动物从灌木丛中探出头来，用好奇而友善的眼神打量着你们。这里的空气清新甘甜，让人感到安心和放松。"
            },
            "冒险": {
                "default": "前方，未知的冒险正在召唤！这片森林充满了探索的机会，每一条小径都可能通向意想不到的发现。那些神秘的光芒就像是指引冒险者的信标，引导着勇敢的心灵踏上未知的旅程。空气中弥漫着兴奋的气息，仿佛整个世界都在等待着你们去探索和征服。"
            }
        }
        
        # 选择合适的演示描述
        if style in demo_descriptions:
            base_desc = demo_descriptions[style]["default"]
        else:
            # 自定义风格，使用通用描述模板
            base_desc = f"你踏入了一个充满'{style}'氛围的神秘场所。根据你所描述的'{english_prompt}'，这里的每一个细节都体现着这种独特的风格。空气中弥漫着特殊的气息，环境的每一个角落都在诉说着不同寻常的故事。这里等待着勇敢的冒险者去探索和发现。"
        
        # 根据目标长度调整描述
        if length < 80:
            # 短版本，取前半部分
            sentences = base_desc.split("。")
            result = "。".join(sentences[:2]) + "。"
        elif length > 150:
            # 长版本，添加更多细节
            additional_details = {
                "描述性": "微风轻拂，带来远方的消息。",
                "戏剧性": "命运的齿轮正在转动！",
                "神秘": "一切都有其深层的含义...",
                "紧张": "时间紧迫，必须马上行动！",
                "恐怖": "不祥的预感在心中蔓延...",
                "浪漫": "美好的回忆在此刻涌现。",
                "幽默": "看来今天会是个有趣的日子。",
                "史诗": "伟大的传说即将续写！",
                "温馨": "心中涌起暖流般的感动。",
                "冒险": "新的征程即将开始！"
            }
            additional = additional_details.get(style, f"这里的'{style}'氛围愈发浓郁。")
            result = base_desc + additional
        else:
            result = base_desc
        
        # 添加演示标记
        result = f"[演示模式] {result}"
        
        logger.info(f"生成演示场景描述，长度: {len(result)}字")
        return result

# 创建全局实例
scene_generator = SceneGenerator()