# OpenCode Controller Skill - 测试记录

## 2026-02-04 测试

### 已修复的 Bug

| 问题 | 修复 |
|------|------|
| `$Host` 变量冲突 | 重命名为 `$ServerHost` |
| `Start-Process` 无法直接启动 npm 脚本 | 使用 `cmd /c opencode serve` |
| `Export-ModuleMember` 警告 | 改为注释说明 |

### 测试成功的功能

- ✅ 服务器启动 (`opencode serve`)
- ✅ 健康检查 API (`/global/health`)
- ✅ 创建会话 API (`POST /session`)
- ✅ 发送消息 API (`POST /session/{id}/message`)
- ✅ 获取消息 API (`GET /session/{id}/message`)
- ✅ 列出 Agents (`GET /agent`)

### 已解决的问题 ✅

**问题：消息未被处理，无 assistant 回复**

**原因：** 发送消息时必须指定 `agent` 参数

**解决方案：**
```powershell
# ❌ 错误方式 - 不指定 agent
$body = @{ parts = @(@{ type = "text"; text = "List files" }) }

# ✅ 正确方式 - 指定 agent = "general"
$body = @{ 
    parts = @(@{ type = "text"; text = "List files" })
    agent = "general"  # <-- 关键参数
}
```

**可用的 Agents：**
- `general` - 通用任务（推荐）
- `chief` - 复杂协调任务
- `explore` - 代码库探索
- `deputy`, `researcher`, `writer`, `editor` - 专业子代理

### 发现的限制

**目录访问限制：**
OpenCode 只能访问以下目录：
- `D:\newtype-profile`
- `C:\Users\admin\Documents`
- `C:\Users\admin\Projects`

### 测试成功的任务

| 测试 | 结果 | 说明 |
|------|------|------|
| 创建文件 | ✅ | `general` agent 成功创建 |
| 写入内容 | ✅ | 内容正确写入 |
| 代码编辑 | ✅ | 读取、修改、保存 Python 文件 |
| 同步发送 + 等待 | ✅ | `Send-OpenCodeMessage` + `Wait-OpenCodeCompletion` |
| 多步骤任务 | ✅ | 读取→修改→保存完整流程 |

### 发现的问题

1. **异步模式 `Send-OpenCodeMessageAsync`** - 发送后未触发处理
   - 可能原因：`prompt_async` 端点需要特定条件或已弃用
   - 建议：使用同步模式 (`noReply=$false`)

2. **`Get-OpenCodeMessages` 返回值异常**
   - 有时返回空数组，但实际消息存在
   - 可能原因：API 响应格式变化或分页问题

3. **消息/状态检测不一致**
   - `session/status` 端点返回空
   - 但直接查询消息端点可以获取数据

### 下一步建议

1. **检查 OpenCode 配置** - 确认是否有 serve 模式的相关配置
2. **尝试指定 agent** - 使用 `agent` 参数发送消息
3. **检查 OpenCode 日志** - 查看是否有错误信息
4. **考虑使用 web 模式** - 尝试 `opencode web` 代替 `opencode serve`

### 已知可用的替代方案

如果 serve 模式无法工作，可以考虑：
- 使用 `opencode web` 启动 Web 界面，然后通过 WebSocket API 控制
- 使用 `opencode run` 命令（虽然 Windows 上可能有 TTY 问题）
- 等待 OpenCode 官方修复或提供新的 API
