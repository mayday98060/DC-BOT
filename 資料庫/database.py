#歌單
song_list = {
    1: "UnwelcomeSchool-Mitsukiyo.wav",
    2: "あの夢をなぞって-YOASOBI.wav",
    3: "青のすみか-キタニタツヤ.wav",
    4: "天ノ弱-164.wav",
    5: "再生-ピコン.wav",
    6: "怪物-YOASOBI.wav",
    7: "紅蓮華-Lisa.wav",
    8: "ベテルギウス-優里.wav",
    9: "証-flumpool.wav",
    10: "SPECIALZ-King Gnu.wav",
    11: "打上花火-DAOKO x 米津玄師.wav",
    12: "炎-Lisa.wav",
    13: "Subtitle-Official髭男dism.wav",
    14: "ロミオとシンデレラ-doriko.wav",
    15: "獨りんぼエンヴィー-koyori.wav",
    16: "アスノヨゾラ哨戒班-Orangestar.wav",
    17: "地球最後の告白を-kemu.wav",
    18: "TATTOO-Official髭男dism.wav",
    19: "ツキミソウ-Novelbright.wav",
    20: "I hate me-Lilyu.wav",
    21: "不為誰而作的歌-林俊傑.wav",
    22: "我還是愛著你-MP魔幻力量.wav",
    23: "傷心的人別聽慢歌-五月天.wav",
    24: "初音ミクの消失-cosMo@暴走P.wav",
    25: "HERO-Ayase.wav",
    26: "君に届け-flumpool.wav",
    27: "勇者-YOASOBI.wav",
    28: "粛聖!!ロリ神レクイエム☆-しぐれうい.wav",
    29: "Happy Halloween-Junky.wav",
    30: "ノンブレス・オブリージュ.wav",
    31: "spiral-LONGMAN.wav",
    32: "宿命-Official髭男dism.wav",
    33: "私奔到月球-五月天.wav",
    34: "天外來物-薛之謙.wav",
    35: "我期待的不是雪-張妙格.wav",
    36: "說愛你-蔡依林.wav",
    37: "那些年-胡夏.wav",
    38: "雪の音-Novelbright.wav",
    39: "クリスマスイブ-優里.wav",
    40: "Heart beat-YOASOBI.wav",
    41: "天ノ弱-akie秋绘.wav",
    42: "酔いどれ知らず-Kanaria.wav",
    43: "ただ声ーつ-ロクデナシ.wav",
    44: "Bling-Bang-BangBorn-CreepyNuts.wav",
    45: "Dec.-kanaria.wav",
    46: "心做し-蝶々P.wav",
    47: "Good night ojosama-ASMRZ.wav",
    48: "守りたいもの-大原ゆい子.wav",
    49: "相思相愛-aiko.wav",
    50: "XY&Z-サトシ.wav",
    51: "aLIEz-澤野弘之.wav",
    52: "ファタール-GEMN.wav",
    53: "ANIMA-ReoNa.wav",
    54: "うい麦畑でつかまえて-しぐれうい.wav",
    55: "舞台に立って-YOASOBI.wav",
    56: "一番輝く星-上坂すみれ.wav",
    57: "Tell your world-kz.wav",
    58: "がらくた-米津玄師.wav",
    59: "柯南主題曲-大野克夫.wav",
    60: "Don’t Fight The Music-黑魔.wav",
    61: "only my railgun-fripSide.wav",
    63: "六兆年と一夜物語-kemu.wav",
    64: "Azalea-米津玄師.wav",
    65: "アイビー-Novelbright.wav",
    66: "50%-Official髭男dism.wav",
    67: "東京テディベア-Neru.wav",
    68: "暮色迴響-吉星出租.wav",
    69: "童話-光良.wav",
    70: "步步-五月天.wav",
    71: "我們青春-李玉璽.wav",
    72: "任性-五月天.wav",
    73: "APT.-ROSÉ & Bruno Mars.wav",
    74: "snooze-wotaku.wav",
    75: "ゴーストルール-DECO_27.wav",
    76: "余花にみとれて-keeno.wav"
}
#抽籤獎勵
fortune_rewards = {
    '上籤' : '200靈石', 
    '上上籤' : '100靈石', 
    '上中籤' : '95靈石', 
    '上平籤' : '90靈石', 
    '上下籤' : '85靈石', 
    '大吉籤' : '80靈石', 
    '上吉籤' : '75靈石', 
    '中吉籤' : '70靈石', 
    '下吉籤' : '65靈石', 
    '中籤' : '60靈石', 
    '中上籤' : '55靈石', 
    '中平籤' : '50靈石', 
    '中中籤' : '45靈石', 
    '中下籤' : '40靈石', 
    '下籤' : '35靈石', 
    '下上籤' : '30靈石', 
    '下中籤' : '25靈石', 
    '下下籤' : '20靈石', 
    '下兇籤' : '15靈石', 
    '不吉籤' : '10靈石'
}
#定義敵人
enemies = {
    "外勁一層武者": {"health": 750, "attack": 140, "defense": 46},
    "外勁六層武者": {"health": 1025, "attack": 190, "defense": 61},
    "外勁大圓滿武者": {"health": 1300, "attack": 240, "defense": 76},
    "內勁一層武者": {"health": 1355, "attack": 250, "defense": 79},
    "內勁六層武者": {"health": 1630, "attack": 300, "defense": 91},
}
items = {
    "生命藥水": {"type": "heal", "value": 50, "use_restriction": "both"},   # 戰鬥內外皆可使用
    "力量藥水": {"type": "buff", "attack": 10, "use_restriction": "combat"},  # 僅能在戰鬥中使用
    "防禦藥水": {"type": "buff", "defense": 5, "use_restriction": "combat"},  # 僅能在戰鬥中使用
    "修為": {"type": "gain_cultivation", "value": 100, "use_restriction": "non_combat"},  # 僅能在戰鬥之外使用
    "精華": {"type": "gain_quench", "value": 100, "use_restriction": "non_combat"}  # 僅能在戰鬥之外使用
}
# 定義道具價格
item_prices = {
    "生命藥水": 10,  # 每個 10 靈石
    "力量藥水": 20,  # 每個 20 靈石
    "防禦藥水": 15,  # 每個 15 靈石
    "修為": 100,
    "精華": 250,
}
