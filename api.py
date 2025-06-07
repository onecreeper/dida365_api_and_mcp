import requests
import json
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dateutil import parser


logging.basicConfig(
    level=logging.DEBUG,  # 设置日志级别
    format='%(asctime)s - %(levelname)s - %(message)s',  # 设置日志格式
    filename='api.log',  # 设置日志输出文件
    filemode='a',  # 写入模式为追加
    encoding='utf-8'
)

def write_tmp(str):
    with open('tmp.txt', 'a', encoding='utf-8') as file:
        file.write(str)
        file.write('\n')


class Task:
    def __init__(self, task_dict=None):

        # 任务唯一标识符（字符串格式，如"681473bbf92b2938d3ab5d45"）
        self.id = None  
        
        # 任务标题（字符串，必填字段）
        self.title = None  
        
        # 所属项目ID（字符串，如"6778eeb7c71c710000000114"表示特定项目）
        self.projectId = None  
        
        # 开始时间（ISO 8601格式字符串，如"2025-05-21T16:00:00.000+0000"）
        self.startDate = None  
        
        # 子任务列表（数组，存储子任务对象，默认空数组）
        self.items = None  
        
        # 提醒时间列表（数组，存储提醒时间点，默认空数组）
        self.reminders = None  
        
        # 排除的重复日期（数组，存储重复任务中跳过的时间点，默认空数组）
        self.exDate = None  
        
        # 截止时间（ISO 8601格式字符串，可为None表示无截止时间）
        self.dueDate = None  
        
        # 优先级（整数1-5，5最高，0表示无优先级）
        self.priority = None  
        
        # 是否为全天任务（布尔值，True表示全天任务）
        self.isAllDay = None  
        
        # 重复规则（字符串，如"RRULE:FREQ=DAILY"，None表示不重复）
        self.repeatFlag = None  
        
        # 进度百分比（整数0-100，0表示未开始）
        self.progress = None  
        
        # 任务负责人（用户ID，None表示无人负责）
        self.assignee = None  
        
        # 排序权重（数值越小越靠前，通常为大负数）
        self.sortOrder = None  
        
        # 是否为浮动时间（布尔值，True表示忽略时区）
        self.isFloating = None  
        
        # 任务状态（整数：0=未完成，1=已完成，2=已归档）
        self.status = None  
        
        # 任务类型扩展字段（保留字段，通常为None）
        self.kind = None  
        
        # 创建时间（ISO 8601格式字符串）
        self.createdTime = None  
        
        # 最后修改时间（ISO 8601格式字符串）
        self.modifiedTime = None  
        
        # 标签列表（数组，存储字符串类型的标签）
        self.tags = None  
        
        # 时区标识（字符串，如"Asia/Hong_Kong"）
        self.timeZone = None  
        
        # 任务描述内容（字符串，可为空）
        self.content = None  

        # 如果有输入字典，覆盖对应字段
        if task_dict:
            self.__dict__.update(task_dict)
    
    def to_dict(self):
        return {key: value for key, value in self.__dict__.items() if value is not None}        

class Tag:
    def __init__(self, task_dict=None):

        self.name = None
        self.rawName = None
        self.label = None
        self.sortOrder = None
        self.sortType = None
        self.color = None
        self.etag = None
        self.type = None
        
               
        if task_dict:
            self.__dict__.update(task_dict)
    
    def to_dict(self):
        return {key: value for key, value in self.__dict__.items() if value is not None}        

class Project:
    def __init__(self, task_dict=None):
        self.id = None
        self.name = None
        self.isOwner = None
        self.color = None
        self.sortOrder = None
        self.sortOption = None
        self.sortType = None
        self.userCount = None
        self.etag = None
        self.modifiedTime = None
        self.inAll = None
        self.showType = None
        self.muted = None
        self.reminderType = None
        self.closed = None
        self.transferred = None
        self.groupId = None
        self.viewMode = None
        self.notificationOptions = None
        self.teamId = None
        self.permission = None
        self.kind = None
        self.timeline = None
        self.needAudit = None
        self.barcodeNeedAudit = None
        self.openToTeam = None
        self.teamMemberPermission = None
        self.source = None

        # 如果提供了字典，则更新对象的属性
        if task_dict:
            self.__dict__.update(task_dict)

    def to_dict(self):
        # 返回一个字典，过滤掉值为 None 的属性
        return {key: value for key, value in self.__dict__.items() if value is not None}

class User:

    def __init__(self,token = ""):
        # 初始化方法，构造函数
        # 参数token默认为空字符串，用于存储用户的token信息
        self.token = token
        # 定义请求头的一部分，包含多个HTTP头部字段
        self.headers_part = {
            "authority": "api.dida365.com",  # 请求的目标服务器
            "accept": "application/json, text/plain, */*",  # 接受的响应内容类型
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",  # 接受的语言
            "hl": "zh_CN",  # 语言环境
            "origin": "https://dida365.com",  # 请求的来源
            "priority": "u=1, i",  # 请求优先级
            "referer": "https://dida365.com/",  # 引荐来源
            "sec-ch-ua": "\"Chromium\";v=\"136\", \"Microsoft Edge\";v=\"136\", \"Not.A/Brand\";v=\"99\"",  # 客户端用户代理
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "traceid": "67e7de9df92b296c74156809",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            "x-csrftoken": "_Kn8xUIloPuZVLznSNrpZIQrFwZXqLlFG0FlEavXhEQ-1743248166",
            "x-device": "{\"platform\":\"web\",\"os\":\"Windows 10\",\"device\":\"Chrome 136.0.0.0\",\"name\":\"\",\"version\":6246,\"id\":\"66c5c4f4efae8477e84eb688\",\"channel\":\"website\",\"campaign\":\"\",\"websocket\":\"67e7de9bf92b296c741567e0\"}"
        }
        self.headers = {}
        self.build_headers()
        
        self.name = ""
        self.email = ""
        self.phone = ""
        self.username = ""
        
        
        self.tasks = []
        self.tags = []
        self.projects = []

    def sign_with_phone(self,phone_number,password):
        pass

    def sign_with_email(self,email,password):
        pass

    def sign_with_username(self,username,password):
        pass

    def build_headers(self):
        self.headers = self.headers_part
        self.headers.update({
            "cookie": self.token
        }) 
    
    def update_token(self,token):
        self.token = token
        self.build_headers()
    
    def get_user_info(self):
        url = "https://api.dida365.com/api/v2/user/profile"
        try:
            response = requests.request("GET", url, headers = self.headers, data={})
        except requests.exceptions.RequestException as e:
            logging.error(f"请求失败: {e}")
            if 'response' in locals():
                if response is not None:
                    logging.error(f"响应状态码: {response.status_code}")
                    logging.error(f"响应内容: {response.text}")
                else:
                    logging.error("响应对象为None")
            else:
                logging.error("未获取到响应对象")
            return None

        data = json.loads(response.text)
        if data.get("errorCode", None) == "user_not_sign_on":
            logging.error("用户未登录")
            return None
        else:
            logging.info("用户已登录")
            self.name = data.get("name", "")
            self.email = data.get("email", "")
            self.phone = data.get("phone", "")
            self.username = data.get("username", "")
            return data
        
    def get_info_about(self):
        url = "https://api.dida365.com/api/v2/batch/check/0"
        try:
            response = requests.request("GET", url, headers = self.headers, data={})
        except requests.exceptions.RequestException as e:
            logging.error(f"请求失败: {e}")
            if 'response' in locals():
                if response is not None:
                    logging.error(f"响应状态码: {response.status_code}")
                    logging.error(f"响应内容: {response.text}")
                else:
                    logging.error("响应对象为None")
            else:
                logging.error("未获取到响应对象")
            return None
        
        data = json.loads(response.text)
        # Tag
        for i in data.get("tags",[]):
            if i != []:
                self.tags.append(Tag(i))
        # Project
        for i in data.get("projectProfiles",[]):
            if i != []:
                self.projects.append(Project(i))
        # Task
        for i in data.get("syncTaskBean",{}).get("update",[]):
            if i != []:
                self.tasks.append(Task(i))
        return data

    def tool_get_task_info(self,id = None):
        if id is None:
            res = []
            for i in self.tasks:
                res.append(i.to_dict())
            return res
        else:
            for i in self.tasks:
                if i.id == id:
                    return i.to_dict()
            return None

    def tool_get_project_info(self,id = None):
        if id is None:
            res = []
            for i in self.projects:
                res.append(i.to_dict())
            return res
        else:
            for i in self.projects:
                if i.id == id:
                    return i.to_dict()
            return None
        
    def tool_get_tag_info(self,name = None):
        if name is None:
            res = []
            for i in self.tags:
                res.append(i.to_dict())
            return res
        else:
            for i in self.tags:
                if i.name == name:
                    return i.to_dict()
                
    def tool_get_all_info(self):
        return {
            "tags": self.tool_get_tag_info(),
            "projects": self.tool_get_project_info(),
            "tasks": self.tool_get_task_info()
        }
        
    def add_task(self,task):
        task = task.to_dict()
        payload = {
            "add": [task],
            "update": [],
            "delete": [],
            "addAttachments": [],
            "updateAttachments": [],
            "deleteAttachments": []
        }
        url = "https://api.dida365.com/api/v2/batch/task"
        try:
            response = requests.request("POST", url, headers=self.headers, json=payload)
        except requests.exceptions.RequestException as e:
            logging.error(f"请求失败: {e}")
            if 'response' in locals():
                if response is not None:
                    logging.error(f"响应状态码: {response.status_code}")
                    logging.error(f"响应内容: {response.text}")
                else:
                    logging.error("响应对象为None")
            else:
                logging.error("未获取到响应对象")
            return None
        self.get_info_about()
        return True
    
    def add_tasks(self,tasks):
        tasks = [task.to_dict() for task in tasks]
        payload = {
            "add": tasks,
            "update": [],
            "delete": [],
            "addAttachments": [],
            "updateAttachments": [],
            "deleteAttachments": []
        }
        url = "https://api.dida365.com/api/v2/batch/task"
        try:
            response = requests.request("POST", url, headers=self.headers, json=payload)
        except requests.exceptions.RequestException as e:
            logging.error(f"请求失败: {e}")
            if 'response' in locals():
                if response is not None:
                    logging.error(f"响应状态码: {response.status_code}")
                    logging.error(f"响应内容: {response.text}")
                else:
                    logging.error("响应对象为None")
            else:
                logging.error("未获取到响应对象")
            return None
        self.get_info_about()
        return True
        
    def remove_task(self,task):
        if task is None:
            return False
        task = task.to_dict()
        task_id = task.get("id")
        project_id = task.get("projectId")
        payload = {
            "add": [],
            "update": [],
            "delete": [
                {
                    "taskId": task_id,
                    "projectId": project_id
                }
            ],
            "addAttachments": [],
            "updateAttachments": [],
            "deleteAttachments": []
        }
        url = "https://api.dida365.com/api/v2/batch/task"
        try:
            response = requests.request("POST", url, headers = self.headers, json=payload)
        except requests.exceptions.RequestException as e:
            logging.error(f"请求失败: {e}")
            if 'response' in locals():
                if response is not None:
                    logging.error(f"响应状态码: {response.status_code}")
                    logging.error(f"响应内容: {response.text}")
                else:
                    logging.error("响应对象为None")
            else:
                logging.error("未获取到响应对象")
            return None
        self.get_info_about()
        return True
             
    def remove_tasks(self,tasks):
        flag = True
        tasks = [task.to_dict() for task in tasks]
        task_ids = [task.get("id") for task in tasks]
        project_ids = [task.get("projectId") for task in tasks]
        payload = {
            "add": [],
            "update": [],
            "delete": [
                {
                    "taskId": task_id,
                    "projectId": project_id
                } for task_id, project_id in zip(task_ids, project_ids)
            ],
            "addAttachments": [],
            "updateAttachments": [],
            "deleteAttachments": []
        }
        url = "https://api.dida365.com/api/v2/batch/task"
        try:
            response = requests.request("POST", url, headers=self.headers, json=payload)
        except requests.exceptions.RequestException as e:
            logging.error(f"请求失败: {e}")
            if 'response' in locals():
                if response is not None:
                    logging.error(f"响应状态码: {response.status_code}")
                    logging.error(f"响应内容: {response.text}")
                else:
                    logging.error("响应对象为None")
            else:
                logging.error("未获取到响应对象")
            return None
        self.get_info_about()
        if flag == False:
            return False
        return True
        
    def find_task_by_id(self,id):    
        for i in self.tasks:
            if i.id == id:
                return i
        return None

    def find_task_by_title(self,title):
        for i in self.tasks:
            if i.title == title:
                return i
        return None
            
    def modify_task(self,task):
        if task is None:
            return False
        task = task.to_dict()
        payload = {
            "add": [],
            "update": [task],
            "delete": [],
            "addAttachments": [],
            "updateAttachments": [],
            "deleteAttachments": []
        }
        url = "https://api.dida365.com/api/v2/batch/task"
        try:
            response = requests.request("POST", url, headers=self.headers, json=payload)
        except requests.exceptions.RequestException as e:
            logging.error(f"请求失败: {e}")
            if 'response' in locals():
                if response is not None:
                    logging.error(f"响应状态码: {response.status_code}")
                    logging.error(f"响应内容: {response.text}")
                else:
                    logging.error("响应对象为None")
            else:
                logging.error("未获取到响应对象")
            return None
        self.get_info_about()
        return True

    # ========== 项目管理方法 ==========
    def add_project(self, project):
        """创建单个项目"""
        if project is None:
            return False
        project_data = project.to_dict()
        url = "https://api.dida365.com/api/v2/project"
        try:
            response = requests.request("POST", url, headers=self.headers, json=project_data)
        except requests.exceptions.RequestException as e:
            logging.error(f"请求失败: {e}")
            if 'response' in locals():
                if response is not None:
                    logging.error(f"响应状态码: {response.status_code}")
                    logging.error(f"响应内容: {response.text}")
                else:
                    logging.error("响应对象为None")
            else:
                logging.error("未获取到响应对象")
            return None
        self.get_info_about()
        return True

    def remove_project(self, project_id):
        """删除项目"""
        if project_id is None:
            return False
        payload = {
            "add": [],
            "update": [],
            "delete": [project_id]
        }
        url = "https://api.dida365.com/api/v2/batch/project"
        try:
            response = requests.request("POST", url, headers=self.headers, json=payload)
        except requests.exceptions.RequestException as e:
            logging.error(f"请求失败: {e}")
            if 'response' in locals():
                if response is not None:
                    logging.error(f"响应状态码: {response.status_code}")
                    logging.error(f"响应内容: {response.text}")
                else:
                    logging.error("响应对象为None")
            else:
                logging.error("未获取到响应对象")
            return None
        self.get_info_about()
        return True

    def modify_project(self, project):
        """修改项目"""
        if project is None:
            return False
        project_data = project.to_dict()
        payload = {
            "add": [],
            "update": [project_data],
            "delete": []
        }
        url = "https://api.dida365.com/api/v2/batch/project"
        try:
            response = requests.request("POST", url, headers=self.headers, json=payload)
        except requests.exceptions.RequestException as e:
            logging.error(f"请求失败: {e}")
            if 'response' in locals():
                if response is not None:
                    logging.error(f"响应状态码: {response.status_code}")
                    logging.error(f"响应内容: {response.text}")
                else:
                    logging.error("响应对象为None")
            else:
                logging.error("未获取到响应对象")
            return None
        self.get_info_about()
        return True

    def find_project_by_id(self, id):
        """根据ID查找项目"""
        for i in self.projects:
            if i.id == id:
                return i
        return None

    def find_project_by_name(self, name):
        """根据名称查找项目"""
        for i in self.projects:
            if i.name == name:
                return i
        return None

    # ========== 标签管理方法 ==========
    def add_tag(self, tag):
        """创建标签"""
        if tag is None:
            return False
        tag_data = tag.to_dict()
        payload = {
            "add": [tag_data],
            "update": []
        }
        url = "https://api.dida365.com/api/v2/batch/tag"
        try:
            response = requests.request("POST", url, headers=self.headers, json=payload)
        except requests.exceptions.RequestException as e:
            logging.error(f"请求失败: {e}")
            if 'response' in locals():
                if response is not None:
                    logging.error(f"响应状态码: {response.status_code}")
                    logging.error(f"响应内容: {response.text}")
                else:
                    logging.error("响应对象为None")
            else:
                logging.error("未获取到响应对象")
            return None
        self.get_info_about()
        return True

    def modify_tag(self, tag):
        """修改标签"""
        if tag is None:
            return False
        tag_data = tag.to_dict()
        payload = {
            "add": [],
            "update": [tag_data]
        }
        url = "https://api.dida365.com/api/v2/batch/tag"
        try:
            response = requests.request("POST", url, headers=self.headers, json=payload)
        except requests.exceptions.RequestException as e:
            logging.error(f"请求失败: {e}")
            if 'response' in locals():
                if response is not None:
                    logging.error(f"响应状态码: {response.status_code}")
                    logging.error(f"响应内容: {response.text}")
                else:
                    logging.error("响应对象为None")
            else:
                logging.error("未获取到响应对象")
            return None
        self.get_info_about()
        return True

    def remove_tag(self, tag_name):
        """删除标签"""
        if tag_name is None:
            return False
        payload = {
            "name": tag_name
        }
        url = "https://api.dida365.com/api/v2/tag/delete"
        try:
            response = requests.request("DELETE", url, headers=self.headers, json=payload)
        except requests.exceptions.RequestException as e:
            logging.error(f"请求失败: {e}")
            if 'response' in locals():
                if response is not None:
                    logging.error(f"响应状态码: {response.status_code}")
                    logging.error(f"响应内容: {response.text}")
                else:
                    logging.error("响应对象为None")
            else:
                logging.error("未获取到响应对象")
            return None
        self.get_info_about()
        return True

    def find_tag_by_name(self, name):
        """根据名称查找标签"""
        for i in self.tags:
            if i.name == name:
                return i
        return None

    def move_task_to_project(self, task_id, from_project_id, to_project_id):
        """移动任务到其他项目"""
        if not task_id or not from_project_id or not to_project_id:
            logging.error("移动任务参数不完整")
            return False
            
        payload = [{
            "taskId": task_id,
            "fromProjectId": from_project_id,
            "toProjectId": to_project_id
        }]
        
        url = "https://api.dida365.com/api/v2/batch/taskProject"
        try:
            response = requests.request("POST", url, headers=self.headers, json=payload)
            if response.status_code == 200:
                logging.info(f"成功移动任务 {task_id} 从项目 {from_project_id} 到项目 {to_project_id}")
                self.get_info_about()  # 刷新数据
                return True
            else:
                logging.error(f"移动任务失败，状态码: {response.status_code}, 响应: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            logging.error(f"移动任务请求失败: {e}")
            return False

    def move_tasks_to_project(self, task_moves):
        """批量移动任务到其他项目
        
        Args:
            task_moves: 任务移动列表，格式为:
                [{"taskId": "xxx", "fromProjectId": "xxx", "toProjectId": "xxx"}, ...]
        """
        if not task_moves or not isinstance(task_moves, list):
            logging.error("批量移动任务参数错误")
            return False
            
        url = "https://api.dida365.com/api/v2/batch/taskProject"
        try:
            response = requests.request("POST", url, headers=self.headers, json=task_moves)
            if response.status_code == 200:
                logging.info(f"成功批量移动 {len(task_moves)} 个任务")
                self.get_info_about()  # 刷新数据
                return True
            else:
                logging.error(f"批量移动任务失败，状态码: {response.status_code}, 响应: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            logging.error(f"批量移动任务请求失败: {e}")
            return False

    def batch_update_tasks(self, add_tasks=None, update_tasks=None, delete_tasks=None, 
                          add_attachments=None, update_attachments=None, delete_attachments=None):
        """批量更新任务
        
        Args:
            add_tasks: 要添加的任务列表
            update_tasks: 要更新的任务列表
            delete_tasks: 要删除的任务列表
            add_attachments: 要添加的附件列表
            update_attachments: 要更新的附件列表
            delete_attachments: 要删除的附件列表
        """
        payload = {
            "add": add_tasks or [],
            "update": update_tasks or [],
            "delete": delete_tasks or [],
            "addAttachments": add_attachments or [],
            "updateAttachments": update_attachments or [],
            "deleteAttachments": delete_attachments or []
        }
        
        url = "https://api.dida365.com/api/v2/batch/task"
        try:
            response = requests.request("POST", url, headers=self.headers, json=payload)
            if response.status_code == 200:
                logging.info("批量更新任务成功")
                self.get_info_about()  # 刷新数据
                return True
            else:
                logging.error(f"批量更新任务失败，状态码: {response.status_code}, 响应: {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            logging.error(f"批量更新任务请求失败: {e}")
            return False

    def update_task_with_checklist(self, task_id, title=None, project_id=None, status=None, 
                                  start_date=None, tags=None, checklist_items=None, **kwargs):
        """更新带有清单的任务
        
        Args:
            task_id: 任务ID
            title: 任务标题
            project_id: 项目ID
            status: 任务状态 (0=未完成, 1=已完成)
            start_date: 开始时间
            tags: 标签列表
            checklist_items: 清单项目列表，格式为 [{"id": "xxx", "status": 0, "title": "xxx", "sortOrder": 0}, ...]
            **kwargs: 其他任务属性
        """
        # 查找现有任务
        existing_task = self.find_task_by_id(task_id)
        if not existing_task:
            logging.error(f"未找到任务 {task_id}")
            return False
            
        # 构建更新数据
        task_data = existing_task.to_dict()
        
        # 更新指定字段
        if title is not None:
            task_data['title'] = title
        if project_id is not None:
            task_data['projectId'] = project_id
        if status is not None:
            task_data['status'] = status
        if start_date is not None:
            task_data['startDate'] = start_date
        if tags is not None:
            task_data['tags'] = tags
        if checklist_items is not None:
            task_data['items'] = checklist_items
            
        # 更新其他属性
        for key, value in kwargs.items():
            if value is not None:
                task_data[key] = value
                
        return self.batch_update_tasks(update_tasks=[task_data])
            

class ProjectBuilder:
    def __init__(self, name: str):
        self._data = {
            'name': name,
            'inAll': True,
            'muted': False,
            'isOwner': True,
            'kind': 'TASK',
            'viewMode': 'list',
            'openToTeam': False
        }
    
    def color(self, color_code: str):
        """设置项目颜色"""
        self._data['color'] = color_code
        return self
        
    def group(self, group_id: str):
        """设置项目分组"""
        if group_id:
            self._data['groupId'] = group_id
        return self
        
    def sort_order(self, order: int):
        """设置排序顺序"""
        self._data['sortOrder'] = order
        return self
        
    def team(self, team_id: str):
        """设置团队ID"""
        if team_id:
            self._data['teamId'] = team_id
        return self
        
    def view_mode(self, mode: str):
        """设置视图模式 (list/kanban)"""
        self._data['viewMode'] = mode
        return self
        
    def build(self):
        return Project(self._data)

class TagBuilder:
    def __init__(self, name: str):
        self._data = {
            'name': name,
            'label': name,
            'sortType': 'project'
        }
    
    def color(self, color_code: str):
        """设置标签颜色"""
        self._data['color'] = color_code
        return self
        
    def sort_order(self, order: int):
        """设置排序顺序"""
        self._data['sortOrder'] = order
        return self
        
    def parent(self, parent_tag: str):
        """设置父标签"""
        if parent_tag:
            self._data['parent'] = parent_tag
        return self
        
    def sort_type(self, sort_type: str):
        """设置排序类型"""
        self._data['sortType'] = sort_type
        return self
        
    def build(self):
        return Tag(self._data)

class TaskBuilder:
    def __init__(self, title: str):
        self._data = {
            'title': title,
            'status': 0,
            'progress': 0,
            'isAllDay': True,
            'timeZone': 'Asia/Hong_Kong'
        }
    
    def project(self, project_id: str):
        if project_id:  # 只有非空时才设置projectId
            self._data['projectId'] = project_id
        return self
        
    def content(self, text: str):
        if text:  # 只有非空时才设置content
            self._data['content'] = text
        return self
        
    def start(self, time_str: str = "today"):
        """设置开始时间，默认今天开始"""
        if time_str.lower() == "today":
            self._data['startDate'] = datetime.now().isoformat()
        else:
            self._data['startDate'] = self._parse_time(time_str)
        return self
        
    def due(self, time_str: str):
        self._data['dueDate'] = self._parse_time(time_str)
        return self
        
    def priority(self, level: int):
        self._data['priority'] = min(max(1, level), 5)
        return self
        
    def tag(self, *tags: str):
        self._data.setdefault('tags', []).extend(tags)
        return self
        
    def floating(self, is_floating: bool = True):
        self._data['isFloating'] = is_floating
        return self
        
    def all_day(self, is_all_day: bool = True):
        self._data['isAllDay'] = is_all_day
        return self
        
    def build(self):
        return Task(self._data)
        
    def _parse_time(self, time_str: str) -> str:
        """解析相对/绝对时间并返回ISO格式字符串"""
        if delta := self._parse_relative(time_str):
            return (datetime.now() + delta).isoformat()
            
        try:
            return parser.parse(time_str).isoformat()
        except:
            raise ValueError(f"无效时间格式: {time_str}")
            
    def _parse_relative(self, time_str: str) -> timedelta:
        """解析相对时间格式（支持YY/MM/WW/DD/HH/mm/ss）"""
        pattern = r'(\d+)(YY|MM|WW|DD|HH|mm|ss)'
        matches = re.findall(pattern, time_str, re.IGNORECASE)
        if not matches:
            return None
            
        delta = timedelta()
        for value, unit in matches:
            value = int(value)
            unit = unit.upper()
            if unit == 'YY': delta += timedelta(days=value*365)
            elif unit == 'MM': delta += timedelta(days=value*30)
            elif unit == 'WW': delta += timedelta(weeks=value)
            elif unit == 'DD': delta += timedelta(days=value)
            elif unit == 'HH': delta += timedelta(hours=value)
            elif unit == 'MM': delta += timedelta(minutes=value)
            elif unit == 'SS': delta += timedelta(seconds=value)
            
        return delta

if __name__ == '__main__':
    # 从key.json文件读取token
    try:
        with open('key.json', 'r', encoding='utf-8') as f:
            key_data = json.load(f)
            token = key_data.get('token', '')
    except FileNotFoundError:
        logging.error("key.json文件不存在，请创建该文件并添加token")
        print("错误：key.json文件不存在")
        print("请创建key.json文件，格式如下：")
        print('{"token": "your_token_here"}')
        exit(1)
    except json.JSONDecodeError:
        logging.error("key.json文件格式错误")
        print("错误：key.json文件格式错误，请检查JSON格式")
        exit(1)
    except Exception as e:
        logging.error(f"读取key.json文件时发生错误: {e}")
        print(f"错误：读取key.json文件时发生错误: {e}")
        exit(1)
    
    if not token:
        logging.error("token为空，请在key.json中设置有效的token")
        print("错误：token为空，请在key.json中设置有效的token")
        exit(1)
    
    onecreeper = User()
    onecreeper.update_token(token)
    onecreeper.get_info_about()
    
    # ========== 使用ProjectBuilder示例 ==========
    # 创建一个工作项目
    project1 = (ProjectBuilder("工作项目")
                .color("#FF6B6B")
                .sort_order(-1100048498688)
                .view_mode("list")
                .build())
    
    # 创建一个个人项目
    project2 = (ProjectBuilder("个人学习")
                .color("#4ECDC4")
                .sort_order(-1100048498687)
                .view_mode("kanban")
                .build())
    
    # 添加项目
    onecreeper.add_project(project1)
    onecreeper.add_project(project2)
    
    # ========== 使用TagBuilder示例 ==========
    # 创建重要标签
    tag1 = (TagBuilder("重要")
            .color("#FFD966")
            .sort_order(-3298534883328)
            .build())
    
    # 创建紧急标签
    tag2 = (TagBuilder("紧急")
            .color("#FF6B6B")
            .sort_order(-3298534883327)
            .build())
    
    # 添加标签
    onecreeper.add_tag(tag1)
    onecreeper.add_tag(tag2)
    
    # ========== 使用TaskBuilder示例 ==========
    # 普通任务(无开始时间)
    task1 = (TaskBuilder("普通任务")
            .content("这是一个普通任务")
            .build())
    
    # 紧急任务(今天开始)
    task2 = (TaskBuilder("紧急任务")
            .start()  # 默认今天开始
            .project("6778eeb7c71c710000000114")
            .due("2025-05-05 15:00")
            .priority(4)
            .tag("重要", "紧急")
            .build())
    
    onecreeper.add_task(task1)
    onecreeper.add_task(task2)
    
    # ========== 演示修改和删除功能 ==========
    # 查找并修改项目
    work_project = onecreeper.find_project_by_name("工作项目")
    if work_project:
        work_project.name = "工作项目-已修改"
        work_project.color = "#35D870"
        onecreeper.modify_project(work_project)
    
    # 查找并修改标签
    important_tag = onecreeper.find_tag_by_name("重要")
    if important_tag:
        important_tag.name = "超级重要"
        important_tag.label = "超级重要"
        important_tag.color = "#35D870"
        onecreeper.modify_tag(important_tag)
    
    # 演示删除功能（注释掉以避免实际删除）
    # onecreeper.remove_tag("紧急")
    # onecreeper.remove_project("project_id_here")
    
    # ========== 演示新增的任务移动和批量更新功能 ==========
    
    # 1. 移动单个任务到其他项目
    # onecreeper.move_task_to_project(
    #     task_id="683d6744aaf2610c051c4777",
    #     from_project_id="6844119ee4b0a70695e768d8",
    #     to_project_id="inbox1015881707"
    # )
    
    # 2. 批量移动任务到其他项目
    # task_moves = [
    #     {
    #         "taskId": "683d6744aaf2610c051c4777",
    #         "fromProjectId": "6844119ee4b0a70695e768d8",
    #         "toProjectId": "inbox1015881707"
    #     }
    # ]
    # onecreeper.move_tasks_to_project(task_moves)
    
    # 3. 批量更新任务（基于您提供的curl命令）
    # update_task_data = {
    #     "items": [{"id": "68441258aaf2613ac64db9f1", "status": 0, "title": "c", "sortOrder": 0}],
    #     "reminders": [],
    #     "exDate": [],
    #     "dueDate": None,
    #     "priority": 0,
    #     "isAllDay": True,
    #     "parentId": None,
    #     "repeatFlag": "",
    #     "progress": 0,
    #     "assignee": None,
    #     "sortOrder": -1099511627776,
    #     "startDate": "2025-07-01T16:00:00.000+0000",
    #     "isFloating": False,
    #     "desc": "",
    #     "status": 0,
    #     "projectId": "684411a0e4b091327a199572",
    #     "kind": "CHECKLIST",
    #     "etag": "qn793ixh",
    #     "createdTime": "2025-06-02T08:56:36.000+0000",
    #     "modifiedTime": "2025-06-07T10:21:24.000+0000",
    #     "title": "表盘",
    #     "tags": ["提上日程"],
    #     "timeZone": "Asia/Hong_Kong",
    #     "content": "",
    #     "id": "683d6744aaf2610c051c4777"
    # }
    # onecreeper.batch_update_tasks(update_tasks=[update_task_data])
    
    # 4. 更新带有清单的任务
    # checklist_items = [
    #     {"id": "68441258aaf2613ac64db9f1", "status": 0, "title": "c", "sortOrder": 0}
    # ]
    # onecreeper.update_task_with_checklist(
    #     task_id="683d6744aaf2610c051c4777",
    #     title="表盘",
    #     project_id="684411a0e4b091327a199572",
    #     status=0,
    #     start_date="2025-07-01T16:00:00.000+0000",
    #     tags=["提上日程"],
    #     checklist_items=checklist_items,
    #     kind="CHECKLIST",
    #     priority=0,
    #     isAllDay=True,
    #     timeZone="Asia/Hong_Kong"
    # )
    
    print("API功能演示完成！")
    print("新增功能包括：")
    print("1. 项目管理：创建、修改、删除项目")
    print("2. 标签管理：创建、修改、删除标签")
    print("3. ProjectBuilder和TagBuilder构建器")
    print("4. 查找功能：按名称/ID查找项目和标签")
    print("5. 任务移动：move_task_to_project() 和 move_tasks_to_project()")
    print("6. 批量更新：batch_update_tasks() 和 update_task_with_checklist()")
