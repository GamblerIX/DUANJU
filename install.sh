#!/data/data/com.termux/files/usr/bin/bash
# 短剧 Termux 一键安装脚本
# 仓库: https://github.com/GamblerIX/DUANJU
# Gitee: https://gitee.com/GamblerIX/DUANJU

set -e

echo "=================================================="
echo "  短剧 Termux 一键安装脚本"
echo "=================================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 安装目录
INSTALL_DIR="$HOME/duanju"
REPO_URL="https://gitee.com/GamblerIX/DUANJU.git"
BRANCH="Termux"

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# 检查并安装依赖
install_dependencies() {
    echo ""
    echo "正在检查和安装依赖..."
    
    # 更新包列表
    pkg update -y || {
        print_error "更新包列表失败"
        exit 1
    }
    
    # 安装 Python
    if ! command -v python &> /dev/null; then
        echo "正在安装 Python..."
        pkg install -y python || {
            print_error "安装 Python 失败"
            exit 1
        }
    fi
    print_status "Python 已安装"
    
    # 安装 Git
    if ! command -v git &> /dev/null; then
        echo "正在安装 Git..."
        pkg install -y git || {
            print_error "安装 Git 失败"
            exit 1
        }
    fi
    print_status "Git 已安装"
    
    # 安装 pip 包
    echo "正在安装 Python 依赖..."
    pip install flask requests || {
        print_error "安装 Python 依赖失败"
        exit 1
    }
    print_status "Python 依赖已安装"
}


# 克隆或更新仓库
setup_project() {
    echo ""
    echo "正在设置项目..."
    
    if [ -d "$INSTALL_DIR" ]; then
        print_warning "检测到已有安装，正在更新..."
        cd "$INSTALL_DIR"
        git pull origin "$BRANCH" || {
            print_warning "更新失败，尝试重新克隆..."
            cd "$HOME"
            rm -rf "$INSTALL_DIR"
            git clone -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR" || {
                print_error "克隆仓库失败"
                exit 1
            }
        }
    else
        git clone -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR" || {
            print_error "克隆仓库失败"
            exit 1
        }
    fi
    print_status "项目已设置"
}

# 配置快捷指令
setup_shortcut() {
    echo ""
    echo "正在配置快捷指令..."
    
    # 确定 shell 配置文件
    if [ -f "$HOME/.zshrc" ]; then
        SHELL_RC="$HOME/.zshrc"
    else
        SHELL_RC="$HOME/.bashrc"
    fi
    
    # 检查是否已存在 dj 别名
    if grep -q "alias dj=" "$SHELL_RC" 2>/dev/null; then
        # 更新现有别名
        sed -i '/alias dj=/d' "$SHELL_RC"
    fi
    
    # 添加别名
    echo "alias dj='cd $INSTALL_DIR && python server.py'" >> "$SHELL_RC"
    print_status "快捷指令 'dj' 已配置"
}

# 显示完成信息
show_completion() {
    echo ""
    echo "=================================================="
    echo -e "${GREEN}  安装完成！${NC}"
    echo "=================================================="
    echo ""
    echo "  使用方法:"
    echo "  1. 重新打开 Termux 或执行: source ~/.bashrc"
    echo "  2. 输入 'dj' 启动服务端"
    echo "  3. 在浏览器访问显示的地址"
    echo ""
    echo "  或者直接运行:"
    echo "  cd $INSTALL_DIR && python server.py"
    echo ""
    echo "=================================================="
}

# 主函数
main() {
    install_dependencies
    setup_project
    setup_shortcut
    show_completion
}

main
