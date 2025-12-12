# 短剧 Termux 版

在 Android 手机上通过 Termux 运行短剧服务端，使用浏览器观看。

## 功能

- 🚀 一键安装
- ⚡ 快捷指令 `dj` 启动
- 🌐 浏览器访问，无需 APP
- 📺 搜索、分类、播放

## 安装

### 一键安装

```bash
# Gitee
pkg install -y curl && curl -sL https://gitee.com/GamblerIX/DUANJU/raw/termux/install.sh | bash

# GitHub
pkg install -y curl && curl -sL https://raw.githubusercontent.com/GamblerIX/DUANJU/termux/install.sh | bash
```

### 手动安装

```bash
pkg update && pkg install -y python git
git clone -b termux https://gitee.com/GamblerIX/DUANJU.git ~/duanju
pip install flask requests
echo "alias dj='cd ~/duanju && python server.py'" >> ~/.bashrc
source ~/.bashrc
```

## 使用

```bash
# 启动服务
dj

# 或
cd ~/duanju && python server.py
```

启动后在浏览器打开显示的地址（如 `http://192.168.1.100:8080`）。

按 `Ctrl + C` 停止服务。

## 配置

编辑 `server.py` 修改：

```python
HOST = "0.0.0.0"      # 监听地址
PORT = 8080           # 端口号
REQUEST_TIMEOUT = 30  # API 超时(秒)
```

## 常见问题

- 端口被占用：修改 `PORT` 变量
- 无法访问：确保手机和浏览器在同一网络
- 视频无法播放：部分视频有地区限制，尝试切换清晰度

## 相关链接

- [GitHub](https://github.com/GamblerIX/DUANJU)
- [Gitee](https://gitee.com/GamblerIX/DUANJU)
- [Termux](https://termux.dev/)
