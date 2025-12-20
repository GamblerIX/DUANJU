# DuanjuApp 自动化测试框架

全自动化测试框架，支持 AI 辅助的测试生成、错误诊断和自动修复建议。
当前测试覆盖 **1199 个测试用例**，代码覆盖率 **87%**，确保代码质量和用户使用时的稳定性。

## 快速开始

### 安装测试依赖

```bash
pip install -r test/requirements-test.txt
```

### 运行所有测试

```bash
# 方式1: 使用测试运行器
python test/run_tests.py

# 方式2: 直接使用 pytest
pytest test/ -v

# 方式3: 使用自动测试运行器
python test/auto_test_runner.py
```

### 运行特定测试

```bash
# 只运行单元测试（快速验证）
python test/run_tests.py -q
python test/auto_test_runner.py -q

# 运行匹配关键词的测试
pytest test/ -k "test_search"
python test/auto_test_runner.py -k search

# 运行特定文件
pytest test/test_models.py -v

# 运行与源文件相关的测试
python test/auto_test_runner.py -f src/data/cache/cache_manager.py
```

## 测试框架结构

```
test/
├── __init__.py              # 测试包初始化
├── conftest.py              # pytest 配置和共享 fixtures
├── pytest.ini               # pytest 配置文件
├── requirements-test.txt    # 测试依赖
├── README.md                # 本文档
│
├── run_tests.py             # 测试入口脚本
├── auto_test_runner.py      # 自动测试运行器（含错误分析）
├── ai_test_assistant.py     # AI 测试助手
├── auto_test_generator.py   # 自动测试生成器
│
├── test_models.py           # 数据模型测试 (66 tests)
├── test_models_equality.py  # 模型相等性测试 (18 tests)
├── test_utils.py            # 工具函数测试 (21 tests)
├── test_services.py         # 服务层测试 (48 tests)
├── test_api_client.py       # API 客户端测试 (9 tests)
├── test_response_parser.py  # 响应解析器测试 (41 tests)
├── test_cache_manager.py    # 缓存管理器测试 (44 tests)
├── test_config_manager.py   # 配置管理器测试 (20 tests)
├── test_favorites_history.py # 收藏和历史测试 (28 tests)
├── test_providers.py        # 数据提供者测试 (41 tests)
├── test_adapters.py         # API 适配器测试 (161 tests)
├── test_json_serializer.py  # JSON 序列化测试 (16 tests)
├── test_log_manager.py      # 日志管理器测试 (61 tests)
├── test_async_worker.py     # 异步工作线程测试 (48 tests)
├── test_download_service.py # 下载服务测试 (61 tests)
├── test_download_service_v2.py # 下载服务V2测试 (54 tests)
├── test_image_loader.py     # 图片加载器测试 (70 tests)
├── test_network_monitor.py  # 网络监控测试 (37 tests)
├── test_video_service.py    # 视频服务测试 (28 tests)
├── test_category_service.py # 分类服务测试 (28 tests)
├── test_integration.py      # 集成测试 (15 tests)
└── test_end_to_end.py       # 端到端测试 (12 tests)
```

## 核心功能

### 1. 自动测试运行器 (auto_test_runner.py)

自动发现、运行测试并分析错误：

```python
from test.auto_test_runner import AutoTestRunner

runner = AutoTestRunner()
report = runner.run_all_tests()

# 生成 JSON 报告
runner.generate_json_report(Path("report.json"))
```

### 2. AI 测试助手 (ai_test_assistant.py)

提供代码分析、测试建议和错误诊断：

```python
from test.ai_test_assistant import AITestAssistant

assistant = AITestAssistant()

# 分析项目
summary = assistant.analyze_project()

# 获取测试覆盖报告
coverage = assistant.get_test_coverage_report()

# 诊断错误
diagnosis = assistant.diagnose_error("ImportError: cannot import name 'xxx'")
```

### 3. 错误自动分析

测试失败时自动分析错误原因并提供修复建议：

- ImportError: 检查导入路径
- ModuleNotFoundError: 安装缺失模块
- AttributeError: 检查属性名
- TypeError: 检查参数类型
- AssertionError: 检查测试期望值

## 命令行选项

```bash
python test/run_tests.py [选项]

选项:
  -v, --verbose    详细输出模式
  -q, --quick      快速测试模式（跳过集成测试）
  -a, --analyze    运行 AI 分析
  -r, --report     生成 JSON 报告
```

## 测试标记

使用 pytest 标记来分类测试：

```python
@pytest.mark.unit
def test_unit_example():
    """单元测试"""
    pass

@pytest.mark.integration
def test_integration_example():
    """集成测试"""
    pass

@pytest.mark.slow
def test_slow_example():
    """慢速测试"""
    pass

@pytest.mark.asyncio
async def test_async_example():
    """异步测试"""
    pass
```

运行特定标记的测试：

```bash
pytest test/ -m unit        # 只运行单元测试
pytest test/ -m "not slow"  # 跳过慢速测试
```

## 编写测试指南

### 1. 使用 fixtures

```python
def test_example(sample_drama, mock_api_client):
    """使用 conftest.py 中定义的 fixtures"""
    assert sample_drama.title == "测试短剧"
```

### 2. 异步测试

```python
@pytest.mark.asyncio
async def test_async_api():
    """异步测试示例"""
    client = ApiClient()
    response = await client.get(params={"name": "test"})
    assert response.success
```

### 3. Mock 使用

```python
from unittest.mock import MagicMock, AsyncMock, patch

def test_with_mock():
    """使用 mock 的测试"""
    mock_service = MagicMock()
    mock_service.search = AsyncMock(return_value=SearchResult(...))
    
    # 测试逻辑
```

## 测试报告

运行测试后会生成详细报告，包括：

- 测试通过/失败统计
- 执行时间
- 错误分析和修复建议
- 测试覆盖率（如果启用）

生成 HTML 报告：

```bash
pytest test/ --html=report.html
```

生成覆盖率报告：

```bash
pytest test/ --cov=src --cov-report=html
```

## 自动测试生成

为新代码自动生成测试框架：

```bash
# 分析测试覆盖情况
python test/auto_test_generator.py -a

# 为所有源文件生成测试框架
python test/auto_test_generator.py -g

# 指定输出目录
python test/auto_test_generator.py -g -o test/generated
```

## 持续集成

### 文件变更时自动测试

```bash
# 运行与变更文件相关的测试
python test/auto_test_runner.py -f src/data/cache/cache_manager.py
```

### 完整测试套件

```bash
# 运行完整测试并生成报告
python test/auto_test_runner.py --full
```

## 测试覆盖范围

| 模块 | 测试文件 | 测试数 | 覆盖内容 |
|------|----------|--------|----------|
| 数据模型 | test_models.py | 66 | DramaInfo, EpisodeInfo, VideoInfo, SearchResult 等 |
| 模型相等性 | test_models_equality.py | 18 | 模型对象的相等性比较 |
| 工具函数 | test_utils.py | 21 | 字符串处理、文件大小格式化等 |
| API 客户端 | test_api_client.py | 9 | HTTP 请求、超时处理、错误处理 |
| API 适配器 | test_adapters.py | 161 | Cenguigui、Uuuka、DuanjuSearch 适配器 |
| 响应解析 | test_response_parser.py | 41 | 搜索结果、剧集列表、视频信息解析 |
| 缓存管理 | test_cache_manager.py | 44 | 缓存存取、过期、LRU 淘汰 |
| 配置管理 | test_config_manager.py | 20 | 配置读写、验证、持久化 |
| 收藏/历史 | test_favorites_history.py | 28 | 收藏管理、观看历史 |
| 数据提供者 | test_providers.py | 41 | Provider 注册、切换、接口 |
| JSON 序列化 | test_json_serializer.py | 16 | 配置、短剧、剧集序列化 |
| 日志管理 | test_log_manager.py | 61 | 日志记录、轮转、格式化 |
| 异步工作线程 | test_async_worker.py | 48 | 异步任务执行、取消、错误处理 |
| 下载服务 | test_download_service.py | 61 | 下载任务管理、进度跟踪 |
| 下载服务V2 | test_download_service_v2.py | 54 | 新版下载服务 |
| 图片加载 | test_image_loader.py | 70 | 图片缓存、异步加载 |
| 网络监控 | test_network_monitor.py | 37 | 网络状态检测、连接监控 |
| 视频服务 | test_video_service.py | 28 | 视频URL获取、播放控制 |
| 分类服务 | test_category_service.py | 28 | 分类列表、分类内容获取 |
| 服务层 | test_services.py | 48 | 搜索、分类、视频服务逻辑 |
| 集成测试 | test_integration.py | 15 | 模块间协作、数据流 |
| 端到端测试 | test_end_to_end.py | 12 | 完整用户流程 |

## 新增代码测试指南

### 1. 新增数据模型

在 `test_models.py` 中添加测试：

```python
class TestNewModel:
    def test_create(self):
        model = NewModel(...)
        assert model.field == expected
    
    def test_equality(self):
        m1 = NewModel(...)
        m2 = NewModel(...)
        assert m1 == m2
```

### 2. 新增服务

在 `test_services.py` 中添加测试：

```python
class TestNewServiceLogic:
    def test_business_logic(self):
        # 测试业务逻辑
        pass
```

### 3. 新增 API 适配器

在 `test_providers.py` 中添加测试：

```python
class TestNewAdapter:
    @pytest.mark.asyncio
    async def test_search(self):
        adapter = NewAdapter()
        result = await adapter.search("test")
        assert result.code == 200
```

### 4. 新增工具函数

在 `test_utils.py` 中添加测试：

```python
def test_new_util_function():
    result = new_function(input)
    assert result == expected
```

## 错误诊断

测试失败时，自动测试运行器会分析错误并提供修复建议：

```
🔍 错误分析与修复建议
------------------------------------------------------------

[1] ImportError
    📁 文件: test_xxx.py
    💬 错误: cannot import name 'xxx'
    💡 建议: 检查模块导入路径是否正确，确保依赖已安装
    🔧 修复: pip install <missing_module> 或检查相对导入路径
    📊 置信度: 80%
```

## 最佳实践

1. **每次提交前运行快速验证**: `python test/auto_test_runner.py -q`
2. **新增功能时同步添加测试**: 确保测试覆盖新代码
3. **使用 fixtures**: 复用测试数据和 mock 对象
4. **标记测试类型**: 使用 `@pytest.mark.unit/integration/e2e`
5. **定期运行完整测试**: `python test/auto_test_runner.py --full`

## 测试文件合并

项目使用 `smart_merge.py` 脚本来合并重复的测试文件，避免测试代码冗余：

```bash
# 运行合并脚本
python smart_merge.py
```

合并脚本会：
- 自动识别同一模块的多个测试文件（如 `test_xxx.py`、`test_xxx_full.py`、`test_xxx_coverage.py`）
- 智能合并导入语句，去除重复
- 自动重命名重复的测试类，避免覆盖
- 保留所有独特的测试用例

