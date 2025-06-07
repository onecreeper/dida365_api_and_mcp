# server.py
from mcp.server.fastmcp import FastMCP
import api
import os
import json
import logging
from typing import Optional, List, Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_or_create_json(file_path='key.json'):
    """读取或创建JSON配置文件"""
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False)
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def save_json(data, file_path='key.json'):
    """保存JSON配置文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 创建MCP服务器
mcp = FastMCP("Dida365")
