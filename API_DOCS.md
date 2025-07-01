# 密评考试题库系统 - API文档

## 概述

本文档描述了密评考试题库系统的RESTful API接口。所有API都基于HTTP协议，使用JSON格式进行数据交换。

### 基础信息
- **Base URL**: `http://localhost:5000/api`
- **Content-Type**: `application/json`
- **认证方式**: Session-based认证

### 响应格式
```json
{
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

### 错误响应
```json
{
  "success": false,
  "message": "错误描述",
  "error_code": "ERROR_CODE"
}
```

## 认证接口

### 用户注册
**POST** `/api/auth/register`

注册新用户账户。

**请求参数:**
```json
{
  "username": "string",     // 用户名，3-20字符
  "email": "string",        // 邮箱地址
  "password": "string"      // 密码，至少6位
}
```

**响应示例:**
```json
{
  "success": true,
  "message": "注册成功",
  "data": {
    "user_id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "role": "USER"
  }
}
```

**错误码:**
- `USERNAME_EXISTS`: 用户名已存在
- `EMAIL_EXISTS`: 邮箱已存在
- `INVALID_INPUT`: 输入参数无效

### 用户登录
**POST** `/api/auth/login`

用户登录系统。

**请求参数:**
```json
{
  "username": "string",     // 用户名
  "password": "string"      // 密码
}
```

**响应示例:**
```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "user_id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "role": "USER",
    "last_login": "2025-07-01T10:30:00Z"
  }
}
```

**错误码:**
- `INVALID_CREDENTIALS`: 用户名或密码错误
- `USER_NOT_FOUND`: 用户不存在

### 用户登出
**POST** `/api/auth/logout`

用户登出系统。

**响应示例:**
```json
{
  "success": true,
  "message": "登出成功"
}
```

### 获取用户信息
**GET** `/api/auth/profile`

获取当前登录用户的信息。

**响应示例:**
```json
{
  "success": true,
  "data": {
    "user_id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "role": "USER",
    "created_at": "2025-07-01T10:00:00Z",
    "last_login": "2025-07-01T10:30:00Z"
  }
}
```

**错误码:**
- `UNAUTHORIZED`: 未登录或会话过期

## 题目管理接口

### 获取题目列表
**GET** `/api/questions`

获取题目列表，支持分页和筛选。

**查询参数:**
- `page`: 页码，默认1
- `per_page`: 每页数量，默认20
- `type`: 题型筛选（SINGLE_CHOICE, MULTIPLE_CHOICE, TRUE_FALSE）
- `search`: 搜索关键词

**响应示例:**
```json
{
  "success": true,
  "data": {
    "questions": [
      {
        "id": 1,
        "content": "题目内容",
        "type": "SINGLE_CHOICE",
        "options": ["选项A", "选项B", "选项C", "选项D"],
        "correct_answer": "A",
        "created_at": "2025-07-01T10:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 100,
      "pages": 5
    }
  }
}
```

### 添加题目
**POST** `/api/questions`

添加新题目（需要管理员权限）。

**请求参数:**
```json
{
  "content": "string",              // 题目内容
  "type": "SINGLE_CHOICE",         // 题型
  "options": ["A", "B", "C", "D"], // 选项数组
  "correct_answer": "A"            // 正确答案
}
```

**响应示例:**
```json
{
  "success": true,
  "message": "题目添加成功",
  "data": {
    "id": 1,
    "content": "题目内容",
    "type": "SINGLE_CHOICE",
    "options": ["选项A", "选项B", "选项C", "选项D"],
    "correct_answer": "A"
  }
}
```

### 更新题目
**PUT** `/api/questions/{id}`

更新指定题目（需要管理员权限）。

**请求参数:**
```json
{
  "content": "string",              // 题目内容
  "type": "SINGLE_CHOICE",         // 题型
  "options": ["A", "B", "C", "D"], // 选项数组
  "correct_answer": "A"            // 正确答案
}
```

### 删除题目
**DELETE** `/api/questions/{id}`

删除指定题目（需要管理员权限）。

**响应示例:**
```json
{
  "success": true,
  "message": "题目删除成功"
}
```

### Excel题库导入
**POST** `/api/admin/import-excel`

从Excel文件导入题库（需要管理员权限）。

**请求参数:**
- Content-Type: `multipart/form-data`
- 文件字段: `file`

**响应示例:**
```json
{
  "success": true,
  "message": "题库导入成功",
  "data": {
    "imported_count": 150,
    "skipped_count": 5,
    "error_count": 2
  }
}
```

## 考试接口

### 开始考试
**POST** `/api/exam/start`

开始新的考试，系统会随机抽取题目。

**响应示例:**
```json
{
  "success": true,
  "message": "考试开始",
  "data": {
    "exam_id": 1,
    "total_questions": 140,
    "question_types": {
      "MULTIPLE_CHOICE": 60,
      "SINGLE_CHOICE": 60,
      "TRUE_FALSE": 20
    },
    "start_time": "2025-07-01T10:30:00Z"
  }
}
```

### 获取考试题目
**GET** `/api/exam/{exam_id}/questions`

获取指定考试的题目列表。

**查询参数:**
- `page`: 页码，默认1

**响应示例:**
```json
{
  "success": true,
  "data": {
    "exam_id": 1,
    "current_page": 1,
    "total_questions": 140,
    "question": {
      "id": 1,
      "content": "题目内容",
      "type": "SINGLE_CHOICE",
      "options": ["选项A", "选项B", "选项C", "选项D"]
    },
    "user_answer": null,
    "answered_count": 0
  }
}
```

### 提交答案
**POST** `/api/exam/{exam_id}/answer`

提交单题答案。

**请求参数:**
```json
{
  "question_id": 1,
  "answer": "A"  // 单选题为单个选项，多选题为选项数组
}
```

**响应示例:**
```json
{
  "success": true,
  "message": "答案已保存"
}
```

### 提交考试
**POST** `/api/exam/{exam_id}/submit`

提交整个考试，系统进行判分。

**响应示例:**
```json
{
  "success": true,
  "message": "考试提交成功",
  "data": {
    "exam_id": 1,
    "score": 85.5,
    "correct_count": 120,
    "total_count": 140,
    "wrong_count": 20,
    "completion_time": "2025-07-01T11:30:00Z",
    "duration_minutes": 60
  }
}
```

### 获取考试结果
**GET** `/api/exam/{exam_id}/result`

获取考试详细结果。

**响应示例:**
```json
{
  "success": true,
  "data": {
    "exam_id": 1,
    "score": 85.5,
    "correct_count": 120,
    "total_count": 140,
    "start_time": "2025-07-01T10:30:00Z",
    "end_time": "2025-07-01T11:30:00Z",
    "duration_minutes": 60,
    "question_stats": {
      "SINGLE_CHOICE": {
        "total": 60,
        "correct": 55
      },
      "MULTIPLE_CHOICE": {
        "total": 60,
        "correct": 45
      },
      "TRUE_FALSE": {
        "total": 20,
        "correct": 20
      }
    }
  }
}
```

### 获取考试记录
**GET** `/api/exams`

获取用户的考试记录列表。

**查询参数:**
- `page`: 页码，默认1
- `per_page`: 每页数量，默认10

**响应示例:**
```json
{
  "success": true,
  "data": {
    "exams": [
      {
        "id": 1,
        "score": 85.5,
        "correct_count": 120,
        "total_count": 140,
        "start_time": "2025-07-01T10:30:00Z",
        "end_time": "2025-07-01T11:30:00Z",
        "duration_minutes": 60
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total": 5,
      "pages": 1
    }
  }
}
```

## 错题本接口

### 获取错题列表
**GET** `/api/wrong-questions`

获取当前用户的错题列表。

**查询参数:**
- `type`: 题型筛选
- `mastered`: 是否已掌握（true/false）

**响应示例:**
```json
{
  "success": true,
  "data": {
    "wrong_questions": [
      {
        "id": 1,
        "question": {
          "id": 1,
          "content": "题目内容",
          "type": "SINGLE_CHOICE",
          "options": ["选项A", "选项B", "选项C", "选项D"],
          "correct_answer": "A"
        },
        "user_answer": "B",
        "wrong_count": 2,
        "mastered": false,
        "last_wrong_time": "2025-07-01T11:30:00Z"
      }
    ]
  }
}
```

### 标记错题为已掌握
**POST** `/api/wrong-questions/{id}/master`

将错题标记为已掌握。

**响应示例:**
```json
{
  "success": true,
  "message": "已标记为掌握"
}
```

### 取消掌握标记
**DELETE** `/api/wrong-questions/{id}/master`

取消错题的掌握标记。

**响应示例:**
```json
{
  "success": true,
  "message": "已取消掌握标记"
}
```

## 用户管理接口（管理员）

### 获取用户列表
**GET** `/api/admin/users`

获取所有用户列表（需要管理员权限）。

**查询参数:**
- `page`: 页码，默认1
- `per_page`: 每页数量，默认20
- `role`: 角色筛选（USER, ADMIN）

**响应示例:**
```json
{
  "success": true,
  "data": {
    "users": [
      {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "role": "USER",
        "created_at": "2025-07-01T10:00:00Z",
        "last_login": "2025-07-01T10:30:00Z",
        "exam_count": 5
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 50,
      "pages": 3
    }
  }
}
```

### 更新用户角色
**PUT** `/api/admin/users/{id}/role`

更新用户角色（需要管理员权限）。

**请求参数:**
```json
{
  "role": "ADMIN"  // USER 或 ADMIN
}
```

### 获取系统统计
**GET** `/api/admin/stats`

获取系统统计信息（需要管理员权限）。

**响应示例:**
```json
{
  "success": true,
  "data": {
    "total_users": 100,
    "total_questions": 500,
    "total_exams": 1000,
    "question_types": {
      "SINGLE_CHOICE": 200,
      "MULTIPLE_CHOICE": 200,
      "TRUE_FALSE": 100
    },
    "recent_exams": 50
  }
}
```

## 错误码说明

### 通用错误码
- `INVALID_INPUT`: 输入参数无效
- `UNAUTHORIZED`: 未授权访问
- `FORBIDDEN`: 权限不足
- `NOT_FOUND`: 资源不存在
- `INTERNAL_ERROR`: 服务器内部错误

### 认证相关错误码
- `USERNAME_EXISTS`: 用户名已存在
- `EMAIL_EXISTS`: 邮箱已存在
- `INVALID_CREDENTIALS`: 登录凭据无效
- `USER_NOT_FOUND`: 用户不存在
- `SESSION_EXPIRED`: 会话已过期

### 考试相关错误码
- `EXAM_NOT_FOUND`: 考试不存在
- `EXAM_ALREADY_SUBMITTED`: 考试已提交
- `QUESTION_NOT_FOUND`: 题目不存在
- `INVALID_ANSWER`: 答案格式无效

### 文件相关错误码
- `FILE_TOO_LARGE`: 文件过大
- `INVALID_FILE_FORMAT`: 文件格式无效
- `UPLOAD_FAILED`: 文件上传失败

## 使用示例

### JavaScript示例
```javascript
// 用户登录
async function login(username, password) {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ username, password })
  });
  
  const result = await response.json();
  if (result.success) {
    console.log('登录成功', result.data);
  } else {
    console.error('登录失败', result.message);
  }
}

// 开始考试
async function startExam() {
  const response = await fetch('/api/exam/start', {
    method: 'POST',
    credentials: 'include'
  });
  
  const result = await response.json();
  if (result.success) {
    return result.data.exam_id;
  }
}

// 获取题目
async function getQuestion(examId, page) {
  const response = await fetch(`/api/exam/${examId}/questions?page=${page}`, {
    credentials: 'include'
  });
  
  return await response.json();
}
```

### Python示例
```python
import requests

# 创建会话
session = requests.Session()

# 用户登录
def login(username, password):
    response = session.post('/api/auth/login', json={
        'username': username,
        'password': password
    })
    return response.json()

# 开始考试
def start_exam():
    response = session.post('/api/exam/start')
    return response.json()

# 提交答案
def submit_answer(exam_id, question_id, answer):
    response = session.post(f'/api/exam/{exam_id}/answer', json={
        'question_id': question_id,
        'answer': answer
    })
    return response.json()
```

## 版本信息

- **API版本**: v1.0
- **最后更新**: 2025-07-01
- **兼容性**: 向后兼容

---

**如有疑问，请联系技术支持。**

