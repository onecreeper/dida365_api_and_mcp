

```python
import requests
from typing import List, Dict, Optional
from datetime import datetime
import json

class Task:
    def __init__(self, 
                 title: str,
                 project_id: str,
                 content: str = "",
                 priority: int = 5,
                 is_all_day: bool = True,
                 start_date: Optional[str] = None,
                 tags: List[str] = None):
        self.title = title
        self.content = content
        self.project_id = project_id
        self.priority = priority
        self.is_all_day = is_all_day
        self.start_date = start_date
        self.tags = tags or []
        self.id = None
        
    def to_dict(self) -> Dict:
        """将任务转换为API所需的字典格式"""
        return {
            "items": [],
            "reminders": [],
            "exDate": [],
            "dueDate": None,
            "priority": self.priority,
            "isAllDay": self.is_all_day,
            "repeatFlag": None,
            "progress": 0,
            "assignee": None,
            "sortOrder": -3299608625152,
            "startDate": self.start_date,
            "isFloating": False,
            "status": 0,
            "projectId": self.project_id,
            "kind": None,
            "title": self.title,
            "tags": self.tags,
            "timeZone": "Asia/Hong_Kong",
            "content": self.content,
            "id": self.id
        }

class DidaAPI:
    BASE_URL = "https://api.dida365.com/api/v2"
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            'hl': 'zh_CN',
            'priority': 'u=1, i',
            'x-device': json.dumps({
                "platform": "web",
                "os": "Windows 10",
                "device": "Chrome 137.0.0.0",
                "name": "",
                "version": 6261,
                "channel": "website"
            }),
            'x-tz': 'Asia/Hong_Kong',
            'Cookie': token,
            'content-type': 'application/json;charset=UTF-8'
        }

    def _make_request(self, data: Dict) -> Dict:
        """发送批量操作请求"""
        url = f"{self.BASE_URL}/batch/task"
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def add_tasks(self, tasks: List[Task]) -> Dict:
        """添加多个任务"""
        data = {
            "add": [task.to_dict() for task in tasks],
            "update": [],
            "delete": [],
            "addAttachments": [],
            "updateAttachments": [],
            "deleteAttachments": []
        }
        return self._make_request(data)

    def update_task(self, task: Task) -> Dict:
        """更新任务"""
        data = {
            "add": [],
            "update": [task.to_dict()],
            "delete": [],
            "addAttachments": [],
            "updateAttachments": [],
            "deleteAttachments": []
        }
        return self._make_request(data)

    def delete_tasks(self, task_ids: List[Dict[str, str]]) -> Dict:
        """删除多个任务"""
        data = {
            "add": [],
            "update": [],
            "delete": task_ids,
            "addAttachments": [],
            "updateAttachments": [],
            "deleteAttachments": []
        }
        return self._make_request(data)

# 使用示例
def main():
    # 初始化API（需要替换为实际的token）
    token = "your_token_here"
    dida = DidaAPI(token)
    
    # 创建任务示例
    task = Task(
        title="测试任务",
        project_id="6778eeb7c71c710000000114",
        content="任务内容",
        tags=["桌面台历显示"],
        start_date="2025-05-21T16:00:00.000+0000"
    )
    
    try:
        # 添加任务
        result = dida.add_tasks([task])
        print("添加任务成功:", result)
        
        # 更新任务
        task.content = "更新后的内容"
        result = dida.update_task(task)
        print("更新任务成功:", result)
        
        # 删除任务
        delete_info = [{
            "taskId": task.id,
            "projectId": task.project_id
        }]
        result = dida.delete_tasks(delete_info)
        print("删除任务成功:", result)
        
    except requests.exceptions.RequestException as e:
        print(f"API请求失败: {e}")

if __name__ == "__main__":
    main()
```

这个实现包含了以下主要组件：

1. `Task` 类：
   - 表示一个任务对象
   - 包含任务的所有属性
   - 提供将任务转换为API所需格式的方法

2. `DidaAPI` 类：
   - 处理与滴答清单API的所有交互
   - 提供添加、更新和删除任务的方法
   - 处理HTTP请求和响应

主要特点：

- 使用类型提示增加代码可读性和可维护性
- 错误处理机制
- 模块化设计，便于扩展
- 清晰的接口定义

使用方法：

1. 首先创建 `DidaAPI` 实例：
```python
dida = DidaAPI("your_token_here")
```

2. 创建任务：
```python
task = Task(
    title="新任务",
    project_id="your_project_id",
    content="任务描述",
    tags=["标签1", "标签2"]
)
```

3. 执行操作：
```python
# 添加任务
dida.add_tasks([task])

# 更新任务
dida.update_task(task)

# 删除任务
dida.delete_tasks([{"taskId": "task_id", "projectId": "project_id"}])
```

注意事项：
1. 使用前需要替换实际的token
2. 所有时间相关的字段都使用UTC时间
3. 建议在生产环境中添加更多的错误处理和日志记录
4. 可以根据需要扩展更多的功能，如查询任务、处理附件等