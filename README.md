# OpenCode Controller

[![GitHub stars](https://img.shields.io/github/stars/wumajiehechuan-lab/opencode-controller?style=flat-square)](https://github.com/wumajiehechuan-lab/opencode-controller/stargazers)
[![License](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](LICENSE)
[![PowerShell](https://img.shields.io/badge/PowerShell-5.1%2B-blue.svg?style=flat-square)](https://docs.microsoft.com/powershell/)

> **通过 HTTP API 以编程方式控制 OpenCode 的 Skill**

OpenCode Controller 是一个自动化工具，让你能够通过代码控制 OpenCode AI 助手。它解决了 Windows 上 `opencode run` 命令卡住的问题，提供稳定可靠的 HTTP API 接口。

---

## ✨ 功能特性

- 🚀 **自动服务器管理** - 自动启动、监控和重启 OpenCode HTTP 服务器
- 💬 **会话管理** - 创建、管理和删除多个 OpenCode 会话
- 📝 **任务发送** - 发送编码任务并获取结果
- 🔄 **异步支持** - 支持同步等待和异步发送模式
- 🖥️ **跨平台** - PowerShell (Windows) 和 Python 双版本
- 🔧 ** oh-my-opencode 兼容** - 支持 ultrawork 等高级模式

---

## 📦 安装

### 前置要求

- OpenCode 已安装 (`opencode --version`)
- PowerShell 5.1+ (Windows) 或 Python 3.x

### 快速开始

```powershell
# 克隆仓库
git clone https://github.com/wumajiehechuan-lab/opencode-controller.git
cd opencode-controller

# 加载 PowerShell 模块
. .\scripts\opencode_controller.ps1

# 创建控制器实例
$ctrl = New-OpenCodeController -WorkingDir "D:\newtype-profile"

# 创建会话并发送任务
$session = New-OpenCodeSession -Controller $ctrl -Title "My Task"
$response = Send-OpenCodeMessage -Controller $ctrl `
    -SessionId $session.id `
    -Message "Create a hello.txt file" `
    -Agent "general"
```

---

## 🚀 使用示例

### 示例 1: 简单的文件操作

```powershell
# 加载模块
. .\scripts\opencode_controller.ps1

# 初始化控制器
$ctrl = New-OpenCodeController -WorkingDir "D:\newtype-profile"

# 创建会话
$session = New-OpenCodeSession -Controller $ctrl -Title "File Creation"

# 发送任务（必须使用 -Agent 参数！）
$response = Send-OpenCodeMessage -Controller $ctrl `
    -SessionId $session.id `
    -Message "Create a file at D:\newtype-profile\test.txt with content 'Hello World'" `
    -Agent "general"

# 查看响应
$response.parts | Where-Object { $_.type -eq "text" } | ForEach-Object { $_.text }

# 清理
Remove-OpenCodeSession -Controller $ctrl -SessionId $session.id
```

### 示例 2: 代码编辑任务

```powershell
. .\scripts\opencode_controller.ps1

$ctrl = New-OpenCodeController -WorkingDir "D:\newtype-profile\my-project"
$session = New-OpenCodeSession -Controller $ctrl -Title "Code Refactor"

$task = @"
Read the file at D:\newtype-profile\my-project\utils.py and:
1. Add docstrings to all functions
2. Add type hints
3. Save the updated file
"@

$response = Send-OpenCodeMessage -Controller $ctrl `
    -SessionId $session.id `
    -Message $task `
    -Agent "general"

# 等待几秒让后台执行
Start-Sleep -Seconds 5

# 验证结果
if (Test-Path "D:\newtype-profile\my-project\utils.py") {
    Write-Host "✓ Task completed!"
}
```

### 示例 3: 使用 ultrawork 模式

```powershell
. .\scripts\opencode_controller.ps1

$ctrl = New-OpenCodeController -WorkingDir "D:\newtype-profile"
$session = New-OpenCodeSession -Controller $ctrl -Title "Build Web App"

$task = @"
ultrawork

Create a modern todo list web application at D:\newtype-profile\todo-app\index.html
Requirements:
- Use Tailwind CSS
- Add/delete/complete tasks
- Local storage persistence
- Responsive design
"@

$response = Send-OpenCodeMessage -Controller $ctrl `
    -SessionId $session.id `
    -Message $task `
    -Agent "general" `
    -TimeoutSec 300
```

---

## ⚠️ 重要提示

### 必须指定 Agent 参数

**这是最常见的错误！** 发送消息时必须指定 `-Agent` 参数：

```powershell
# ❌ 错误 - 消息不会被处理
Send-OpenCodeMessage -SessionId $id -Message "List files"

# ✅ 正确 - 使用 general agent
Send-OpenCodeMessage -SessionId $id -Message "List files" -Agent "general"
```

### 目录访问限制

OpenCode 只能访问以下目录：
- `D:\newtype-profile`
- `C:\Users\admin\Documents`
- `C:\Users\admin\Projects`

---

## 📚 API 文档

### 核心函数

#### `New-OpenCodeController`
创建控制器实例。

```powershell
$ctrl = New-OpenCodeController `
    -Port 4096 `                    # 服务器端口
    -ServerHost "127.0.0.1" `       # 服务器主机
    -WorkingDir "D:\newtype-profile" `  # 工作目录
    -AutoStart $true               # 自动启动服务器
```

#### `New-OpenCodeSession`
创建新会话。

```powershell
$session = New-OpenCodeSession `
    -Controller $ctrl `
    -Title "Task description"

# 返回: @{ id = "ses_xxx"; title = "..."; ... }
```

#### `Send-OpenCodeMessage`
发送消息（推荐）。

```powershell
$response = Send-OpenCodeMessage `
    -Controller $ctrl `
    -SessionId $session.id `
    -Message "Your task" `
    -Agent "general" `              # 必需！
    -TimeoutSec 120
```

#### `Remove-OpenCodeSession`
删除会话。

```powershell
Remove-OpenCodeSession -Controller $ctrl -SessionId $session.id
```

---

## 🔧 故障排除

### "Server failed to start"

```powershell
# 检查 OpenCode 安装
opencode --version

# 检查端口占用
Get-NetTCPConnection -LocalPort 4096

# 检查进程
Get-Process -Name "opencode","node"
```

### "Message not processed"

- ✅ 确保使用了 `-Agent "general"` 参数
- ✅ 检查工作目录是否在允许列表中
- ✅ 尝试更简单的任务

### "Timeout waiting for completion"

这是已知问题。建议直接验证结果：

```powershell
# 不要依赖 Wait-OpenCodeCompletion
# 而是直接检查结果
if (Test-Path "expected-output.txt") {
    Write-Host "✓ Success!"
}
```

---

## 🧪 测试记录

详细的测试记录见 [TEST_LOG.md](TEST_LOG.md)。

测试覆盖：
- ✅ 服务器启动/停止
- ✅ 会话创建/删除
- ✅ 消息发送与响应
- ✅ 文件操作
- ✅ 代码编辑任务
- ✅ oh-my-opencode 插件安装
- ✅ ultrawork 模式任务执行

---

## 📁 项目结构

```
opencode-controller/
├── SKILL.md                          # 详细文档
├── TEST_LOG.md                       # 测试记录
├── README.md                         # 本文件
├── scripts/
│   ├── opencode_controller.ps1      # PowerShell 控制器
│   ├── opencode_controller.py       # Python 控制器
│   ├── example.py                   # 使用示例
│   └── requirements.txt             # Python 依赖
└── .gitignore
```

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发流程

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 📄 许可证

[MIT](LICENSE) © wumajiehechuan-lab

---

## 🔗 相关链接

- [OpenCode 官网](https://opencode.ai)
- [OpenCode 文档](https://docs.opencode.ai)
- [oh-my-opencode 插件](https://github.com/code-yeongyu/oh-my-opencode)

---

## 💡 为什么创建这个项目？

在 Windows 上使用 `opencode run` 命令时，经常会遇到 TTY 问题导致命令卡住。OpenCode Controller 通过 HTTP API 绕过这个问题，提供稳定可靠的程序化控制方式。

同时，它让你能够：
- 从 PowerShell/Python 脚本中调用 OpenCode
- 批量处理多个任务
- 集成到自动化工作流中
- 构建自己的 AI 驱动工具

---

**用 ❤️ 和 🦞 制作**
