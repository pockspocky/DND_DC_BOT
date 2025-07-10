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
            style: 描述风格（描述性/戏剧性/神秘/紧张）
            
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
        style_instructions = {
            "描述性": "使用丰富的形容词和感官描述，让玩家能够想象出生动的画面",
            "戏剧性": "使用戏剧化的语言，增强情感冲击力，让场景更加引人入胜",
            "神秘": "营造神秘氛围，使用含蓄的描述和暗示，让玩家产生好奇心",
            "紧张": "使用紧迫的语言和短句，营造紧张刺激的氛围"
        }
        
        return f"""你是一个专业的龙与地下城（D&D）地下城主（DM）助手。你的任务是根据英文描述生成适合DM朗读的中文场景描述。

要求：
1. 文本长度控制在{length}字左右（可以上下浮动20%）
2. 风格：{style_instructions.get(style, "描述性和沉浸感并重")}
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
    
    def get_available_styles(self) -> list:
        """获取可用的描述风格"""
        return ["描述性", "戏剧性", "神秘", "紧张"]
    
    def _generate_demo_description(self, english_prompt: str, length: int, style: str) -> str:
        """生成演示场景描述（当API不可用时使用）"""
        # 基于输入生成合适的演示内容
        demo_descriptions = {
            "描述性": {
                "forest": "夜幕降临在这片古老的森林中，月光透过茂密的树冠洒下斑驳的银辉。远处，几团神秘的蓝绿色光芒在树丛间若隐若现，仿佛精灵在暗中窃窃私语。空气中弥漫着潮湿的泥土气息和青草的清香，偶尔传来一声不明野兽的低吼声，让人不禁心生戒备。",
                "tavern": "酒馆里热闹非凡，篝火在壁炉中熊熊燃烧，为整个房间带来温暖的橙色光芒。几桌冒险者正在高声谈论着他们的英勇事迹，酒杯与酒杯碰撞发出清脆的声响。酒保忙碌地在吧台后穿梭，为客人们端上泡沫丰富的麦酒。整个酒馆弥漫着烤肉和麦芽的香味，让人感到温馨和舒适。",
                "dragon": "红龙俯冲而下，巨大的翅膀掀起狂风，村庄瞬间陷入恐慌。龙炎从天而降，点燃了茅草屋顶，浓烟滚滚升起。村民们惊慌失措地四散奔逃，孩子们的哭声与成年人的呼喊声混杂在一起。空气中弥漫着烟雾和恐惧的气息，这场灾难来得如此突然。",
                "library": "这座古老的图书馆仿佛拥有自己的生命，书页在空中优雅地飞舞，散发着淡淡的金色光芒。巨大的书架直达天花板，上面摆满了各种神秘的典籍。魔法符文在书脊上闪烁着光芒，时不时有羽毛笔自动在羊皮纸上书写着什么。整个空间充满了古老智慧的气息，仿佛每一本书都在诉说着远古的秘密。"
            },
            "戏剧性": {
                "forest": "黑暗如潮水般吞噬着森林！诡异的光芒在树林深处闪烁，仿佛来自异世界的召唤！每一缕月光都透露着不祥的预兆，每一声风响都可能是危险的先兆！冒险者们，你们是否有勇气踏入这片被诅咒的土地？",
                "tavern": "推门而入，一股暖流瞬间包围了你们！这里是冒险者的天堂，每一张桌子都有故事，每一杯酒都见证着传奇！英雄们在这里分享着他们的辉煌战绩，而新的冒险正在酝酿之中！",
                "dragon": "末日降临了！巨龙的怒吼震天动地，村庄在烈火中燃烧！这是一场生死存亡的战斗，英雄们，村民们的生命就掌握在你们手中！每一秒钟都至关重要，每一个决定都关乎生死！",
                "library": "踏入这座传奇的图书馆，你们见证了魔法的真正力量！书籍在空中起舞，仿佛在欢迎真正的知识寻求者！这里蕴藏着改变世界的力量，但同时也隐藏着致命的危险！"
            },
            "神秘": {
                "forest": "森林中隐藏着不为人知的秘密...那些飘忽的光芒似乎在暗示着什么，或许是古老的魔法，或许是失落的灵魂。树木的阴影中似乎有什么在窥视着，但当你仔细观察时，却什么也看不到。这片森林保守着它的秘密，等待着勇敢者去揭开真相。",
                "tavern": "酒馆的角落里，一位斗篷人正在低声交谈...他们的话语中提到了一些不寻常的事情。其他客人似乎都在刻意避开那张桌子，仿佛知道什么不能说的秘密。酒保时不时投向那个方向的眼神，透露着某种担忧。",
                "dragon": "这不是一次普通的龙袭...村民们的表情中除了恐惧，还有一丝说不出的认命。似乎他们早就知道这一天会到来。而那头龙，它的眼神中闪烁着超越野兽本能的智慧，仿佛在寻找着什么特定的东西。",
                "library": "这座图书馆中蕴藏着被遗忘的知识...每本书都可能隐藏着改变命运的秘密。书页的翻动声似乎在诉说着古老的咒语，而那些飘浮的羽毛笔，正在记录着什么人无法理解的内容。"
            },
            "紧张": {
                "forest": "危险！树影中有什么在移动！那些诡异的光芒越来越近，时间不多了！你们必须立刻做出决定：是前进还是后退？每一步都可能踏入陷阱！保持警惕，准备战斗！",
                "tavern": "突然间，酒馆里的喧闹声停止了！所有人都转过头看向门口，那里站着一个不速之客。气氛瞬间变得凝重，你们能感觉到危险正在逼近。快，必须立刻行动！",
                "dragon": "没时间了！龙炎越来越近，村民们的生命危在旦夕！你们必须立刻采取行动，每一秒的犹豫都可能导致更多伤亡！冲向前去，现在就是英雄诞生的时刻！",
                "library": "小心！魔法符文开始闪烁，这意味着什么不好的事情即将发生！那些飘浮的书籍突然停止了，仿佛在警告着什么。你们必须快速找到需要的信息，否则就太晚了！"
            }
        }
        
        # 根据关键词匹配合适的演示描述
        prompt_lower = english_prompt.lower()
        if "forest" in prompt_lower or "tree" in prompt_lower or "woods" in prompt_lower:
            base_desc = demo_descriptions[style]["forest"]
        elif "tavern" in prompt_lower or "inn" in prompt_lower or "bar" in prompt_lower:
            base_desc = demo_descriptions[style]["tavern"]
        elif "dragon" in prompt_lower or "fire" in prompt_lower or "attack" in prompt_lower:
            base_desc = demo_descriptions[style]["dragon"]
        elif "library" in prompt_lower or "book" in prompt_lower or "magic" in prompt_lower:
            base_desc = demo_descriptions[style]["library"]
        else:
            # 默认使用森林场景
            base_desc = demo_descriptions[style]["forest"]
        
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
                "紧张": "时间紧迫，必须马上行动！"
            }
            result = base_desc + additional_details[style]
        else:
            result = base_desc
        
        # 添加演示标记
        result = f"[演示模式] {result}"
        
        logger.info(f"生成演示场景描述，长度: {len(result)}字")
        return result

# 创建全局实例
scene_generator = SceneGenerator()