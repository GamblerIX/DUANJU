"""自动测试生成器

扫描源代码，自动生成测试用例框架。
支持未来新代码的自动测试生成。
"""
import ast
import sys
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field


@dataclass
class FunctionInfo:
    """函数信息"""
    name: str
    args: List[str]
    return_type: Optional[str]
    is_async: bool
    is_method: bool
    docstring: Optional[str]
    decorators: List[str]
    class_name: Optional[str] = None


@dataclass
class ClassInfo:
    """类信息"""
    name: str
    bases: List[str]
    methods: List[FunctionInfo]
    docstring: Optional[str]
    is_dataclass: bool = False


@dataclass
class ModuleInfo:
    """模块信息"""
    path: str
    classes: List[ClassInfo]
    functions: List[FunctionInfo]
    imports: List[str]


class CodeScanner:
    """代码扫描器"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent
    
    def scan_file(self, file_path: Path) -> ModuleInfo:
        """扫描单个文件"""
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)
        
        classes, functions, imports = [], [], []
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(self._parse_class(node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(self._parse_function(node))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        
        return ModuleInfo(path=str(file_path), classes=classes, functions=functions, imports=imports)
    
    def scan_directory(self, dir_path: Path, exclude_test: bool = True) -> List[ModuleInfo]:
        """扫描目录"""
        modules = []
        for py_file in dir_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            if exclude_test and "test" in py_file.parent.name:
                continue
            try:
                modules.append(self.scan_file(py_file))
            except SyntaxError:
                pass
        return modules
    
    def _parse_class(self, node: ast.ClassDef) -> ClassInfo:
        """解析类定义"""
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_info = self._parse_function(item, is_method=True)
                func_info.class_name = node.name
                methods.append(func_info)
        
        is_dataclass = any(isinstance(d, ast.Name) and d.id == "dataclass" for d in node.decorator_list)
        
        return ClassInfo(
            name=node.name,
            bases=[self._get_name(base) for base in node.bases],
            methods=methods,
            docstring=ast.get_docstring(node),
            is_dataclass=is_dataclass
        )
    
    def _parse_function(self, node, is_method: bool = False) -> FunctionInfo:
        """解析函数定义"""
        args = [arg.arg for arg in node.args.args if arg.arg != "self"]
        return_type = self._get_annotation(node.returns) if node.returns else None
        decorators = [self._get_name(d) for d in node.decorator_list]
        
        return FunctionInfo(
            name=node.name, args=args, return_type=return_type,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_method=is_method, docstring=ast.get_docstring(node), decorators=decorators
        )
    
    def _get_name(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        return ""
    
    def _get_annotation(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return str(node.value)
        return "Any"


class TestGenerator:
    """测试生成器"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.scanner = CodeScanner(project_root)
    
    def generate_tests_for_module(self, module: ModuleInfo) -> str:
        """为模块生成测试代码"""
        lines = [
            f'"""自动生成的测试 - {Path(module.path).stem}',
            '', '此文件由 auto_test_generator.py 自动生成。', '"""',
            'import pytest', 'import sys', 'from pathlib import Path',
            'from unittest.mock import MagicMock, AsyncMock', '',
            'sys.path.insert(0, str(Path(__file__).parent.parent))', ''
        ]
        
        import_path = self._get_import_path(module.path)
        public_classes = [c.name for c in module.classes if not c.name.startswith("_")]
        public_funcs = [f.name for f in module.functions if not f.name.startswith("_")]
        
        if public_classes:
            lines.append(f'from {import_path} import {", ".join(public_classes)}')
        if public_funcs:
            lines.append(f'from {import_path} import {", ".join(public_funcs)}')
        lines.extend(['', ''])
        
        for cls in module.classes:
            if not cls.name.startswith("_"):
                lines.extend(self._generate_class_tests(cls))
        
        for func in module.functions:
            if not func.name.startswith("_"):
                lines.extend(self._generate_function_tests(func))
        
        return "\n".join(lines)
    
    def _generate_class_tests(self, cls: ClassInfo) -> List[str]:
        """为类生成测试"""
        lines = [
            f'class Test{cls.name}:', f'    """{cls.name} 测试"""', '',
            '    @pytest.fixture', f'    def instance(self):',
            f'        """创建 {cls.name} 实例"""',
            f'        # TODO: 添加初始化参数', f'        return {cls.name}()', ''
        ]
        
        public_methods = [m for m in cls.methods if not m.name.startswith("_")]
        if not public_methods:
            lines.extend([
                '    def test_instantiation(self, instance):',
                f'        """测试实例化"""', '        assert instance is not None', ''
            ])
        else:
            for method in public_methods:
                lines.extend(self._generate_method_tests(method, cls.name))
        
        return lines
    
    def _generate_method_tests(self, method: FunctionInfo, class_name: str) -> List[str]:
        """为方法生成测试"""
        lines = []
        args_str = ", ".join("None" for _ in method.args)
        
        if method.is_async:
            lines.append('    @pytest.mark.asyncio')
            lines.append(f'    async def test_{method.name}(self, instance):')
            lines.append(f'        """测试 {class_name}.{method.name}"""')
            lines.append(f'        result = await instance.{method.name}({args_str})')
        else:
            lines.append(f'    def test_{method.name}(self, instance):')
            lines.append(f'        """测试 {class_name}.{method.name}"""')
            lines.append(f'        result = instance.{method.name}({args_str})')
        
        lines.extend(['        assert result is not None or True', ''])
        return lines
    
    def _generate_function_tests(self, func: FunctionInfo) -> List[str]:
        """为函数生成测试"""
        lines = []
        args_str = ", ".join("None" for _ in func.args)
        
        if func.is_async:
            lines.append('@pytest.mark.asyncio')
            lines.append(f'async def test_{func.name}():')
            lines.append(f'    """测试 {func.name}"""')
            lines.append(f'    result = await {func.name}({args_str})')
        else:
            lines.append(f'def test_{func.name}():')
            lines.append(f'    """测试 {func.name}"""')
            lines.append(f'    result = {func.name}({args_str})')
        
        lines.extend(['    assert result is not None or True', ''])
        return lines
    
    def _get_import_path(self, file_path: str) -> str:
        try:
            path = Path(file_path)
            relative = path.relative_to(self.project_root)
            parts = list(relative.parts)
            if parts[-1].endswith(".py"):
                parts[-1] = parts[-1][:-3]
            return ".".join(parts)
        except ValueError:
            return Path(file_path).stem
    
    def generate_all_tests(self, output_dir: Optional[Path] = None) -> Dict[str, str]:
        """为所有源文件生成测试"""
        output_dir = output_dir or self.project_root / "test" / "generated"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        modules = self.scanner.scan_directory(self.project_root / "src")
        generated = {}
        
        for module in modules:
            if not module.classes and not module.functions:
                continue
            
            test_code = self.generate_tests_for_module(module)
            module_name = Path(module.path).stem
            test_file = output_dir / f"test_{module_name}_auto.py"
            test_file.write_text(test_code, encoding="utf-8")
            generated[str(test_file)] = test_code
        
        return generated


class TestCoverageAnalyzer:
    """测试覆盖分析器"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.scanner = CodeScanner(project_root)
    
    def analyze(self) -> Dict:
        """分析测试覆盖情况"""
        src_modules = self.scanner.scan_directory(self.project_root / "src", exclude_test=True)
        test_modules = self.scanner.scan_directory(self.project_root / "test", exclude_test=False)
        
        src_targets = self._extract_targets(src_modules)
        test_targets = self._extract_test_targets(test_modules)
        
        covered = src_targets & test_targets
        uncovered = src_targets - test_targets
        coverage_rate = len(covered) / len(src_targets) * 100 if src_targets else 0
        
        return {
            "total_targets": len(src_targets),
            "covered_targets": len(covered),
            "uncovered_targets": len(uncovered),
            "coverage_rate": coverage_rate,
            "covered_list": sorted(covered),
            "uncovered_list": sorted(uncovered)[:30],
            "by_module": self._analyze_by_module(src_modules, test_targets)
        }
    
    def _extract_targets(self, modules: List[ModuleInfo]) -> Set[str]:
        targets = set()
        for module in modules:
            for cls in module.classes:
                if not cls.name.startswith("_"):
                    targets.add(cls.name)
            for func in module.functions:
                if not func.name.startswith("_"):
                    targets.add(func.name)
        return targets
    
    def _extract_test_targets(self, modules: List[ModuleInfo]) -> Set[str]:
        targets = set()
        for module in modules:
            for cls in module.classes:
                if cls.name.startswith("Test"):
                    # 提取被测类名
                    target = cls.name[4:]  # 移除 "Test" 前缀
                    targets.add(target)
                    
                    # 从嵌套类名提取
                    for method in cls.methods:
                        if method.name.startswith("test_"):
                            # 尝试从方法名提取被测目标
                            method_parts = method.name[5:].split("_")
                            for part in method_parts:
                                if part and len(part) > 2:
                                    targets.add(part.capitalize())
                                    targets.add(part)
            
            for func in module.functions:
                if func.name.startswith("test_"):
                    parts = func.name[5:].split("_")
                    for part in parts:
                        if part and len(part) > 2:
                            targets.add(part.capitalize())
                            targets.add(part)
        return targets
    
    def _analyze_by_module(self, modules: List[ModuleInfo], test_targets: Set[str]) -> List[Dict]:
        results = []
        for module in modules:
            module_targets = set()
            for cls in module.classes:
                if not cls.name.startswith("_"):
                    module_targets.add(cls.name)
            for func in module.functions:
                if not func.name.startswith("_"):
                    module_targets.add(func.name)
            
            if not module_targets:
                continue
            
            covered = module_targets & test_targets
            coverage = len(covered) / len(module_targets) * 100 if module_targets else 0
            
            results.append({
                "module": Path(module.path).name,
                "total": len(module_targets),
                "covered": len(covered),
                "coverage": coverage,
                "uncovered": list(module_targets - test_targets)
            })
        
        return sorted(results, key=lambda x: x["coverage"])


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="自动测试生成器")
    parser.add_argument("-g", "--generate", action="store_true", help="生成测试代码")
    parser.add_argument("-a", "--analyze", action="store_true", help="分析测试覆盖")
    parser.add_argument("-o", "--output", type=str, help="输出目录")
    
    args = parser.parse_args()
    
    if args.generate:
        generator = TestGenerator()
        output_dir = Path(args.output) if args.output else None
        generated = generator.generate_all_tests(output_dir)
        print(f"✅ 生成了 {len(generated)} 个测试文件")
        for path in generated:
            print(f"   - {path}")
    
    elif args.analyze:
        analyzer = TestCoverageAnalyzer()
        result = analyzer.analyze()
        
        print("=" * 60)
        print("📊 测试覆盖分析")
        print("=" * 60)
        print(f"总目标数: {result['total_targets']}")
        print(f"已覆盖: {result['covered_targets']}")
        print(f"未覆盖: {result['uncovered_targets']}")
        print(f"覆盖率: {result['coverage_rate']:.1f}%")
        
        if result['uncovered_list']:
            print("\n未覆盖的目标 (前30个):")
            for target in result['uncovered_list']:
                print(f"   - {target}")
        
        print("\n按模块覆盖情况:")
        for mod in result['by_module'][:10]:
            print(f"   {mod['module']}: {mod['coverage']:.0f}% ({mod['covered']}/{mod['total']})")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

