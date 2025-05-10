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
    onecreeper = User()
    onecreeper.update_token(f'oai=48F39478D2BAEF3EDAF275DFC0290DEBC1BB8A442B5AB9B2EA065A42E8FE5D244D3F9B7BF482069A1E5E292B5DB005AC9740EB8915E8134161528B72129784D7741D8DE1B70D55264D029A99D56C262FE092895D6BFDD2B003552D410F41A05ED3056E5F14F482701E13238CD2F459BA8D075374026E5E2BC86E5290EE534A8BD420B1FC222EC424D78F8DF25C0B3971CC7400CB2CC8C1DD9B2C16BF6B69C5F6; t=73AE2E6CC13DD9679B108734F08D5DDCDE2D4DB2C9321F66977A01F458D7BB67C01F9B4514585EACB7569442426196A4401595BE1E94744DA788BABBD5E67DC4325615680C54FD42CE398C6B730FA600C50FAD376CA9C4981CFA075647187468385AA04082B6E13207380EE6E17F65D78B498442A0F01A224A27CA3201467CF3EFB0107AE6CEBEDF1056D5B8CC2FBEECC8BAF774BEA14875A9AEAD1B0C41CF9F4C4FFBD3D1FB387E; AWSALB=vySUZoltIOX+iVR6i61YEliTkGbzIzVNTDepUb0uD6PnAcd8RgSJO75N76U0FONo/W6Zdv/9JwnAP8k5nUYjXBUK2sXk5VNgilLH0dB5F+RkFJJekbfAraau4sRh; AWSALBCORS=vySUZoltIOX+iVR6i61YEliTkGbzIzVNTDepUb0uD6PnAcd8RgSJO75N76U0FONo/W6Zdv/9JwnAP8k5nUYjXBUK2sXk5VNgilLH0dB5F+RkFJJekbfAraau4sRh')
    onecreeper.get_info_about()
    
    # 使用TaskBuilder示例
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
            .build())
    
    onecreeper.add_task(task1)
    onecreeper.add_task(task2)
