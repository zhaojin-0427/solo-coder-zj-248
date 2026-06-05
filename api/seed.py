from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session
from database import SessionLocal
from models import (
    User, KitListing, KitMatch, Tutorial, TutorialStep,
    PaintRecord, WeatheringDetail, Artwork, Tool, Favorite,
)


def seed_database():
    db = SessionLocal()
    try:
        if db.query(User).first():
            return

        users = _seed_users(db)
        listings = _seed_listings(db, users)
        _seed_matches(db, listings)
        tutorials = _seed_tutorials(db, users)
        _seed_tutorial_details(db, tutorials)
        _seed_artworks(db, users)
        _seed_tools(db, users)
        _seed_favorites(db, users, tutorials)

        db.commit()
    finally:
        db.close()


def _seed_users(db: Session):
    users_data = [
        {"username": "装甲老兵", "email": "zhuangjia@example.com", "role": "expert", "avatar": "/avatars/1.jpg"},
        {"username": "模型新手", "email": "xinshou@example.com", "role": "player", "avatar": "/avatars/2.jpg"},
        {"username": "涂装达人", "email": "tuzhuang@example.com", "role": "expert", "avatar": "/avatars/3.jpg"},
        {"username": "军迷小王", "email": "junmi@example.com", "role": "player", "avatar": "/avatars/4.jpg"},
        {"username": "旧化大师", "email": "jiuhua@example.com", "role": "expert", "avatar": "/avatars/5.jpg"},
        {"username": "战舰收藏家", "email": "zhanjian@example.com", "role": "player", "avatar": "/avatars/6.jpg"},
        {"username": "喷笔侠", "email": "penbi@example.com", "role": "expert", "avatar": "/avatars/7.jpg"},
        {"username": "飞机控", "email": "feiji@example.com", "role": "player", "avatar": "/avatars/8.jpg"},
    ]
    users = []
    for i, u in enumerate(users_data):
        user = User(
            **u,
            created_at=datetime.utcnow() - timedelta(days=random.randint(30, 365)),
        )
        db.add(user)
        users.append(user)
    db.flush()
    return users


def _seed_listings(db: Session, users):
    listings_data = [
        {"user_id": 1, "title": "田宫 虎式坦克 1/35 全新未拆", "type": "sell", "scale": "1/35", "manufacturer": "田宫", "condition": "sealed", "subject": "坦克", "price": 268, "description": "田宫经典虎I初期生产型，全新未拆封，板件完好，附带蚀刻片。"},
        {"user_id": 2, "title": "求购 虎式坦克 1/35 任何品牌均可", "type": "buy", "scale": "1/35", "manufacturer": "", "condition": "opened", "subject": "坦克", "price": 200, "description": "想入手一台虎式练手，已拆封也可以，板件齐全即可。"},
        {"user_id": 3, "title": "长谷川 F-16战隼 1/48 全新", "type": "sell", "scale": "1/48", "manufacturer": "长谷川", "condition": "sealed", "subject": "战斗机", "price": 188, "description": "长谷川F-16C战隼，含树脂座舱，全新密封。"},
        {"user_id": 4, "title": "求购 F-16战隼 1/48 长谷川优先", "type": "buy", "scale": "1/48", "manufacturer": "长谷川", "condition": "opened", "subject": "战斗机", "price": 160, "description": "想做个F-16，长谷川最好，其他品牌也可考虑。"},
        {"user_id": 5, "title": "田宫 俾斯麦战列舰 1/350 全新", "type": "sell", "scale": "1/350", "manufacturer": "田宫", "condition": "sealed", "subject": "战舰", "price": 680, "description": "田宫1/350俾斯麦号战列舰，附金属炮管，全新未拆。"},
        {"user_id": 6, "title": "求购 俾斯麦战列舰 1/350", "type": "buy", "scale": "1/350", "manufacturer": "田宫", "condition": "partial", "subject": "战舰", "price": 500, "description": "缺舰载机零件可接受，主体板件齐全即可。"},
        {"user_id": 7, "title": "威龙 豹2A6主战坦克 1/35 已开盒检视", "type": "sell", "scale": "1/35", "manufacturer": "威龙", "condition": "opened", "subject": "坦克", "price": 298, "description": "威龙Smart Kit系列豹2A6，已开盒检视板件，全齐未组。"},
        {"user_id": 1, "title": "爱德美 M1A2艾布拉姆斯 1/35 全新", "type": "sell", "scale": "1/35", "manufacturer": "爱德美", "condition": "sealed", "subject": "坦克", "price": 228, "description": "爱德美M1A2，含独立履带，全新未拆。"},
        {"user_id": 8, "title": "求购 Bf-109战斗机 1/48", "type": "buy", "scale": "1/48", "manufacturer": "", "condition": "sealed", "subject": "战斗机", "price": 150, "description": "想做个二战德军经典战斗机，品牌不限。"},
        {"user_id": 3, "title": "小号手 T-34/85坦克 1/35", "type": "sell", "scale": "1/35", "manufacturer": "小号手", "condition": "sealed", "subject": "坦克", "price": 128, "description": "小号手T-34/85苏联中型坦克，全新密封。"},
        {"user_id": 5, "title": "田宫 大和号战列舰 1/350 全新", "type": "sell", "scale": "1/350", "manufacturer": "田宫", "condition": "sealed", "subject": "战舰", "price": 880, "description": "田宫1/350大和号，含木甲板贴片，全新未拆封。"},
        {"user_id": 4, "title": "求购 豹2A6主战坦克 1/35 威龙优先", "type": "buy", "scale": "1/35", "manufacturer": "威龙", "condition": "opened", "subject": "坦克", "price": 250, "description": "想组一台现代主战坦克，威龙优先。"},
        {"user_id": 7, "title": "长谷川 零式舰载战斗机 1/48 全新", "type": "sell", "scale": "1/48", "manufacturer": "长谷川", "condition": "sealed", "subject": "战斗机", "price": 145, "description": "长谷川零战52型，细节优秀，全新密封。"},
        {"user_id": 2, "title": "求购 M1A2艾布拉姆斯 1/35", "type": "buy", "scale": "1/35", "manufacturer": "", "condition": "sealed", "subject": "坦克", "price": 200, "description": "想尝试美系现代坦克，品牌不限，全新优先。"},
        {"user_id": 6, "title": "求购 大和号战列舰 1/350", "type": "buy", "scale": "1/350", "manufacturer": "田宫", "condition": "partial", "subject": "战舰", "price": 700, "description": "田宫大和号，缺小零件可接受。"},
    ]
    listings = []
    for i, l in enumerate(listings_data):
        listing = KitListing(
            **l,
            missing_parts="",
            images=[],
            status="active",
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 60)),
        )
        db.add(listing)
        listings.append(listing)
    db.flush()
    return listings


def _seed_matches(db: Session, listings):
    matches_data = [
        {"sell_idx": 0, "buy_idx": 1, "score": 80.0},
        {"sell_idx": 2, "buy_idx": 3, "score": 100.0},
        {"sell_idx": 4, "buy_idx": 5, "score": 80.0},
        {"sell_idx": 6, "buy_idx": 12, "score": 80.0},
        {"sell_idx": 7, "buy_idx": 13, "score": 80.0},
        {"sell_idx": 10, "buy_idx": 14, "score": 80.0},
    ]
    for m in matches_data:
        match = KitMatch(
            sell_listing_id=listings[m["sell_idx"]].id,
            buy_listing_id=listings[m["buy_idx"]].id,
            match_score=m["score"],
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
        )
        db.add(match)
    db.flush()


def _seed_tutorials(db: Session, users):
    tutorials_data = [
        {"user_id": 1, "title": "虎式坦克旧化入门——从基础到进阶", "subject": "坦克", "difficulty": "beginner", "cover_image": "/covers/tiger1.jpg"},
        {"user_id": 3, "title": "F-16战隼迷彩涂装完全指南", "subject": "战斗机", "difficulty": "intermediate", "cover_image": "/covers/f16.jpg"},
        {"user_id": 5, "title": "战舰水贴与拉线技巧详解", "subject": "战舰", "difficulty": "advanced", "cover_image": "/covers/bismarck.jpg"},
        {"user_id": 7, "title": "喷笔基础——渐变色与阴影喷涂", "subject": "通用技巧", "difficulty": "beginner", "cover_image": "/covers/airbrush.jpg"},
        {"user_id": 1, "title": "豹2A6现代坦克CMK涂装实战", "subject": "坦克", "difficulty": "intermediate", "cover_image": "/covers/leopard2.jpg"},
        {"user_id": 3, "title": "零式战斗机日式涂装与标志水贴", "subject": "战斗机", "difficulty": "beginner", "cover_image": "/covers/zero.jpg"},
        {"user_id": 5, "title": "大和号木甲板与细节升级教程", "subject": "战舰", "difficulty": "intermediate", "cover_image": "/covers/yamato.jpg"},
        {"user_id": 7, "title": "战损与弹痕效果制作大全", "subject": "通用技巧", "difficulty": "advanced", "cover_image": "/covers/battle_damage.jpg"},
    ]
    tutorials = []
    for t in tutorials_data:
        tutorial = Tutorial(
            **t,
            views=random.randint(100, 3000),
            completions=random.randint(10, 500),
            favorites=random.randint(5, 200),
            created_at=datetime.utcnow() - timedelta(days=random.randint(10, 180)),
        )
        db.add(tutorial)
        tutorials.append(tutorial)
    db.flush()
    return tutorials


def _seed_tutorial_details(db: Session, tutorials):
    steps_data = {
        0: [
            {"order_num": 1, "title": "板件清洗与准备", "description": "用温水加洗洁精清洗板件，去除脱模剂，晾干后剪裁零件。", "technique": "基础准备"},
            {"order_num": 2, "title": "组装与打磨", "description": "按说明书组装主要部件，使用400-800目砂纸打磨合模线。", "technique": "基础组装"},
            {"order_num": 3, "title": "底漆喷涂", "description": "使用郡士C181灰色水补土整体喷涂一遍，等待12小时完全干燥。", "technique": "底漆"},
            {"order_num": 4, "title": "基础色涂装", "description": "用田宫XF-60暗黄色喷涂整车，注意均匀覆盖。", "technique": "基础涂装"},
            {"order_num": 5, "title": "旧化第一步——渍洗", "description": "使用深棕色油画颜料稀释后进行渍洗，突出面板线条。", "technique": "渍洗"},
            {"order_num": 6, "title": "旧化第二步——干扫", "description": "用浅黄色颜料干扫凸起部分，模拟磨损效果。", "technique": "干扫"},
        ],
        1: [
            {"order_num": 1, "title": "零件处理与组装", "description": "清洗板件，组装机身主结构，填补缝隙。", "technique": "基础准备"},
            {"order_num": 2, "title": "座舱涂装", "description": "使用AV漆涂装座舱细节，安全带用蚀刻片。", "technique": "细节涂装"},
            {"order_num": 3, "title": "迷彩遮盖", "description": "使用遮盖带制作F-16蛇形迷彩遮盖模板。", "technique": "遮盖涂装"},
            {"order_num": 4, "title": "迷彩喷涂", "description": "依次喷涂灰色和深灰色迷彩区块，注意边缘柔化。", "technique": "渐变喷涂"},
            {"order_num": 5, "title": "水贴与渗线", "description": "贴上标记水贴，使用黑色渗线液加强面板线条。", "technique": "渗线"},
        ],
        2: [
            {"order_num": 1, "title": "船体组装与改造", "description": "组装船体主体，用补土加固接缝处。", "technique": "基础组装"},
            {"order_num": 2, "title": "甲板木纹涂装", "description": "使用AV木色系颜料逐条涂装甲板木纹。", "technique": "木纹涂装"},
            {"order_num": 3, "title": "拉线与缆绳", "description": "使用0.1mm钢琴线制作天线和缆绳拉线。", "technique": "拉线"},
            {"order_num": 4, "title": "船底防污漆", "description": "喷涂红色船底防污漆，注意水线位置。", "technique": "分区涂装"},
        ],
        3: [
            {"order_num": 1, "title": "喷笔拆解与清洗", "description": "拆解喷笔各部件，用专用清洗剂彻底清洗。", "technique": "喷笔维护"},
            {"order_num": 2, "title": "漆料稀释比例", "description": "掌握不同品牌漆料的稀释比例，田宫1:2，郡士1:1。", "technique": "调漆"},
            {"order_num": 3, "title": "渐变色喷涂练习", "description": "在废料上练习渐变过渡，从深色到浅色。", "technique": "渐变喷涂"},
            {"order_num": 4, "title": "阴影预置技法", "description": "在面板缝隙预喷深色阴影，再覆盖主色。", "technique": "预置阴影"},
        ],
        4: [
            {"order_num": 1, "title": "组装与细节追加", "description": "组装豹2A6，追加金属炮管和蚀刻片细节。", "technique": "细节改造"},
            {"order_num": 2, "title": "CMK涂装原理", "description": "理解CMK（曲率贴图）原理：高光、中间色、阴影三区。", "technique": "CMK涂装"},
            {"order_num": 3, "title": "高光区喷涂", "description": "先在曲面最高点喷涂亮色，形成高光。", "technique": "高光喷涂"},
            {"order_num": 4, "title": "阴影区喷涂", "description": "在曲面最低点和面板缝隙喷涂深色阴影。", "technique": "阴影喷涂"},
        ],
        5: [
            {"order_num": 1, "title": "零战组装要点", "description": "注意起落架舱和发动机细节的组装顺序。", "technique": "基础组装"},
            {"order_num": 2, "title": "日军标志水贴", "description": "正确贴敷日之丸和编号水贴，使用软化剂。", "technique": "水贴"},
            {"order_num": 3, "title": "日军标准涂装", "description": "零战上灰下绿的经典涂装方案。", "technique": "双色涂装"},
        ],
        6: [
            {"order_num": 1, "title": "木甲板贴片安装", "description": "使用专用木甲板贴片逐条粘贴，注意对齐。", "technique": "木甲板"},
            {"order_num": 2, "title": "舰桥细节升级", "description": "用蚀刻片替换塑料栏杆和天线细节。", "technique": "蚀刻片"},
            {"order_num": 3, "title": "小艇与武器涂装", "description": "涂装舰载小艇和各口径火炮细节。", "technique": "细节涂装"},
        ],
        7: [
            {"order_num": 1, "title": "弹孔制作", "description": "用电钻和加热针制作不同口径弹孔效果。", "technique": "弹痕"},
            {"order_num": 2, "title": "战损边缘处理", "description": "用刀片和砂纸制作金属翻边的弹片损伤。", "technique": "战损"},
            {"order_num": 3, "title": "烧灼与烟熏效果", "description": "用深色粉彩和透明漆模拟烧灼痕迹。", "technique": "烟熏效果"},
            {"order_num": 4, "title": "碎片与残骸", "description": "用废料制作散落的碎片和残骸场景。", "technique": "场景制作"},
        ],
    }

    for t_idx, steps in steps_data.items():
        for s in steps:
            step = TutorialStep(
                tutorial_id=tutorials[t_idx].id,
                **s,
                image="",
            )
            db.add(step)

    paints_data = {
        0: [
            {"name": "暗黄色", "brand": "田宫", "color_code": "XF-60", "usage": "基础色"},
            {"name": "深棕色", "brand": "AV漆", "color_code": "70.863", "usage": "渍洗"},
            {"name": "橄榄绿", "brand": "田宫", "color_code": "XF-58", "usage": "迷彩斑块"},
            {"name": "红棕色", "brand": "田宫", "color_code": "XF-64", "usage": "迷彩斑块"},
        ],
        1: [
            {"name": "中性灰", "brand": "郡士", "color_code": "C-339", "usage": "迷彩主色"},
            {"name": "深灰色", "brand": "郡士", "color_code": "C-340", "usage": "迷彩暗色"},
            {"name": "浅灰色", "brand": "郡士", "color_code": "C-338", "usage": "迷彩亮色"},
            {"name": "金属银", "brand": "田宫", "color_code": "X-11", "usage": "金属细节"},
        ],
        2: [
            {"name": "舰船灰", "brand": "郡士", "color_code": "C-44", "usage": "舰体主色"},
            {"name": "甲板木色", "brand": "AV漆", "color_code": "70.847", "usage": "甲板"},
            {"name": "防污红", "brand": "郡士", "color_code": "C-49", "usage": "船底"},
        ],
        3: [
            {"name": "白色", "brand": "田宫", "color_code": "X-2", "usage": "渐变练习"},
            {"name": "黑色", "brand": "田宫", "color_code": "X-1", "usage": "阴影"},
            {"name": "灰色水补土", "brand": "郡士", "color_code": "C-181", "usage": "底漆"},
        ],
        4: [
            {"name": "北约绿", "brand": "田宫", "color_code": "XF-67", "usage": "CMK中间色"},
            {"name": "浅北约绿", "brand": "AV漆", "color_code": "70.888", "usage": "CMK高光"},
            {"name": "深北约绿", "brand": "AV漆", "color_code": "70.889", "usage": "CMK阴影"},
        ],
        5: [
            {"name": "明灰白", "brand": "郡士", "color_code": "C-361", "usage": "机腹"},
            {"name": "暗绿色", "brand": "郡士", "color_code": "C-126", "usage": "机背"},
        ],
        6: [
            {"name": "吴海军工厂灰", "brand": "郡士", "color_code": "C-44", "usage": "舰体"},
            {"name": "木甲板黄", "brand": "AV漆", "color_code": "70.847", "usage": "甲板"},
        ],
        7: [
            {"name": "烧焦黑", "brand": "AV漆", "color_code": "70.292", "usage": "烧灼痕迹"},
            {"name": "铁锈色", "brand": "AV漆", "color_code": "70.310", "usage": "锈蚀效果"},
            {"name": "金属银", "brand": "田宫", "color_code": "X-11", "usage": "刮擦露出金属"},
        ],
    }

    for t_idx, paints in paints_data.items():
        for p in paints:
            paint = PaintRecord(
                tutorial_id=tutorials[t_idx].id,
                **p,
            )
            db.add(paint)

    weathering_data = {
        0: [
            {"type": "渍洗", "products": ["AV漆深棕油画颜料", "ZIPPO打火机油"], "technique": "全车渍洗", "description": "稀释后的油画颜料涂抹全车，擦除凸起部分保留凹陷处。"},
            {"type": "干扫", "products": ["田宫XF-59沙漠黄"], "technique": "边缘干扫", "description": "用硬毛笔蘸取少量颜料，在纸上去除多余后干扫边缘。"},
            {"type": "泥浆", "products": ["AV漆泥浆土", "细沙"], "technique": "车轮泥浆", "description": "混合泥浆土和细沙，涂抹在车轮和挡泥板处。"},
        ],
        1: [
            {"type": "渗线", "products": ["田宫黑色渗线液", "X-20稀释剂"], "technique": "面板渗线", "description": "渗线液沿面板缝隙流动，突出飞机表面线条。"},
            {"type": "尾焰", "products": ["郡士SM06超级银", "AV漆透明橙"], "technique": "喷口烧灼", "description": "在发动机喷口处叠加银色和透明橙色，模拟高温灼烧。"},
        ],
        2: [
            {"type": "水渍", "products": ["AV漆水渍效果液"], "technique": "船体水渍", "description": "在水线位置涂抹水渍效果液，模拟水线痕迹。"},
            {"type": "锈蚀", "products": ["AV漆锈蚀效果液", "锈迹贴纸"], "technique": "锚链锈蚀", "description": "在锚链和甲板边缘添加锈蚀效果。"},
        ],
        3: [],
        4: [
            {"type": "滤镜", "products": ["AV漆滤镜液"], "technique": "整车滤镜", "description": "使用不同色调滤镜液统一整车色调。"},
            {"type": "干泥", "products": ["AV漆泥浆土"], "technique": "车体干泥", "description": "在车体侧面和底部添加干泥效果。"},
        ],
        5: [
            {"type": "渗线", "products": ["田宫黑色渗线液"], "technique": "面板渗线", "description": "突出飞机表面面板线条。"},
        ],
        6: [
            {"type": "水贴软化", "products": ["田宫水贴软化剂"], "technique": "标志水贴", "description": "使用软化剂使水贴贴合曲面。"},
            {"type": "拉线", "products": ["0.1mm钢琴线", "CA胶水"], "technique": "天线拉线", "description": "用钢琴线制作舰桥天线和信号旗线。"},
        ],
        7: [
            {"type": "弹孔", "products": ["电钻", "加热针"], "technique": "弹孔穿孔", "description": "用电钻和加热针制作不同口径弹孔。"},
            {"type": "烧灼", "products": ["AV漆透明黑", "AV漆透明橙"], "technique": "烧灼痕迹", "description": "叠加透明黑和透明橙模拟高温烧灼效果。"},
        ],
    }

    for t_idx, weatherings in weathering_data.items():
        for w in weatherings:
            wd = WeatheringDetail(
                tutorial_id=tutorials[t_idx].id,
                **w,
            )
            db.add(wd)

    db.flush()


def _seed_artworks(db: Session, users):
    artworks_data = [
        {"user_id": 1, "title": "虎I初期型——东线1943", "subject": "坦克", "scale": "1/35", "kit_name": "田宫虎式坦克", "images": ["/artworks/tiger1_1.jpg", "/artworks/tiger1_2.jpg"], "paints": ["田宫XF-60暗黄", "田宫XF-58橄榄绿", "田宫XF-64红棕"], "techniques": ["渍洗", "干扫", "CMK"], "weathering": ["泥浆效果", "锈蚀"]},
        {"user_id": 3, "title": "F-16C战隼——蛇形迷彩", "subject": "战斗机", "scale": "1/48", "kit_name": "长谷川F-16C", "images": ["/artworks/f16_1.jpg"], "paints": ["郡士C-339中性灰", "郡士C-340深灰"], "techniques": ["遮盖涂装", "渐变喷涂"], "weathering": ["渗线", "尾焰"]},
        {"user_id": 5, "title": "俾斯麦号——北大西洋出击", "subject": "战舰", "scale": "1/350", "kit_name": "田宫俾斯麦号", "images": ["/artworks/bismarck_1.jpg", "/artworks/bismarck_2.jpg"], "paints": ["郡士C-44舰船灰", "AV漆甲板木色"], "techniques": ["木纹涂装", "拉线"], "weathering": ["水渍", "锈蚀"]},
        {"user_id": 7, "title": "豹2A6——北约三色涂装", "subject": "坦克", "scale": "1/35", "kit_name": "威龙豹2A6", "images": ["/artworks/leopard_1.jpg"], "paints": ["田宫XF-67北约绿", "AV漆北约棕"], "techniques": ["CMK涂装", "滤镜"], "weathering": ["干泥", "渍洗"]},
        {"user_id": 2, "title": "T-34/85——库尔斯克之夏", "subject": "坦克", "scale": "1/35", "kit_name": "小号手T-34/85", "images": ["/artworks/t34_1.jpg"], "paints": ["田宫XF-60暗黄", "AV漆苏联绿"], "techniques": ["基础涂装", "干扫"], "weathering": ["泥浆", "锈蚀"]},
        {"user_id": 4, "title": "零战52型——硫磺岛上空", "subject": "战斗机", "scale": "1/48", "kit_name": "长谷川零式战斗机", "images": ["/artworks/zero_1.jpg"], "paints": ["郡士C-361明灰白", "郡士C-126暗绿"], "techniques": ["双色涂装", "水贴"], "weathering": ["渗线"]},
        {"user_id": 6, "title": "大和号——最后的出击", "subject": "战舰", "scale": "1/350", "kit_name": "田宫大和号", "images": ["/artworks/yamato_1.jpg", "/artworks/yamato_2.jpg"], "paints": ["郡士C-44舰船灰", "AV漆木甲板色"], "techniques": ["木甲板", "蚀刻片"], "weathering": ["水渍", "锈蚀"]},
        {"user_id": 8, "title": "M1A2艾布拉姆斯——沙漠风暴", "subject": "坦克", "scale": "1/35", "kit_name": "爱德美M1A2", "images": ["/artworks/m1a2_1.jpg"], "paints": ["田宫XF-59沙漠黄", "AV漆沙漠色"], "techniques": ["基础涂装", "干扫"], "weathering": ["沙尘", "渍洗"]},
        {"user_id": 1, "title": "战损虎式——诺曼底1944", "subject": "坦克", "scale": "1/35", "kit_name": "田宫虎式坦克", "images": ["/artworks/damaged_tiger_1.jpg"], "paints": ["田宫XF-60暗黄", "AV漆烧焦黑"], "techniques": ["战损制作", "弹痕"], "weathering": ["烧灼", "锈蚀", "弹孔"]},
        {"user_id": 3, "title": "Bf-109G-6——地中海涂装", "subject": "战斗机", "scale": "1/48", "kit_name": "长谷川Bf-109G-6", "images": ["/artworks/bf109_1.jpg"], "paints": ["郡士C-62德军灰", "AV漆沙黄"], "techniques": ["遮盖涂装", "渗线"], "weathering": ["尾焰", "油污"]},
    ]
    for a in artworks_data:
        artwork = Artwork(
            **a,
            likes=random.randint(5, 200),
            favorites=random.randint(2, 80),
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 90)),
        )
        db.add(artwork)
    db.flush()


def _seed_tools(db: Session, users):
    tools_data = [
        {"name": "郡士PS-2890双动喷笔", "category": "airbrush", "brand": "郡士", "rating": 4.8, "review_count": 356, "description": "0.3mm口径双动喷笔，适合细节和渐变喷涂，新手入门首选。", "image": "/tools/ps2890.jpg", "recommended_by": ["装甲老兵", "喷笔侠"]},
        {"name": "田宫87038侧流剪钳", "category": "tool", "brand": "田宫", "rating": 4.6, "review_count": 512, "description": "薄刃设计，剪切平整，减少打磨工作量。", "image": "/tools/tamiya_cutter.jpg", "recommended_by": ["装甲老兵", "涂装达人"]},
        {"name": "AV漆丙烯颜料套装", "category": "paint", "brand": "AV漆", "rating": 4.7, "review_count": 289, "description": "16色军事常用色套装，笔涂喷涂均可，附赠调色盘。", "image": "/tools/av_paint.jpg", "recommended_by": ["涂装达人", "旧化大师"]},
        {"name": "田宫87155面相笔套装", "category": "brush", "brand": "田宫", "rating": 4.5, "review_count": 198, "description": "三支装面相笔，适合细小细节涂装和水贴软化剂涂抹。", "image": "/tools/tamiya_brush.jpg", "recommended_by": ["涂装达人"]},
        {"name": "郡士C-181灰色水补土", "category": "paint", "brand": "郡士", "rating": 4.9, "review_count": 678, "description": "500ml大容量，颗粒细腻，附着力强，喷漆前必备。", "image": "/tools/mr_surfacer.jpg", "recommended_by": ["装甲老兵", "喷笔侠", "旧化大师"]},
        {"name": "AV漆旧化效果液套装", "category": "weathering", "brand": "AV漆", "rating": 4.6, "review_count": 167, "description": "含锈蚀液、油污液、泥浆土，旧化效果一步到位。", "image": "/tools/av_weathering.jpg", "recommended_by": ["旧化大师", "装甲老兵"]},
        {"name": "田宫87003模型锉刀套装", "category": "tool", "brand": "田宫", "rating": 4.4, "review_count": 234, "description": "三把不同形状锉刀，适合打磨合模线和零件修整。", "image": "/tools/tamiya_file.jpg", "recommended_by": ["装甲老兵"]},
        {"name": "郡士PS-270单动喷笔", "category": "airbrush", "brand": "郡士", "rating": 4.3, "review_count": 145, "description": "0.5mm口径单动喷笔，适合大面积底色喷涂。", "image": "/tools/ps270.jpg", "recommended_by": ["喷笔侠"]},
        {"name": "田宫渗线液黑色", "category": "paint", "brand": "田宫", "rating": 4.7, "review_count": 445, "description": "自带笔头的渗线液，流动性好，方便快捷。", "image": "/tools/tamiya_panel.jpg", "recommended_by": ["涂装达人", "旧化大师"]},
        {"name": "AV漆干扫笔", "category": "brush", "brand": "AV漆", "rating": 4.5, "review_count": 98, "description": "专用干扫笔，扁平笔头，适合旧化干扫技法。", "image": "/tools/av_drybrush.jpg", "recommended_by": ["旧化大师"]},
        {"name": "优质遮盖带套装", "category": "tool", "brand": "田宫", "rating": 4.6, "review_count": 312, "description": "多种宽度遮盖带，粘性适中，不留残胶。", "image": "/tools/tamiya_tape.jpg", "recommended_by": ["涂装达人", "喷笔侠"]},
        {"name": "郡士SM06超级银", "category": "paint", "brand": "郡士", "rating": 4.8, "review_count": 267, "description": "极致金属质感银色漆，适合发动机和金属细节。", "image": "/tools/mr_super_silver.jpg", "recommended_by": ["喷笔侠", "涂装达人"]},
    ]
    for t in tools_data:
        tool = Tool(**t)
        db.add(tool)
    db.flush()


def _seed_favorites(db: Session, users, tutorials):
    favs_data = [
        {"user_idx": 0, "target_type": "tutorial", "target_idx": 0},
        {"user_idx": 1, "target_type": "tutorial", "target_idx": 3},
        {"user_idx": 2, "target_type": "tutorial", "target_idx": 7},
        {"user_idx": 3, "target_type": "artwork", "target_idx": 0},
        {"user_idx": 4, "target_type": "artwork", "target_idx": 8},
        {"user_idx": 5, "target_type": "tutorial", "target_idx": 2},
        {"user_idx": 6, "target_type": "tutorial", "target_idx": 4},
        {"user_idx": 7, "target_type": "artwork", "target_idx": 5},
    ]

    artwork_ids = [a.id for a in db.query(Artwork).all()]

    for f in favs_data:
        if f["target_type"] == "tutorial":
            target_id = tutorials[f["target_idx"]].id
        else:
            target_id = artwork_ids[f["target_idx"]]
        favorite = Favorite(
            user_id=users[f["user_idx"]].id,
            target_type=f["target_type"],
            target_id=target_id,
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
        )
        db.add(favorite)
    db.flush()


if __name__ == "__main__":
    from models import Base
    from database import engine
    Base.metadata.create_all(bind=engine)
    seed_database()
    print("种子数据填充完成！")
