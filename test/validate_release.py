#!/usr/bin/env python
"""发布验证脚本

在发布前运行此脚本，确保所有测试通过且代码质量达标。
通过此验证后，用户使用时应该不会遇到问题。
"""
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Tuple, Dict
from dataclasses import dataclass

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class ValidationResult:
    """验证结果"""
    name: str
    passed: bool
    message: str
    duration: float = 0.0


class ReleaseValidator:
    """发布验证器
    
    执行一系列验证检查，确保代码可以安全发布。
    """
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.results: List[ValidationResult] = []
    
    def run_all_validations(self) -> bool:
        """运行所有验证"""
        print("=" * 70)
        print("🔍 DuanjuApp 发布验证")
        print("=" * 70)
        print()
        
        validations = [
            ("导入检查", self._validate_imports),
            ("单元测试", self._validate_unit_tests),
            ("集成测试", self._validate_integration_tests),
            ("端到端测试", self._validate_e2e_tests),
            ("数据模型", self._validate_models),
            ("API 解析", self._validate_api_parsing),
            ("缓存系统", self._validate_cache),
            ("配置系统", self._validate_config),
            ("持久化", self._validate_persistence),
            ("错误处理", self._validate_error_handling),
        ]
        
        all_passed = True
        
        for name, validator in validations:
            print(f"⏳ 验证: {name}...", end=" ", flush=True)
            start = time.time()
            
            try:
                passed, message = validator()
                duration = time.time() - start
                
                result = ValidationResult(
                    name=name,
                    passed=passed,
                    message=message,
                    duration=duration
                )
                self.results.append(result)
                
                if passed:
                    print(f"✅ 通过 ({duration:.2f}s)")
                else:
                    print(f"❌ 失败")
                    print(f"   {message}")
                    all_passed = False
                    
            except Exception as e:
                duration = time.time() - start
                result = ValidationResult(
                    name=name,
                    passed=False,
                    message=str(e),
                    duration=duration
                )
                self.results.append(result)
                print(f"❌ 错误: {e}")
                all_passed = False
        
        self._print_summary()
        return all_passed
    
    def _validate_imports(self) -> Tuple[bool, str]:
        """验证所有模块可以正确导入"""
        modules_to_check = [
            "src.core.models",
            "src.utils.string_utils",
            "src.utils.log_manager",
            "src.utils.json_serializer",
            "src.data.api_client",
            "src.data.response_parser",
            "src.data.cache_manager",
            "src.data.config_manager",
            "src.data.favorites_manager",
            "src.data.history_manager",
            "src.data.providers.provider_base",
            "src.data.providers.provider_registry",
        ]
        
        failed = []
        for module in modules_to_check:
            try:
                __import__(module)
            except ImportError as e:
                failed.append(f"{module}: {e}")
        
        if failed:
            return False, f"导入失败: {', '.join(failed)}"
        return True, f"成功导入 {len(modules_to_check)} 个模块"
    
    def _validate_unit_tests(self) -> Tuple[bool, str]:
        """运行单元测试"""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "test/", "-m", "unit", "-q", "--tb=no"],
            capture_output=True,
            text=True,
            cwd=str(self.project_root),
            timeout=120
        )
        
        if result.returncode == 0:
            # 提取通过数量
            output = result.stdout
            if "passed" in output:
                return True, output.strip().split("\n")[-1]
            return True, "所有单元测试通过"
        else:
            return False, result.stdout + result.stderr
    
    def _validate_integration_tests(self) -> Tuple[bool, str]:
        """运行集成测试"""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "test/test_integration.py", "-q", "--tb=no"],
            capture_output=True,
            text=True,
            cwd=str(self.project_root),
            timeout=60
        )
        
        if result.returncode == 0:
            return True, "集成测试通过"
        return False, result.stdout + result.stderr
    
    def _validate_e2e_tests(self) -> Tuple[bool, str]:
        """运行端到端测试"""
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "test/test_end_to_end.py", "-q", "--tb=no"],
            capture_output=True,
            text=True,
            cwd=str(self.project_root),
            timeout=60
        )
        
        if result.returncode == 0:
            return True, "端到端测试通过"
        return False, result.stdout + result.stderr
    
    def _validate_models(self) -> Tuple[bool, str]:
        """验证数据模型"""
        from src.core.models import (
            DramaInfo, EpisodeInfo, VideoInfo, SearchResult,
            EpisodeList, AppConfig, ThemeMode
        )
        
        # 测试创建模型
        drama = DramaInfo(book_id="1", title="Test", cover="url")
        assert drama.book_id == "1"
        assert drama.name == drama.title  # 向后兼容
        
        episode = EpisodeInfo(video_id="v1", title="Ep1")
        assert episode.video_id == "v1"
        
        video = VideoInfo(code=200, url="http://test.com/video.m3u8")
        assert video.video_url == video.url  # 向后兼容
        
        config = AppConfig()
        assert config.theme_mode == ThemeMode.AUTO
        
        return True, "数据模型验证通过"
    
    def _validate_api_parsing(self) -> Tuple[bool, str]:
        """验证 API 解析"""
        import json
        from src.data.response_parser import ResponseParser
        
        # 测试搜索结果解析
        search_json = json.dumps({
            "code": 200,
            "msg": "success",
            "data": [{"book_id": "1", "title": "Test", "cover": "url", "episode_cnt": 10}]
        })
        result = ResponseParser.parse_search_result(search_json)
        assert result.code == 200
        assert len(result.data) == 1
        
        # 测试剧集解析
        episode_json = json.dumps({
            "code": 200,
            "book_name": "Test",
            "data": [{"video_id": "v1", "title": "第1集"}]
        })
        result = ResponseParser.parse_episode_list(episode_json)
        assert result.code == 200
        
        # 测试视频解析
        video_json = json.dumps({
            "code": 200,
            "data": {"url": "http://test.com/video.m3u8", "info": {}}
        })
        result = ResponseParser.parse_video_info(video_json)
        assert result.url.startswith("http")
        
        return True, "API 解析验证通过"
    
    def _validate_cache(self) -> Tuple[bool, str]:
        """验证缓存系统"""
        from src.data.cache_manager import CacheManager
        
        cache = CacheManager(max_entries=10, enable_persistence=False)
        
        # 测试基本操作
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # 测试过期
        cache.set("key2", "value2", ttl=1)
        import time
        time.sleep(0.01)
        assert cache.get("key2") is None
        
        # 测试清空
        cache.clear()
        assert cache.size == 0
        
        return True, "缓存系统验证通过"
    
    def _validate_config(self) -> Tuple[bool, str]:
        """验证配置系统"""
        import tempfile
        from src.data.config_manager import ConfigManager
        from src.core.models import ThemeMode
        
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"
            
            # 测试创建和保存
            manager = ConfigManager(str(config_path))
            manager.theme_mode = ThemeMode.DARK
            manager.api_timeout = 5000
            
            # 测试重新加载
            manager2 = ConfigManager(str(config_path))
            assert manager2.theme_mode == ThemeMode.DARK
            assert manager2.api_timeout == 5000
        
        return True, "配置系统验证通过"
    
    def _validate_persistence(self) -> Tuple[bool, str]:
        """验证持久化"""
        import tempfile
        from src.data.favorites_manager import FavoritesManager
        from src.data.history_manager import HistoryManager
        from src.core.models import DramaInfo
        
        drama = DramaInfo(book_id="1", title="Test", cover="url")
        
        with tempfile.TemporaryDirectory() as tmp:
            # 测试收藏持久化
            fav_path = Path(tmp) / "favorites.json"
            fav1 = FavoritesManager(str(fav_path))
            fav1.add(drama)
            
            fav2 = FavoritesManager(str(fav_path))
            assert fav2.is_favorite("1")
            
            # 测试历史持久化
            hist_path = Path(tmp) / "history.json"
            hist1 = HistoryManager(str(hist_path))
            hist1.add(drama, 1, 5000)
            
            hist2 = HistoryManager(str(hist_path))
            item = hist2.get("1")
            assert item is not None
            assert item.position_ms == 5000
        
        return True, "持久化验证通过"
    
    def _validate_error_handling(self) -> Tuple[bool, str]:
        """验证错误处理"""
        import json
        from src.data.response_parser import ResponseParser, ApiResponseError
        
        # 测试错误响应处理
        error_json = json.dumps({"code": 500, "msg": "服务器错误"})
        
        try:
            ResponseParser.parse_search_result(error_json)
            return False, "应该抛出异常"
        except ApiResponseError as e:
            assert e.code == 500
        
        # 测试无效 JSON 处理
        error = ResponseParser.parse_error("invalid json")
        assert error.code == 0
        
        return True, "错误处理验证通过"
    
    def _print_summary(self):
        """打印验证摘要"""
        print()
        print("=" * 70)
        print("📊 验证摘要")
        print("=" * 70)
        
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        total_time = sum(r.duration for r in self.results)
        
        print(f"总计: {len(self.results)} 项验证")
        print(f"通过: {passed} ✅")
        print(f"失败: {failed} ❌")
        print(f"耗时: {total_time:.2f}s")
        print()
        
        if failed > 0:
            print("失败的验证:")
            for r in self.results:
                if not r.passed:
                    print(f"  ❌ {r.name}: {r.message}")
            print()
        
        if failed == 0:
            print("✅ 所有验证通过！代码可以安全发布。")
        else:
            print("❌ 存在验证失败，请修复后再发布。")
        
        print("=" * 70)


def main():
    """主函数"""
    validator = ReleaseValidator()
    success = validator.run_all_validations()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

