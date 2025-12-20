# 即刻短剧 API 调用文档

## 概述

本文档描述了即刻短剧 API (api.uuuka.com) 的完整调用方式。该 API 提供短剧、动漫、电影、电视剧等内容的索引和搜索服务。

**注意**: 此 API 返回的是外部链接 (`source_link`)，而非直接的视频播放地址。

## 基本信息

- **基础URL**: `https://api.uuuka.com`
- **请求方法**: GET
- **响应格式**: JSON
- **API版本**: v2.2.1
- **技术支持邮箱**: uchatrun@gmail.com

---

## 内容类型说明

| 类型标识 | 名称 | 描述 |
|----------|------|------|
| post | 短剧 | 热门短剧、微剧、网剧内容 |
| dongman | 动漫 | 国产动漫、日漫、欧美动画 |
| movie | 电影 | 院线电影、网络电影资源 |
| tv | 电视剧 | 热播剧集、经典电视剧 |
| xuexi | 学习资源 | 教育视频、技能培训内容 |
| baidu | 百度短剧 | 百度短剧资源内容 |

---

## API 接口列表

### 1. 获取所有内容

获取所有类型的内容列表。

**请求地址**

```
GET /api/contents
```

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| page | int | 否 | 1 | 页码，范围：1-1000 |
| limit | int | 否 | 20 | 每页数量，范围：1-100 |
| today | string | 否 | - | 查询今日更新，传入任意值即可 |

**调用示例**

```
GET https://api.uuuka.com/api/contents?page=1&limit=20
GET https://api.uuuka.com/api/contents?today&page=1&limit=20
```

**响应示例**

```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "items": [
      {
        "title": "霸道总裁的小甜妻",
        "source_link": "https://example.com/drama1",
        "type": "post",
        "update_time": "2024-01-01 10:30:00"
      }
    ],
    "total": 1000,
    "page": 1,
    "limit": 20,
    "total_pages": 50
  }
}
```

---

### 2. 按类型获取内容

获取指定类型的内容列表，支持关键词搜索。

**请求地址**

```
GET /api/contents/{content_type}
```

**路径参数**

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| content_type | string | 是 | 内容类型：post/dongman/movie/tv/xuexi/baidu |

**查询参数**

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| page | int | 否 | 1 | 页码，范围：1-1000 |
| limit | int | 否 | 20 | 每页数量，范围：1-100 |
| keyword | string | 否 | - | 搜索关键词，支持模糊搜索 |
| today | string | 否 | - | 查询今日更新，传入任意值即可 |

**调用示例**

```
GET https://api.uuuka.com/api/contents/post?page=1&limit=20
GET https://api.uuuka.com/api/contents/post?keyword=霸道总裁&page=1&limit=20
GET https://api.uuuka.com/api/contents/post?today&page=1&limit=20
GET https://api.uuuka.com/api/contents/baidu?page=1&limit=20
```

**响应示例**

```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "items": [
      {
        "title": "霸道总裁的小甜妻",
        "source_link": "https://example.com/drama1",
        "type": "post",
        "update_time": "2024-01-01 10:30:00"
      }
    ],
    "total": 50,
    "page": 1,
    "limit": 20,
    "total_pages": 3,
    "content_type": "post",
    "keyword": "霸道总裁"
  }
}
```

---

### 3. 获取指定类型的全部内容

获取指定类型的所有数据，不进行分页。

**⚠️ 重要限制**: 此接口每分钟只能请求一次！限流基于 IP 地址，全局限流，不区分内容类型。

**请求地址**

```
GET /api/contents/{content_type}/all
```

**路径参数**

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| content_type | string | 是 | 内容类型：post/dongman/movie/tv/xuexi/baidu |

**调用示例**

```
GET https://api.uuuka.com/api/contents/post/all
GET https://api.uuuka.com/api/contents/movie/all
GET https://api.uuuka.com/api/contents/dongman/all
GET https://api.uuuka.com/api/contents/baidu/all
```

**响应示例**

```json
{
  "success": true,
  "message": "获取全部内容成功",
  "data": {
    "items": [
      {
        "title": "短剧标题1",
        "source_link": "https://example.com/drama1",
        "update_time": "2024-01-15 10:30:00",
        "type": "post"
      }
    ],
    "total": 5000,
    "content_type": "post",
    "is_all_data": true
  }
}
```

**限流错误响应**

```json
{
  "success": false,
  "message": "请求频率超过限制",
  "error": "全部内容接口每分钟只能请求一次，请等待 45 秒后重试",
  "error_code": "RATE_LIMIT_EXCEEDED"
}
```

---

### 4. 获取今日更新内容

查询指定内容类型在今日更新的所有内容。

**请求地址**

```
GET /api/contents/{content_type}?today
```

**路径参数**

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| content_type | string | 是 | 内容类型：post/dongman/movie/tv/xuexi/baidu |

**查询参数**

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| today | string | 是 | - | 查询今日更新，传入任意值即可 |
| page | int | 否 | 1 | 页码，范围：1-1000 |
| limit | int | 否 | 20 | 每页数量，范围：1-100 |

**调用示例**

```
GET https://api.uuuka.com/api/contents/post?today
GET https://api.uuuka.com/api/contents/post?today&page=1&limit=20
GET https://api.uuuka.com/api/contents?today
```

**响应示例**

```json
{
  "success": true,
  "message": "获取今日数据成功",
  "data": {
    "items": [
      {
        "title": "今日更新的短剧标题",
        "source_link": "https://example.com/drama1",
        "update_time": "2024-01-15 10:30:00",
        "type": "post"
      }
    ],
    "total": 50,
    "page": 1,
    "limit": 20,
    "total_pages": 3,
    "content_type": "post",
    "today": true
  }
}
```

---

### 5. 获取支持的内容类型

获取 API 支持的所有内容类型列表。

**请求地址**

```
GET /api/types
```

**调用示例**

```
GET https://api.uuuka.com/api/types
```

**响应示例**

```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "supported_types": {
      "post": {
        "name": "短剧",
        "description": "热门短剧、微剧、网剧内容"
      },
      "dongman": {
        "name": "动漫",
        "description": "国产动漫、日漫、欧美动画"
      },
      "movie": {
        "name": "电影",
        "description": "院线电影、网络电影资源"
      },
      "tv": {
        "name": "电视剧",
        "description": "热播剧集、经典电视剧"
      },
      "xuexi": {
        "name": "学习资源",
        "description": "教育视频、技能培训内容"
      },
      "baidu": {
        "name": "百度短剧",
        "description": "百度短剧资源内容"
      }
    },
    "total_types": 6
  }
}
```

---

### 6. 搜索接口

全局搜索内容，支持按类型过滤。

**请求地址**

```
GET /api/search
```

**请求参数**

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| keyword | string | 是 | - | 搜索关键词，长度：1-100字符 |
| content_type | string | 否 | - | 内容类型过滤 |
| page | int | 否 | 1 | 页码，范围：1-1000 |
| limit | int | 否 | 20 | 每页数量，范围：1-100 |

**调用示例**

```
GET https://api.uuuka.com/api/search?keyword=霸道总裁
GET https://api.uuuka.com/api/search?keyword=霸道总裁&content_type=post&page=1&limit=20
```

**响应示例**

```json
{
  "success": true,
  "message": "搜索成功",
  "data": {
    "items": [
      {
        "title": "霸道总裁的小甜妻",
        "source_link": "https://example.com/drama1",
        "type": "post",
        "update_time": "2024-01-01 10:30:00"
      }
    ],
    "total": 25,
    "page": 1,
    "limit": 20,
    "total_pages": 2,
    "keyword": "霸道总裁",
    "content_type": "post"
  }
}
```

---

### 7. 系统状态接口

获取 API 服务状态信息。

**请求地址**

```
GET /api/status
```

**调用示例**

```
GET https://api.uuuka.com/api/status
```

**响应示例**

```json
{
  "success": true,
  "message": "API服务正常运行",
  "data": {
    "service": "即刻短剧API",
    "version": "2.2.1",
    "status": "running",
    "environment": "production",
    "features": [
      "短剧内容管理",
      "智能搜索引擎",
      "安全防护系统",
      "实时数据同步",
      "移动端优化"
    ]
  }
}
```

---

### 8. 健康检查接口

检查 API 服务健康状态。

**请求地址**

```
GET /api/health
```

**调用示例**

```
GET https://api.uuuka.com/api/health
```

**响应示例**

```json
{
  "success": true,
  "message": "服务健康",
  "data": {
    "status": "healthy",
    "database": "connected",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

---

## 响应字段说明

### 通用响应结构

| 字段 | 类型 | 描述 |
|------|------|------|
| success | boolean | 请求是否成功 |
| message | string | 响应消息 |
| data | object | 响应数据 |

### 内容项字段

| 字段 | 类型 | 描述 |
|------|------|------|
| title | string | 内容标题 |
| source_link | string | 外部来源链接 |
| type | string | 内容类型 |
| update_time | string | 更新时间 |

### 分页字段

| 字段 | 类型 | 描述 |
|------|------|------|
| total | int | 总数量 |
| page | int | 当前页码 |
| limit | int | 每页数量 |
| total_pages | int | 总页数 |

---

## 错误码说明

| 状态码 | 错误码 | 说明 | 解决方案 |
|--------|--------|------|----------|
| 200 | - | 请求成功 | - |
| 400 | BAD_REQUEST | 请求参数错误 | 检查请求参数格式和取值范围 |
| 404 | RESOURCE_NOT_FOUND | 请求的资源不存在 | 检查请求URL是否正确 |
| 429 | RATE_LIMIT_EXCEEDED | 请求频率超过限制 | 稍后重试或联系技术支持 |
| 500 | INTERNAL_SERVER_ERROR | 服务器内部错误 | 稍后重试或联系技术支持 |

**错误响应格式**

```json
{
  "success": false,
  "message": "错误描述",
  "error_code": "ERROR_CODE",
  "error": "详细错误信息",
  "suggestion": "解决建议"
}
```

---

## Python 调用示例

### 使用 aiohttp 调用

```python
import aiohttp
import asyncio

BASE_URL = "https://api.uuuka.com"

async def search_content(keyword: str, content_type: str = "post", page: int = 1, limit: int = 20):
    """搜索内容"""
    async with aiohttp.ClientSession() as session:
        params = {
            "keyword": keyword,
            "content_type": content_type,
            "page": page,
            "limit": limit
        }
        async with session.get(f"{BASE_URL}/api/search", params=params) as response:
            return await response.json()

async def get_contents_by_type(content_type: str, page: int = 1, limit: int = 20, keyword: str = None):
    """按类型获取内容"""
    async with aiohttp.ClientSession() as session:
        params = {"page": page, "limit": limit}
        if keyword:
            params["keyword"] = keyword
        async with session.get(f"{BASE_URL}/api/contents/{content_type}", params=params) as response:
            return await response.json()

async def get_today_updates(content_type: str = "post", page: int = 1, limit: int = 20):
    """获取今日更新"""
    async with aiohttp.ClientSession() as session:
        params = {"today": "today", "page": page, "limit": limit}
        async with session.get(f"{BASE_URL}/api/contents/{content_type}", params=params) as response:
            return await response.json()

async def get_all_contents(content_type: str):
    """获取全部内容（每分钟只能请求一次）"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/api/contents/{content_type}/all") as response:
            return await response.json()

async def get_supported_types():
    """获取支持的内容类型"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/api/types") as response:
            return await response.json()

async def check_status():
    """检查API状态"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/api/status") as response:
            return await response.json()

# 使用示例
async def main():
    # 搜索短剧
    result = await search_content("霸道总裁", content_type="post")
    if result.get("success"):
        print("搜索结果:", result["data"]["items"])
    
    # 获取短剧列表
    dramas = await get_contents_by_type("post", page=1, limit=10)
    if dramas.get("success"):
        print("短剧列表:", dramas["data"]["items"])
    
    # 获取今日更新
    today = await get_today_updates("post")
    if today.get("success"):
        print("今日更新:", today["data"]["items"])
    
    # 获取百度短剧
    baidu = await get_contents_by_type("baidu", page=1, limit=20)
    if baidu.get("success"):
        print("百度短剧:", baidu["data"]["items"])
    
    # 检查API状态
    status = await check_status()
    print("API状态:", status)

asyncio.run(main())
```

### 使用 requests 调用

```python
import requests

BASE_URL = "https://api.uuuka.com"

# 搜索短剧
response = requests.get(f"{BASE_URL}/api/search", params={
    "keyword": "霸道总裁",
    "content_type": "post",
    "page": 1,
    "limit": 20
})

if response.status_code == 200:
    data = response.json()
    if data["success"]:
        print("搜索结果:", data["data"]["items"])
    else:
        print("搜索失败:", data["message"])

# 获取短剧列表
response = requests.get(f"{BASE_URL}/api/contents/post", params={
    "page": 1,
    "limit": 10,
    "keyword": "霸道总裁"
})

if response.status_code == 200:
    data = response.json()
    if data["success"]:
        print("短剧列表:", data["data"]["items"])

# 获取今日更新
response = requests.get(f"{BASE_URL}/api/contents/post", params={
    "today": "today",
    "page": 1,
    "limit": 10
})

if response.status_code == 200:
    data = response.json()
    if data["success"]:
        print("今日更新:", data["data"]["items"])

# 获取全部短剧（每分钟只能请求一次）
response = requests.get(f"{BASE_URL}/api/contents/post/all")

if response.status_code == 200:
    data = response.json()
    if data["success"]:
        print("全部短剧:", data["data"]["items"])
        print("总数:", data["data"]["total"])
    elif data.get("error_code") == "RATE_LIMIT_EXCEEDED":
        print("请求过于频繁:", data["error"])
```

---

## cURL 调用示例

```bash
# 获取所有内容
curl -X GET "https://api.uuuka.com/api/contents?page=1&limit=20"

# 获取指定类型内容
curl -X GET "https://api.uuuka.com/api/contents/post?page=1&limit=10&keyword=霸道总裁"

# 获取百度短剧
curl -X GET "https://api.uuuka.com/api/contents/baidu?page=1&limit=20"

# 搜索百度短剧
curl -X GET "https://api.uuuka.com/api/contents/baidu?keyword=关键词&page=1&limit=20"

# 获取指定类型的全部内容（每分钟只能请求一次）
curl -X GET "https://api.uuuka.com/api/contents/post/all"

# 获取今日更新内容
curl -X GET "https://api.uuuka.com/api/contents/post?today"
curl -X GET "https://api.uuuka.com/api/contents/post?today&page=1&limit=20"

# 搜索内容
curl -X GET "https://api.uuuka.com/api/search?keyword=霸道总裁&content_type=post&page=1&limit=20"

# 获取支持的内容类型
curl -X GET "https://api.uuuka.com/api/types"

# 获取系统状态
curl -X GET "https://api.uuuka.com/api/status"

# 健康检查
curl -X GET "https://api.uuuka.com/api/health"
```

---

## JavaScript 调用示例

```javascript
const BASE_URL = "https://api.uuuka.com";

// 搜索短剧
fetch(`${BASE_URL}/api/search?keyword=霸道总裁&content_type=post&page=1&limit=20`)
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      console.log("搜索结果:", data.data.items);
    } else {
      console.error("搜索失败:", data.message);
    }
  })
  .catch(error => {
    console.error("请求错误:", error);
  });

// 获取短剧列表
fetch(`${BASE_URL}/api/contents/post?page=1&limit=10`)
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      console.log("短剧列表:", data.data.items);
    }
  });

// 获取今日更新的短剧
fetch(`${BASE_URL}/api/contents/post?today&page=1&limit=10`)
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      console.log("今日更新:", data.data.items);
    }
  });

// 获取百度短剧
fetch(`${BASE_URL}/api/contents/baidu?page=1&limit=20`)
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      console.log("百度短剧:", data.data.items);
    }
  });

// 获取全部短剧（每分钟只能请求一次）
fetch(`${BASE_URL}/api/contents/post/all`)
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      console.log("全部短剧:", data.data.items);
      console.log("总数:", data.data.total);
    } else if (data.error_code === "RATE_LIMIT_EXCEEDED") {
      console.error("请求过于频繁:", data.error);
    }
  });
```

---

## 注意事项

1. **限流规则**
   - 普通接口：建议控制在 10 秒 5 次以内
   - `/all` 接口：每分钟只能请求一次，全局限流，不区分内容类型

2. **数据特点**
   - 此 API 返回的是外部链接 (`source_link`)，不是直接的视频播放地址
   - 需要通过外部链接访问实际内容

3. **最佳实践**
   - 日常查询请使用分页接口
   - 仅在需要完整数据时使用 `/all` 接口
   - 搜索关键词请避免使用特殊字符
   - 建议在生产环境中使用 HTTPS 协议

4. **缓存说明**
   - `/all` 接口结果会缓存 1 小时，提高响应速度

---

## 联系方式

- **技术支持邮箱**: uchatrun@gmail.com
- **商务合作邮箱**: uchatrun@gmail.com
- **API版本**: v2.2.1
- **最后更新**: 2025年6月

---

## 本项目适配器说明

本项目中的 `UuukaAdapter` 适配器 (`src/data/providers/adapters/uuuka_adapter.py`) 实现了对此 API 的调用。

**支持的功能**:
- ✅ 搜索短剧
- ✅ 分类浏览（短剧、动漫、电影、电视剧、学习资源、百度短剧）
- ✅ 获取今日更新（推荐内容）

**不支持的功能**:
- ❌ 获取剧集列表（API 不提供）
- ❌ 获取视频播放地址（API 返回外部链接）
- ❌ 清晰度选择（API 不提供）

由于此 API 的特性，选择此数据源后，点击短剧将显示外部链接信息，需要通过外部链接访问实际内容。
