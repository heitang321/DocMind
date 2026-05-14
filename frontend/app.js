// frontend/app.js
// 后端 API 基础 URL（开发环境）
const API_BASE = '/api/v1';

// DOM 元素
const authSection = document.getElementById('auth-section');
const appMain = document.getElementById('app-main');
const loginTab = document.getElementById('login-tab');
const registerTab = document.getElementById('register-tab');
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const loginBtn = document.getElementById('login-btn');
const registerBtn = document.getElementById('register-btn');
const uploadBtn = document.getElementById('upload-btn');
const askBtn = document.getElementById('ask-btn');
const fileInput = document.getElementById('file-input');
const questionInput = document.getElementById('question');
const answerDiv = document.getElementById('answer-text');
const sourcesDiv = document.getElementById('sources-list');
const uploadStatus = document.getElementById('upload-status');

// 辅助函数：显示消息
function showMessage(element, msg, isError = false) {
    element.innerHTML = `<span style="color:${isError ? 'red' : 'green'}">${msg}</span>`;
    setTimeout(() => element.innerHTML = '', 3000);
}

// 存储 token
function setToken(token) {
    localStorage.setItem('access_token', token);
}

function getToken() {
    return localStorage.getItem('access_token');
}

function isLoggedIn() {
    return !!getToken();
}

// 登出（可选）
function logout() {
    localStorage.removeItem('access_token');
    authSection.style.display = 'block';
    appMain.style.display = 'none';
}

// 添加认证头
function authHeaders() {
    const token = getToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// 注册
async function register(username, email, password) {
    const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password })
    });
    if (res.ok) {
        showMessage(document.getElementById('register-message'), '注册成功，请登录');
        // 切换到登录标签
        loginTab.click();
        return true;
    } else {
        const err = await res.json();
        showMessage(document.getElementById('register-message'), err.detail || '注册失败', true);
        return false;
    }
}

// 登录
async function login(username, password) {
    // 注意：登录接口使用 OAuth2 表单格式（application/x-www-form-urlencoded）
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
    });
    if (res.ok) {
        const data = await res.json();
        setToken(data.access_token);
        authSection.style.display = 'none';
        appMain.style.display = 'block';
        return true;
    } else {
        const err = await res.json();
        showMessage(document.getElementById('login-message'), err.detail || '登录失败', true);
        return false;
    }
}

// 上传文档
async function uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/documents/upload`, {
        method: 'POST',
        headers: authHeaders(),
        body: formData
    });
    if (res.ok) {
        const data = await res.json();
        uploadStatus.innerHTML = `<span style="color:green">✅ 上传成功！分块数: ${data.chunk_count}</span>`;
        setTimeout(() => uploadStatus.innerHTML = '', 3000);
    } else {
        const err = await res.json();
        uploadStatus.innerHTML = `<span style="color:red">❌ 上传失败: ${err.detail}</span>`;
    }
}

// 提问
async function askQuestion(question, topK = 5) {
    const res = await fetch(`${API_BASE}/qa/ask`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...authHeaders()
        },
        body: JSON.stringify({ question, top_k: topK })
    });
    if (res.ok) {
        const data = await res.json();
        answerDiv.innerText = data.answer || '无答案';
        // 渲染来源
        sourcesDiv.innerHTML = '';
        if (data.sources && data.sources.length) {
            data.sources.forEach(src => {
                const div = document.createElement('div');
                div.className = 'source-item';
                div.innerHTML = `<div class="source-score">相似度: ${src.score.toFixed(4)}</div>
                                 <div>${src.content.substring(0, 200)}${src.content.length > 200 ? '...' : ''}</div>`;
                sourcesDiv.appendChild(div);
            });
        } else {
            sourcesDiv.innerHTML = '<div>没有找到相关参考资料</div>';
        }
    } else {
        const err = await res.json();
        answerDiv.innerText = `错误: ${err.detail || '未知错误'}`;
    }
}

// 事件绑定
loginTab.addEventListener('click', () => {
    loginTab.classList.add('active');
    registerTab.classList.remove('active');
    loginForm.classList.add('active');
    registerForm.classList.remove('active');
});
registerTab.addEventListener('click', () => {
    registerTab.classList.add('active');
    loginTab.classList.remove('active');
    registerForm.classList.add('active');
    loginForm.classList.remove('active');
});
loginBtn.addEventListener('click', async () => {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    await login(username, password);
});
registerBtn.addEventListener('click', async () => {
    const username = document.getElementById('reg-username').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    await register(username, email, password);
});
uploadBtn.addEventListener('click', () => {
    const file = fileInput.files[0];
    if (!file) {
        uploadStatus.innerHTML = '<span style="color:red">请选择文件</span>';
        return;
    }
    uploadDocument(file);
});
askBtn.addEventListener('click', () => {
    const question = questionInput.value.trim();
    if (!question) {
        answerDiv.innerText = '请输入问题';
        return;
    }
    askQuestion(question);
});

// 检查登录状态
if (isLoggedIn()) {
    authSection.style.display = 'none';
    appMain.style.display = 'block';
} else {
    authSection.style.display = 'block';
    appMain.style.display = 'none';
}