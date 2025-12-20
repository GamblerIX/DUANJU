#!/usr/bin/env python
"""测试入口脚本

提供简单的命令行接口来运行测试。
"""
import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_all_tests(verbose: bool = False):
    """运行所有测试"""
    from test.auto_test_runner import AutoTestRunner
    
    runner = AutoTestRunner()
    report = runner.run_all_tests(verbose=verbose)
    
    return report.failed == 0 and report.errors == 0


def run_quick_tests():
    """运行快速测试（只运行单元测试）"""
    from test.auto_test_runner import AutoTestRunner
    
    runner = AutoTestRunner()
    report = runner.run_specific_tests("not integration")
    
    return report.failed == 0 and report.errors == 0


def run_ai_analysis():
    """运行 AI 分析"""
    from test.ai_test_assistant import AITestAssistant
    
    assistant = AITestAssistant()
    
    print("=" * 60)
    print("🤖 AI 测试分析")
    print("=" * 60)
    
    # 项目分析
    summary = assistant.analyze_project()
    print(f"\n📊 项目概况:")
    print(f"   - 源文件: {summary['total_files']} 个")
    print(f"   - 类: {summary['total_classes']} 个")
    print(f"   - 函数: {summary['total_functions']} 个")
    print(f"   - 代码行: {summary['total_lines']} 行")
    
    # 覆盖率分析
    coverage = assistant.get_test_coverage_report()
    print(f"\n📈 测试覆盖:")
    print(f"   - 覆盖率: {coverage['coverage_rate']:.1f}%")
    print(f"   - {coverage['recommendation']}")
    
    return True


def generate_report(output_path: str):
    """生成测试报告"""
    from test.auto_test_runner import AutoTestRunner
    
    runner = AutoTestRunner()
    report = runner.run_all_tests(verbose=False)
    runner.generate_json_report(Path(output_path))
    
    print(f"📄 报告已生成: {output_path}")
    return report.failed == 0 and report.errors == 0


def main():
    parser = argparse.ArgumentParser(
        description="DuanjuApp 测试运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_tests.py              # 运行所有测试
  python run_tests.py -v           # 详细模式运行
  python run_tests.py -q           # 快速测试
  python run_tests.py -a           # AI 分析
  python run_tests.py -r report.json  # 生成报告
        """
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细输出模式"
    )
    parser.add_argument(
        "-q", "--quick",
        action="store_true",
        help="快速测试模式（跳过集成测试）"
    )
    parser.add_argument(
        "-a", "--analyze",
        action="store_true",
        help="运行 AI 分析"
    )
    parser.add_argument(
        "-r", "--report",
        type=str,
        metavar="PATH",
        help="生成 JSON 报告到指定路径"
    )
    
    args = parser.parse_args()
    
    success = True
    
    if args.analyze:
        success = run_ai_analysis()
    elif args.quick:
        success = run_quick_tests()
    elif args.report:
        success = generate_report(args.report)
    else:
        success = run_all_tests(verbose=args.verbose)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

