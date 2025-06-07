# 滴答清单 MCP 服务器

这是一个基于 Model Context Protocol (MCP) 的滴答清单 API 服务器，提供完整的任务管理功能和 AI 辅助清单管理。

## 功能特性

### 🔐 用户认证
- `login_with_token`: 使用 token 登录滴答清单
- `get_user_info`: 获取当前用户信息

### 📋 任务管理
- `get_tasks`: 获取任务列表（包含项目和标签详细信息）
- `add_task`: 添加新任务
- `modify_task`: 修改任务
- `remove_task`: 删除任务
- `complete_task`: 完成任务
- `find_task_by_title`: 根据标题查找任务

### 📁 项目和标签管理
- `get_projects`: 获取项目列表
- `get_tags`: 获取标签列表
- `get_all_info`: 获取所有信息（任务、项目、标签）
- `refresh_data`: 刷新用户数据

### 🤖 AI 辅助清单管理
- `ai_suggest_task_optimization`: AI 分析任务并提供优化建议
- `ai_auto_categorize_tasks`: AI 自动分析任务并建议分类和标签
- `ai_batch_update_tasks`: AI 批量更新任务
- `ai_smart_schedule_tasks`: AI 智能安排任务时间
- `ai_task_summary_report`: AI 生成任务总结报告

### 🛠️ 任务构建工具
- `build_task`: 使用 TaskBuilder 构建任务（不会自动添加到服务器）

### 📊 资源提供
- `user://profile`: 用户资料资源
- `tasks://all`: 所有任务资源
- `projects://all`: 所有项目资源
- `tags://all`: 所有标签资源
- `greeting://{name}`: 个性化问候语

## 安装和使用

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

或者使用 uv：

```bash
uv sync
```

### 2. 获取滴答清单 Token

1. 在浏览器中登录 [滴答清单](https://dida365.com/)
2. 打开开发者工具 (F12)
3. 在网络标签页中找到任意一个 API 请求
4. 复制请求头中的 `Cookie` 值

### 3. 启动服务器

```bash
python server.py
```

### 4. 登录

使用 `login_with_token` 工具，传入你的 Cookie 值：

```json
{
  "token": "你的Cookie值"
}
```

## 使用示例

### 添加任务

```json
{
  "title": "完成项目报告",
  "content": "需要包含数据分析和结论",
  "project_id": "项目ID",
  "due_date": "2025-01-15",
  "priority": 4,
  "tags": ["工作", "重要"]
}
```

### 获取任务（增强版）

调用 `get_tasks` 会返回包含项目名称和标签详细信息的任务：

```json
{
  "success": true,
  "tasks": [
    {
      "id": "任务ID",
      "title": "任务标题",
      "projectId": "项目ID",
      "projectName": "项目名称",
      "projectInfo": {
        "id": "项目ID",
        "name": "项目名称"
      },
      "tags": ["工作", "重要"],
      "tagDetails": [
        {
          "name": "工作",
          "label": "工作",
          "color": "#ff0000"
        }
      ]
    }
  ]
}
```

### AI 功能示例

#### 获取任务优化建议

```json
{
  "success": true,
  "suggestions": [
    {
      "task_id": "任务ID",
      "task_title": "任务标题",
      "suggestions": [
        "高优先级任务建议设置截止时间",
        "建议将任务分配到具体项目中"
      ]
    }
  ]
}
```

#### 智能任务分类

```json
{
  "success": true,
  "suggestions": [
    {
      "task_id": "任务ID",
      "task_title": "会议准备",
      "suggested_project": {
        "id": "项目ID",
        "name": "工作项目",
        "reason": "包含工作相关关键词: 会议"
      },
      "suggested_tags": ["工作", "重要"]
    }
  ]
}
```

## 时间格式支持

TaskBuilder 支持多种时间格式：

- 相对时间：`1DD`（1天后）、`2WW`（2周后）、`1MM`（1月后）
- 绝对时间：`2025-01-15`、`2025-01-15 14:30`
- 特殊值：`today`（今天）

## 配置文件

服务器会自动创建 `key.json` 文件来保存用户 token，无需手动配置。

## 错误处理

所有工具都返回统一的响应格式：

```json
{
  "success": true/false,
  "message": "操作结果信息",
  "data": "具体数据（成功时）"
}
```

## 注意事项

1. Token 会保存在本地 `key.json` 文件中
2. 服务器启动时会自动尝试使用保存的 token 登录
3. 如果 token 过期，需要重新获取并使用 `login_with_token` 登录
4. AI 功能基于简单的关键词匹配，可以根据需要扩展

## 开发

### 项目结构

```
├── api.py          # 滴答清单 API 客户端
├── server.py       # MCP 服务器实现
├── pyproject.toml  # 项目配置
└── README.md       # 使用说明
```

### 扩展功能

可以在 `server.py` 中添加更多工具和资源，参考现有的实现模式。

## 许可证

MIT License
