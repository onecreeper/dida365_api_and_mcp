
# 滴答清单任务批量操作 API 文档

## 接口信息

- **接口URL**: `https://api.dida365.com/api/v2/batch/task`
- **请求方法**: POST
- **Content-Type**: application/json;charset=UTF-8

## 请求头

| 请求头 | 说明 | 示例值 |
|--------|------|---------|
| hl | 语言设置 | zh_CN |
| priority | 优先级信息 | u=1, i |
| traceid | 追踪ID | 动态生成的ID |
| x-csrftoken | CSRF令牌 | - |
| x-device | 设备信息 | JSON对象包含平台、操作系统等信息 |
| x-tz | 时区 | Asia/Hong_Kong |

## 请求体结构

```json
{
    "add": Array<Task>,          // 添加的任务列表
    "update": Array<Task>,       // 更新的任务列表
    "delete": Array<DeleteTask>, // 删除的任务列表
    "addAttachments": Array,     // 添加的附件列表
    "updateAttachments": Array,  // 更新的附件列表
    "deleteAttachments": Array   // 删除的附件列表
}
```

### Task 对象结构

```json
{
    "items": [],
    "reminders": [],
    "exDate": [],
    "dueDate": null,
    "priority": Number,          // 优先级
    "isAllDay": Boolean,        // 是否全天
    "repeatFlag": null,
    "progress": Number,         // 进度
    "assignee": null,
    "sortOrder": Number,        // 排序顺序
    "startDate": String,        // 开始时间
    "isFloating": Boolean,
    "status": Number,           // 状态
    "projectId": String,        // 项目ID
    "kind": null,
    "etag": String,            // 仅更新时需要
    "createdTime": String,      // 创建时间
    "modifiedTime": String,     // 修改时间
    "title": String,           // 任务标题
    "tags": Array<String>,     // 标签列表
    "timeZone": String,        // 时区
    "content": String,         // 任务内容
    "id": String              // 任务ID
}
```

### DeleteTask 对象结构

```json
{
    "taskId": String,          // 要删除的任务ID
    "projectId": String        // 任务所属项目ID
}
```

## 使用示例

### 1. 更新任务

```json
{
    "update": [{
        "title": "sdfsdfsdf123",
        "content": "1321231",
        "id": "681473bbf92b2938d3ab5d45",
        // ... 其他任务属性
    }]
}
```

### 2. 添加任务

```json
{
    "add": [{
        "title": "sdfsdfsdf",
        "content": "",
        "id": "681473bbf92b2938d3ab5d45",
        // ... 其他任务属性
    }]
}
```

### 3. 删除任务

```json
{
    "delete": [{
        "taskId": "68147317f92b2938d3ab5cf6",
        "projectId": "inbox1015881707"
    }]
}
```

## 注意事项

1. 所有时间相关字段都使用 ISO 8601 格式
2. 批量操作支持同时进行添加、更新和删除操作
3. 请确保在更新操作时包含 etag 字段
4. 时区信息需要在请求头和任务对象中都正确设置