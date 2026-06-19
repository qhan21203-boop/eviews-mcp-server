# EViews MCP Server

通过 [Model Context Protocol (MCP)](https://modelcontextprotocol.io) 让 Claude Code / Claude Desktop / Cursor / Codex 等 AI 助手直接操控 [EViews](https://www.eviews.com) 计量经济学软件。

## 功能（22 个工具）

| 类别 | 工具 | 说明 |
|------|------|------|
| 连接 | `eviews_connect` `eviews_status` `eviews_disconnect` | 启动/连接/断开 EViews |
| 工作文件 | `eviews_create_workfile` `eviews_open_workfile` `eviews_save_workfile` `eviews_fetch` | 创建、打开、保存、读取 |
| 命令 | `eviews_run` `eviews_run_program` | 执行任意 EViews 命令/程序 |
| 数据读写 | `eviews_get_scalar` `eviews_put_scalar` `eviews_get_series` `eviews_put_series` `eviews_get_group` | 标量/序列/组 读与写 |
| 数据导入 | `eviews_import_csv` | CSV 导入（无依赖，兼容所有版本） |
| 回归分析 | `eviews_ols` | OLS 回归，自动返回系数表 |
| 方程诊断 | `eviews_eq_stats` `eviews_eq_coefficients` | R²、DW、F、系数/标准误/t 值 |
| 输出 | `eviews_freeze` `eviews_save_table` | 冻结输出为表格、保存为文本 |
| 查看 | `eviews_lookup` `eviews_show` | 查询对象类型、显示视图 |

## 环境要求

- **Windows** 系统
- **EViews 9 或更高版本**（需 COM 自动化支持）
- **32 位 Python 3.12+**（EViews COM 接口仅支持 32 位客户端）

## 快速开始（3 步）

### 步骤 1：安装 32 位 Python + 依赖

**方式 A — 自动安装（推荐）**

```powershell
# 在解压后的目录中运行
python setup.py
```

脚本会自动下载 32-bit Python 到 `./python32/`，安装 pip 和依赖（pywin32、mcp）。

**方式 B — 手动安装**

1. 从 https://www.python.org/downloads/ 下载 32-bit Python（带 "x86" 或 "win32" 标识）
2. 安装到某个目录如 `D:\python32\`
3. 安装依赖：

```powershell
D:\python32\python.exe -m pip install pywin32 mcp
```

**方式 C — 便携版**

如果你已有 32-bit Python 环境，直接安装依赖：

```powershell
pip install pywin32 mcp
```

### 步骤 2：注册 EViews COM

以**管理员身份**运行 PowerShell：

```powershell
# 找到你的 EViews 安装路径，运行：
& "C:\Program Files (x86)\EViews 9\EViews9.exe" /regserver
```

### 步骤 3：配置 MCP

在你的 AI 助手的 MCP 配置文件中添加：

**Claude Code** → 编辑 `%USERPROFILE%\.claude\mcp.json`：

```json
{
  "mcpServers": {
    "eviews": {
      "command": "D:\\python32\\python.exe",
      "args": ["D:\\eviews-mcp-server\\server.py"],
      "cwd": "D:\\eviews-mcp-server"
    }
  }
}
```

**Claude Desktop** → 编辑 `%APPDATA%\Claude\claude_desktop_config.json`，格式同上。

**Codex / Cursor** → 在设置 → MCP Servers 中添加：
- Name: `eviews`
- Command: `D:\python32\python.exe D:\eviews-mcp-server\server.py`
- Working Directory: `D:\eviews-mcp-server`

> **注意**：路径中的 `D:\\` 在 JSON 中需要双反斜杠，在设置 UI 中直接用 `D:\` 即可。

## 验证是否成功

重新启动你的 AI 助手后，输入：

> 连接 EViews

如果 agent 能成功执行 `eviews_connect` 并返回 "Connected to EViews."，就说明配置成功了。

## 使用示例

### 完整的 STIRPAT 回归分析

只需对 agent 说一句话：

> 用 EViews 做 STIRPAT 分析：连接 EViews，创建年度工作文件 1990-2022，导入 d:/data/stirpat.csv，运行 OLS 回归 lnCO2 = C + lnGDP + lnEI + lnCOAL，告诉我 R²、DW 和所有系数。

Agent 会自动调用：

1. `eviews_connect` → 连接 EViews
2. `eviews_create_workfile(page_type="a", frequency="1990 2022")` → 创建工作文件
3. `eviews_import_csv(filepath="d:/data/stirpat.csv")` → 导入数据
4. `eviews_ols(eq_name="eq1", dep_var="LNCO2", indep_vars="LNGDP LNEI LNCOAL")` → 运行回归
5. `eviews_eq_coefficients(eq_name="eq1")` → 获取系数表

### 运行任意 EViews 命令

> 对 EViews 运行：freeze(bg_test) eq1.auto(2)，然后告诉我 BG 检验结果

### 批量程序

> 用 EViews 运行这段程序：
> ```
> ' 创建变量
> series DLNCO2 = D(LNCO2)
> series ECM = resid
> series ECM1 = ECM(-1)
> ' ECM 估计
> equation eq_ecm.ls DLNCO2 C DLNGDP DLNEI DLNCOAL ECM1
> ```

## 文件说明

```
eviews-mcp-server/
├── server.py            # MCP 服务主程序（22 个工具）
├── eviews_client.py     # EViews COM 封装
├── setup.py             # 32 位 Python 环境自动安装
├── requirements.txt     # Python 依赖
├── .mcp.json.example    # MCP 配置模板
├── .gitignore
└── README.md
```

## 工作原理

```
Claude Code ──MCP stdio──> server.py ──COM──> EViews.Manager.9
                                                  │
                                             32 位 COM 桥接
                                                  │
                                             EViews 应用程序
```

EViews COM 接口是 32 位的，所以必须用 32 位 Python 作为桥接层。MCP Server 通过 `pywin32` 的 COM 自动化向 EViews 发送命令并读取结果。

## 常见问题

**Q: 提示 "EViews.Manager.9" 找不到？**
A: 以管理员身份运行 EViews 安装目录下的 `EViews9.exe /regserver` 注册 COM。

**Q: 32 位 Python 选哪个？**
A: 必须是标有 "x86" 或 "win32" 的安装包，不能是 "x64" 或 "ARM64"。推荐 Python 3.12。

**Q: 能用 64 位 Python 吗？**
A: 不行。EViews 9 的 COM 接口是 32 位，必须用 32 位 Python 调用。

**Q: 支持 EViews 12/13 吗？**
A: 支持。如有版本号问题，编辑 `eviews_client.py` 中的 `EnsureDispatch("EViews.Manager.9")` 改为对应版本号。

## License

MIT
