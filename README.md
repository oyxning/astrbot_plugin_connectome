# astrbot_plugin_connectome

让 AI 具备“类人脑”多尺度思考能力：连接组协同 + 海马体记忆 + 强化学习 + 时间天气感知 + 可视化 WebUI。

![Python](https://img.shields.io/badge/Python-3.13-blue) ![License](https://img.shields.io/badge/License-MIT-green) ![FastAPI](https://img.shields.io/badge/FastAPI-%F0%9F%9A%80-teal)

**概述**
- 面向 AstrBot 的插件化思考引擎，融合神经生物学与认知心理学，实现分层、可记忆、可学习的推理过程。
- 支持 WebUI 与命令行配置，参数更新持久化到 SQLite 并在思考前动态重载。

**特性**
- 多网络协同：默认模式、显著性、控制、注意、语言、视觉、听觉、感觉-运动、边缘网络。
- E/I 平衡与分层推理：能量/疲劳与昼夜相位共同决定有效步数与偏好。
- 海马体记忆与回放：基于 SQLite 的会话隔离记忆库，支持重放与睡眠巩固。
- 强化学习：对最近路径奖励，更新模块权重并持久化（`rl_weights`）。
- 时间与天气感知：自动获取本地时间/天气，注入上下文并联动昼夜/能量。
- 守护与审计：伦理守护器评估并记录审计日志（`role='audit'`）。
- WebUI：仪表化查看与编辑参数，审计列表与表单提交即时生效。
 - 指标输出：可将核心指标周期性输出到官方控制台，支持命令与配置控制。
 - LLM 提示增强：自动将 Connectome 状态与策略注入系统提示，促使模型进行更“类人”的思考与表达。

**环境要求**
- Python `3.13`
- 依赖：`networkx`、`fastapi`、`uvicorn`、`jinja2`、`python-multipart`、`requests`

**安装**
- 将本仓库放置到 AstrBot 的 `data/plugins/astrbot_plugin_connectome` 目录。
- 在插件根目录执行 `pip install -r requirements.txt` 安装依赖。

**快速开始**
- 启动 AstrBot 后，插件根据配置自动启动 WebUI。
- 在聊天中执行：
  - ` /connectome on` 启用本会话的类人脑思考模式。
  - ` /connectome think <内容>` 发起分层思考并返回结论与轨迹。
  - ` /audit` 查看守护评估审计条目。

**配置**
- 配置项由 `_conf_schema.json` 驱动，核心字段包括：
  - 基本：`enable_by_default`、`memory_db_path`、`max_memory_per_session`
  - 推理：`ei_balance`、`reasoning_depth`、`modules`、`reward_keywords`
  - 强化学习：`rl_enable`、`rl_alpha`、`rl_gamma`、`auto_reward`
  - 生物/心理/辅助系统：`neuromodulators`、`oscillation`、`plasticity`、`myelination`、`cortical_layers`、`basal_ganglia`、`cerebellum`、`hippocampus`、`attention`、`working_memory`、`learning`、`decision`、`executive`、`metacognition`、`emotion`、`motivation`、`habit`、`homeostasis`、`autonomic`、`hormones`、`circadian`、`pain_immune`、`development`、`individual`、`body_schema`、`norms`、`ethics`、`identity`
  - WebUI：`webui_enable`、`webui_host`、`webui_port`
  - 感知：`perception.enable`、`perception.time_zone`、`perception.geo_city`、`perception.geo_lat`、`perception.geo_lon`
  - 指标：`metrics.enable`、`metrics.interval`、`metrics.on_think`
  - 提示增强：`llm_hook.enable`、`llm_hook.log`

**命令**
- 思考与管理：
  - ` /connectome on|off|status|think <内容>|reward <值>`
  - ` /remember <内容>` 写入记忆；` /replay [k]` 重放；` /sleep [replay_k alpha gamma]` 睡眠巩固
  - ` /audit [limit=10]` 审计日志；` /guard on|off|status` 守护器开关；` /act <计划描述>` 行动评估
- 参数更新：
  - ` /neuromod ...`、` /wm ...`、` /policy ...`、` /emotion ...`
  - ` /homeostasis ...`、` /autonomic ...`、` /hormone ...`、` /circadian ...`
  - ` /pain ...`、` /development ...`、` /agency ...`、` /norms ...`、` /ethics ...`、` /identity ...`
- WebUI 控制：` /webui start|stop|status|open`
  - 感知系统：` /perception status|on|off|lock on|off|refresh|tz <TZ>|city <名称>|coord <lat> <lon>`
  - 模块权重：` /modules dmn=... salience=... control=... dorsal_attention=... ventral_attention=... language=... visual=... auditory=... sensorimotor=... limbic=...`
 - 指标控制：` /metrics status|start|stop|interval <秒>|once|on_think on|off`
 - 提示查看：` /prompt [last|status|on|off|clear]`

**WebUI**
- 自动启动：插件初始化时按配置启动 Uvicorn，并通过 `CONNECTOME_DB_PATH` 传递数据库路径。
- 访问：`http://127.0.0.1:8000/`
- 功能：仪表盘参数编辑、审计表格、表单保存到 SQLite `adaptive_params` 并在思考前重载。

**时间与天气感知**
- 刷新时机：引擎初始化与每次 ` /connectome think` 前自动刷新（若已锁定则跳过）。
- 联动：将本地小时映射到 `circadian_phase` 与 `sleep_pressure`，在分层步骤中加入环境上下文，并对 `homeostasis.energy` 进行轻微调制（锁定时不派生、不调制）。
- 控制：` /perception on|off` 控制是否自动刷新；` /perception lock on|off` 控制是否进行派生与时间后备（锁定后你的零值将如实展示）。
- 设置：通过命令或配置调整时区、城市或坐标。

**指标输出（官方控制台）**
- 内容：`ei_balance`、`reasoning_depth`、模块数量与各系统快照（体内平衡、自主神经、激素、昼夜、疼痛免疫）以及环境（时间/天气/坐标）。
- 配置：在 `_conf_schema.json` 中使用 `metrics.enable` 开启，`metrics.interval` 设定输出间隔秒数，`metrics.on_think` 控制是否在每次思考后追加一次输出。
- 命令：使用 ` /metrics status|start|stop|interval <秒>|once|on_think on|off` 管理运行状态与行为。

**LLM 提示增强（自动思考策略）**
- 行为：在每次向 LLM 发起请求前，插件会将 Connectome 的关键状态（能量/疲劳、昼夜相位、环境感知、模块权重 Top 等）与简洁的思考策略注入系统提示，使模型无需额外指令即可采用更贴近“人类思考”的方式组织回答。
- 策略：先澄清目标与要点；按能量/疲劳调整推理深度；参考高权重模块组织结构；输出可执行建议并标注风险/不确定性。
- 透明：该注入不改变用户输入，仅增强系统提示；如需关闭，在配置中设置 `llm_hook.enable=false`。若需在控制台观测注入事件与状态，保持 `llm_hook.log=true`（默认启用）。
- 查看最近提示：使用 ` /prompt last` 可显示最近一次发送给 AI 的系统提示（在当前钩子时刻捕获，通常包含其他插件已注入的内容）；可用 ` /prompt status|on|off|clear` 管理捕获。
- 载荷调试：使用 ` /llmhook debug on` 打印最终请求载荷预览（脱敏），确认是否确实注入到 `system_prompt`。钩子严格返回修改后的 ProviderRequest，遵循 AstrBot 官方 on_llm_request 注入格式（仅修改 `req.system_prompt`）。

**持久化与表结构**
- 记忆库：`memories(id, session_id, role, content, created_at)`
- 强化学习：`rl_weights(node, weight)`
- 参数库：`adaptive_params(key, value)`

**架构**
- 引擎：`connectome/engine.py` 使用 NetworkX 构建模块图；依据权重/EI/生理与昼夜等因素选择路径；生成分层步骤与总结。
- 系统模块：`connectome/systems/` 包含体内平衡、自主神经、激素、昼夜、疼痛免疫、发育、个体、身体图式、规范、伦理、守护器、行动评估、感知。
- WebUI：`webui/` 包含 FastAPI 应用与模板静态资源；入口 `webui.run:app`。

**故障排查**
- WebUI 启动失败：检查端口占用，修改 `webui_port` 或执行 ` /webui stop` 后重启；确认已安装 `python-multipart`。
- 天气查询失败：网络不可达或地理编码失败时自动跳过，使用 ` /perception refresh` 重试或改用坐标。
- SQLite 写入异常：在 Windows 下确认路径可写，建议使用绝对路径。

**贡献**
- 欢迎提交 Issue/PR：包括新系统模块、联动规则、WebUI 交互优化、性能与兼容性改进。
- 代码风格：保持模块化与最小侵入；避免无关更改；文档与配置需同步更新。

**许可证**
- MIT
