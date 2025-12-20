"""AI 测试助手

提供 AI 辅助的测试生成、错误诊断和自动修复功能。
"""
import ast
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field


@dataclass
class CodeAnalysis:
    """代码分析结果"""
    file_path: str
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    complexity: int = 0
    lines_of_code: int = 0
    test_coverage_hints: List[str] = field(default_factory=list)


@dataclass
class TestSuggestion:
    """测试建议"""
    target: str  # 被测目标（类名或函数名）
    test_type: str  # 测试类型
    description: str  # 测试描述
    test_code: str  # 建议的测试代码
    priority: int = 1  # 优先级 1-5


@dataclass
class FixSuggestion:
    """修复建议"""
    file_path: str
    line_number: int
    original_code: str
    fixed_code: str
    explanation: str
    confidence: float


class CodeAnalyzer:
    """代码分析器
    
    分析 Python 源代码，提取类、函数、依赖等信息。
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent
    
    def analyze_file(self, file_path: Path) -> CodeAnalysis:
        """分析单个文件"""
        analysis = CodeAnalysis(file_path=str(file_path))
        
        try:
            content = file_path.read_text(encoding="utf-8")
            analysis.lines_of_code = len(content.splitlines())
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    analysis.classes.append(node.name)
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    # 只记录顶层函数
                    if not any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree)):
                        analysis.functions.append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        analysis.imports.append(node.module)
            
            # 计算复杂度（简化版）
            analysis.complexity = self._calculate_complexity(tree)
            
            # 生成测试覆盖提示
            analysis.test_coverage_hints = self._generate_coverage_hints(analysis)
            
        except SyntaxError as e:
            analysis.test_coverage_hints.append(f"语法错误: {e}")
        except Exception as e:
            analysis.test_coverage_hints.append(f"分析错误: {e}")
        
        return analysis
    
    def analyze_directory(self, dir_path: Path) -> List[CodeAnalysis]:
        """分析目录下所有 Python 文件"""
        analyses = []
        
        for py_file in dir_path.rglob("*.py"):
            if "__pycache__" not in str(py_file):
                analysis = self.analyze_file(py_file)
                analyses.append(analysis)
        
        return analyses
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """计算代码复杂度（简化的圈复杂度）"""
        complexity = 1
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _generate_coverage_hints(self, analysis: CodeAnalysis) -> List[str]:
        """生成测试覆盖提示"""
        hints = []
        
        for cls in analysis.classes:
            hints.append(f"需要测试类 '{cls}' 的所有公开方法")
        
        for func in analysis.functions:
            if not func.startswith("_"):
                hints.append(f"需要测试函数 '{func}'")
        
        if analysis.complexity > 10:
            hints.append(f"代码复杂度较高 ({analysis.complexity})，建议增加边界测试")
        
        return hints


class TestGenerator:
    """测试生成器
    
    基于代码分析自动生成测试建议和测试代码框架。
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.analyzer = CodeAnalyzer(project_root)
    
    def generate_test_suggestions(self, file_path: Path) -> List[TestSuggestion]:
        """为文件生成测试建议"""
        suggestions = []
        analysis = self.analyzer.analyze_file(file_path)
        
        # 为每个类生成测试建议
        for cls in analysis.classes:
            suggestions.extend(self._generate_class_tests(cls, file_path))
        
        # 为每个函数生成测试建议
        for func in analysis.functions:
            if not func.startswith("_"):
                suggestions.extend(self._generate_function_tests(func, file_path))
        
        return suggestions
    
    def _generate_class_tests(self, class_name: str, file_path: Path) -> List[TestSuggestion]:
        """为类生成测试建议"""
        suggestions = []
        
        # 基本实例化测试
        suggestions.append(TestSuggestion(
            target=class_name,
            test_type="instantiation",
            description=f"测试 {class_name} 类的实例化",
            test_code=self._generate_class_test_code(class_name, file_path),
            priority=1
        ))
        
        # 属性测试
        suggestions.append(TestSuggestion(
            target=class_name,
            test_type="properties",
            description=f"测试 {class_name} 类的属性访问",
            test_code=f"""
def test_{class_name.lower()}_properties():
    \"\"\"测试 {class_name} 属性\"\"\"
    instance = {class_name}(...)  # 添加必要参数
    # 验证属性
    assert hasattr(instance, 'expected_property')
""",
            priority=2
        ))
        
        return suggestions
    
    def _generate_function_tests(self, func_name: str, file_path: Path) -> List[TestSuggestion]:
        """为函数生成测试建议"""
        suggestions = []
        
        # 正常情况测试
        suggestions.append(TestSuggestion(
            target=func_name,
            test_type="normal",
            description=f"测试 {func_name} 函数的正常情况",
            test_code=f"""
def test_{func_name}_normal():
    \"\"\"测试 {func_name} 正常情况\"\"\"
    result = {func_name}(...)  # 添加参数
    assert result is not None
""",
            priority=1
        ))
        
        # 边界情况测试
        suggestions.append(TestSuggestion(
            target=func_name,
            test_type="edge_case",
            description=f"测试 {func_name} 函数的边界情况",
            test_code=f"""
def test_{func_name}_edge_cases():
    \"\"\"测试 {func_name} 边界情况\"\"\"
    # 空输入
    # result = {func_name}(None)
    # 极端值
    # result = {func_name}(extreme_value)
    pass
""",
            priority=2
        ))
        
        # 异常情况测试
        suggestions.append(TestSuggestion(
            target=func_name,
            test_type="exception",
            description=f"测试 {func_name} 函数的异常处理",
            test_code=f"""
def test_{func_name}_exceptions():
    \"\"\"测试 {func_name} 异常处理\"\"\"
    import pytest
    with pytest.raises(ValueError):
        {func_name}(invalid_input)
""",
            priority=3
        ))
        
        return suggestions
    
    def _generate_class_test_code(self, class_name: str, file_path: Path) -> str:
        """生成类测试代码"""
        module_path = self._get_module_path(file_path)
        
        return f"""
import pytest
from {module_path} import {class_name}


class Test{class_name}:
    \"\"\"测试 {class_name} 类\"\"\"
    
    def test_instantiation(self):
        \"\"\"测试实例化\"\"\"
        instance = {class_name}(...)  # 添加必要参数
        assert instance is not None
    
    def test_default_values(self):
        \"\"\"测试默认值\"\"\"
        instance = {class_name}(...)
        # 验证默认值
        pass
"""
    
    def _get_module_path(self, file_path: Path) -> str:
        """获取模块导入路径"""
        try:
            relative = file_path.relative_to(self.project_root)
            parts = list(relative.parts)
            if parts[-1].endswith(".py"):
                parts[-1] = parts[-1][:-3]
            return ".".join(parts)
        except ValueError:
            return file_path.stem


class ErrorDiagnostic:
    """错误诊断器
    
    分析测试错误，提供详细的诊断信息和修复建议。
    """
    
    # 常见错误模式
    ERROR_PATTERNS = {
        r"ImportError: cannot import name '(\w+)'": {
            "type": "ImportError",
            "diagnosis": "无法导入指定的名称，可能是名称拼写错误或模块结构变化",
            "fix_template": "检查 {0} 是否存在于目标模块中"
        },
        r"ModuleNotFoundError: No module named '([\w.]+)'": {
            "type": "ModuleNotFoundError",
            "diagnosis": "模块未找到，可能未安装或路径错误",
            "fix_template": "运行 pip install {0} 或检查 PYTHONPATH"
        },
        r"AttributeError: '(\w+)' object has no attribute '(\w+)'": {
            "type": "AttributeError",
            "diagnosis": "对象没有指定的属性",
            "fix_template": "检查 {0} 类是否有 {1} 属性"
        },
        r"TypeError: (\w+)\(\) (missing \d+ required|takes \d+ positional)": {
            "type": "TypeError",
            "diagnosis": "函数参数数量不匹配",
            "fix_template": "检查 {0} 函数的参数签名"
        },
        r"AssertionError: assert (.+) == (.+)": {
            "type": "AssertionError",
            "diagnosis": "断言失败，实际值与期望值不匹配",
            "fix_template": "实际值 {0} 不等于期望值 {1}"
        },
        r"KeyError: '(\w+)'": {
            "type": "KeyError",
            "diagnosis": "字典中不存在指定的键",
            "fix_template": "键 '{0}' 不存在，检查数据结构"
        },
        r"ValueError: (.+)": {
            "type": "ValueError",
            "diagnosis": "值错误",
            "fix_template": "检查输入值: {0}"
        },
    }
    
    def diagnose(self, error_message: str, traceback: str = "") -> Dict:
        """诊断错误"""
        result = {
            "error_type": "Unknown",
            "diagnosis": "未知错误",
            "suggestions": [],
            "related_files": [],
            "confidence": 0.0
        }
        
        for pattern, info in self.ERROR_PATTERNS.items():
            match = re.search(pattern, error_message)
            if match:
                result["error_type"] = info["type"]
                result["diagnosis"] = info["diagnosis"]
                result["suggestions"].append(
                    info["fix_template"].format(*match.groups())
                )
                result["confidence"] = 0.8
                break
        
        # 从 traceback 提取相关文件
        if traceback:
            file_pattern = r'File "([^"]+)", line (\d+)'
            for match in re.finditer(file_pattern, traceback):
                result["related_files"].append({
                    "path": match.group(1),
                    "line": int(match.group(2))
                })
        
        # 添加通用建议
        result["suggestions"].extend(self._get_general_suggestions(result["error_type"]))
        
        return result
    
    def _get_general_suggestions(self, error_type: str) -> List[str]:
        """获取通用修复建议"""
        suggestions = {
            "ImportError": [
                "检查模块是否正确安装",
                "验证导入路径是否正确",
                "检查 __init__.py 文件"
            ],
            "ModuleNotFoundError": [
                "运行 pip install <module>",
                "检查虚拟环境是否激活",
                "验证 PYTHONPATH 设置"
            ],
            "AttributeError": [
                "检查对象类型",
                "验证属性名拼写",
                "确认对象已正确初始化"
            ],
            "TypeError": [
                "检查函数签名",
                "验证参数类型",
                "查看函数文档"
            ],
            "AssertionError": [
                "检查测试期望值",
                "验证被测代码逻辑",
                "考虑边界情况"
            ],
        }
        
        return suggestions.get(error_type, ["仔细阅读错误信息", "检查相关代码"])


class AITestAssistant:
    """AI 测试助手主类
    
    整合代码分析、测试生成和错误诊断功能。
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.analyzer = CodeAnalyzer(project_root)
        self.generator = TestGenerator(project_root)
        self.diagnostic = ErrorDiagnostic()
    
    def analyze_project(self) -> Dict:
        """分析整个项目"""
        src_dir = self.project_root / "src"
        analyses = self.analyzer.analyze_directory(src_dir)
        
        summary = {
            "total_files": len(analyses),
            "total_classes": sum(len(a.classes) for a in analyses),
            "total_functions": sum(len(a.functions) for a in analyses),
            "total_lines": sum(a.lines_of_code for a in analyses),
            "avg_complexity": sum(a.complexity for a in analyses) / len(analyses) if analyses else 0,
            "files": [
                {
                    "path": a.file_path,
                    "classes": a.classes,
                    "functions": a.functions,
                    "complexity": a.complexity,
                    "coverage_hints": a.test_coverage_hints
                }
                for a in analyses
            ]
        }
        
        return summary
    
    def suggest_tests_for_file(self, file_path: str) -> List[Dict]:
        """为指定文件生成测试建议"""
        path = Path(file_path)
        if not path.is_absolute():
            path = self.project_root / path
        
        suggestions = self.generator.generate_test_suggestions(path)
        
        return [
            {
                "target": s.target,
                "type": s.test_type,
                "description": s.description,
                "code": s.test_code,
                "priority": s.priority
            }
            for s in suggestions
        ]
    
    def diagnose_error(self, error_message: str, traceback: str = "") -> Dict:
        """诊断测试错误"""
        return self.diagnostic.diagnose(error_message, traceback)
    
    def get_test_coverage_report(self) -> Dict:
        """获取测试覆盖情况报告"""
        src_analyses = self.analyzer.analyze_directory(self.project_root / "src")
        test_analyses = self.analyzer.analyze_directory(self.project_root / "test")
        
        # 提取所有被测试的目标
        tested_targets: Set[str] = set()
        for analysis in test_analyses:
            for cls in analysis.classes:
                if cls.startswith("Test"):
                    tested_targets.add(cls[4:])  # 移除 "Test" 前缀
            for func in analysis.functions:
                if func.startswith("test_"):
                    # 提取被测函数名
                    parts = func[5:].split("_")
                    if parts:
                        tested_targets.add(parts[0])
        
        # 计算覆盖情况
        all_targets = set()
        for analysis in src_analyses:
            all_targets.update(analysis.classes)
            all_targets.update(f for f in analysis.functions if not f.startswith("_"))
        
        covered = all_targets & tested_targets
        uncovered = all_targets - tested_targets
        
        coverage_rate = len(covered) / len(all_targets) * 100 if all_targets else 0
        
        return {
            "coverage_rate": coverage_rate,
            "total_targets": len(all_targets),
            "covered_targets": len(covered),
            "uncovered_targets": list(uncovered)[:20],  # 只显示前20个
            "recommendation": self._get_coverage_recommendation(coverage_rate)
        }
    
    def _get_coverage_recommendation(self, coverage_rate: float) -> str:
        """根据覆盖率生成建议"""
        if coverage_rate >= 80:
            return "✅ 测试覆盖率良好，继续保持"
        elif coverage_rate >= 60:
            return "⚠️ 测试覆盖率一般，建议增加核心功能测试"
        elif coverage_rate >= 40:
            return "⚠️ 测试覆盖率较低，建议优先覆盖关键路径"
        else:
            return "❌ 测试覆盖率过低，需要大幅增加测试用例"


def main():
    """主函数"""
    assistant = AITestAssistant()
    
    print("=" * 60)
    print("🤖 AI 测试助手")
    print("=" * 60)
    
    # 分析项目
    print("\n📊 项目分析:")
    summary = assistant.analyze_project()
    print(f"   文件数: {summary['total_files']}")
    print(f"   类数量: {summary['total_classes']}")
    print(f"   函数数: {summary['total_functions']}")
    print(f"   代码行: {summary['total_lines']}")
    print(f"   平均复杂度: {summary['avg_complexity']:.1f}")
    
    # 测试覆盖报告
    print("\n📈 测试覆盖情况:")
    coverage = assistant.get_test_coverage_report()
    print(f"   覆盖率: {coverage['coverage_rate']:.1f}%")
    print(f"   已覆盖: {coverage['covered_targets']}/{coverage['total_targets']}")
    print(f"   建议: {coverage['recommendation']}")
    
    if coverage['uncovered_targets']:
        print(f"\n   未覆盖的目标 (前10个):")
        for target in coverage['uncovered_targets'][:10]:
            print(f"      - {target}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

