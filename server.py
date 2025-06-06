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

# 全局用户实例
user_instance = None

def get_user_instance():
    """获取用户实例，如果不存在则创建"""
    global user_instance
    if user_instance is None:
        config = read_or_create_json()
        token = config.get('token', '')
        user_instance = api.User(token)
        if token:
            # 先尝试获取用户信息以验证token
            try:
                user_info = user_instance.get_user_info()
                if user_info:
                    user_instance.get_info_about()  # 加载任务、项目、标签信息
                else:
                    # 获取用户信息失败，可能需要重新登录
                    logger.warning("获取用户信息失败，token可能已过期")
            except Exception as e:
                logger.error(f"验证token时出错: {e}")
    return user_instance

def enhance_tasks_with_names(user, tasks):
    """为任务添加项目名称和标签名称信息"""
    if not isinstance(tasks, list):
        tasks = [tasks] if tasks else []
    
    # 创建项目ID到名称的映射
    project_map = {}
    for project in user.projects:
        project_map[project.id] = project.name
    
    # 创建标签名称到标签对象的映射
    tag_map = {}
    for tag in user.tags:
        tag_map[tag.name] = tag
    
    enhanced_tasks = []
    for task in tasks:
        if isinstance(task, dict):
            enhanced_task = task.copy()
            
            # 添加项目名称
            project_id = task.get('projectId')
            if project_id and project_id in project_map:
                enhanced_task['projectName'] = project_map[project_id]
            
            # 添加标签详细信息
            task_tags = task.get('tags', [])
            if task_tags:
                enhanced_tags = []
                for tag_name in task_tags:
                    if tag_name in tag_map:
                        tag_obj = tag_map[tag_name]
                        enhanced_tags.append({
                            'name': tag_obj.name,
                            'label': tag_obj.label,
                            'color': tag_obj.color
                        })
                    else:
                        enhanced_tags.append({'name': tag_name})
                enhanced_task['tagDetails'] = enhanced_tags
            
            enhanced_tasks.append(enhanced_task)
        else:
            enhanced_tasks.append(task)
    
    return enhanced_tasks[0] if len(enhanced_tasks) == 1 and not isinstance(tasks, list) else enhanced_tasks

@mcp.tool()
def set_token(token: str) -> str:
    """设置滴答清单的认证token"""
    try:
        config = read_or_create_json()
        config['token'] = token
        save_json(config)
        
        # 更新用户实例
        global user_instance
        user_instance = api.User(token)
        user_info = user_instance.get_user_info()
        
        if user_info:
            user_instance.get_info_about()
            return f"Token设置成功，用户: {user_instance.name or user_instance.username}"
        else:
            return "Token设置失败，请检查token是否有效"
    except Exception as e:
        logger.error(f"设置token失败: {e}")
        return f"设置token失败: {str(e)}"

@mcp.tool()
def get_user_info() -> Dict[str, Any]:
    """获取当前用户信息"""
    try:
        user = get_user_instance()
        if not user.token:
            return {"error": "请先设置token"}
        
        user_info = user.get_user_info()
        if user_info:
            return {
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "username": user.username
            }
        else:
            return {"error": "获取用户信息失败，请检查token"}
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        return {"error": str(e)}

@mcp.tool()
def get_all_tasks() -> List[Dict[str, Any]]:
    """获取所有任务"""
    try:
        user = get_user_instance()
        if not user.token:
            return [{"error": "请先设置token"}]
        
        user.get_info_about()  # 刷新数据
        tasks = user.tool_get_task_info()
        return enhance_tasks_with_names(user, tasks)
    except Exception as e:
        logger.error(f"获取任务失败: {e}")
        return [{"error": str(e)}]

@mcp.tool()
def get_task_by_id(task_id: str) -> Optional[Dict[str, Any]]:
    """根据ID获取特定任务"""
    try:
        user = get_user_instance()
        if not user.token:
            return {"error": "请先设置token"}
        
        user.get_info_about()  # 刷新数据
        task_info = user.tool_get_task_info(task_id)
        if task_info:
            return enhance_tasks_with_names(user, task_info)
        else:
            return {"error": f"未找到ID为{task_id}的任务"}
    except Exception as e:
        logger.error(f"获取任务失败: {e}")
        return {"error": str(e)}

@mcp.tool()
def get_all_projects() -> List[Dict[str, Any]]:
    """获取所有项目"""
    try:
        user = get_user_instance()
        if not user.token:
            return [{"error": "请先设置token"}]
        
        user.get_info_about()  # 刷新数据
        return user.tool_get_project_info()
    except Exception as e:
        logger.error(f"获取项目失败: {e}")
        return [{"error": str(e)}]

@mcp.tool()
def get_project_by_id(project_id: str) -> Optional[Dict[str, Any]]:
    """根据ID获取特定项目"""
    try:
        user = get_user_instance()
        if not user.token:
            return {"error": "请先设置token"}
        
        user.get_info_about()  # 刷新数据
        project_info = user.tool_get_project_info(project_id)
        return project_info if project_info else {"error": f"未找到ID为{project_id}的项目"}
    except Exception as e:
        logger.error(f"获取项目失败: {e}")
        return {"error": str(e)}

@mcp.tool()
def get_all_tags() -> List[Dict[str, Any]]:
    """获取所有标签"""
    try:
        user = get_user_instance()
        if not user.token:
            return [{"error": "请先设置token"}]
        
        user.get_info_about()  # 刷新数据
        return user.tool_get_tag_info()
    except Exception as e:
        logger.error(f"获取标签失败: {e}")
        return [{"error": str(e)}]

@mcp.tool()
def create_simple_task(title: str, content: str = "", project_id: str = "") -> str:
    """创建简单任务"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        # 使用TaskBuilder创建任务
        builder = api.TaskBuilder(title)
        if content:
            builder.content(content)
        if project_id:
            builder.project(project_id)
        
        task = builder.build()
        result = user.add_task(task)
        
        if result:
            return f"任务'{title}'创建成功"
        else:
            return f"任务'{title}'创建失败"
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        return f"创建任务失败: {str(e)}"

@mcp.tool()
def create_advanced_task(
    title: str,
    content: str = "",
    project_id: str = "",
    due_date: str = "",
    priority: int = 0,
    tags: List[str] = None,
    start_date: str = "today"
) -> str:
    """创建高级任务（支持更多参数）"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        # 使用TaskBuilder创建任务
        builder = api.TaskBuilder(title)
        
        if content:
            builder.content(content)
        if project_id:
            builder.project(project_id)
        if start_date:
            builder.start(start_date)
        if due_date:
            builder.due(due_date)
        if priority > 0:
            builder.priority(priority)
        if tags:
            builder.tag(*tags)
        
        task = builder.build()
        result = user.add_task(task)
        
        if result:
            return f"高级任务'{title}'创建成功"
        else:
            return f"高级任务'{title}'创建失败"
    except Exception as e:
        logger.error(f"创建高级任务失败: {e}")
        return f"创建高级任务失败: {str(e)}"

@mcp.tool()
def delete_task_by_id(task_id: str) -> str:
    """根据ID删除任务"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        task = user.find_task_by_id(task_id)
        if not task:
            return f"未找到ID为{task_id}的任务"
        
        result = user.remove_task(task)
        if result:
            return f"任务'{task.title}'删除成功"
        else:
            return f"任务'{task.title}'删除失败"
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        return f"删除任务失败: {str(e)}"

@mcp.tool()
def delete_task_by_title(title: str) -> str:
    """根据标题删除任务"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        task = user.find_task_by_title(title)
        if not task:
            return f"未找到标题为'{title}'的任务"
        
        result = user.remove_task(task)
        if result:
            return f"任务'{title}'删除成功"
        else:
            return f"任务'{title}'删除失败"
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        return f"删除任务失败: {str(e)}"

@mcp.tool()
def update_task_status(task_id: str, status: int) -> str:
    """更新任务状态 (0=未完成，1=已完成，2=已归档)"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        task = user.find_task_by_id(task_id)
        if not task:
            return f"未找到ID为{task_id}的任务"
        
        task.status = status
        result = user.modify_task(task)
        
        status_text = {0: "未完成", 1: "已完成", 2: "已归档"}.get(status, "未知状态")
        
        if result:
            return f"任务'{task.title}'状态更新为'{status_text}'"
        else:
            return f"任务'{task.title}'状态更新失败"
    except Exception as e:
        logger.error(f"更新任务状态失败: {e}")
        return f"更新任务状态失败: {str(e)}"

@mcp.tool()
def update_task_title(task_id: str, new_title: str) -> str:
    """更新任务标题"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        task = user.find_task_by_id(task_id)
        if not task:
            return f"未找到ID为{task_id}的任务"
        
        old_title = task.title
        task.title = new_title
        result = user.modify_task(task)
        
        if result:
            return f"任务标题从'{old_title}'更新为'{new_title}'"
        else:
            return f"任务标题更新失败"
    except Exception as e:
        logger.error(f"更新任务标题失败: {e}")
        return f"更新任务标题失败: {str(e)}"

@mcp.tool()
def update_advanced_task(
    task_id: str,
    title: str = "",
    content: str = "",
    project_id: str = "",
    due_date: str = "",
    start_date: str = "",
    priority: int = -1,
    tags: List[str] = None,
    status: int = -1,
    progress: int = -1
) -> str:
    """高级任务修改功能（支持修改多个属性）"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        task = user.find_task_by_id(task_id)
        if not task:
            return f"未找到ID为{task_id}的任务"
        
        changes = []
        
        # 更新标题
        if title:
            old_title = task.title
            task.title = title
            changes.append(f"标题: '{old_title}' → '{title}'")
        
        # 更新内容
        if content:
            task.content = content
            changes.append(f"内容已更新")
        
        # 更新项目
        if project_id:
            task.projectId = project_id
            changes.append(f"项目ID: {project_id}")
        
        # 更新截止时间
        if due_date:
            from dateutil import parser
            try:
                if due_date.lower() == "clear":
                    task.dueDate = None
                    changes.append("截止时间已清除")
                else:
                    task.dueDate = parser.parse(due_date).isoformat()
                    changes.append(f"截止时间: {due_date}")
            except:
                return f"无效的截止时间格式: {due_date}"
        
        # 更新开始时间
        if start_date:
            from dateutil import parser
            try:
                if start_date.lower() == "clear":
                    task.startDate = None
                    changes.append("开始时间已清除")
                elif start_date.lower() == "today":
                    from datetime import datetime
                    task.startDate = datetime.now().isoformat()
                    changes.append("开始时间设为今天")
                else:
                    task.startDate = parser.parse(start_date).isoformat()
                    changes.append(f"开始时间: {start_date}")
            except:
                return f"无效的开始时间格式: {start_date}"
        
        # 更新优先级
        if priority >= 0:
            priority = min(max(0, priority), 5)
            task.priority = priority
            priority_text = {0: "无", 1: "低", 2: "中低", 3: "中", 4: "中高", 5: "高"}.get(priority, str(priority))
            changes.append(f"优先级: {priority_text}")
        
        # 更新标签
        if tags is not None:
            if len(tags) == 0:
                task.tags = []
                changes.append("标签已清空")
            else:
                task.tags = tags
                changes.append(f"标签: {', '.join(tags)}")
        
        # 更新状态
        if status >= 0:
            status = min(max(0, status), 2)
            task.status = status
            status_text = {0: "未完成", 1: "已完成", 2: "已归档"}.get(status, str(status))
            changes.append(f"状态: {status_text}")
        
        # 更新进度
        if progress >= 0:
            progress = min(max(0, progress), 100)
            task.progress = progress
            changes.append(f"进度: {progress}%")
        
        if not changes:
            return "没有提供任何要修改的内容"
        
        result = user.modify_task(task)
        
        if result:
            changes_text = "、".join(changes)
            return f"任务'{task.title}'修改成功，更新内容: {changes_text}"
        else:
            return f"任务'{task.title}'修改失败"
    except Exception as e:
        logger.error(f"高级修改任务失败: {e}")
        return f"高级修改任务失败: {str(e)}"

@mcp.tool()
def update_task_project(task_id: str, project_id: str) -> str:
    """修改任务所属项目"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        task = user.find_task_by_id(task_id)
        if not task:
            return f"未找到ID为{task_id}的任务"
        
        # 获取项目名称用于显示
        project_name = "未知项目"
        for project in user.projects:
            if project.id == project_id:
                project_name = project.name
                break
        
        task.projectId = project_id
        result = user.modify_task(task)
        
        if result:
            return f"任务'{task.title}'已移动到项目'{project_name}'"
        else:
            return f"任务'{task.title}'项目修改失败"
    except Exception as e:
        logger.error(f"修改任务项目失败: {e}")
        return f"修改任务项目失败: {str(e)}"

@mcp.tool()
def update_task_tags(task_id: str, tags: List[str]) -> str:
    """修改任务标签"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        task = user.find_task_by_id(task_id)
        if not task:
            return f"未找到ID为{task_id}的任务"
        
        task.tags = tags
        result = user.modify_task(task)
        
        if result:
            if tags:
                return f"任务'{task.title}'标签已更新为: {', '.join(tags)}"
            else:
                return f"任务'{task.title}'标签已清空"
        else:
            return f"任务'{task.title}'标签修改失败"
    except Exception as e:
        logger.error(f"修改任务标签失败: {e}")
        return f"修改任务标签失败: {str(e)}"

@mcp.tool()
def update_task_due_date(task_id: str, due_date: str) -> str:
    """修改任务截止时间"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        task = user.find_task_by_id(task_id)
        if not task:
            return f"未找到ID为{task_id}的任务"
        
        if due_date.lower() == "clear":
            task.dueDate = None
            result = user.modify_task(task)
            if result:
                return f"任务'{task.title}'截止时间已清除"
            else:
                return f"任务'{task.title}'截止时间清除失败"
        else:
            from dateutil import parser
            try:
                task.dueDate = parser.parse(due_date).isoformat()
                result = user.modify_task(task)
                if result:
                    return f"任务'{task.title}'截止时间已设置为: {due_date}"
                else:
                    return f"任务'{task.title}'截止时间修改失败"
            except:
                return f"无效的时间格式: {due_date}"
    except Exception as e:
        logger.error(f"修改任务截止时间失败: {e}")
        return f"修改任务截止时间失败: {str(e)}"

@mcp.tool()
def update_task_start_date(task_id: str, start_date: str) -> str:
    """修改任务开始时间"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        task = user.find_task_by_id(task_id)
        if not task:
            return f"未找到ID为{task_id}的任务"
        
        if start_date.lower() == "clear":
            task.startDate = None
            result = user.modify_task(task)
            if result:
                return f"任务'{task.title}'开始时间已清除"
            else:
                return f"任务'{task.title}'开始时间清除失败"
        elif start_date.lower() == "today":
            from datetime import datetime
            task.startDate = datetime.now().isoformat()
            result = user.modify_task(task)
            if result:
                return f"任务'{task.title}'开始时间已设置为今天"
            else:
                return f"任务'{task.title}'开始时间修改失败"
        else:
            from dateutil import parser
            try:
                task.startDate = parser.parse(start_date).isoformat()
                result = user.modify_task(task)
                if result:
                    return f"任务'{task.title}'开始时间已设置为: {start_date}"
                else:
                    return f"任务'{task.title}'开始时间修改失败"
            except:
                return f"无效的时间格式: {start_date}"
    except Exception as e:
        logger.error(f"修改任务开始时间失败: {e}")
        return f"修改任务开始时间失败: {str(e)}"

@mcp.tool()
def update_task_priority(task_id: str, priority: int) -> str:
    """修改任务优先级 (0=无，1=低，2=中低，3=中，4=中高，5=高)"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        task = user.find_task_by_id(task_id)
        if not task:
            return f"未找到ID为{task_id}的任务"
        
        priority = min(max(0, priority), 5)
        task.priority = priority
        result = user.modify_task(task)
        
        priority_text = {0: "无", 1: "低", 2: "中低", 3: "中", 4: "中高", 5: "高"}.get(priority, str(priority))
        
        if result:
            return f"任务'{task.title}'优先级已设置为: {priority_text}"
        else:
            return f"任务'{task.title}'优先级修改失败"
    except Exception as e:
        logger.error(f"修改任务优先级失败: {e}")
        return f"修改任务优先级失败: {str(e)}"

@mcp.tool()
def update_task_content(task_id: str, content: str) -> str:
    """修改任务内容/描述"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        task = user.find_task_by_id(task_id)
        if not task:
            return f"未找到ID为{task_id}的任务"
        
        task.content = content
        result = user.modify_task(task)
        
        if result:
            if content:
                return f"任务'{task.title}'内容已更新"
            else:
                return f"任务'{task.title}'内容已清空"
        else:
            return f"任务'{task.title}'内容修改失败"
    except Exception as e:
        logger.error(f"修改任务内容失败: {e}")
        return f"修改任务内容失败: {str(e)}"

@mcp.tool()
def update_task_progress(task_id: str, progress: int) -> str:
    """修改任务进度 (0-100)"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        task = user.find_task_by_id(task_id)
        if not task:
            return f"未找到ID为{task_id}的任务"
        
        progress = min(max(0, progress), 100)
        task.progress = progress
        result = user.modify_task(task)
        
        if result:
            return f"任务'{task.title}'进度已设置为: {progress}%"
        else:
            return f"任务'{task.title}'进度修改失败"
    except Exception as e:
        logger.error(f"修改任务进度失败: {e}")
        return f"修改任务进度失败: {str(e)}"

@mcp.tool()
def complete_task(task_id: str) -> str:
    """标记任务为已完成"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        task = user.find_task_by_id(task_id)
        if not task:
            return f"未找到ID为{task_id}的任务"
        
        task.status = 1
        task.progress = 100
        result = user.modify_task(task)
        
        if result:
            return f"任务'{task.title}'已标记为完成"
        else:
            return f"任务'{task.title}'完成标记失败"
    except Exception as e:
        logger.error(f"完成任务失败: {e}")
        return f"完成任务失败: {str(e)}"

@mcp.tool()
def reopen_task(task_id: str) -> str:
    """重新打开已完成的任务"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        task = user.find_task_by_id(task_id)
        if not task:
            return f"未找到ID为{task_id}的任务"
        
        task.status = 0
        result = user.modify_task(task)
        
        if result:
            return f"任务'{task.title}'已重新打开"
        else:
            return f"任务'{task.title}'重新打开失败"
    except Exception as e:
        logger.error(f"重新打开任务失败: {e}")
        return f"重新打开任务失败: {str(e)}"

@mcp.tool()
def search_tasks_by_title(keyword: str) -> List[Dict[str, Any]]:
    """根据关键词搜索任务"""
    try:
        user = get_user_instance()
        if not user.token:
            return [{"error": "请先设置token"}]
        
        user.get_info_about()  # 刷新数据
        all_tasks = user.tool_get_task_info()
        
        # 搜索包含关键词的任务
        matching_tasks = []
        for task in all_tasks:
            if keyword.lower() in task.get('title', '').lower():
                matching_tasks.append(task)
        
        return enhance_tasks_with_names(user, matching_tasks)
    except Exception as e:
        logger.error(f"搜索任务失败: {e}")
        return [{"error": str(e)}]

@mcp.tool()
def get_tasks_by_project(project_id: str) -> List[Dict[str, Any]]:
    """获取指定项目的所有任务"""
    try:
        user = get_user_instance()
        if not user.token:
            return [{"error": "请先设置token"}]
        
        user.get_info_about()  # 刷新数据
        all_tasks = user.tool_get_task_info()
        
        # 筛选指定项目的任务
        project_tasks = []
        for task in all_tasks:
            if task.get('projectId') == project_id:
                project_tasks.append(task)
        
        return enhance_tasks_with_names(user, project_tasks)
    except Exception as e:
        logger.error(f"获取项目任务失败: {e}")
        return [{"error": str(e)}]

@mcp.tool()
def get_completed_tasks() -> List[Dict[str, Any]]:
    """获取所有已完成的任务"""
    try:
        user = get_user_instance()
        if not user.token:
            return [{"error": "请先设置token"}]
        
        user.get_info_about()  # 刷新数据
        all_tasks = user.tool_get_task_info()
        
        # 筛选已完成的任务 (status = 1)
        completed_tasks = []
        for task in all_tasks:
            if task.get('status') == 1:
                completed_tasks.append(task)
        
        return enhance_tasks_with_names(user, completed_tasks)
    except Exception as e:
        logger.error(f"获取已完成任务失败: {e}")
        return [{"error": str(e)}]

@mcp.tool()
def get_pending_tasks() -> List[Dict[str, Any]]:
    """获取所有待完成的任务"""
    try:
        user = get_user_instance()
        if not user.token:
            return [{"error": "请先设置token"}]
        
        user.get_info_about()  # 刷新数据
        all_tasks = user.tool_get_task_info()
        
        # 筛选待完成的任务 (status = 0)
        pending_tasks = []
        for task in all_tasks:
            if task.get('status') == 0:
                pending_tasks.append(task)
        
        return enhance_tasks_with_names(user, pending_tasks)
    except Exception as e:
        logger.error(f"获取待完成任务失败: {e}")
        return [{"error": str(e)}]

# ========== 项目管理工具 ==========

@mcp.tool()
def create_project(
    name: str,
    color: str = "",
    group_id: str = "",
    sort_order: int = 0,
    view_mode: str = "list",
    team_id: str = ""
) -> str:
    """创建新项目"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        # 使用ProjectBuilder创建项目
        builder = api.ProjectBuilder(name)
        
        if color:
            builder.color(color)
        if group_id:
            builder.group(group_id)
        if sort_order != 0:
            builder.sort_order(sort_order)
        if view_mode:
            builder.view_mode(view_mode)
        if team_id:
            builder.team(team_id)
        
        project = builder.build()
        result = user.add_project(project)
        
        if result:
            return f"项目'{name}'创建成功"
        else:
            return f"项目'{name}'创建失败"
    except Exception as e:
        logger.error(f"创建项目失败: {e}")
        return f"创建项目失败: {str(e)}"

@mcp.tool()
def delete_project_by_id(project_id: str) -> str:
    """根据ID删除项目"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        # 先获取项目信息用于显示
        project = user.find_project_by_id(project_id)
        project_name = project.name if project else f"ID为{project_id}的项目"
        
        result = user.remove_project(project_id)
        if result:
            return f"项目'{project_name}'删除成功"
        else:
            return f"项目'{project_name}'删除失败"
    except Exception as e:
        logger.error(f"删除项目失败: {e}")
        return f"删除项目失败: {str(e)}"

@mcp.tool()
def delete_project_by_name(name: str) -> str:
    """根据名称删除项目"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        project = user.find_project_by_name(name)
        if not project:
            return f"未找到名称为'{name}'的项目"
        
        result = user.remove_project(project.id)
        if result:
            return f"项目'{name}'删除成功"
        else:
            return f"项目'{name}'删除失败"
    except Exception as e:
        logger.error(f"删除项目失败: {e}")
        return f"删除项目失败: {str(e)}"

@mcp.tool()
def update_project_name(project_id: str, new_name: str) -> str:
    """修改项目名称"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        project = user.find_project_by_id(project_id)
        if not project:
            return f"未找到ID为{project_id}的项目"
        
        old_name = project.name
        project.name = new_name
        result = user.modify_project(project)
        
        if result:
            return f"项目名称从'{old_name}'更新为'{new_name}'"
        else:
            return f"项目名称更新失败"
    except Exception as e:
        logger.error(f"更新项目名称失败: {e}")
        return f"更新项目名称失败: {str(e)}"

@mcp.tool()
def update_project_color(project_id: str, color: str) -> str:
    """修改项目颜色"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        project = user.find_project_by_id(project_id)
        if not project:
            return f"未找到ID为{project_id}的项目"
        
        project.color = color
        result = user.modify_project(project)
        
        if result:
            return f"项目'{project.name}'颜色已更新为'{color}'"
        else:
            return f"项目'{project.name}'颜色更新失败"
    except Exception as e:
        logger.error(f"更新项目颜色失败: {e}")
        return f"更新项目颜色失败: {str(e)}"

@mcp.tool()
def update_project_view_mode(project_id: str, view_mode: str) -> str:
    """修改项目视图模式 (list/kanban)"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        if view_mode not in ["list", "kanban"]:
            return "视图模式只能是 'list' 或 'kanban'"
        
        project = user.find_project_by_id(project_id)
        if not project:
            return f"未找到ID为{project_id}的项目"
        
        project.viewMode = view_mode
        result = user.modify_project(project)
        
        if result:
            return f"项目'{project.name}'视图模式已更新为'{view_mode}'"
        else:
            return f"项目'{project.name}'视图模式更新失败"
    except Exception as e:
        logger.error(f"更新项目视图模式失败: {e}")
        return f"更新项目视图模式失败: {str(e)}"

@mcp.tool()
def update_advanced_project(
    project_id: str,
    name: str = "",
    color: str = "",
    view_mode: str = "",
    sort_order: int = -1,
    group_id: str = "",
    team_id: str = ""
) -> str:
    """高级项目修改功能（支持修改多个属性）"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        project = user.find_project_by_id(project_id)
        if not project:
            return f"未找到ID为{project_id}的项目"
        
        changes = []
        
        # 更新名称
        if name:
            old_name = project.name
            project.name = name
            changes.append(f"名称: '{old_name}' → '{name}'")
        
        # 更新颜色
        if color:
            project.color = color
            changes.append(f"颜色: {color}")
        
        # 更新视图模式
        if view_mode:
            if view_mode in ["list", "kanban"]:
                project.viewMode = view_mode
                changes.append(f"视图模式: {view_mode}")
            else:
                return "视图模式只能是 'list' 或 'kanban'"
        
        # 更新排序顺序
        if sort_order >= 0:
            project.sortOrder = sort_order
            changes.append(f"排序顺序: {sort_order}")
        
        # 更新分组ID
        if group_id:
            project.groupId = group_id
            changes.append(f"分组ID: {group_id}")
        
        # 更新团队ID
        if team_id:
            project.teamId = team_id
            changes.append(f"团队ID: {team_id}")
        
        if not changes:
            return "没有提供任何要修改的内容"
        
        result = user.modify_project(project)
        
        if result:
            changes_text = "、".join(changes)
            return f"项目'{project.name}'修改成功，更新内容: {changes_text}"
        else:
            return f"项目'{project.name}'修改失败"
    except Exception as e:
        logger.error(f"高级修改项目失败: {e}")
        return f"高级修改项目失败: {str(e)}"

@mcp.tool()
def find_project_by_name(name: str) -> Optional[Dict[str, Any]]:
    """根据名称查找项目"""
    try:
        user = get_user_instance()
        if not user.token:
            return {"error": "请先设置token"}
        
        user.get_info_about()  # 刷新数据
        project = user.find_project_by_name(name)
        if project:
            return project.to_dict()
        else:
            return {"error": f"未找到名称为'{name}'的项目"}
    except Exception as e:
        logger.error(f"查找项目失败: {e}")
        return {"error": str(e)}

# ========== 标签管理工具 ==========

@mcp.tool()
def create_tag(
    name: str,
    color: str = "",
    sort_order: int = 0,
    parent: str = "",
    sort_type: str = "project"
) -> str:
    """创建新标签"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        # 使用TagBuilder创建标签
        builder = api.TagBuilder(name)
        
        if color:
            builder.color(color)
        if sort_order != 0:
            builder.sort_order(sort_order)
        if parent:
            builder.parent(parent)
        if sort_type:
            builder.sort_type(sort_type)
        
        tag = builder.build()
        result = user.add_tag(tag)
        
        if result:
            return f"标签'{name}'创建成功"
        else:
            return f"标签'{name}'创建失败"
    except Exception as e:
        logger.error(f"创建标签失败: {e}")
        return f"创建标签失败: {str(e)}"

@mcp.tool()
def delete_tag_by_name(name: str) -> str:
    """根据名称删除标签"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        # 先检查标签是否存在
        tag = user.find_tag_by_name(name)
        if not tag:
            return f"未找到名称为'{name}'的标签"
        
        result = user.remove_tag(name)
        if result:
            return f"标签'{name}'删除成功"
        else:
            return f"标签'{name}'删除失败"
    except Exception as e:
        logger.error(f"删除标签失败: {e}")
        return f"删除标签失败: {str(e)}"

@mcp.tool()
def update_tag_name(old_name: str, new_name: str) -> str:
    """修改标签名称"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        tag = user.find_tag_by_name(old_name)
        if not tag:
            return f"未找到名称为'{old_name}'的标签"
        
        tag.name = new_name
        tag.label = new_name
        result = user.modify_tag(tag)
        
        if result:
            return f"标签名称从'{old_name}'更新为'{new_name}'"
        else:
            return f"标签名称更新失败"
    except Exception as e:
        logger.error(f"更新标签名称失败: {e}")
        return f"更新标签名称失败: {str(e)}"

@mcp.tool()
def update_tag_color(name: str, color: str) -> str:
    """修改标签颜色"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        tag = user.find_tag_by_name(name)
        if not tag:
            return f"未找到名称为'{name}'的标签"
        
        tag.color = color
        result = user.modify_tag(tag)
        
        if result:
            return f"标签'{name}'颜色已更新为'{color}'"
        else:
            return f"标签'{name}'颜色更新失败"
    except Exception as e:
        logger.error(f"更新标签颜色失败: {e}")
        return f"更新标签颜色失败: {str(e)}"

@mcp.tool()
def update_advanced_tag(
    name: str,
    new_name: str = "",
    color: str = "",
    sort_order: int = -1,
    parent: str = "",
    sort_type: str = ""
) -> str:
    """高级标签修改功能（支持修改多个属性）"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        tag = user.find_tag_by_name(name)
        if not tag:
            return f"未找到名称为'{name}'的标签"
        
        changes = []
        
        # 更新名称
        if new_name:
            old_name = tag.name
            tag.name = new_name
            tag.label = new_name
            changes.append(f"名称: '{old_name}' → '{new_name}'")
        
        # 更新颜色
        if color:
            tag.color = color
            changes.append(f"颜色: {color}")
        
        # 更新排序顺序
        if sort_order >= 0:
            tag.sortOrder = sort_order
            changes.append(f"排序顺序: {sort_order}")
        
        # 更新父标签
        if parent:
            tag.parent = parent
            changes.append(f"父标签: {parent}")
        
        # 更新排序类型
        if sort_type:
            tag.sortType = sort_type
            changes.append(f"排序类型: {sort_type}")
        
        if not changes:
            return "没有提供任何要修改的内容"
        
        result = user.modify_tag(tag)
        
        if result:
            changes_text = "、".join(changes)
            return f"标签'{tag.name}'修改成功，更新内容: {changes_text}"
        else:
            return f"标签'{tag.name}'修改失败"
    except Exception as e:
        logger.error(f"高级修改标签失败: {e}")
        return f"高级修改标签失败: {str(e)}"

@mcp.tool()
def find_tag_by_name(name: str) -> Optional[Dict[str, Any]]:
    """根据名称查找标签"""
    try:
        user = get_user_instance()
        if not user.token:
            return {"error": "请先设置token"}
        
        user.get_info_about()  # 刷新数据
        tag = user.find_tag_by_name(name)
        if tag:
            return tag.to_dict()
        else:
            return {"error": f"未找到名称为'{name}'的标签"}
    except Exception as e:
        logger.error(f"查找标签失败: {e}")
        return {"error": str(e)}

@mcp.tool()
def get_tasks_by_tag(tag_name: str) -> List[Dict[str, Any]]:
    """获取包含指定标签的所有任务"""
    try:
        user = get_user_instance()
        if not user.token:
            return [{"error": "请先设置token"}]
        
        user.get_info_about()  # 刷新数据
        all_tasks = user.tool_get_task_info()
        
        # 筛选包含指定标签的任务
        tagged_tasks = []
        for task in all_tasks:
            task_tags = task.get('tags', [])
            if tag_name in task_tags:
                tagged_tasks.append(task)
        
        return enhance_tasks_with_names(user, tagged_tasks)
    except Exception as e:
        logger.error(f"获取标签任务失败: {e}")
        return [{"error": str(e)}]

@mcp.tool()
def get_high_priority_tasks() -> List[Dict[str, Any]]:
    """获取高优先级任务（优先级4-5）"""
    try:
        user = get_user_instance()
        if not user.token:
            return [{"error": "请先设置token"}]
        
        user.get_info_about()  # 刷新数据
        all_tasks = user.tool_get_task_info()
        
        # 筛选高优先级任务
        high_priority_tasks = []
        for task in all_tasks:
            priority = task.get('priority', 0)
            if priority >= 4:
                high_priority_tasks.append(task)
        
        return enhance_tasks_with_names(user, high_priority_tasks)
    except Exception as e:
        logger.error(f"获取高优先级任务失败: {e}")
        return [{"error": str(e)}]

@mcp.tool()
def get_overdue_tasks() -> List[Dict[str, Any]]:
    """获取已过期的任务"""
    try:
        user = get_user_instance()
        if not user.token:
            return [{"error": "请先设置token"}]
        
        user.get_info_about()  # 刷新数据
        all_tasks = user.tool_get_task_info()
        
        from datetime import datetime
        now = datetime.now()
        
        # 筛选已过期的任务
        overdue_tasks = []
        for task in all_tasks:
            due_date = task.get('dueDate')
            if due_date and task.get('status', 0) == 0:  # 未完成且有截止时间
                try:
                    from dateutil import parser
                    due_datetime = parser.parse(due_date)
                    if due_datetime < now:
                        overdue_tasks.append(task)
                except:
                    continue
        
        return enhance_tasks_with_names(user, overdue_tasks)
    except Exception as e:
        logger.error(f"获取过期任务失败: {e}")
        return [{"error": str(e)}]

@mcp.tool()
def get_today_tasks() -> List[Dict[str, Any]]:
    """获取今天的任务（开始时间或截止时间在今天）"""
    try:
        user = get_user_instance()
        if not user.token:
            return [{"error": "请先设置token"}]
        
        user.get_info_about()  # 刷新数据
        all_tasks = user.tool_get_task_info()
        
        from datetime import datetime, date
        today = date.today()
        
        # 筛选今天的任务
        today_tasks = []
        for task in all_tasks:
            start_date = task.get('startDate')
            due_date = task.get('dueDate')
            
            is_today_task = False
            
            # 检查开始时间
            if start_date:
                try:
                    from dateutil import parser
                    start_datetime = parser.parse(start_date)
                    if start_datetime.date() == today:
                        is_today_task = True
                except:
                    pass
            
            # 检查截止时间
            if due_date and not is_today_task:
                try:
                    from dateutil import parser
                    due_datetime = parser.parse(due_date)
                    if due_datetime.date() == today:
                        is_today_task = True
                except:
                    pass
            
            if is_today_task:
                today_tasks.append(task)
        
        return enhance_tasks_with_names(user, today_tasks)
    except Exception as e:
        logger.error(f"获取今天任务失败: {e}")
        return [{"error": str(e)}]

@mcp.tool()
def get_task_statistics() -> Dict[str, Any]:
    """获取任务统计信息"""
    try:
        user = get_user_instance()
        if not user.token:
            return {"error": "请先设置token"}
        
        user.get_info_about()  # 刷新数据
        all_tasks = user.tool_get_task_info()
        
        # 统计信息
        total_tasks = len(all_tasks)
        completed_tasks = len([t for t in all_tasks if t.get('status') == 1])
        pending_tasks = len([t for t in all_tasks if t.get('status') == 0])
        archived_tasks = len([t for t in all_tasks if t.get('status') == 2])
        
        # 优先级统计
        priority_stats = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for task in all_tasks:
            priority = task.get('priority', 0)
            priority_stats[priority] += 1
        
        # 项目统计
        project_stats = {}
        for task in all_tasks:
            project_id = task.get('projectId', '无项目')
            project_name = '无项目'
            if project_id != '无项目':
                for project in user.projects:
                    if project.id == project_id:
                        project_name = project.name
                        break
            
            if project_name not in project_stats:
                project_stats[project_name] = 0
            project_stats[project_name] += 1
        
        # 过期任务统计
        from datetime import datetime
        now = datetime.now()
        overdue_count = 0
        for task in all_tasks:
            due_date = task.get('dueDate')
            if due_date and task.get('status', 0) == 0:
                try:
                    from dateutil import parser
                    due_datetime = parser.parse(due_date)
                    if due_datetime < now:
                        overdue_count += 1
                except:
                    continue
        
        return {
            "总任务数": total_tasks,
            "已完成": completed_tasks,
            "待完成": pending_tasks,
            "已归档": archived_tasks,
            "过期任务": overdue_count,
            "完成率": f"{(completed_tasks/total_tasks*100):.1f}%" if total_tasks > 0 else "0%",
            "优先级分布": {
                "无优先级": priority_stats[0],
                "低优先级": priority_stats[1],
                "中低优先级": priority_stats[2],
                "中优先级": priority_stats[3],
                "中高优先级": priority_stats[4],
                "高优先级": priority_stats[5]
            },
            "项目分布": project_stats,
            "项目总数": len(user.projects),
            "标签总数": len(user.tags)
        }
    except Exception as e:
        logger.error(f"获取任务统计失败: {e}")
        return {"error": str(e)}

# ========== 任务移动功能 ==========

@mcp.tool()
def move_task_to_project(task_id: str, from_project_id: str, to_project_id: str) -> str:
    """移动单个任务到其他项目"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        # 验证任务是否存在
        task = user.find_task_by_id(task_id)
        if not task:
            return f"未找到ID为{task_id}的任务"
        
        # 验证源项目ID是否匹配
        if task.projectId != from_project_id:
            return f"任务'{task.title}'当前不在指定的源项目中（当前项目ID: {task.projectId}）"
        
        # 验证目标项目是否存在
        target_project = user.find_project_by_id(to_project_id)
        if not target_project:
            return f"未找到目标项目ID: {to_project_id}"
        
        # 获取源项目名称用于显示
        source_project_name = "未知项目"
        source_project = user.find_project_by_id(from_project_id)
        if source_project:
            source_project_name = source_project.name
        
        # 执行移动操作
        result = user.move_task_to_project(task_id, from_project_id, to_project_id)
        
        if result:
            return f"任务'{task.title}'已成功从项目'{source_project_name}'移动到项目'{target_project.name}'"
        else:
            return f"移动任务'{task.title}'失败"
    except Exception as e:
        logger.error(f"移动任务失败: {e}")
        return f"移动任务失败: {str(e)}"

@mcp.tool()
def move_task_to_project_by_name(task_id: str, from_project_name: str, to_project_name: str) -> str:
    """通过项目名称移动单个任务到其他项目"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        # 验证任务是否存在
        task = user.find_task_by_id(task_id)
        if not task:
            return f"未找到ID为{task_id}的任务"
        
        # 查找源项目
        source_project = user.find_project_by_name(from_project_name)
        if not source_project:
            return f"未找到源项目: {from_project_name}"
        
        # 查找目标项目
        target_project = user.find_project_by_name(to_project_name)
        if not target_project:
            return f"未找到目标项目: {to_project_name}"
        
        # 验证任务是否在源项目中
        if task.projectId != source_project.id:
            return f"任务'{task.title}'当前不在项目'{from_project_name}'中"
        
        # 执行移动操作
        result = user.move_task_to_project(task_id, source_project.id, target_project.id)
        
        if result:
            return f"任务'{task.title}'已成功从项目'{from_project_name}'移动到项目'{to_project_name}'"
        else:
            return f"移动任务'{task.title}'失败"
    except Exception as e:
        logger.error(f"移动任务失败: {e}")
        return f"移动任务失败: {str(e)}"

@mcp.tool()
def move_multiple_tasks_to_project(task_moves: List[Dict[str, str]]) -> str:
    """批量移动多个任务到其他项目
    
    参数格式: [{"taskId": "xxx", "fromProjectId": "xxx", "toProjectId": "xxx"}, ...]
    """
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        if not task_moves or not isinstance(task_moves, list):
            return "请提供有效的任务移动列表"
        
        # 验证每个移动请求
        validated_moves = []
        for move in task_moves:
            if not isinstance(move, dict):
                return "任务移动项必须是字典格式"
            
            task_id = move.get("taskId")
            from_project_id = move.get("fromProjectId")
            to_project_id = move.get("toProjectId")
            
            if not all([task_id, from_project_id, to_project_id]):
                return "每个移动项必须包含 taskId, fromProjectId, toProjectId"
            
            # 验证任务存在
            task = user.find_task_by_id(task_id)
            if not task:
                return f"未找到任务ID: {task_id}"
            
            # 验证任务在源项目中
            if task.projectId != from_project_id:
                return f"任务'{task.title}'不在指定的源项目中"
            
            # 验证目标项目存在
            target_project = user.find_project_by_id(to_project_id)
            if not target_project:
                return f"未找到目标项目ID: {to_project_id}"
            
            validated_moves.append(move)
        
        # 执行批量移动
        result = user.move_tasks_to_project(validated_moves)
        
        if result:
            return f"成功批量移动 {len(validated_moves)} 个任务"
        else:
            return "批量移动任务失败"
    except Exception as e:
        logger.error(f"批量移动任务失败: {e}")
        return f"批量移动任务失败: {str(e)}"

@mcp.tool()
def move_all_tasks_from_project(from_project_id: str, to_project_id: str) -> str:
    """将一个项目中的所有任务移动到另一个项目"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        # 验证源项目和目标项目存在
        source_project = user.find_project_by_id(from_project_id)
        if not source_project:
            return f"未找到源项目ID: {from_project_id}"
        
        target_project = user.find_project_by_id(to_project_id)
        if not target_project:
            return f"未找到目标项目ID: {to_project_id}"
        
        # 获取源项目中的所有任务
        user.get_info_about()  # 刷新数据
        all_tasks = user.tool_get_task_info()
        source_tasks = [task for task in all_tasks if task.get('projectId') == from_project_id]
        
        if not source_tasks:
            return f"项目'{source_project.name}'中没有任务需要移动"
        
        # 构建移动列表
        task_moves = []
        for task in source_tasks:
            task_moves.append({
                "taskId": task['id'],
                "fromProjectId": from_project_id,
                "toProjectId": to_project_id
            })
        
        # 执行批量移动
        result = user.move_tasks_to_project(task_moves)
        
        if result:
            return f"成功将 {len(source_tasks)} 个任务从项目'{source_project.name}'移动到项目'{target_project.name}'"
        else:
            return f"移动项目'{source_project.name}'中的任务失败"
    except Exception as e:
        logger.error(f"移动项目任务失败: {e}")
        return f"移动项目任务失败: {str(e)}"

@mcp.tool()
def move_all_tasks_from_project_by_name(from_project_name: str, to_project_name: str) -> str:
    """通过项目名称将一个项目中的所有任务移动到另一个项目"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        # 查找源项目和目标项目
        source_project = user.find_project_by_name(from_project_name)
        if not source_project:
            return f"未找到源项目: {from_project_name}"
        
        target_project = user.find_project_by_name(to_project_name)
        if not target_project:
            return f"未找到目标项目: {to_project_name}"
        
        # 调用按ID移动的方法
        return move_all_tasks_from_project(source_project.id, target_project.id)
    except Exception as e:
        logger.error(f"移动项目任务失败: {e}")
        return f"移动项目任务失败: {str(e)}"

@mcp.tool()
def move_tasks_by_tag_to_project(tag_name: str, to_project_id: str) -> str:
    """将包含指定标签的所有任务移动到指定项目"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        # 验证目标项目存在
        target_project = user.find_project_by_id(to_project_id)
        if not target_project:
            return f"未找到目标项目ID: {to_project_id}"
        
        # 验证标签存在
        tag = user.find_tag_by_name(tag_name)
        if not tag:
            return f"未找到标签: {tag_name}"
        
        # 获取包含指定标签的所有任务
        user.get_info_about()  # 刷新数据
        all_tasks = user.tool_get_task_info()
        tagged_tasks = []
        for task in all_tasks:
            task_tags = task.get('tags', [])
            if tag_name in task_tags:
                tagged_tasks.append(task)
        
        if not tagged_tasks:
            return f"没有找到包含标签'{tag_name}'的任务"
        
        # 构建移动列表
        task_moves = []
        for task in tagged_tasks:
            current_project_id = task.get('projectId')
            if current_project_id and current_project_id != to_project_id:
                task_moves.append({
                    "taskId": task['id'],
                    "fromProjectId": current_project_id,
                    "toProjectId": to_project_id
                })
        
        if not task_moves:
            return f"所有包含标签'{tag_name}'的任务都已在目标项目'{target_project.name}'中"
        
        # 执行批量移动
        result = user.move_tasks_to_project(task_moves)
        
        if result:
            return f"成功将 {len(task_moves)} 个包含标签'{tag_name}'的任务移动到项目'{target_project.name}'"
        else:
            return f"移动包含标签'{tag_name}'的任务失败"
    except Exception as e:
        logger.error(f"按标签移动任务失败: {e}")
        return f"按标签移动任务失败: {str(e)}"

@mcp.tool()
def move_tasks_by_tag_to_project_by_name(tag_name: str, to_project_name: str) -> str:
    """通过项目名称将包含指定标签的所有任务移动到指定项目"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        # 查找目标项目
        target_project = user.find_project_by_name(to_project_name)
        if not target_project:
            return f"未找到目标项目: {to_project_name}"
        
        # 调用按ID移动的方法
        return move_tasks_by_tag_to_project(tag_name, target_project.id)
    except Exception as e:
        logger.error(f"按标签移动任务失败: {e}")
        return f"按标签移动任务失败: {str(e)}"

@mcp.tool()
def get_task_move_preview(task_id: str, to_project_id: str) -> Dict[str, Any]:
    """预览任务移动操作（不实际执行移动）"""
    try:
        user = get_user_instance()
        if not user.token:
            return {"error": "请先设置token"}
        
        # 验证任务存在
        task = user.find_task_by_id(task_id)
        if not task:
            return {"error": f"未找到ID为{task_id}的任务"}
        
        # 获取当前项目信息
        current_project_name = "未知项目"
        current_project = user.find_project_by_id(task.projectId)
        if current_project:
            current_project_name = current_project.name
        
        # 验证目标项目存在
        target_project = user.find_project_by_id(to_project_id)
        if not target_project:
            return {"error": f"未找到目标项目ID: {to_project_id}"}
        
        # 检查是否需要移动
        if task.projectId == to_project_id:
            return {
                "需要移动": False,
                "原因": "任务已在目标项目中",
                "任务信息": {
                    "ID": task.id,
                    "标题": task.title,
                    "当前项目": current_project_name,
                    "目标项目": target_project.name
                }
            }
        
        return {
            "需要移动": True,
            "任务信息": {
                "ID": task.id,
                "标题": task.title,
                "内容": task.content or "无",
                "状态": {0: "未完成", 1: "已完成", 2: "已归档"}.get(task.status, "未知"),
                "优先级": task.priority or 0,
                "标签": task.tags or [],
                "当前项目": {
                    "ID": task.projectId,
                    "名称": current_project_name
                },
                "目标项目": {
                    "ID": to_project_id,
                    "名称": target_project.name
                }
            },
            "移动操作": {
                "taskId": task_id,
                "fromProjectId": task.projectId,
                "toProjectId": to_project_id
            }
        }
    except Exception as e:
        logger.error(f"预览任务移动失败: {e}")
        return {"error": str(e)}

# 资源定义
@mcp.resource("dida365://user")
def get_user_resource() -> str:
    """获取用户信息资源"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        user_info = user.get_user_info()
        if user_info:
            return json.dumps({
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "username": user.username
            }, ensure_ascii=False, indent=2)
        else:
            return "获取用户信息失败"
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.resource("dida365://tasks")
def get_tasks_resource() -> str:
    """获取所有任务资源"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        user.get_info_about()
        tasks = user.tool_get_task_info()
        enhanced_tasks = enhance_tasks_with_names(user, tasks)
        return json.dumps(enhanced_tasks, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.resource("dida365://projects")
def get_projects_resource() -> str:
    """获取所有项目资源"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        user.get_info_about()
        projects = user.tool_get_project_info()
        return json.dumps(projects, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"错误: {str(e)}"

@mcp.resource("dida365://tags")
def get_tags_resource() -> str:
    """获取所有标签资源"""
    try:
        user = get_user_instance()
        if not user.token:
            return "请先设置token"
        
        user.get_info_about()
        tags = user.tool_get_tag_info()
        return json.dumps(tags, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"错误: {str(e)}"






if __name__ == "__main__":
    mcp.run(transport='stdio')
