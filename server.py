#!/usr/bin/env python3
"""短剧 Termux 服务端

基于 Flask 的轻量级服务器，提供 API 代理和静态文件服务。
"""
import os
import signal
import socket
import sys
from flask import Flask, send_from_directory, jsonify, request
import requests

app = Flask(__name__, static_folder='static', static_url_path='/static')

# 配置
UPSTREAM_API = "https://api.cenguigui.cn/api/duanju/api.php"
REQUEST_TIMEOUT = 30
HOST = "0.0.0.0"
PORT = 8080


def get_local_ip():
    """获取本机局域网 IP 地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def add_cors_headers(response):
    """添加 CORS 头部"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


@app.after_request
def after_request(response):
    """为所有响应添加 CORS 头部"""
    return add_cors_headers(response)


# 静态文件路由
@app.route('/')
def index():
    """返回首页"""
    return send_from_directory('static', 'index.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    """提供静态文件"""
    return send_from_directory('static', filename)


# API 代理路由
def proxy_request(params):
    """代理请求到上游 API"""
    try:
        resp = requests.get(UPSTREAM_API, params=params, timeout=REQUEST_TIMEOUT)
        return resp.json(), resp.status_code
    except requests.Timeout:
        return {"code": 504, "msg": "请求超时", "error": "Gateway Timeout"}, 504
    except requests.RequestException as e:
        return {"code": 500, "msg": "请求失败", "error": str(e)}, 500
    except Exception as e:
        return {"code": 500, "msg": "服务器错误", "error": str(e)}, 500


@app.route('/api/search')
def api_search():
    """搜索短剧"""
    name = request.args.get('name', '')
    page = request.args.get('page', '1')
    data, status = proxy_request({'name': name, 'page': page})
    return jsonify(data), status


@app.route('/api/categories')
def api_categories():
    """获取分类短剧"""
    classname = request.args.get('classname', '推荐榜')
    offset = request.args.get('offset', '1')
    data, status = proxy_request({'classname': classname, 'offset': offset})
    return jsonify(data), status


@app.route('/api/drama/<book_id>')
def api_drama_detail(book_id):
    """获取剧集列表"""
    data, status = proxy_request({'book_id': book_id})
    return jsonify(data), status


@app.route('/api/video/<video_id>')
def api_video_url(video_id):
    """获取视频播放地址"""
    level = request.args.get('level', '1080p')
    data, status = proxy_request({'video_id': video_id, 'level': level, 'type': 'json'})
    return jsonify(data), status


@app.route('/api/recommend')
def api_recommend():
    """获取推荐短剧"""
    data, status = proxy_request({'type': 'recommend'})
    return jsonify(data), status


@app.route('/api/detail/<series_id>')
def api_series_detail(series_id):
    """获取视频详情"""
    data, status = proxy_request({'series_id': series_id})
    return jsonify(data), status


@app.route('/api/test')
def api_test():
    """测试 API 连接"""
    try:
        # 测试搜索接口
        data, status = proxy_request({'name': '总裁', 'page': '1'})
        return jsonify({
            'status': 'ok',
            'upstream_code': data.get('code'),
            'upstream_msg': data.get('msg'),
            'data_count': len(data.get('data', []))
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


def signal_handler(sig, frame):
    """处理终止信号"""
    print("\n正在关闭服务器...")
    sys.exit(0)


def main():
    """启动服务器"""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    local_ip = get_local_ip()
    print("=" * 50)
    print("  短剧 Termux 服务端")
    print("=" * 50)
    print(f"  本地访问: http://127.0.0.1:{PORT}")
    print(f"  局域网访问: http://{local_ip}:{PORT}")
    print("=" * 50)
    print("  按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    try:
        app.run(host=HOST, port=PORT, debug=False, threaded=True)
    except OSError as e:
        if "Address already in use" in str(e) or "10048" in str(e):
            print(f"\n错误: 端口 {PORT} 已被占用")
            print("请先关闭占用该端口的程序，或修改 PORT 变量")
            sys.exit(1)
        raise


if __name__ == '__main__':
    main()
