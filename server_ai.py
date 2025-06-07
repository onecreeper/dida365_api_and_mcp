# server.py
from mcp.server.fastmcp import FastMCP
import api
import os
import json
import logging
import re
from datetime import datetime, timedelta
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
user_instance: Optional[api.User] = None

def get_user_instance() -> api.User:
    """获取或创建用户实例"""
    global user_instance
    if user_instance is None:
        config = read_or_create_json()
        token = config.get('token', '')
        user_instance = api.User(token)
        if token:
            try:
                user_info = user_instance.get_user_info()
                if user_info:
                    user_instance.get_info_about()  # 加载任务、项目、标签数据
                    logger.info(f"用户已登录: {user_instance.username or user_instance.email}")
                else:
                    logger.warning("Token可能已过期，请重新登录")
            except Exception as e:
                logger.error(f"初始化用户失败: {e}")
    return user_instance

def ensure_logged_in():
    """确保用户已登录，自动检测登录状态"""
    user = get_user_instance()
    if not user.token:
        raise ValueError("用户未登录，请先使用login_with_token工具登录")
    
    # 尝试验证token是否有效
    try:
        user_info = user.get_user_info()
        if not user_info:
            raise ValueError("Token已过期或无效，请使用login_with_token工具重新登录")
    except Exception as e:
        logger.warning(f"Token验证失败: {e}")
        raise ValueError("Token已过期或无效，请使用login_with_token工具重新登录")
    
    return user

def safe_api_call(func, *args, **kwargs):
    """安全的API调用，自动处理登录状态"""
    try:
        user = ensure_logged_in()
        return func(*args, **kwargs)
    except ValueError as e:
        if "登录" in str(e):
            return {
                "success": False,
                "message": str(e),
                "action_required": "login",
                "hint": "请使用login_with_token工具登录，或检查token是否有效"
            }
        else:
            return {
                "success": False,
                "message": str(e)
            }
    except Exception as e:
        logger.error(f"API调用失败: {e}")
        return {
            "success": False,
            "message": f"操作失败: {str(e)}"
        }

# ==================== 用户认证工具 ====================

@mcp.tool()
def login_with_token(token: str) -> Dict[str, Any]:
    """使用token登录滴答清单
    
    Args:
        token: 滴答清单的认证token（cookie格式）
    
    Returns:
        登录结果和用户信息
    """
    try:
        global user_instance
        user_instance = api.User(token)
        user_info = user_instance.get_user_info()
        
        if user_info:
            # 保存token到配置文件
            config = read_or_create_json()
            config['token'] = token
            save_json(config)
            
            # 加载用户数据
            user_instance.get_info_about()
            
            return {
                "success": True,
                "message": "登录成功",
                "user_info": {
                    "name": user_instance.name,
                    "email": user_instance.email,
                    "phone": user_instance.phone,
                    "username": user_instance.username
                }
            }
        else:
            return {
                "success": False,
                "message": "登录失败，token无效或已过期"
            }
    except Exception as e:
        logger.error(f"登录失败: {e}")
        return {
            "success": False,
            "message": f"登录失败: {str(e)}"
        }

@mcp.tool()
def get_user_info() -> Dict[str, Any]:
    """获取当前用户信息"""
    try:
        user = ensure_logged_in()
        return {
            "success": True,
            "user_info": {
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "username": user.username
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

# ==================== 任务管理工具 ====================

@mcp.tool()
def get_tasks(task_id: Optional[str] = None) -> Dict[str, Any]:
    """获取任务列表或指定任务（包含项目和标签的详细信息）
    
    Args:
        task_id: 可选，指定任务ID获取单个任务
    
    Returns:
        任务信息（包含项目名称和标签名称）
    """
    try:
        user = ensure_logged_in()
        tasks_data = user.tool_get_task_info(task_id)
        
        # 如果是单个任务，转换为列表处理
        if task_id and tasks_data:
            tasks_data = [tasks_data]
        elif task_id and not tasks_data:
            return {
                "success": False,
                "message": "任务不存在"
            }
        
        # 增强任务信息，添加项目和标签的名称
        enhanced_tasks = []
        for task in tasks_data if tasks_data else []:
            enhanced_task = task.copy()
            
            # 添加项目名称
            if task.get('projectId'):
                project_info = user.tool_get_project_info(task['projectId'])
                if project_info:
                    enhanced_task['projectName'] = project_info.get('name', '未知项目')
                    enhanced_task['projectInfo'] = {
                        'id': task['projectId'],
                        'name': project_info.get('name', '未知项目')
                    }
            
            # 添加标签名称
            if task.get('tags'):
                tag_details = []
                for tag_name in task['tags']:
                    tag_info = user.tool_get_tag_info(tag_name)
                    if tag_info:
                        tag_details.append({
                            'name': tag_name,
                            'label': tag_info.get('label', tag_name),
                            'color': tag_info.get('color', None)
                        })
                    else:
                        tag_details.append({
                            'name': tag_name,
                            'label': tag_name,
                            'color': None
                        })
                enhanced_task['tagDetails'] = tag_details
            
            enhanced_tasks.append(enhanced_task)
        
        # 如果原本请求的是单个任务，返回单个任务
        if task_id:
            return {
                "success": True,
                "task": enhanced_tasks[0] if enhanced_tasks else None
            }
        else:
            return {
                "success": True,
                "tasks": enhanced_tasks
            }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@mcp.tool()
def add_task(title: str, content: Optional[str] = None, project_id: Optional[str] = None, 
             due_date: Optional[str] = None, priority: Optional[int] = None, 
             tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """添加新任务
    
    Args:
        title: 任务标题
        content: 任务内容描述
        project_id: 所属项目ID
        due_date: 截止时间（ISO格式或相对时间如"1DD"）
        priority: 优先级（1-5，5最高）
        tags: 标签列表
    
    Returns:
        添加结果
    """
    try:
        user = ensure_logged_in()
        
        # 使用TaskBuilder构建任务
        builder = api.TaskBuilder(title)
        
        if content:
            builder.content(content)
        if project_id:
            builder.project(project_id)
        if due_date:
            builder.due(due_date)
        if priority:
            builder.priority(priority)
        if tags:
            builder.tag(*tags)
            
        task = builder.build()
        result = user.add_task(task)
        
        if result:
            return {
                "success": True,
                "message": "任务添加成功"
            }
        else:
            return {
                "success": False,
                "message": "任务添加失败"
            }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@mcp.tool()
def modify_task(task_id: str, title: Optional[str] = None, content: Optional[str] = None,
                status: Optional[int] = None, priority: Optional[int] = None,
                due_date: Optional[str] = None) -> Dict[str, Any]:
    """修改任务
    
    Args:
        task_id: 任务ID
        title: 新标题
        content: 新内容
        status: 新状态（0=未完成，1=已完成，2=已归档）
        priority: 新优先级（1-5）
        due_date: 新截止时间
    
    Returns:
        修改结果
    """
    try:
        user = ensure_logged_in()
        task = user.find_task_by_id(task_id)
        
        if not task:
            return {
                "success": False,
                "message": "任务不存在"
            }
        
        # 更新任务属性
        if title is not None:
            task.title = title
        if content is not None:
            task.content = content
        if status is not None:
            task.status = status
        if priority is not None:
            task.priority = priority
        if due_date is not None:
            # 这里需要解析时间格式
            task.dueDate = due_date
            
        result = user.modify_task(task)
        
        if result:
            return {
                "success": True,
                "message": "任务修改成功"
            }
        else:
            return {
                "success": False,
                "message": "任务修改失败"
            }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@mcp.tool()
def remove_task(task_id: str) -> Dict[str, Any]:
    """删除任务
    
    Args:
        task_id: 任务ID
    
    Returns:
        删除结果
    """
    try:
        user = ensure_logged_in()
        task = user.find_task_by_id(task_id)
        
        if not task:
            return {
                "success": False,
                "message": "任务不存在"
            }
            
        result = user.remove_task(task)
        
        if result:
            return {
                "success": True,
                "message": "任务删除成功"
            }
        else:
            return {
                "success": False,
                "message": "任务删除失败"
            }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@mcp.tool()
def find_task_by_title(title: str) -> Dict[str, Any]:
    """根据标题查找任务
    
    Args:
        title: 任务标题
    
    Returns:
        查找结果
    """
    try:
        user = ensure_logged_in()
        task = user.find_task_by_title(title)
        
        if task:
            return {
                "success": True,
                "task": task.to_dict()
            }
        else:
            return {
                "success": False,
                "message": "未找到匹配的任务"
            }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@mcp.tool()
def complete_task(task_id: str) -> Dict[str, Any]:
    """完成任务（将状态设为已完成）
    
    Args:
        task_id: 任务ID
    
    Returns:
        操作结果
    """
    return modify_task(task_id, status=1)

# ==================== 项目和标签管理工具 ====================

@mcp.tool()
def get_projects(project_id: Optional[str] = None) -> Dict[str, Any]:
    """获取项目列表或指定项目
    
    Args:
        project_id: 可选，指定项目ID获取单个项目
    
    Returns:
        项目信息
    """
    try:
        user = ensure_logged_in()
        projects = user.tool_get_project_info(project_id)
        return {
            "success": True,
            "projects": projects
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@mcp.tool()
def get_tags(tag_name: Optional[str] = None) -> Dict[str, Any]:
    """获取标签列表或指定标签
    
    Args:
        tag_name: 可选，指定标签名获取单个标签
    
    Returns:
        标签信息
    """
    try:
        user = ensure_logged_in()
        tags = user.tool_get_tag_info(tag_name)
        return {
            "success": True,
            "tags": tags
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@mcp.tool()
def get_all_info() -> Dict[str, Any]:
    """获取所有信息（任务、项目、标签）
    
    Returns:
        所有信息
    """
    try:
        user = ensure_logged_in()
        all_info = user.tool_get_all_info()
        return {
            "success": True,
            "data": all_info
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@mcp.tool()
def refresh_data() -> Dict[str, Any]:
    """刷新用户数据（重新从服务器获取最新数据）
    
    Returns:
        刷新结果
    """
    try:
        user = ensure_logged_in()
        user.get_info_about()
        return {
            "success": True,
            "message": "数据刷新成功"
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

# ==================== AI辅助清单管理工具 ====================

@mcp.tool()
def ai_suggest_task_optimization(task_id: Optional[str] = None) -> Dict[str, Any]:
    """AI分析任务并提供优化建议
    
    Args:
        task_id: 可选，指定任务ID分析单个任务，否则分析所有任务
    
    Returns:
        优化建议
    """
    try:
        user = ensure_logged_in()
        
        if task_id:
            task_data = user.tool_get_task_info(task_id)
            if not task_data:
                return {
                    "success": False,
                    "message": "任务不存在"
                }
            tasks = [task_data]
        else:
            tasks = user.tool_get_task_info()
        
        suggestions = []
        
        for task in tasks:
            task_suggestions = []
            
            # 检查任务是否缺少截止时间
            if not task.get('dueDate') and task.get('priority', 0) >= 3:
                task_suggestions.append("高优先级任务建议设置截止时间")
            
            # 检查任务是否缺少项目分类
            if not task.get('projectId'):
                task_suggestions.append("建议将任务分配到具体项目中")
            
            # 检查任务标题是否过于简单
            if len(task.get('title', '')) < 5:
                task_suggestions.append("任务标题过于简单，建议添加更多描述")
            
            # 检查是否有长期未完成的任务
            if task.get('status') == 0 and task.get('createdTime'):
                # 这里可以添加时间检查逻辑
                task_suggestions.append("长期未完成任务，建议重新评估优先级")
            
            # 检查是否缺少内容描述
            if not task.get('content') and task.get('priority', 0) >= 3:
                task_suggestions.append("重要任务建议添加详细描述")
            
            if task_suggestions:
                suggestions.append({
                    "task_id": task.get('id'),
                    "task_title": task.get('title'),
                    "suggestions": task_suggestions
                })
        
        return {
            "success": True,
            "suggestions": suggestions,
            "summary": f"分析了 {len(tasks)} 个任务，发现 {len(suggestions)} 个任务可以优化"
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@mcp.tool()
def ai_auto_categorize_tasks() -> Dict[str, Any]:
    """AI自动分析任务并建议分类和标签
    
    Returns:
        分类建议
    """
    try:
        user = ensure_logged_in()
        tasks = user.tool_get_task_info()
        projects = user.tool_get_project_info()
        
        categorization_suggestions = []
        
        # 创建项目名称映射
        project_map = {p.get('name', '').lower(): p.get('id') for p in projects if projects}
        
        for task in tasks:
            if task.get('projectId'):  # 已经有项目的跳过
                continue
                
            title = task.get('title', '').lower()
            content = task.get('content', '').lower()
            text = f"{title} {content}"
            
            suggestions = {
                "task_id": task.get('id'),
                "task_title": task.get('title'),
                "suggested_project": None,
                "suggested_tags": [],
                "confidence": "medium"
            }
            
            # 基于关键词的简单分类逻辑
            work_keywords = ['工作', '会议', '报告', '项目', '客户', '邮件', '文档', 'work', 'meeting', 'report']
            personal_keywords = ['购物', '健身', '学习', '读书', '电影', '旅行', 'shopping', 'fitness', 'study']
            urgent_keywords = ['紧急', '立即', '马上', '今天', 'urgent', 'asap', 'today']
            
            # 建议项目
            for keyword in work_keywords:
                if keyword in text:
                    # 查找工作相关项目
                    for proj_name, proj_id in project_map.items():
                        if '工作' in proj_name or 'work' in proj_name:
                            suggestions["suggested_project"] = {
                                "id": proj_id,
                                "name": proj_name,
                                "reason": f"包含工作相关关键词: {keyword}"
                            }
                            break
                    break
            
            # 建议标签
            if any(keyword in text for keyword in urgent_keywords):
                suggestions["suggested_tags"].append("紧急")
            
            if any(keyword in text for keyword in work_keywords):
                suggestions["suggested_tags"].append("工作")
            
            if any(keyword in text for keyword in personal_keywords):
                suggestions["suggested_tags"].append("个人")
            
            # 基于优先级建议标签
            priority = task.get('priority', 0)
            if priority >= 4:
                suggestions["suggested_tags"].append("重要")
            
            if suggestions["suggested_project"] or suggestions["suggested_tags"]:
                categorization_suggestions.append(suggestions)
        
        return {
            "success": True,
            "suggestions": categorization_suggestions,
            "summary": f"为 {len(categorization_suggestions)} 个任务提供了分类建议"
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@mcp.tool()
def ai_batch_update_tasks(updates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """AI批量更新任务
    
    Args:
        updates: 更新列表，每个元素包含task_id和要更新的字段
        格式: [{"task_id": "xxx", "project_id": "yyy", "tags": ["tag1"], "priority": 3}]
    
    Returns:
        批量更新结果
    """
    try:
        user = ensure_logged_in()
        results = []
        
        for update in updates:
            task_id = update.get('task_id')
            if not task_id:
                results.append({
                    "task_id": None,
                    "success": False,
                    "message": "缺少task_id"
                })
                continue
            
            task = user.find_task_by_id(task_id)
            if not task:
                results.append({
                    "task_id": task_id,
                    "success": False,
                    "message": "任务不存在"
                })
                continue
            
            # 更新任务属性
            updated = False
            if 'title' in update:
                task.title = update['title']
                updated = True
            if 'content' in update:
                task.content = update['content']
                updated = True
            if 'project_id' in update:
                task.projectId = update['project_id']
                updated = True
            if 'priority' in update:
                task.priority = update['priority']
                updated = True
            if 'status' in update:
                task.status = update['status']
                updated = True
            if 'tags' in update:
                task.tags = update['tags']
                updated = True
            if 'due_date' in update:
                task.dueDate = update['due_date']
                updated = True
            
            if updated:
                result = user.modify_task(task)
                results.append({
                    "task_id": task_id,
                    "success": result,
                    "message": "更新成功" if result else "更新失败"
                })
            else:
                results.append({
                    "task_id": task_id,
                    "success": False,
                    "message": "没有需要更新的字段"
                })
        
        success_count = sum(1 for r in results if r['success'])
        
        return {
            "success": True,
            "results": results,
            "summary": f"批量更新完成，成功: {success_count}/{len(updates)}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@mcp.tool()
def ai_smart_schedule_tasks(date_range: str = "7DD") -> Dict[str, Any]:
    """AI智能安排任务时间
    
    Args:
        date_range: 时间范围（如"7DD"表示7天，"2WW"表示2周）
    
    Returns:
        时间安排建议
    """
    try:
        user = ensure_logged_in()
        tasks = user.tool_get_task_info()
        
        # 筛选未完成且没有开始时间的任务
        unscheduled_tasks = [
            task for task in tasks 
            if task.get('status') == 0 and not task.get('startDate')
        ]
        
        # 按优先级排序
        unscheduled_tasks.sort(key=lambda x: x.get('priority', 0), reverse=True)
        
        schedule_suggestions = []
        
        # 解析时间范围
        match = re.match(r'(\d+)(DD|WW|MM)', date_range.upper())
        if match:
            value, unit = int(match.group(1)), match.group(2)
            if unit == 'DD':
                end_date = datetime.now() + timedelta(days=value)
            elif unit == 'WW':
                end_date = datetime.now() + timedelta(weeks=value)
            elif unit == 'MM':
                end_date = datetime.now() + timedelta(days=value*30)
        else:
            end_date = datetime.now() + timedelta(days=7)
        
        # 简单的时间分配逻辑
        current_date = datetime.now()
        days_available = (end_date - current_date).days
        
        for i, task in enumerate(unscheduled_tasks[:days_available]):
            suggested_date = current_date + timedelta(days=i)
            
            schedule_suggestions.append({
                "task_id": task.get('id'),
                "task_title": task.get('title'),
                "suggested_start_date": suggested_date.isoformat(),
                "priority": task.get('priority', 0),
                "reason": f"基于优先级 {task.get('priority', 0)} 安排在第 {i+1} 天"
            })
        
        return {
            "success": True,
            "suggestions": schedule_suggestions,
            "summary": f"为 {len(schedule_suggestions)} 个任务提供了时间安排建议"
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@mcp.tool()
def ai_task_summary_report() -> Dict[str, Any]:
    """AI生成任务总结报告
    
    Returns:
        任务总结报告
    """
    try:
        user = ensure_logged_in()
        tasks = user.tool_get_task_info()
        projects = user.tool_get_project_info()
        
        # 统计数据
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.get('status') == 1])
        pending_tasks = len([t for t in tasks if t.get('status') == 0])
        high_priority_tasks = len([t for t in tasks if t.get('priority', 0) >= 4])
        
        # 项目分布
        project_stats = {}
        for task in tasks:
            project_id = task.get('projectId')
            if project_id:
                project_name = next((p.get('name') for p in projects if p.get('id') == project_id), '未知项目')
                project_stats[project_name] = project_stats.get(project_name, 0) + 1
        
        # 优先级分布
        priority_stats = {}
        for task in tasks:
            priority = task.get('priority', 0)
            priority_stats[f"优先级{priority}"] = priority_stats.get(f"优先级{priority}", 0) + 1
        
        # 生成建议
        suggestions = []
        if pending_tasks > completed_tasks:
            suggestions.append("待完成任务较多，建议优先处理高优先级任务")
        
        if high_priority_tasks > 5:
            suggestions.append("高优先级任务过多，建议重新评估任务优先级")
        
        overdue_tasks = []  # 这里可以添加过期任务检查逻辑
        
        report = {
            "overview": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "pending_tasks": pending_tasks,
                "completion_rate": f"{(completed_tasks/total_tasks*100):.1f}%" if total_tasks > 0 else "0%"
            },
            "priority_distribution": priority_stats,
            "project_distribution": project_stats,
            "high_priority_tasks": high_priority_tasks,
            "suggestions": suggestions,
            "generated_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "report": report
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

# ==================== 任务构建工具 ====================

@mcp.tool()
def build_task(title: str, project_id: Optional[str] = None, content: Optional[str] = None,
               start_time: str = "today", due_time: Optional[str] = None, 
               priority: Optional[int] = None, tags: Optional[List[str]] = None,
               is_all_day: bool = True, is_floating: bool = True) -> Dict[str, Any]:
    """使用TaskBuilder构建任务（不会自动添加到服务器）
    
    Args:
        title: 任务标题
        project_id: 项目ID
        content: 任务内容
        start_time: 开始时间（默认"today"）
        due_time: 截止时间
        priority: 优先级（1-5）
        tags: 标签列表
        is_all_day: 是否全天任务
        is_floating: 是否浮动时间
    
    Returns:
        构建的任务对象
    """
    try:
        builder = api.TaskBuilder(title)
        
        if project_id:
            builder.project(project_id)
        if content:
            builder.content(content)
        if start_time:
            builder.start(start_time)
        if due_time:
            builder.due(due_time)
        if priority:
            builder.priority(priority)
        if tags:
            builder.tag(*tags)
            
        builder.all_day(is_all_day).floating(is_floating)
        
        task = builder.build()
        
        return {
            "success": True,
            "task": task.to_dict()
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

# ==================== 资源提供 ====================

@mcp.resource("user://profile")
def get_user_profile() -> str:
    """获取用户资料资源"""
    try:
        user = get_user_instance()
        if not user.token:
            return "用户未登录"
        
        profile = {
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "username": user.username
        }
        return json.dumps(profile, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"获取用户资料失败: {str(e)}"

@mcp.resource("tasks://all")
def get_all_tasks() -> str:
    """获取所有任务资源"""
    try:
        user = get_user_instance()
        if not user.token:
            return "用户未登录"
        
        tasks = user.tool_get_task_info()
        return json.dumps(tasks, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"获取任务失败: {str(e)}"

@mcp.resource("projects://all")
def get_all_projects() -> str:
    """获取所有项目资源"""
    try:
        user = get_user_instance()
        if not user.token:
            return "用户未登录"
        
        projects = user.tool_get_project_info()
        return json.dumps(projects, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"获取项目失败: {str(e)}"

@mcp.resource("tags://all")
def get_all_tags() -> str:
    """获取所有标签资源"""
    try:
        user = get_user_instance()
        if not user.token:
            return "用户未登录"
        
        tags = user.tool_get_tag_info()
        return json.dumps(tags, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"获取标签失败: {str(e)}"

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """获取个性化问候语"""
    return f"你好, {name}! 欢迎使用滴答清单MCP服务器!"

if __name__ == "__main__":
    # 初始化用户实例
    get_user_instance()
    logger.info("滴答清单MCP服务器启动")
    mcp.run(transport='stdio')
