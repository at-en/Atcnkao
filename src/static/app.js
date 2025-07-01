// 全局变量
let currentUser = null;
let currentExam = null;
let examQuestions = [];
let currentQuestionIndex = 0;
let userAnswers = {};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    checkLoginStatus();
    setupEventListeners();
});

// 设置事件监听器
function setupEventListeners() {
    // 登录表单
    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    
    // 个人资料表单
    document.getElementById('profileForm').addEventListener('submit', handleUpdateProfile);
    
    // 修改密码表单
    document.getElementById('changePasswordForm').addEventListener('submit', handleChangePassword);
    
    // 导入表单
    document.getElementById('importForm').addEventListener('submit', handleImport);
}

// 检查登录状态
async function checkLoginStatus() {
    try {
        const response = await fetch('/api/auth/profile');
        if (response.ok) {
            const data = await response.json();
            currentUser = data.user;
            updateNavigation();
        }
    } catch (error) {
        console.error('检查登录状态失败:', error);
    }
}

// 更新导航栏
function updateNavigation() {
    if (currentUser) {
        document.getElementById('loginNav').style.display = 'none';
        document.getElementById('userNav').style.display = 'block';
        document.getElementById('examNav').style.display = 'block';
        document.getElementById('wrongQuestionsNav').style.display = 'block';
        document.getElementById('historyNav').style.display = 'block';
        
        if (currentUser.role === 'ADMIN') {
            document.getElementById('adminNav').style.display = 'block';
        }
        
        document.getElementById('usernameDisplay').textContent = currentUser.username;
    } else {
        document.getElementById('loginNav').style.display = 'block';
        document.getElementById('userNav').style.display = 'none';
        document.getElementById('examNav').style.display = 'none';
        document.getElementById('wrongQuestionsNav').style.display = 'none';
        document.getElementById('historyNav').style.display = 'none';
        document.getElementById('adminNav').style.display = 'none';
    }
}

// 显示页面
function showPage(pageId) {
    // 隐藏所有页面
    const pages = document.querySelectorAll('.page');
    pages.forEach(page => page.style.display = 'none');
    
    // 显示指定页面
    document.getElementById(pageId).style.display = 'block';
}

// 页面导航函数
function showHome() {
    showPage('homePage');
}

function showLogin() {
    showPage('loginPage');
}

function showProfile() {
    if (!currentUser) {
        showToast('请先登录', 'warning');
        showLogin();
        return;
    }
    showPage('profilePage');
    loadUserProfile();
}

function showChangePassword() {
    if (!currentUser) {
        showToast('请先登录', 'warning');
        showLogin();
        return;
    }
    showPage('changePasswordPage');
    // 清空表单
    document.getElementById('changePasswordForm').reset();
}

function showExam() {
    if (!currentUser) {
        showToast('请先登录', 'warning');
        showLogin();
        return;
    }
    showPage('examPage');
    document.getElementById('examStart').style.display = 'block';
    document.getElementById('examContent').style.display = 'none';
}

function showWrongQuestions() {
    if (!currentUser) {
        showToast('请先登录', 'warning');
        showLogin();
        return;
    }
    showPage('wrongQuestionsPage');
    loadWrongQuestions();
}

function showHistory() {
    if (!currentUser) {
        showToast('请先登录', 'warning');
        showLogin();
        return;
    }
    showPage('historyPage');
    loadExamHistory();
}

function showAdmin() {
    if (!currentUser || currentUser.role !== 'ADMIN') {
        showToast('需要管理员权限', 'error');
        return;
    }
    showPage('adminPage');
    loadQuestionStats();
    
    // 监听选项卡切换
    const tabs = document.querySelectorAll('#adminTabs button[data-bs-toggle="tab"]');
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(e) {
            const target = e.target.getAttribute('data-bs-target');
            if (target === '#users') {
                loadUsersList();
            } else if (target === '#questions') {
                loadQuestionsList();
            }
        });
    });
}

// 登录处理
async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentUser = data.user;
            updateNavigation();
            showToast('登录成功', 'success');
            showHome();
        } else {
            showToast(data.error || '登录失败', 'error');
        }
    } catch (error) {
        showToast('网络错误', 'error');
    }
}

// 加载用户资料
async function loadUserProfile() {
    try {
        const response = await fetch('/api/users/profile');
        if (response.ok) {
            const data = await response.json();
            const user = data;
            
            document.getElementById('profileUsername').value = user.username || '';
            document.getElementById('profileEmail').value = user.email || '';
            document.getElementById('profileRole').value = user.role === 'ADMIN' ? '管理员' : '普通用户';
            document.getElementById('profileCreated').value = user.created_at ? 
                new Date(user.created_at).toLocaleString() : '';
        } else {
            showToast('加载用户资料失败', 'error');
        }
    } catch (error) {
        showToast('网络错误', 'error');
    }
}

// 更新用户资料
async function handleUpdateProfile(event) {
    event.preventDefault();
    
    const username = document.getElementById('profileUsername').value;
    const email = document.getElementById('profileEmail').value;
    
    try {
        const response = await fetch(`/api/users/${currentUser.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, email }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentUser.username = username;
            currentUser.email = email;
            updateNavigation();
            showToast('个人资料更新成功', 'success');
        } else {
            showToast(data.error || '更新失败', 'error');
        }
    } catch (error) {
        showToast('网络错误', 'error');
    }
}

// 修改密码
async function handleChangePassword(event) {
    event.preventDefault();
    
    const oldPassword = document.getElementById('oldPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmNewPassword = document.getElementById('confirmNewPassword').value;
    
    if (newPassword !== confirmNewPassword) {
        showToast('两次输入的新密码不一致', 'error');
        return;
    }
    
    if (newPassword.length < 6) {
        showToast('新密码长度至少6位', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/users/change-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('密码修改成功', 'success');
            document.getElementById('changePasswordForm').reset();
            showHome();
        } else {
            showToast(data.error || '密码修改失败', 'error');
        }
    } catch (error) {
        showToast('网络错误', 'error');
    }
}

// 加载用户列表
async function loadUsersList() {
    try {
        const response = await fetch('/api/users?page=1&per_page=20');
        if (response.ok) {
            const data = await response.json();
            displayUsersList(data.users);
        } else {
            showToast('加载用户列表失败', 'error');
        }
    } catch (error) {
        showToast('网络错误', 'error');
    }
}

// 显示用户列表
function displayUsersList(users) {
    const container = document.getElementById('usersList');
    
    if (users.length === 0) {
        container.innerHTML = '<div class="text-center text-muted">暂无用户</div>';
        return;
    }
    
    const html = `
        <div class="table-responsive">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>用户名</th>
                        <th>邮箱</th>
                        <th>角色</th>
                        <th>注册时间</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    ${users.map(user => `
                        <tr>
                            <td>${user.id}</td>
                            <td>${user.username}</td>
                            <td>${user.email || '-'}</td>
                            <td>
                                <span class="badge ${user.role === 'ADMIN' ? 'bg-danger' : 'bg-primary'}">
                                    ${user.role === 'ADMIN' ? '管理员' : '普通用户'}
                                </span>
                            </td>
                            <td>${user.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}</td>
                            <td>
                                <button class="btn btn-sm btn-outline-primary me-1" onclick="resetUserPassword(${user.id})">
                                    <i class="bi bi-key"></i>
                                </button>
                                ${user.id !== currentUser.id ? `
                                    <button class="btn btn-sm btn-outline-danger" onclick="deleteUser(${user.id})">
                                        <i class="bi bi-trash"></i>
                                    </button>
                                ` : ''}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

// 显示创建用户对话框
function showCreateUser() {
    const modal = new bootstrap.Modal(document.getElementById('createUserModal'));
    modal.show();
    document.getElementById('createUserForm').reset();
}

// 创建用户
async function createUser() {
    const username = document.getElementById('newUsername').value;
    const email = document.getElementById('newEmail').value;
    const password = document.getElementById('newPassword').value;
    const role = document.getElementById('newRole').value;
    
    if (!username || !password) {
        showToast('用户名和密码不能为空', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, email, password, role }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('用户创建成功', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('createUserModal'));
            modal.hide();
            loadUsersList();
        } else {
            showToast(data.error || '创建用户失败', 'error');
        }
    } catch (error) {
        showToast('网络错误', 'error');
    }
}

// 重置用户密码
async function resetUserPassword(userId) {
    const newPassword = prompt('请输入新密码:');
    if (!newPassword) return;
    
    if (newPassword.length < 6) {
        showToast('密码长度至少6位', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/users/${userId}/reset-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ new_password: newPassword }),
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('密码重置成功', 'success');
        } else {
            showToast(data.error || '密码重置失败', 'error');
        }
    } catch (error) {
        showToast('网络错误', 'error');
    }
}

// 删除用户
async function deleteUser(userId) {
    if (!confirm('确定要删除这个用户吗？此操作不可撤销！')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/users/${userId}`, {
            method: 'DELETE',
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('用户删除成功', 'success');
            loadUsersList();
        } else {
            showToast(data.error || '删除失败', 'error');
        }
    } catch (error) {
        showToast('网络错误', 'error');
    }
}

// 加载题目列表
async function loadQuestionsList() {
    try {
        const response = await fetch('/api/questions?page=1&per_page=20');
        if (response.ok) {
            const data = await response.json();
            displayQuestionsList(data.questions);
        } else {
            showToast('加载题目列表失败', 'error');
        }
    } catch (error) {
        showToast('网络错误', 'error');
    }
}

// 显示题目列表
function displayQuestionsList(questions) {
    const container = document.getElementById('questionsList');
    
    if (questions.length === 0) {
        container.innerHTML = '<div class="text-center text-muted">暂无题目</div>';
        return;
    }
    
    const html = questions.map(question => `
        <div class="card mb-3">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="d-flex align-items-center mb-2">
                            <span class="badge bg-info me-2">${getQuestionTypeText(question.question_type)}</span>
                            <small class="text-muted">ID: ${question.id}</small>
                        </div>
                        <h6 class="card-title">${question.question_text}</h6>
                        ${question.option_a ? `<p class="mb-1"><small>A. ${question.option_a}</small></p>` : ''}
                        ${question.option_b ? `<p class="mb-1"><small>B. ${question.option_b}</small></p>` : ''}
                        ${question.option_c ? `<p class="mb-1"><small>C. ${question.option_c}</small></p>` : ''}
                        ${question.option_d ? `<p class="mb-1"><small>D. ${question.option_d}</small></p>` : ''}
                        <p class="mb-0"><strong>正确答案：</strong>${question.correct_answer}</p>
                    </div>
                    <div class="ms-3">
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteQuestion(${question.id})">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

// 搜索题目
async function searchQuestions() {
    const search = document.getElementById('questionSearch').value;
    try {
        const response = await fetch(`/api/questions?search=${encodeURIComponent(search)}&page=1&per_page=20`);
        if (response.ok) {
            const data = await response.json();
            displayQuestionsList(data.questions);
        } else {
            showToast('搜索失败', 'error');
        }
    } catch (error) {
        showToast('网络错误', 'error');
    }
}

// 删除题目
async function deleteQuestion(questionId) {
    if (!confirm('确定要删除这道题目吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/questions/${questionId}`, {
            method: 'DELETE',
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('题目删除成功', 'success');
            loadQuestionsList();
            loadQuestionStats();
        } else {
            showToast(data.error || '删除失败', 'error');
        }
    } catch (error) {
        showToast('网络错误', 'error');
    }
}

// 清空题库
async function clearQuestions() {
    if (!confirm('确定要清空整个题库吗？此操作不可撤销！')) {
        return;
    }
    
    try {
        const response = await fetch('/api/admin/questions/clear', {
            method: 'POST',
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message, 'success');
            loadQuestionsList();
            loadQuestionStats();
        } else {
            showToast(data.error || '清空失败', 'error');
        }
    } catch (error) {
        showToast('网络错误', 'error');
    }
}

// 退出登录
async function logout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
        currentUser = null;
        updateNavigation();
        showToast('已退出登录', 'success');
        showHome();
    } catch (error) {
        showToast('退出登录失败', 'error');
    }
}

// 开始考试
async function startExam() {
    try {
        const response = await fetch('/api/questions/random');
        const data = await response.json();
        
        if (response.ok) {
            examQuestions = data.questions;
            currentQuestionIndex = 0;
            userAnswers = {};
            
            document.getElementById('examStart').style.display = 'none';
            document.getElementById('examContent').style.display = 'block';
            document.getElementById('totalQuestions').textContent = examQuestions.length;
            
            displayQuestion();
        } else {
            showToast(data.error || '开始考试失败', 'error');
        }
    } catch (error) {
        showToast('网络错误', 'error');
    }
}

// 显示题目
function displayQuestion() {
    if (currentQuestionIndex >= examQuestions.length) return;
    
    const question = examQuestions[currentQuestionIndex];
    const container = document.getElementById('questionContainer');
    
    document.getElementById('currentQuestion').textContent = currentQuestionIndex + 1;
    
    let optionsHtml = '';
    const inputType = question.question_type === 'multiple' ? 'checkbox' : 'radio';
    const inputName = `question_${question.id}`;
    
    if (question.question_type === 'judge') {
        optionsHtml = `
            <div class="option-item" onclick="selectOption(this, '正确')">
                <input type="radio" name="${inputName}" value="正确" id="${inputName}_true">
                <label for="${inputName}_true">正确</label>
            </div>
            <div class="option-item" onclick="selectOption(this, '错误')">
                <input type="radio" name="${inputName}" value="错误" id="${inputName}_false">
                <label for="${inputName}_false">错误</label>
            </div>
        `;
    } else {
        ['A', 'B', 'C', 'D'].forEach(option => {
            const optionText = question[`option_${option.toLowerCase()}`];
            if (optionText) {
                optionsHtml += `
                    <div class="option-item" onclick="selectOption(this, '${option}')">
                        <input type="${inputType}" name="${inputName}" value="${option}" id="${inputName}_${option}">
                        <label for="${inputName}_${option}">${option}. ${optionText}</label>
                    </div>
                `;
            }
        });
    }
    
    container.innerHTML = `
        <div class="question-card">
            <div class="question-type-badge badge bg-info">${getQuestionTypeText(question.question_type)}</div>
            <h5 class="mb-3">${question.question_text}</h5>
            <div class="options">
                ${optionsHtml}
            </div>
        </div>
    `;
    
    // 恢复之前的答案
    if (userAnswers[question.id]) {
        const answers = Array.isArray(userAnswers[question.id]) ? userAnswers[question.id] : [userAnswers[question.id]];
        answers.forEach(answer => {
            const input = document.querySelector(`input[name="${inputName}"][value="${answer}"]`);
            if (input) {
                input.checked = true;
                input.closest('.option-item').classList.add('selected');
            }
        });
    }
    
    // 更新按钮状态
    document.getElementById('prevBtn').disabled = currentQuestionIndex === 0;
    document.getElementById('nextBtn').style.display = currentQuestionIndex === examQuestions.length - 1 ? 'none' : 'block';
    document.getElementById('submitBtn').style.display = currentQuestionIndex === examQuestions.length - 1 ? 'block' : 'none';
}

// 选择选项
function selectOption(element, value) {
    const question = examQuestions[currentQuestionIndex];
    const inputName = `question_${question.id}`;
    const input = element.querySelector('input');
    
    if (question.question_type === 'multiple') {
        // 多选题
        input.checked = !input.checked;
        element.classList.toggle('selected');
        
        // 更新答案
        if (!userAnswers[question.id]) {
            userAnswers[question.id] = [];
        }
        
        if (input.checked) {
            if (!userAnswers[question.id].includes(value)) {
                userAnswers[question.id].push(value);
            }
        } else {
            userAnswers[question.id] = userAnswers[question.id].filter(v => v !== value);
        }
    } else {
        // 单选题和判断题
        const allOptions = document.querySelectorAll(`input[name="${inputName}"]`);
        allOptions.forEach(opt => {
            opt.checked = false;
            opt.closest('.option-item').classList.remove('selected');
        });
        
        input.checked = true;
        element.classList.add('selected');
        userAnswers[question.id] = value;
    }
}

// 上一题
function previousQuestion() {
    if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        displayQuestion();
    }
}

// 下一题
function nextQuestion() {
    if (currentQuestionIndex < examQuestions.length - 1) {
        currentQuestionIndex++;
        displayQuestion();
    }
}

// 提交考试
async function submitExam() {
    if (!confirm('确定要提交考试吗？提交后无法修改答案。')) {
        return;
    }
    
    // 计算得分（简单的客户端计算）
    let correctCount = 0;
    examQuestions.forEach(question => {
        const userAnswer = userAnswers[question.id];
        if (userAnswer) {
            const answerStr = Array.isArray(userAnswer) ? userAnswer.sort().join(',') : userAnswer;
            const correctStr = question.correct_answer;
            if (answerStr === correctStr) {
                correctCount++;
            }
        }
    });
    
    const score = (correctCount / examQuestions.length) * 100;
    
    showToast(`考试完成！得分：${score.toFixed(1)}分`, 'success');
    showExamResult({ score, correct_count: correctCount, total_questions: examQuestions.length });
}

// 显示考试结果
function showExamResult(result) {
    const container = document.getElementById('questionContainer');
    container.innerHTML = `
        <div class="text-center">
            <h2 class="text-primary mb-4">考试完成</h2>
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body">
                            <h3 class="card-title">考试成绩</h3>
                            <div class="score-badge badge bg-primary mb-3 fs-3">${result.score.toFixed(1)}分</div>
                            <p>正确题数：${result.correct_count} / ${result.total_questions}</p>
                            <p>正确率：${((result.correct_count / result.total_questions) * 100).toFixed(1)}%</p>
                            <div class="mt-4">
                                <button class="btn btn-primary me-2" onclick="showExam()">再次考试</button>
                                <button class="btn btn-outline-primary" onclick="showHome()">返回首页</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('prevBtn').style.display = 'none';
    document.getElementById('nextBtn').style.display = 'none';
    document.getElementById('submitBtn').style.display = 'none';
}

// 加载错题本
async function loadWrongQuestions() {
    // 这里暂时显示模拟数据
    const container = document.getElementById('wrongQuestionsList');
    container.innerHTML = '<div class="text-center text-muted">错题本功能开发中...</div>';
}

// 加载考试记录
async function loadExamHistory() {
    // 这里暂时显示模拟数据
    const container = document.getElementById('examHistoryList');
    container.innerHTML = '<div class="text-center text-muted">考试记录功能开发中...</div>';
}

// 处理题库导入
async function handleImport(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('excelFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showToast('请选择Excel文件', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/admin/import-excel', {
            method: 'POST',
            body: formData,
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message, 'success');
            updateImportLog(data);
            loadQuestionStats();
            fileInput.value = '';
        } else {
            showToast(data.error || '导入失败', 'error');
        }
    } catch (error) {
        showToast('网络错误', 'error');
    }
}

// 更新导入日志
function updateImportLog(data) {
    const container = document.getElementById('importLog');
    const time = new Date().toLocaleString();
    const logEntry = `
        <div class="mb-2">
            <div class="d-flex justify-content-between">
                <span>${time}</span>
                <span class="badge bg-success">${data.imported_count}题</span>
            </div>
            ${data.sheets_processed ? `<small class="text-muted">${data.sheets_processed.join(', ')}</small>` : ''}
        </div>
    `;
    
    if (container.innerHTML.includes('暂无导入记录')) {
        container.innerHTML = logEntry;
    } else {
        container.insertAdjacentHTML('afterbegin', logEntry);
    }
}

// 加载题库统计
async function loadQuestionStats() {
    try {
        const response = await fetch('/api/admin/questions/stats');
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('totalQuestions').textContent = data.total;
            document.getElementById('singleQuestions').textContent = data.single;
            document.getElementById('multipleQuestions').textContent = data.multiple;
            document.getElementById('judgeQuestions').textContent = data.judge;
        }
    } catch (error) {
        console.error('加载题库统计失败:', error);
    }
}

// 获取题型文本
function getQuestionTypeText(type) {
    const types = {
        'single': '单选题',
        'multiple': '多选题',
        'judge': '判断题'
    };
    return types[type] || '未知';
}

// 显示提示消息
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    
    // 设置消息内容
    toastMessage.textContent = message;
    
    // 设置样式
    toast.className = 'toast show';
    if (type === 'success') {
        toast.classList.add('text-bg-success');
    } else if (type === 'error') {
        toast.classList.add('text-bg-danger');
    } else if (type === 'warning') {
        toast.classList.add('text-bg-warning');
    } else {
        toast.classList.add('text-bg-info');
    }
    
    // 自动隐藏
    setTimeout(() => {
        toast.classList.remove('show');
        toast.className = 'toast';
    }, 3000);
}

