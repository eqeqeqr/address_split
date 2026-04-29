import re
import json
from dataclasses import dataclass
from uuid import uuid4

from app.core.config import DATA_DIR
from app.schemas.address import SceneRulePayload, SceneRuleResponse
from app.services.db import get_connection, init_db


COMMUNITY_SUFFIX = [
    "苑",
    "庭",
    "郡",
    "邸",
    "居",
    "轩",
    "府",
    "里",
    "小区",
    "公寓",
    "花园",
    "家园",
    "花苑",
    "雅苑",
    "佳苑",
    "名苑",
    "锦苑",
    "御苑",
    "兰苑",
    "馨苑",
    "景苑",
    "鑫苑",
    "悦苑",
    "和苑",
    "华庭",
    "豪庭",
    "名庭",
    "景庭",
    "悦庭",
    "馨庭",
    "福庭",
    "新城",
    "新村",
    "新苑",
    "新寓",
    "新园",
    "公馆",
    "府邸",
    "雅居",
    "逸居",
    "宜居",
    "乐居",
    "别院",
    "庭院",
    "山庄",
    "庄园",
    "碧园",
    "嘉园",
    "福园",
    "锦园",
    "馨园",
    "景园",
    "悦府",
    "华府",
    "王府",
    "学府",
    "书院",
    "水岸",
    "湾景",
    "湖畔",
    "江景",
    "海景",
    "河畔",
    "金城",
    "锦城",
    "锦绣",
    "丽景",
    "阳光",
    "盛世",
    "名都",
    "豪园",
    "碧苑",
    "蓝湾",
    "绿洲",
    "美域",
    "天悦",
    "云顶",
    "观澜",
    "观湖",
    "观山",
    "宸院",
    "玺园",
    "大院",
    "世家",
    "名邸",
    "华邸",
    "鑫城",
    "悦城",
    "新区",
    "国际",
    "雅墅",
    "香溪",
    "语墅",
    "唐韵",
    "人家",
    "郎境",
    "岸溪",
    "景城",
    "名城",
    "别墅区",
    "凤凰城",
    "望府",
]


@dataclass(frozen=True)
class ScenePattern:
    code: str
    label: str
    pattern: re.Pattern[str]


def _compile(pattern: str, code: str, label: str) -> ScenePattern:
    return ScenePattern(code=code, label=label, pattern=re.compile(pattern))


SCENE_PATTERNS = [
    _compile(
        rf"^[\u4e00-\u9fa5A-Za-z0-9]*(?:小区|公寓|别墅|家属院|职工宿舍|公租房|廉租房|安置区|边境小区|{'|'.join(COMMUNITY_SUFFIX)})$",
        "1",
        "居民小区",
    ),
    _compile(r"^[\u4e00-\u9fa5A-Za-z0-9]*(?:村|自然村|行政村|庄|寨|屯|组|队|湾|坝|坡|岭|沟|箐|坪|岒)$", "2", "农村住宅"),
    _compile(
        r"^[\u4e00-\u9fa5A-Za-z0-9]*(?:写字楼|大厦|商务楼|商厦|办公楼|商业大厦|商业中心|商办楼|商务中心|商住楼|中心大厦|地标|总部中心|企业中心|孵化器|金融中心|传媒中心|创意中心|双子塔|环球中心|万达广场|银泰中心|来福士|恒隆广场|太古汇|大悦城|龙湖天街|吾悦广场|印象城|万达茂|万科广场|华润万象|印象汇|天虹|银座|购物中心|商栋|创业大厦|科技大厦|财富中心|商业写字楼)$",
        "3",
        "商务楼宇",
    ),
    _compile(
        r"^[\u4e00-\u9fa5A-Za-z0-9]*(?:市场|商城|商贸城|建材城|电子数码市场|服饰鞋帽市场|汽配汽修市场|农产品交易市场|文化日用品市场|家居软装市场|五金机电市场|花鸟鱼虫市场|农资农具市场|集贸市场|商业广场|农贸市场|购物广场)$",
        "4",
        "专业市场",
    ),
    _compile(
        r"^[\u4e00-\u9fa5A-Za-z0-9]*(?:景区|风景区|旅游区|度假区|森林公园|地质公园|湿地公园|水利风景区|乐园|游乐园|动物园|植物园|遗址|故里|古镇|古城|名山大川|名胜|古迹|文物保护区|度假村|休闲山庄|主题乐园|水上乐园|海洋公园|海底世界|恐龙园|欢乐谷|方特|长隆|迪士尼|海洋王国|野生动物园|熊猫基地|猴山|鸟语林|蝴蝶谷|百合园|玫瑰园|牡丹园|梅花园|樱花园|桃花源|油菜花田|薰衣草园|采摘园|农庄|农家乐|生态园|观光园|示范园|盆景园|花卉园|苗圃|茶园|果园|竹林|松林|枫林|原始森林|自然保护区|国家公园|矿山公园|森林保护区|草原保护区|沙漠公园|戈壁公园|山川|名山|高山|中山|丘陵|平原|草甸|沼泽|溪流|峡谷|峰林|石林|溶洞|地下河|瀑布|温泉|地热|火山|地震|遗迹|博物馆|纪念馆|展览馆|美术馆)$",
        "5",
        "旅游景区",
    ),
    _compile(r"^[\u4e00-\u9fa5A-Za-z0-9]*(?:园区|产业园|工业园|科技园|创业园|文创园|电商园|物流园|农业园区|化工园区|康养园区|工业园区|双创园区|临空经济园区)$", "6", "园区"),
    _compile(r"^[\u4e00-\u9fa5A-Za-z0-9]*(?:幼儿园|小学|初中|高中|大学|学校|学院|中学|托儿所|附中|附小|职高|中专|技校|职业学校|进修学校|特殊教育学校|教育集团|教育培训|书院|私塾|学堂|党校|行政学院|社会主义学院|团校|军校|警校|体校|艺校|武校|教学点|分校|校区|附幼)$", "7", "学校"),
    _compile(r"^[\u4e00-\u9fa5A-Za-z0-9]*(?:酒店|宾馆|旅馆|招待所|民宿|客栈|青年旅舍|农家乐|度假村|山庄|驿站|营地|露营地|度假酒店|精品酒店|主题酒店|快捷酒店|商务酒店|连锁酒店|公寓式酒店|温泉酒店|海滨酒店|商务宾馆|经济宾馆|连锁宾馆|快捷宾馆|家庭旅馆|青年旅馆|背包客|太空舱|胶囊|民宿客栈|度假民宿|五星|四星|三星)$", "8", "泛酒店"),
    _compile(r"^[\u4e00-\u9fa5A-Za-z0-9]*(?:预防中心|医院|卫生院|保健院|妇幼保健院|康复医院|疗养院|急救中心|诊所|住院部|急诊部|门诊|门诊部|社区卫生服务中心|社区医院|职业病防治院|专科医院|口腔医院|眼科医院|骨科医院|肛肠医院|肿瘤医院|传染病医院|精神卫生中心|疾控中心|急救站|卫生室|卫生站|医务室|医务所|卫生服务站|社区卫生站|乡镇卫生院|街道卫生院|村卫生室|村卫生站|国医馆|中医馆|中西医结合医院|牙科诊所|眼科诊所|美容医院|整形医院|妇产医院|儿童医院|老年医院|康复中心|疗养中心|体检中心)$", "9", "医院"),
    _compile(r"^[\u4e00-\u9fa5A-Za-z0-9]*(?:慈善总会|技术局|厂|集团|公安局|派出所|管理所|出入境接待大厅|公司|企业|生产型企业|商贸型企业|党政军机关单位|党政军宿舍|武警军区|事业单位|社会组织|场馆|教育机构|金融机构|休闲娱乐场所|宗教场所|公墓)$", "10", "独立企业/机构"),
    _compile(r"^[\u4e00-\u9fa5A-Za-z0-9]*(?:机场|火车站|高铁站|普铁站|地铁站|汽车站|客运站|港口|码头|高速公路|高速|国道|省道|道路|隧道|广场|公园|沙漠|戈壁|湖泊|河流|水域|航道|停车场|绿地|山区|牧场|林地|农田|海域|海岸|海滩|公厕|厕所|垃圾站|环卫站|公交站|加油站|地铁口|铁路|轨道|站前广场|交通枢纽|长途汽车站|东站|西站|南站|北站|枢纽站|换乘站|首末站|中途站|站点|服务区|停车区|休息区|电影院|演艺中心|文化广场|体育广场|休闲广场|市民广场|人民广场|中山广场|胜利广场|和平广场|红旗广场|星光广场|时代广场|奥林匹克广场|市民公园|城市公园|主题公园|生态公园|郊野公园|社区公园|街心公园|口袋公园|微型公园)$", "11", "公共区域"),
    _compile(r"^[\u4e00-\u9fa5A-Za-z0-9]*(?:园|苑|新村|区|城).*区$", "12", "居民小区"),
    _compile(r"^[\u4e00-\u9fa5A-Za-z0-9]*(?:村|自然村).*区$", "13", "农村住宅"),
    _compile(r"^[\u4e00-\u9fa5A-Za-z0-9]*$", "14", "其他/沿街商铺"),
]

SCENES_FILE = DATA_DIR / "scenes.json"


def _default_scene_rules() -> list[SceneRuleResponse]:
    return [
        SceneRuleResponse(id=item.code, name=item.label, pattern=item.pattern.pattern, matchField="level_7 / poi", priority=index + 1, statusText="系统默认", editable=False)
        for index, item in enumerate(SCENE_PATTERNS[:-1])
    ]


def _read_scenes() -> list[SceneRuleResponse]:
    _ensure_scene_rows()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, name, pattern, match_field, priority, status_text, editable
            FROM scene_rules
            ORDER BY priority ASC
            """
        ).fetchall()
        return [
            SceneRuleResponse(
                id=row["id"],
                name=row["name"],
                pattern=row["pattern"],
                matchField=row["match_field"],
                priority=row["priority"],
                statusText=row["status_text"],
                editable=bool(row["editable"]),
            )
            for row in rows
        ]


def _write_scenes(rules: list[SceneRuleResponse]) -> None:
    init_db()
    with get_connection() as conn:
        conn.execute("DELETE FROM scene_rules")
        for rule in rules:
            _upsert_scene(conn, rule)


def _upsert_scene(conn, rule: SceneRuleResponse) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO scene_rules
        (id, name, pattern, match_field, priority, status_text, editable)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            rule.id,
            rule.name,
            rule.pattern,
            rule.matchField,
            rule.priority,
            rule.statusText,
            1 if rule.editable else 0,
        ),
    )


def _ensure_scene_rows() -> None:
    init_db()
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS count FROM scene_rules").fetchone()["count"]
        if count:
            return

        if SCENES_FILE.exists():
            rules = [SceneRuleResponse(**item) for item in json.loads(SCENES_FILE.read_text(encoding="utf-8"))]
        else:
            rules = _default_scene_rules()

        for rule in rules:
            _upsert_scene(conn, rule)


def list_scene_rules() -> list[SceneRuleResponse]:
    return sorted(_read_scenes(), key=lambda rule: rule.priority)


def create_scene_rule(payload: SceneRulePayload) -> SceneRuleResponse:
    rule = SceneRuleResponse(
        id=uuid4().hex,
        name=payload.name,
        pattern=payload.pattern,
        matchField=payload.matchField,
        priority=payload.priority,
        statusText="自定义",
        editable=True,
    )
    _ensure_scene_rows()
    with get_connection() as conn:
        _upsert_scene(conn, rule)
    return rule


def update_scene_rule(rule_id: str, payload: SceneRulePayload) -> SceneRuleResponse | None:
    _ensure_scene_rows()
    with get_connection() as conn:
        row = conn.execute("SELECT editable FROM scene_rules WHERE id = ?", (rule_id,)).fetchone()
        if row is None:
            return None
        if not bool(row["editable"]):
            raise ValueError("系统默认规则不可编辑")

        updated = SceneRuleResponse(
            id=rule_id,
            name=payload.name,
            pattern=payload.pattern,
            matchField=payload.matchField,
            priority=payload.priority,
            statusText="自定义",
            editable=True,
        )
        _upsert_scene(conn, updated)
        return updated


def delete_scene_rule(rule_id: str) -> bool:
    _ensure_scene_rows()
    with get_connection() as conn:
        row = conn.execute("SELECT editable FROM scene_rules WHERE id = ?", (rule_id,)).fetchone()
        if row is None:
            return False
        if not bool(row["editable"]):
            raise ValueError("系统默认规则不可删除")

        conn.execute("DELETE FROM scene_rules WHERE id = ?", (rule_id,))
        return True


def detect_scene(value: str) -> dict[str, str]:
    text = str(value or "").strip()
    if not text:
        return {"scene_code": "", "scene": ""}

    for item in list_scene_rules():
        try:
            if re.compile(item.pattern).match(text):
                return {"scene_code": item.id, "scene": item.name}
        except re.error:
            continue

    return {"scene_code": "14", "scene": "其他/沿街商铺"}
