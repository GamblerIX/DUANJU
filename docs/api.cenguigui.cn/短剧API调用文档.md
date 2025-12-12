# 短剧解析接口调用文档

## 概述

本文档描述了短剧解析API的完整调用方式，支持番茄/蛋花/西瓜/悟空/常读/红果等平台的聚合短剧数据获取。

## 基本信息

- **基础URL**: `https://api.cenguigui.cn/api/duanju/api.php`
- **请求方法**: GET / POST
- **响应格式**: JSON
- **开发者**: 笒鬼鬼 (QQ: 2963246343)
- **限流**：接口请求QPS为 10 秒 5 次。

---

## API 接口列表

### 1. 搜索接口

根据短剧名称搜索相关短剧。

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| name | string | 是 | - | 短剧名称关键词 |
| page | int | 是 | - | 页码，每页10条数据 |
| showRawParams | string | 否 | false | 是否返回原始参数 |

**调用示例**

```
GET https://api.cenguigui.cn/api/duanju/api.php?name=总裁&page=1&showRawParams=false
```

**响应示例**

```json
{
    "code": 200,
    "msg": "搜索成功 - 番茄/蛋花/西瓜/悟空/常读/红果 聚合短剧",
    "data": [
        {
            "book_id": "7416545333695499326",
            "title": "总裁有疾闪婚来袭",
            "author": "谢澜川,温以棠",
            "type": "都市情感·都市·全63集",
            "play_cnt": 644756,
            "episode_cnt": 63,
            "cover": "https://p3-reading-sign.fqnovelpic.com/novel-pic/...",
            "intro": "男女主是当地赫赫有名的富豪家庭..."
        }
    ],
    "page": "1",
    "tips": "笒鬼鬼api-获取到对应book_id,然后用于获取全部视频列表",
    "time": "2025-12-06 15:53:53"
}
```


**响应字段说明**

| 字段 | 类型 | 描述 |
|------|------|------|
| book_id | string | 短剧唯一ID，用于获取剧集列表 |
| title | string | 短剧标题 |
| author | string | 主演/作者 |
| type | string | 类型·场景·集数 |
| play_cnt | int | 播放次数 |
| episode_cnt | int | 总集数 |
| cover | string | 封面图片URL |
| intro | string | 剧情简介 |

---

### 2. 视频列表接口

获取指定短剧的所有剧集列表。

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| book_id | int | 是 | - | 短剧ID |
| showRawParams | string | 否 | false | 是否返回原始参数 |

**调用示例**

```
GET https://api.cenguigui.cn/api/duanju/api.php?book_id=7416545333695499326&showRawParams=false
```

**响应示例**

```json
{
    "code": 200,
    "msg": "获取列表成功 - 番茄/蛋花/西瓜/悟空/常读/红果 聚合短剧",
    "data": [
        {
            "video_id": "7416589528229497881",
            "title": "第1集",
            "firstPassTime": "1970-01-01 08:00:00",
            "volume_name": "",
            "chapter_word_number": 843
        },
        {
            "video_id": "7416581856998460441",
            "title": "第2集",
            "firstPassTime": "1970-01-01 08:00:00",
            "volume_name": "",
            "chapter_word_number": 839
        }
    ],
    "total": "63",
    "book_id": "7416545333695499326",
    "book_name": "总裁有疾闪婚来袭",
    "author": "树下的椰子",
    "category": "总裁",
    "desc": "男女主是当地赫赫有名的富豪家庭...",
    "duration": "1小时43分钟",
    "book_pic": "https://p3-novel.byteimg.com/img/novel-pic/...",
    "tips": "笒鬼鬼api-获取到对应video_id,然后用于获取视频下载链接",
    "time": "2025-12-06 15:54:01"
}
```

**响应字段说明**

| 字段 | 类型 | 描述 |
|------|------|------|
| video_id | string | 视频ID，用于获取播放地址 |
| title | string | 集数标题 |
| total | string | 总集数 |
| book_name | string | 短剧名称 |
| author | string | 作者 |
| category | string | 分类 |
| desc | string | 剧情简介 |
| duration | string | 总时长 |
| book_pic | string | 封面图片 |

---

### 3. 视频播放接口

获取视频播放地址，支持多种清晰度和输出格式。

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| video_id | int | 是 | - | 视频ID |
| level | string | 否 | 1080p | 清晰度: 360p/480p/720p/1080p/2160p |
| type | string | 否 | json | 输出类型: json/pic/mp4/url |
| showRawParams | string | 否 | false | 是否返回原始参数 |

**清晰度说明**

| 清晰度 | 描述 |
|--------|------|
| 360p | 流畅 |
| 480p | 标清 |
| 720p | 高清 |
| 1080p | 超清 (默认) |
| 2160p | 4K (不是所有视频都支持) |

**调用示例**

```
GET https://api.cenguigui.cn/api/duanju/api.php?video_id=7416589528229497881&type=json&showRawParams=false
```

**响应示例**

```json
{
    "code": 200,
    "msg": "解析成功-总裁有疾闪婚来袭",
    "data": {
        "title": "总裁有疾闪婚来袭 - 总裁有疾闪婚来袭",
        "pic": "https://p6-fanqiesdk-sign.fanqiesdkpic.com/novel-pic/...",
        "url": "https://v26-m.wkbrowser.com/.../video.mp4?...",
        "info": {
            "author": "树下的椰子",
            "chapter_title": "第1集",
            "create_time": "2024-09-20T10:23:43+08:00",
            "quality": "1080p",
            "fps": 50,
            "bitrate": "1934.28kbps",
            "codec": "h264",
            "duration": "1分42秒",
            "size": 25421326,
            "size_str": "24.24MB",
            "height": 1920,
            "width": 1080
        }
    },
    "tips": "笒鬼鬼api",
    "time": "2025-12-06 15:54:09"
}
```

**响应字段说明**

| 字段 | 类型 | 描述 |
|------|------|------|
| title | string | 视频标题 |
| pic | string | 封面图片URL |
| url | string | 视频播放/下载地址 |
| info.quality | string | 视频清晰度 |
| info.fps | int | 帧率 |
| info.bitrate | string | 码率 |
| info.duration | string | 视频时长 |
| info.size_str | string | 文件大小 |
| info.height | int | 视频高度 |
| info.width | int | 视频宽度 |


---

### 4. 分类接口

按分类获取短剧列表。

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| classname | string | 是 | - | 分类名称 |
| offset | int | 是 | 1 | 翻页偏移量 |
| showRawParams | string | 否 | false | 是否返回原始参数 |

**支持的分类**

推荐榜, 新剧, 逆袭, 霸总, 现代言情, 打脸虐渣, 豪门恩怨, 神豪, 马甲, 都市日常, 战神归来, 小人物, 女性成长, 大女主, 穿越, 都市修仙, 强者回归, 亲情, 古装, 重生, 闪婚, 赘婿逆袭, 虐恋, 追妻, 天下无敌, 家庭伦理, 萌宝, 古风权谋, 职场, 奇幻脑洞, 异能, 无敌神医, 古风言情, 传承觉醒, 现言甜宠, 奇幻爱情, 乡村, 历史古代, 王妃, 高手下山, 娱乐圈, 强强联合, 破镜重圆, 暗恋成真, 民国, 欢喜冤家, 系统, 真假千金, 龙王, 校园, 穿书, 女帝, 团宠, 年代爱情, 玄幻仙侠, 青梅竹马, 悬疑推理, 皇后, 替身, 大叔, 喜剧, 剧情

**调用示例**

```
GET https://api.cenguigui.cn/api/duanju/api.php?classname=穿越&offset=1&showRawParams=false
```

**响应示例**

```json
{
    "code": 200,
    "msg": "成功",
    "data": [
        {
            "cover": "https://p3-reading-sign.fqnovelpic.com/novel-pic/...",
            "duration": 7801,
            "title": "龙凤又呈祥",
            "video_desc": "现代职场女性倪好与民国绣娘绣儿因汉绣瑰宝...",
            "episode": true,
            "vertical": false,
            "play_cnt": 113008,
            "sub_title": "奇幻脑洞·4011万热度",
            "score": "8.3",
            "episode_cnt": 73,
            "video_id": "7568383573917453336",
            "book_id": "7568383039152081944"
        }
    ],
    "time": "2025-12-06 15:54:11"
}
```

---

### 5. 推荐接口

获取随机推荐的短剧列表。

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| type | string | 是 | - | 固定值: recommend |
| showRawParams | string | 否 | false | 是否返回原始参数 |

**调用示例**

```
GET https://api.cenguigui.cn/api/duanju/api.php?type=recommend&showRawParams=false
```

**响应示例**

```json
{
    "code": 200,
    "msg": "成功",
    "data": [
        {
            "hot": 19945770,
            "toutiao_click_rate": "3330071",
            "book_data": {
                "book_id": "7231394787566292027",
                "book_name": "山有木兮卿有意",
                "category": "奇幻爱情",
                "read_count": "3330071",
                "serial_count": "20",
                "thumb_url": "https://p9-fanqiesdk-sign.fanqiesdkpic.com/novel-pic/...",
                "category_tags": [
                    {"CategoryId": 1020, "CategoryName": "奇幻爱情"},
                    {"CategoryId": 1050, "CategoryName": "暗恋成真"}
                ],
                "actor_list": [
                    {"name": "申浩男", "avatar_url": "https://..."},
                    {"name": "孟娜", "avatar_url": "https://..."}
                ]
            }
        }
    ],
    "time": "2025-12-06 15:54:13"
}
```

---

### 6. 视频详情/演员解析接口

获取视频详情和演员信息。

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| series_id | int | 是 | - | 视频/剧集ID |
| showRawParams | string | 否 | false | 是否返回原始参数 |

**调用示例**

```
GET https://api.cenguigui.cn/api/duanju/api.php?series_id=7512797350914444313&showRawParams=false
```

**响应示例**

```json
{
    "code": 200,
    "msg": "基本信息解析成功",
    "data": {
        "series_id": "7512797350914444313",
        "title": "十八岁太奶奶驾到，重整家族荣耀",
        "intro": "1955年，容遇教授意外去世，一睁眼竟穿到了七十年后一位十八岁同名同姓的高中少女身上。如今她的儿子已成为了七十多岁的董事长，并且她还有了几个帅气的重孙子。后来在适应新生活的过程中，容遇凭借智慧和能力开始整顿这群不孝狂孙，同时也在这个全新的时代找到了属于自己的美好！",
        "pic": "https://p3-reading-sign.fqnovelpic.com/novel-pic/dd5eb56b39e57cc219af28d99b0b937d~tplv-81nmtwyey9-superreso-aifit:400:0.heic",
        "play_cnt": 4806255,
        "read_count": "96016",
        "episode_cnt": 90,
        "tags": ["女性成长"],
        "duration": 7228
    },
    "celebrities": [
        {
            "user_id": "4009257392678188",
            "user_name": "听花岛剧场",
            "description": "关注我！《太奶》《夫人》《家里家外》等系列爆款短剧抢先品鉴～",
            "user_avatar": "https://p3-reading-sign.fqnovelpic.com/tos-cn-i-1yzifmftcy/7a37332eba1445ca8e61feeb25833208~tplv-s85hriknmn-jpeg-v1:144:0.jpeg",
            "sub_title": "短剧版权方"
        },
        {
            "user_id": "1792637711689818",
            "user_name": "李柯以",
            "description": "李柯以，中国内地女演员。2000年12月13日出生于河南洛阳，射手座。代表作《原来你也一直深爱我》《朝朝来池》《夜色温柔》等。",
            "user_avatar": "https://p3-reading-sign.fqnovelpic.com/novel-pic/4a146e9fbbe9992d41a7e9b57e558c88~tplv-s85hriknmn-jpeg-v1:144:0.jpeg",
            "sub_title": "饰 容遇"
        },
        {
            "user_id": "2162073617063002",
            "user_name": "王培延",
            "description": "王培延，中国内地男演员。出生于重庆渝北，毕业于西安交通大学。代表作《我家夫君妻管严》、《金枝缠梦》等。",
            "user_avatar": "https://p3-reading-sign.fqnovelpic.com/novel-pic/86906c78192f4b1270116fd934229de4~tplv-s85hriknmn-jpeg-v1:144:0.jpeg",
            "sub_title": "饰 纪舟野"
        }
    ],
    "comments": [
        {
            "comment_id": "7533156816769876798",
            "comment_text": "是一部光看剧名容易被错过的好剧，爷爷大孙子小孙子都帅，尤其大孙子像韩国演员的气质[赞]",
            "create_time": "2025-07-31 21:38:08",
            "user_info": {
                "user_id": "2446846782352376",
                "user_name": "蓝莓与蓝珠",
                "user_avatar": "https://p3-reading-sign.fqnovelpic.com/tos-cn-i-1yzifmftcy/7cbd69f096694c5dbc60832a2199cd7a~tplv-s85hriknmn-jpeg-v1:144:0.heic"
            },
            "score": "10",
            "stat": {
                "digg_count": 3,
                "reply_count": 1
            }
        }
    ],
    "comments_total": 2634,
    "time": "2025-12-06 16:08:07"
}
```

**响应字段说明**

| 字段 | 类型 | 描述 |
|------|------|------|
| series_id | string | 视频ID |
| title | string | 视频标题 |
| intro | string | 视频简介 |
| pic | string | 封面图片URL |
| play_cnt | int | 播放次数 |
| episode_cnt | int | 总集数 |
| tags | array | 标签列表 |
| duration | int | 总时长(秒) |
| celebrities | array | 演员/主创列表 |
| celebrities[].user_id | string | 用户ID |
| celebrities[].user_name | string | 用户名称 |
| celebrities[].user_avatar | string | 用户头像URL |
| celebrities[].sub_title | string | 角色/职位描述 |
| comments | array | 评论列表 |
| comments_total | int | 总评论数 |

---

### 7. 演员信息接口

获取指定演员的信息和作品列表。

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| user_id | int | 是 | - | 演员ID |
| page | int | 是 | 1 | 页码，每页10条数据 |
| showRawParams | string | 否 | false | 是否返回原始参数 |

**调用示例**

```
GET https://api.cenguigui.cn/api/duanju/api.php?user_id=2162073617063002&page=1&showRawParams=false
```

**响应示例**

```json
{
    "code": 200,
    "msg": "演员信息解析成功",
    "actor_info": {
        "user_id": "2162073617063002",
        "user_name": "王培延",
        "user_avatar": "https://p3-reading-sign.fqnovelpic.com/novel-pic/86906c78192f4b1270116fd934229de4~tplv-s85hriknmn-jpeg-v1:144:0.jpeg",
        "gender": 1,
        "description": "王培延，中国内地男演员。出生于重庆渝北，毕业于西安交通大学。代表作《我家夫君妻管严》、《金枝缠梦》等。",
        "is_official_cert": false,
        "is_vip": false,
        "sub_titles": [
            {
                "text": "男演员",
                "text_ext": 0
            },
            {
                "text": "演员榜 No.11",
                "text_ext": 19
            }
        ],
        "fans_count": 1077381,
        "follow_count": 0,
        "digg_count": 113055774
    },
    "videos": [
        {
            "video_id": "7578787460834937881",
            "title": "丞相姐姐你又又又红温了",
            "intro": "入朝为官十余载，崔景钰一直都在为了他人而活。直到她被伤得体无完肤才终于明白，真正爱她的人，会接受她所有的模样。",
            "cover": "https://p3-reading-sign.fqnovelpic.com/novel-pic/59497dc193ebab6c51b7621b530ab223~tplv-81nmtwyey9-superreso-aifit:400:0.heic",
            "sub_titles": ["古风言情", "75集"],
            "play_count": 386786,
            "hot_score": 30704361
        },
        {
            "video_id": "7577339455728520217",
            "title": "家里家外2",
            "intro": "1986年，艳艳家电行开张，同一天，泼辣能干的蔡晓艳生下一个孩子，她和耙耳朵丈夫陈海清给孩子取名陈三轮。",
            "cover": "https://p3-reading-sign.fqnovelpic.com/novel-pic/aeeb74662c4c02ad8c55c1c1d149a124~tplv-81nmtwyey9-superreso-aifit:400:0.heic",
            "sub_titles": ["家庭伦理", "111集"],
            "play_count": 7792584,
            "hot_score": 118053077
        }
    ],
    "total": 10,
    "total_all": 29,
    "time": "2025-12-06 16:08:13"
}
```

**响应字段说明**

| 字段 | 类型 | 描述 |
|------|------|------|
| user_id | string | 演员ID |
| user_name | string | 演员名称 |
| user_avatar | string | 演员头像URL |
| gender | int | 性别 (1=男, 0=女) |
| description | string | 个人简介 |
| is_official_cert | bool | 是否官方认证 |
| is_vip | bool | 是否VIP |
| fans_count | int | 粉丝数 |
| follow_count | int | 关注数 |
| digg_count | int | 获赞数 |
| videos | array | 作品列表 |
| videos[].video_id | string | 视频ID |
| videos[].title | string | 作品标题 |
| videos[].intro | string | 作品简介 |
| videos[].cover | string | 封面图片URL |
| videos[].sub_titles | array | 分类和集数 |
| videos[].play_count | int | 播放次数 |
| videos[].hot_score | int | 热度分数 |
| total | int | 当前页作品数 |
| total_all | int | 总作品数 |

---

### 8. 评论接口

获取视频的评论列表。

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| comments_id | int | 是 | - | 视频ID |
| page | int | 是 | 1 | 页码，每页20条评论 |
| showRawParams | string | 否 | false | 是否返回原始参数 |

**调用示例**

```
GET https://api.cenguigui.cn/api/duanju/api.php?comments_id=7563872366422395966&page=1&showRawParams=false
```

**响应示例**

```json
{
    "code": 200,
    "msg": "成功",
    "data": [
        {
            "comment_id": "7565564165899076377",
            "content": "感情细腻，娓娓道来的爱情故事，演员表演也很到位，尤其是女主，完美演绎。",
            "content_type": 0,
            "comment_type": 0,
            "create_time": "2025-10-27 07:12:43",
            "create_timestamp": 1761520363,
            "status": 1,
            "user_info": {
                "user_id": "652470685797139",
                "user_name": "LWohts",
                "user_avatar": "https://p26.douyinpic.com/aweme/1080x1080/aweme-avatar/tos-cn-i-0813c000-ce_oIF7Z0AASXRnCIABuSPPAh66ihMYDPAT65i9E.jpeg",
                "gender": 0,
                "description": ""
            },
            "user_tag": {
                "is_author": false,
                "is_official_cert": false,
                "is_vip": false
            },
            "stat": {
                "digg_count": 2,
                "reply_count": 0,
                "read_duration": 10236,
                "show_pv": 630
            }
        },
        {
            "comment_id": "7565719310793016089",
            "content": "破镜重圆，对彼此坚定的爱意即使在分开时也能过好自己，再次相遇，他们都成了更好的自己。",
            "content_type": 0,
            "comment_type": 0,
            "create_time": "2025-10-27 13:27:31",
            "create_timestamp": 1761542851,
            "status": 1,
            "user_info": {
                "user_id": "798709504808467",
                "user_name": "阳光花匠花女士",
                "user_avatar": "https://p3-novel.byteimg.com/img/novel-static/1437c63bc45b464bb1cc6cd6a7b0d4f1~tplv-1yzifmftcy-expand:200:0:0.heic",
                "gender": 0,
                "description": ""
            },
            "user_tag": {
                "is_author": false,
                "is_official_cert": false,
                "is_vip": false
            },
            "stat": {
                "digg_count": 2,
                "reply_count": 0,
                "read_duration": 5851,
                "show_pv": 17038
            }
        },
        {
            "comment_id": "7580558037527069502",
            "content": "very good",
            "content_type": 0,
            "comment_type": 0,
            "create_time": "2025-12-06 13:12:23",
            "create_timestamp": 1764997943,
            "status": 1,
            "user_info": {
                "user_id": "3578277553768852",
                "user_name": "善良真千金叶南灯",
                "user_avatar": "https://p3-novel.byteimg.com/img/novel-static/3abe6a50e39b4bf1ba7c29f33074e1a8~tplv-1yzifmftcy-expand:200:0:0.heic",
                "gender": 0,
                "description": ""
            },
            "user_tag": {
                "is_author": false,
                "is_official_cert": false,
                "is_vip": false
            },
            "stat": {
                "digg_count": 0,
                "reply_count": 0,
                "read_duration": 8119,
                "show_pv": 36
            }
        }
    ],
    "time": "2025-12-06 16:08:19"
}
```

**响应字段说明**

| 字段 | 类型 | 描述 |
|------|------|------|
| comment_id | string | 评论ID |
| content | string | 评论内容 |
| content_type | int | 内容类型 (0=文本) |
| comment_type | int | 评论类型 (0=普通评论) |
| create_time | string | 创建时间 |
| create_timestamp | int | 创建时间戳 |
| status | int | 状态 (1=正常) |
| user_info.user_id | string | 用户ID |
| user_info.user_name | string | 用户昵称 |
| user_info.user_avatar | string | 用户头像URL |
| user_info.gender | int | 性别 (0=未知, 1=男, 2=女) |
| user_info.description | string | 用户描述 |
| user_tag.is_author | bool | 是否作者 |
| user_tag.is_official_cert | bool | 是否官方认证 |
| user_tag.is_vip | bool | 是否VIP |
| stat.digg_count | int | 点赞数 |
| stat.reply_count | int | 回复数 |
| stat.read_duration | int | 阅读时长(毫秒) |
| stat.show_pv | int | 展示次数 |

---

## Python 调用示例

### 使用项目内置服务

```python
from src.data.api.api_client import ApiClient
from src.services.search_service import SearchService
from src.services.video_service import VideoService
from src.services.category_service import CategoryService
from src.data.cache.cache_manager import CacheManager

# 初始化
api_client = ApiClient()
cache = CacheManager()

# 搜索服务
search_service = SearchService(api_client, cache)
search_service.search("总裁", page=1)

# 视频服务
video_service = VideoService(api_client)
video_service.fetch_episodes("7416545333695499326")
video_service.fetch_video_url("7416589528229497881", quality="1080p")

# 分类服务
category_service = CategoryService(api_client, cache)
category_service.fetch_categories()
category_service.fetch_category_dramas("穿越", offset=1)
category_service.fetch_recommendations()
```

---

## 联系方式

- **开发者**: 笒鬼鬼
- **QQ**: 2963246343
- **邮箱**: cenguigui@qq.com

> ⚠️ 若侵犯您的利益请联系: cenguigui@qq.com

# 本项目调用岑鬼鬼的第三方短剧API，但是并非岑鬼鬼所开发。侵权请联系岑鬼鬼，API一旦失效项目所有功能自然失效。