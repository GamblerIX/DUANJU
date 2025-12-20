# 全网短剧 API 调用文档

## 概述

全网短剧 API (kuoapp.com) 提供短剧数据的获取、搜索、每日更新和热榜功能。

**重要说明**：此 API 返回的是夸克网盘链接（pan.quark.cn），不提供直接的视频播放地址。

## 基础信息

| 项目 | 说明 |
|------|------|
| 基础 URL | `https://kuoapp.com` |
| 请求方式 | GET |
| 数据格式 | JSON |
| 编码 | UTF-8 |

---

## API 接口列表

### 1. 获取数据内容接口

获取指定日期或全部短剧数据。

**请求地址**
```
GET /duanju/get.php
```

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| day | string | 否 | 日期格式 `YYYY-MM-DD`，为空获取当天数据，无此参数获取所有数据 |

**请求示例**
```
GET https://kuoapp.com/duanju/get.php?day=2024-06-28
GET https://kuoapp.com/duanju/get.php
```

**响应示例**
```json
[
    {
        "id": "667ee09674117",
        "name": "与君青丝共白首（34集）",
        "label": 0,
        "addtime": "2024-06-28",
        "cover": "https://t12.baidu.com/it/u=3859229605,220847762&fm=30&app=106&f=JPEG",
        "url": "https://pan.quark.cn/s/7c6179aeab8f",
        "episodes": "34",
        "state": 0
    }
]
```

---

### 2. 关键词搜索接口

根据关键词搜索短剧，支持分页。

**请求地址**
```
GET /duanju/api.php
```

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| param | string | 是 | 固定值 `1` |
| name | string | 是 | 搜索关键词 |
| page | string | 否 | 页码，默认 1 |

**请求示例**
```
GET https://kuoapp.com/duanju/api.php?param=1&name=总裁&page=1
```

**响应示例**
```json
{
    "page": "1",
    "totalPages": 119,
    "data": [
        {
            "id": "667fb7e8e02e3",
            "name": "哦莫，我把总裁老公拉黑了（90集）",
            "label": 0,
            "addtime": "2024-06-29",
            "cover": "https://t12.baidu.com/it/u=3859229605,220847762&fm=30&app=106&f=JPEG",
            "url": "https://pan.quark.cn/s/923798930923",
            "episodes": "90",
            "state": 0
        }
    ]
}
```

---

### 3. 每日更新列表接口

获取指定日期的更新列表。

**请求地址**
```
GET /duanju/get.php
```

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| day | string | 否 | 日期格式 `YYYY-MM-DD`，指定日期实时更新 |

**请求示例**
```
GET https://kuoapp.com/duanju/get.php?day=2024-06-06
```

**响应示例**
```json
[
    {
        "id": "6661d0982d927",
        "name": "蓄意引诱禁欲老公又野又撩（98集）",
        "label": 0,
        "addtime": "2024-06-06",
        "cover": "https://t12.baidu.com/...",
        "url": "https://pan.quark.cn/s/1d8ed017117b",
        "episodes": "98",
        "state": 0
    }
]
```

---

### 4. 短剧热榜接口

获取热门短剧排行榜。

**请求地址**
```
GET /duanju/hot.php
```

**响应字段说明**

| 字段名 | 类型 | 说明 |
|--------|------|------|
| ranking | integer | 排名 |
| playletId | integer | 短剧ID |
| playletName | string | 短剧名称 |
| totalConsumeNum | integer | 总消费数 |
| consumeNum | integer | 消费数 |
| newFlag | boolean | 是否新剧 |
| coverOss | string | 封面图片 |
| playletTags | array | 标签列表 |

---

## 数据字段说明

### 短剧数据项

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | string | 短剧唯一ID |
| name | string | 短剧名称（通常包含集数） |
| label | integer | 标签 |
| addtime | string | 创建/更新日期 |
| cover | string | 封面图片URL |
| url | string | 夸克网盘链接 |
| episodes | string | 集数 |
| state | integer | 状态 |

---

## 使用限制

- 建议请求频率：10秒内不超过5次
- 返回数据为夸克网盘链接，需要用户自行访问网盘获取资源

---

## 适配器信息

适配器 ID: `duanju_search`
适配器名称: 全网短剧API

---

## 注意事项

1. **网盘链接**：此 API 返回的是夸克网盘链接（pan.quark.cn），不支持直接播放
2. **数据时效**：每日更新数据实时同步，如果当天没有数据会自动查找最近有数据的日期
3. **全量数据**：不带 day 参数会返回全部数据，数据量很大可能导致超时
4. **版权声明**：请遵守相关法律法规，合理使用数据
