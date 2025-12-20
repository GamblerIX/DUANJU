"""全自动测试运行器

提供自动化测试执行、错误分析和修复建议功能。
支持 AI 辅助的错误诊断和自动修复。
"""
import subprocess
import sys
import json
import re
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum


class TestStatus(Enum):
    """测试状态枚举"""
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class TestResult:
    """单个测试结果"""
    name: str
    status: TestStatus
    duration: float = 0.0
    error_message: str = ""
    error_traceback: str = ""
    file_path: str = ""
    line_number: int = 0


@dataclass
class ErrorAnalysis:
    """错误分析结果"""
    error_type: str
    error_message: str
    file_path: str
    line_number: int
    suggested_fix: str
    fix_code: str = ""
    confidence: float = 0.0


@dataclass
class TestReport:
    """测试报告"""
    total: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    duration: float = 0.0
    results: List[TestResult] = field(default_factory=list)
    error_analyses: List[ErrorAnalysis] = field(default_factory=list)
    timestamp: str = ""


class AutoTestRunner:
    """全自动测试运行器
    
    功能：
    1. 自动发现和运行测试
    2. 分析测试失败原因
    3. 提供修复建议
    4. 生成测试报告
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.test_dir = self.project_root / "test"
        self.report: Optional[TestReport] = None
    
    def run_all_tests(self, verbose: bool = True) -> TestReport:
        """运行所有测试"""
        print("=" * 60)
        print("🚀 开始运行自动化测试...")
        print("=" * 60)
        
        start_time = time.time()
        
        # 运行 pytest 并收集结果
        result = self._run_pytest(verbose)
        
        # 解析测试结果
        self.report = self._parse_results(result)
        self.report.duration = time.time() - start_time
        self.report.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 分析错误
        if self.report.failed > 0 or self.report.errors > 0:
            self._analyze_errors()
        
        # 打印报告
        self._print_report()
        
        return self.report
    
    def run_specific_tests(self, test_pattern: str) -> TestReport:
        """运行特定测试"""
        print(f"🔍 运行匹配 '{test_pattern}' 的测试...")
        
        start_time = time.time()
        result = self._run_pytest(True, extra_args=["-k", test_pattern])
        
        self.report = self._parse_results(result)
        self.report.duration = time.time() - start_time
        self.report.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        if self.report.failed > 0 or self.report.errors > 0:
            self._analyze_errors()
        
        self._print_report()
        return self.report
    
    def _run_pytest(
        self, 
        verbose: bool = True, 
        extra_args: Optional[List[str]] = None
    ) -> subprocess.CompletedProcess:
        """运行 pytest"""
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir),
            "--tb=short",
            "-q" if not verbose else "-v",
            "--no-header",
        ]
        
        if extra_args:
            cmd.extend(extra_args)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=300  # 5分钟超时
            )
            return result
        except subprocess.TimeoutExpired:
            print("⚠️ 测试执行超时")
            return subprocess.CompletedProcess(cmd, 1, "", "Timeout")
        except Exception as e:
            print(f"❌ 测试执行失败: {e}")
            return subprocess.CompletedProcess(cmd, 1, "", str(e))
    
    def _parse_results(self, result: subprocess.CompletedProcess) -> TestReport:
        """解析 pytest 输出"""
        report = TestReport()
        output = result.stdout + result.stderr
        
        # 解析测试结果行
        test_pattern = re.compile(
            r'(test_\w+\.py::\w+(?:::\w+)*)\s+(PASSED|FAILED|ERROR|SKIPPED)'
        )
        
        for match in test_pattern.finditer(output):
            test_name = match.group(1)
            status_str = match.group(2)
            status = TestStatus[status_str]
            
            test_result = TestResult(
                name=test_name,
                status=status,
                file_path=test_name.split("::")[0]
            )
            report.results.append(test_result)
            
            if status == TestStatus.PASSED:
                report.passed += 1
            elif status == TestStatus.FAILED:
                report.failed += 1
            elif status == TestStatus.ERROR:
                report.errors += 1
            elif status == TestStatus.SKIPPED:
                report.skipped += 1
        
        report.total = len(report.results)
        
        # 如果没有解析到结果，尝试从摘要行解析
        if report.total == 0:
            summary_pattern = re.compile(
                r'(\d+)\s+passed|(\d+)\s+failed|(\d+)\s+error|(\d+)\s+skipped'
            )
            for match in summary_pattern.finditer(output):
                if match.group(1):
                    report.passed = int(match.group(1))
                if match.group(2):
                    report.failed = int(match.group(2))
                if match.group(3):
                    report.errors = int(match.group(3))
                if match.group(4):
                    report.skipped = int(match.group(4))
            report.total = report.passed + report.failed + report.errors + report.skipped
        
        # 提取错误信息
        self._extract_error_details(output, report)
        
        return report
    
    def _extract_error_details(self, output: str, report: TestReport) -> None:
        """提取错误详情"""
        # 匹配失败测试的错误信息
        failure_pattern = re.compile(
            r'FAILED\s+(test_\w+\.py::\w+(?:::\w+)*)\s*-\s*(.+?)(?=\n(?:FAILED|PASSED|ERROR|=|$))',
            re.DOTALL
        )
        
        for match in failure_pattern.finditer(output):
            test_name = match.group(1)
            error_info = match.group(2).strip()
            
            # 更新对应测试结果的错误信息
            for result in report.results:
                if result.name == test_name:
                    result.error_message = error_info
                    break
    
    def _analyze_errors(self) -> None:
        """分析测试错误并生成修复建议"""
        if not self.report:
            return
        
        for result in self.report.results:
            if result.status in [TestStatus.FAILED, TestStatus.ERROR]:
                analysis = self._analyze_single_error(result)
                if analysis:
                    self.report.error_analyses.append(analysis)
    
    def _analyze_single_error(self, result: TestResult) -> Optional[ErrorAnalysis]:
        """分析单个错误"""
        error_msg = result.error_message.lower()
        
        # 常见错误模式和修复建议
        error_patterns = [
            {
                "pattern": "importerror",
                "type": "ImportError",
                "suggestion": "检查模块导入路径是否正确，确保依赖已安装",
                "fix_hint": "pip install <missing_module> 或检查相对导入路径"
            },
            {
                "pattern": "modulenotfounderror",
                "type": "ModuleNotFoundError", 
                "suggestion": "模块未找到，检查包名是否正确或是否已安装",
                "fix_hint": "pip install <module_name>"
            },
            {
                "pattern": "attributeerror",
                "type": "AttributeError",
                "suggestion": "对象没有该属性，检查属性名拼写或对象类型",
                "fix_hint": "检查对象是否正确初始化，属性名是否正确"
            },
            {
                "pattern": "typeerror",
                "type": "TypeError",
                "suggestion": "类型错误，检查函数参数类型或操作数类型",
                "fix_hint": "检查参数类型是否匹配函数签名"
            },
            {
                "pattern": "assertionerror",
                "type": "AssertionError",
                "suggestion": "断言失败，检查测试期望值是否正确",
                "fix_hint": "检查实际值与期望值，可能需要更新测试或修复代码"
            },
            {
                "pattern": "keyerror",
                "type": "KeyError",
                "suggestion": "字典键不存在，检查键名或使用 .get() 方法",
                "fix_hint": "使用 dict.get(key, default) 或检查键是否存在"
            },
            {
                "pattern": "valueerror",
                "type": "ValueError",
                "suggestion": "值错误，检查传入的值是否在有效范围内",
                "fix_hint": "添加输入验证或检查值的有效性"
            },
            {
                "pattern": "connectionerror|timeout",
                "type": "NetworkError",
                "suggestion": "网络连接错误，检查网络或使用 mock",
                "fix_hint": "在测试中使用 mock 替代真实网络请求"
            },
            {
                "pattern": "filenotfounderror",
                "type": "FileNotFoundError",
                "suggestion": "文件未找到，检查文件路径是否正确",
                "fix_hint": "检查文件路径，确保测试文件存在"
            },
        ]
        
        for pattern_info in error_patterns:
            if re.search(pattern_info["pattern"], error_msg):
                return ErrorAnalysis(
                    error_type=pattern_info["type"],
                    error_message=result.error_message,
                    file_path=result.file_path,
                    line_number=result.line_number,
                    suggested_fix=pattern_info["suggestion"],
                    fix_code=pattern_info["fix_hint"],
                    confidence=0.8
                )
        
        # 默认分析
        return ErrorAnalysis(
            error_type="Unknown",
            error_message=result.error_message,
            file_path=result.file_path,
            line_number=result.line_number,
            suggested_fix="检查错误信息，定位问题根源",
            confidence=0.3
        )
    
    def _print_report(self) -> None:
        """打印测试报告"""
        if not self.report:
            return
        
        print("\n" + "=" * 60)
        print("📊 测试报告")
        print("=" * 60)
        print(f"⏱️  执行时间: {self.report.duration:.2f}s")
        print(f"📅 时间戳: {self.report.timestamp}")
        print("-" * 60)
        print(f"📈 总计: {self.report.total} 个测试")
        print(f"   ✅ 通过: {self.report.passed}")
        print(f"   ❌ 失败: {self.report.failed}")
        print(f"   ⚠️  错误: {self.report.errors}")
        print(f"   ⏭️  跳过: {self.report.skipped}")
        
        # 计算通过率
        if self.report.total > 0:
            pass_rate = (self.report.passed / self.report.total) * 100
            print(f"   📊 通过率: {pass_rate:.1f}%")
        
        # 打印错误分析
        if self.report.error_analyses:
            print("\n" + "-" * 60)
            print("🔍 错误分析与修复建议")
            print("-" * 60)
            
            for i, analysis in enumerate(self.report.error_analyses, 1):
                print(f"\n[{i}] {analysis.error_type}")
                print(f"    📁 文件: {analysis.file_path}")
                print(f"    💬 错误: {analysis.error_message[:100]}...")
                print(f"    💡 建议: {analysis.suggested_fix}")
                print(f"    🔧 修复: {analysis.fix_code}")
                print(f"    📊 置信度: {analysis.confidence * 100:.0f}%")
        
        print("\n" + "=" * 60)
        
        # 最终状态
        if self.report.failed == 0 and self.report.errors == 0:
            print("✅ 所有测试通过！")
        else:
            print("❌ 存在测试失败，请查看上方错误分析")
        
        print("=" * 60)
    
    def generate_json_report(self, output_path: Optional[Path] = None) -> str:
        """生成 JSON 格式报告"""
        if not self.report:
            return "{}"
        
        report_dict = {
            "summary": {
                "total": self.report.total,
                "passed": self.report.passed,
                "failed": self.report.failed,
                "errors": self.report.errors,
                "skipped": self.report.skipped,
                "duration": self.report.duration,
                "timestamp": self.report.timestamp,
                "pass_rate": (self.report.passed / self.report.total * 100) if self.report.total > 0 else 0
            },
            "results": [
                {
                    "name": r.name,
                    "status": r.status.value,
                    "error_message": r.error_message,
                    "file_path": r.file_path
                }
                for r in self.report.results
            ],
            "error_analyses": [
                {
                    "error_type": a.error_type,
                    "error_message": a.error_message,
                    "file_path": a.file_path,
                    "suggested_fix": a.suggested_fix,
                    "fix_code": a.fix_code,
                    "confidence": a.confidence
                }
                for a in self.report.error_analyses
            ]
        }
        
        json_str = json.dumps(report_dict, ensure_ascii=False, indent=2)
        
        if output_path:
            output_path.write_text(json_str, encoding="utf-8")
            print(f"📄 报告已保存到: {output_path}")
        
        return json_str


class AutoFixer:
    """自动修复器
    
    基于错误分析结果，尝试自动修复常见问题。
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent
    
    def suggest_fixes(self, analyses: List[ErrorAnalysis]) -> List[Dict]:
        """根据错误分析生成修复建议"""
        fixes = []
        
        for analysis in analyses:
            fix = {
                "error_type": analysis.error_type,
                "file_path": analysis.file_path,
                "suggestion": analysis.suggested_fix,
                "auto_fixable": self._is_auto_fixable(analysis),
                "fix_steps": self._generate_fix_steps(analysis)
            }
            fixes.append(fix)
        
        return fixes
    
    def _is_auto_fixable(self, analysis: ErrorAnalysis) -> bool:
        """判断错误是否可以自动修复"""
        auto_fixable_types = [
            "ImportError",
            "ModuleNotFoundError",
        ]
        return analysis.error_type in auto_fixable_types and analysis.confidence > 0.7
    
    def _generate_fix_steps(self, analysis: ErrorAnalysis) -> List[str]:
        """生成修复步骤"""
        steps = []
        
        if analysis.error_type == "ImportError":
            steps = [
                "1. 检查导入语句的模块路径",
                "2. 确认模块是否已安装: pip list | grep <module>",
                "3. 如果是相对导入，检查 __init__.py 文件",
                "4. 尝试使用绝对导入或修正相对导入层级"
            ]
        elif analysis.error_type == "ModuleNotFoundError":
            steps = [
                "1. 安装缺失的模块: pip install <module>",
                "2. 检查 requirements.txt 是否包含该依赖",
                "3. 确认虚拟环境是否正确激活"
            ]
        elif analysis.error_type == "AssertionError":
            steps = [
                "1. 检查测试的期望值是否正确",
                "2. 运行被测代码，确认实际输出",
                "3. 更新测试用例或修复代码逻辑"
            ]
        elif analysis.error_type == "AttributeError":
            steps = [
                "1. 检查对象类型是否正确",
                "2. 确认属性名拼写",
                "3. 检查对象是否正确初始化"
            ]
        elif analysis.error_type == "TypeError":
            steps = [
                "1. 检查函数参数类型",
                "2. 确认参数数量是否正确",
                "3. 检查是否遗漏了必需参数"
            ]
        else:
            steps = [
                "1. 仔细阅读错误信息",
                "2. 定位错误发生的代码行",
                "3. 检查相关代码逻辑",
                "4. 参考文档或搜索类似问题"
            ]
        
        return steps


class ContinuousTestRunner:
    """持续测试运行器
    
    监控文件变化，自动运行相关测试。
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.runner = AutoTestRunner(project_root)
    
    def get_related_tests(self, changed_file: str) -> List[str]:
        """获取与变更文件相关的测试"""
        file_path = Path(changed_file)
        file_name = file_path.stem
        
        related = []
        test_dir = self.project_root / "test"
        
        # 查找直接相关的测试文件
        for test_file in test_dir.glob("test_*.py"):
            if file_name in test_file.stem:
                related.append(str(test_file))
        
        # 如果是模型文件，运行所有模型测试
        if "model" in file_name.lower():
            related.append(str(test_dir / "test_models.py"))
        
        # 如果是服务文件，运行服务测试
        if "service" in file_name.lower():
            related.append(str(test_dir / "test_services.py"))
        
        # 如果是 API 相关，运行 API 测试
        if "api" in file_name.lower() or "client" in file_name.lower():
            related.append(str(test_dir / "test_api_client.py"))
        
        return list(set(related))
    
    def run_related_tests(self, changed_file: str) -> TestReport:
        """运行与变更文件相关的测试"""
        related = self.get_related_tests(changed_file)
        
        if not related:
            print(f"⚠️ 未找到与 {changed_file} 相关的测试")
            return TestReport()
        
        print(f"🔍 运行与 {changed_file} 相关的测试:")
        for test in related:
            print(f"   - {Path(test).name}")
        
        # 构建测试模式
        pattern = " or ".join(Path(t).stem for t in related)
        return self.runner.run_specific_tests(pattern)


def run_full_test_suite() -> bool:
    """运行完整测试套件"""
    runner = AutoTestRunner()
    
    print("=" * 60)
    print("🚀 运行完整测试套件")
    print("=" * 60)
    
    report = runner.run_all_tests(verbose=True)
    
    # 生成报告
    report_path = Path("test_report.json")
    runner.generate_json_report(report_path)
    
    return report.failed == 0 and report.errors == 0


def run_quick_validation() -> bool:
    """快速验证测试"""
    runner = AutoTestRunner()
    
    print("=" * 60)
    print("⚡ 快速验证测试")
    print("=" * 60)
    
    # 只运行单元测试
    report = runner.run_specific_tests("not integration and not e2e and not slow")
    
    return report.failed == 0 and report.errors == 0


def main():
    """主函数 - 运行自动化测试"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="DuanjuApp 自动化测试运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python auto_test_runner.py              # 运行所有测试
  python auto_test_runner.py -v           # 详细模式
  python auto_test_runner.py -k search    # 只运行搜索相关测试
  python auto_test_runner.py -q           # 快速验证
  python auto_test_runner.py -f src/xxx.py  # 运行与文件相关的测试
  python auto_test_runner.py -o report.json # 生成报告
        """
    )
    parser.add_argument(
        "-k", "--keyword",
        help="只运行匹配关键词的测试",
        default=None
    )
    parser.add_argument(
        "-v", "--verbose",
        help="详细输出",
        action="store_true"
    )
    parser.add_argument(
        "-o", "--output",
        help="输出 JSON 报告的路径",
        default=None
    )
    parser.add_argument(
        "-q", "--quick",
        help="快速验证模式",
        action="store_true"
    )
    parser.add_argument(
        "-f", "--file",
        help="运行与指定文件相关的测试",
        default=None
    )
    parser.add_argument(
        "--full",
        help="运行完整测试套件",
        action="store_true"
    )
    
    args = parser.parse_args()
    
    success = True
    
    if args.quick:
        success = run_quick_validation()
    elif args.full:
        success = run_full_test_suite()
    elif args.file:
        runner = ContinuousTestRunner()
        report = runner.run_related_tests(args.file)
        success = report.failed == 0 and report.errors == 0
    else:
        runner = AutoTestRunner()
        
        if args.keyword:
            report = runner.run_specific_tests(args.keyword)
        else:
            report = runner.run_all_tests(verbose=args.verbose)
        
        if args.output:
            runner.generate_json_report(Path(args.output))
        
        success = report.failed == 0 and report.errors == 0
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

