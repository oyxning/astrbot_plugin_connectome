from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.provider import ProviderRequest
import os
import threading
import uvicorn
import json
import time

from .memory.hippocampus import Hippocampus
from .connectome.engine import ConnectomeEngine


@register(
    "astrbot_plugin_connectome",
    "LumineStory",
    "让 AI 能如人脑一般思考，具备多尺度连接组与记忆机制",
    "0.1.0",
    "https://github.com/oyxning/astrbot_plugin_connectome",
)
class ConnectomePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

        conf = getattr(context, "conf", {}) or {}
        db_path = conf.get("memory_db_path", "./connectome_memory.db")
        ei_balance = float(conf.get("ei_balance", 0.5))
        reasoning_depth = int(conf.get("reasoning_depth", 3))
        modules = conf.get("modules", {}) or {}
        # 生物学参数
        neuromodulators = conf.get("neuromodulators", {}) or {}
        oscillation = conf.get("oscillation", {}) or {}
        plasticity = conf.get("plasticity", {}) or {}
        myelination = conf.get("myelination", {}) or {}
        cortical_layers = conf.get("cortical_layers", {}) or {}
        basal_ganglia = conf.get("basal_ganglia", {}) or {}
        cerebellum = conf.get("cerebellum", {}) or {}
        hippocampus_conf = conf.get("hippocampus", {}) or {}
        # 心理学参数
        attention = conf.get("attention", {}) or {}
        working_memory = conf.get("working_memory", {}) or {}
        learning = conf.get("learning", {}) or {}
        decision = conf.get("decision", {}) or {}
        executive = conf.get("executive", {}) or {}
        metacognition = conf.get("metacognition", {}) or {}
        emotion = conf.get("emotion", {}) or {}
        motivation = conf.get("motivation", {}) or {}
        habit = conf.get("habit", {}) or {}
        guardian_conf = conf.get("guardian", {}) or {}
        # 辅助系统参数
        homeostasis = conf.get("homeostasis", {}) or {}
        autonomic = conf.get("autonomic", {}) or {}
        hormones = conf.get("hormones", {}) or {}
        circadian = conf.get("circadian", {}) or {}
        pain_immune = conf.get("pain_immune", {}) or {}
        development = conf.get("development", {}) or {}
        individual = conf.get("individual", {}) or {}
        body_schema = conf.get("body_schema", {}) or {}
        norms = conf.get("norms", {}) or {}
        ethics = conf.get("ethics", {}) or {}
        identity = conf.get("identity", {}) or {}
        # 感知配置（时间/天气）
        perception_conf = conf.get("perception", {}) or {}
        self.perception_enable = bool(perception_conf.get("enable", True))
        # 感知锁定：关闭自动派生（昼夜/睡眠压力/能量调制）与时间后备
        self.perception_lock = bool(perception_conf.get("lock", False))
        self.time_zone = str(perception_conf.get("time_zone", "Asia/Shanghai"))
        self.geo_city = str(perception_conf.get("geo_city", "Shanghai"))
        # 坐标可选覆盖城市
        self.geo_lat = perception_conf.get("geo_lat", None)
        self.geo_lon = perception_conf.get("geo_lon", None)
        # 指标配置（官方控制台输出）
        metrics_conf = conf.get("metrics", {}) or {}
        self.metrics_enable = bool(metrics_conf.get("enable", False))
        self.metrics_interval = int(metrics_conf.get("interval", 60))
        self.metrics_on_think = bool(metrics_conf.get("on_think", True))
        self.metrics_thread = None
        self.metrics_stop = threading.Event()
        self.max_memory_per_session = int(conf.get("max_memory_per_session", 200))
        self.rl_enable = bool(conf.get("rl_enable", True))
        self.rl_alpha = float(conf.get("rl_alpha", 0.1))
        self.rl_gamma = float(conf.get("rl_gamma", 0.9))
        self.auto_reward = bool(conf.get("auto_reward", False))
        rk_conf = conf.get("reward_keywords", {}) or {}
        self.rk_positive = [s.strip() for s in str(rk_conf.get("positive", "成功,好,赞,正确")).split(",") if s.strip()]
        self.rk_negative = [s.strip() for s in str(rk_conf.get("negative", "失败,差,不行,错误")).split(",") if s.strip()]

        # LLM 提示增强（自动注入 Connectome 状态）
        llm_hook_conf = conf.get("llm_hook", {}) or {}
        self.llm_hook_enable = bool(llm_hook_conf.get("enable", True))
        self.llm_hook_log_enable = bool(llm_hook_conf.get("log", True))
        self.llm_hook_capture_enable = bool(llm_hook_conf.get("capture", True))
        self.llm_req_count = 0
        self.last_system_prompt = None
        self.last_prompt_time = None
        self.last_prompt_session = None
        logger.info(
            f"LLM Hook: enable={self.llm_hook_enable} log={self.llm_hook_log_enable} capture={self.llm_hook_capture_enable}"
        )

        # WebUI 配置
        self.webui_enable = bool(conf.get("webui_enable", True))
        self.webui_host = str(conf.get("webui_host", "127.0.0.1"))
        self.webui_port = int(conf.get("webui_port", 8000))
        self.webui_server = None
        self.webui_thread = None
        self.webui_running = False

        self.hippocampus = Hippocampus(db_path)
        # 载入自适应参数以覆盖 conf
        try:
            saved_params = self.hippocampus.load_adaptive_params()
            if saved_params:
                neuromodulators.update(saved_params.get("neuromodulators", {}))
                oscillation.update(saved_params.get("oscillation", {}))
                plasticity.update(saved_params.get("plasticity", {}))
                myelination.update(saved_params.get("myelination", {}))
                cortical_layers.update(saved_params.get("cortical_layers", {}))
                basal_ganglia.update(saved_params.get("basal_ganglia", {}))
                cerebellum.update(saved_params.get("cerebellum", {}))
                hippocampus_conf.update(saved_params.get("hippocampus", {}))
                attention.update(saved_params.get("attention", {}))
                working_memory.update(saved_params.get("working_memory", {}))
                learning.update(saved_params.get("learning", {}))
                decision.update(saved_params.get("decision", {}))
                executive.update(saved_params.get("executive", {}))
                metacognition.update(saved_params.get("metacognition", {}))
                emotion.update(saved_params.get("emotion", {}))
                motivation.update(saved_params.get("motivation", {}))
                habit.update(saved_params.get("habit", {}))
                homeostasis.update(saved_params.get("homeostasis", {}))
                autonomic.update(saved_params.get("autonomic", {}))
                hormones.update(saved_params.get("hormones", {}))
                circadian.update(saved_params.get("circadian", {}))
                pain_immune.update(saved_params.get("pain_immune", {}))
                development.update(saved_params.get("development", {}))
                individual.update(saved_params.get("individual", {}))
                body_schema.update(saved_params.get("body_schema", {}))
                norms.update(saved_params.get("norms", {}))
                ethics.update(saved_params.get("ethics", {}))
                identity.update(saved_params.get("identity", {}))
                guardian_conf.update(saved_params.get("guardian", {}))
                logger.info("Connectome: 已加载自适应参数")
        except Exception:
            pass
        self.engine = ConnectomeEngine(
            ei_balance=ei_balance,
            modules=modules,
            depth=reasoning_depth,
            neuromodulators=neuromodulators,
            oscillation=oscillation,
            plasticity=plasticity,
            myelination=myelination,
            cortical_layers=cortical_layers,
            basal_ganglia=basal_ganglia,
            cerebellum=cerebellum,
            hippocampus_conf=hippocampus_conf,
            attention=attention,
            working_memory=working_memory,
            learning=learning,
            decision=decision,
            executive=executive,
            metacognition=metacognition,
            emotion=emotion,
            motivation=motivation,
            habit=habit,
            homeostasis=homeostasis,
            autonomic=autonomic,
            hormones=hormones,
            circadian=circadian,
            pain_immune=pain_immune,
            development=development,
            individual=individual,
            body_schema=body_schema,
            norms=norms,
            ethics=ethics,
            identity=identity,
            # 守护器无需传入，但保留可扩展参数
        )
        # 加载 RL 权重，优先覆盖模块权重
        try:
            rl_weights = self.hippocampus.load_rl_weights()
            if rl_weights:
                self.engine.set_weights(rl_weights)
                logger.info("Connectome: 已加载 RL 权重覆盖模块权重")
        except Exception:
            pass

        self.enabled_sessions = set()
        self.last_paths = {}
        self.guard_enabled = bool(guardian_conf.get("enable", True))
        if conf.get("enable_by_default", False):
            logger.info("Connectome: 默认启用模式，新的会话将自动启用")

        # 初始化刷新环境感知（若未锁定）
        if self.perception_enable and not self.perception_lock:
            try:
                self.engine.refresh_perception(self.time_zone, self.geo_city if (self.geo_lat is None or self.geo_lon is None) else "", self.geo_lat, self.geo_lon)
                logger.info("Connectome: 已刷新时间/天气感知")
            except Exception:
                logger.info("Connectome: 刷新感知失败，后续思考前将再次尝试")

        # 启动 WebUI（根据插件配置）
        try:
            os.environ["CONNECTOME_DB_PATH"] = db_path
        except Exception:
            pass
        if self.webui_enable and not self.webui_running:
            try:
                self._start_webui()
                logger.info(f"Connectome WebUI: 已启动 http://{self.webui_host}:{self.webui_port}/")
            except Exception as e:
                logger.info(f"Connectome WebUI: 启动失败 {e}")

        # 启动指标线程（根据插件配置）
        if self.metrics_enable and not self.metrics_thread:
            try:
                self._start_metrics()
                logger.info(f"Connectome Metrics: 已启动，间隔 {self.metrics_interval}s")
            except Exception as e:
                logger.info(f"Connectome Metrics: 启动失败 {e}")

    def _compose_connectome_prompt(self) -> str:
        # 可选刷新感知，以确保时间/天气最新（若未锁定）
        if self.perception_enable and not self.perception_lock:
            try:
                self.engine.refresh_perception(self.time_zone, self.geo_city if (self.geo_lat is None or self.geo_lon is None) else "", self.geo_lat, self.geo_lon)
            except Exception:
                pass
        m = self.engine.get_metrics() or {}
        env = m.get("env", {})
        circ = m.get("circadian", {})
        homeo = m.get("homeostasis", {})
        # 时间后备：若感知缺失则使用系统当前时间；锁定模式不使用后备
        if not self.perception_lock:
            try:
                from datetime import datetime
                local_time_fallback = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                local_time_fallback = None
            local_time_used = env.get("local_time") or local_time_fallback
        else:
            local_time_used = env.get("local_time")
        # 选取若干关键模块权重，提示思考偏好
        weights = self.engine.get_node_weights()
        top_modules = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:4]
        mod_str = ", ".join([f"{k}:{v:.2f}" for k, v in top_modules])
        # 生成简洁中文系统提示，融合上下文与思考策略
        lines = [
            "你是一个具备连接组与认知策略的思考体。",
            f"偏好模块权重（Top）：{mod_str}",
            f"状态：能量={homeo.get('energy')} 疲劳={homeo.get('fatigue')} 昼夜相位={circ.get('circadian_phase')} 睡眠压力={circ.get('sleep_pressure')}",
        ]
        if not self.perception_lock:
            lines.append(
                f"环境：时间={local_time_used}({env.get('time_zone')}) 天气={env.get('weather')} 温度={env.get('temp_c')}℃ 风速={env.get('wind_ms')}m/s 坐标=({env.get('lat')},{env.get('lon')})"
            )
        lines.extend([
            "请按以下策略组织你的回答：",
            "1. 先进行目标澄清与要点列举（简洁条列）。",
            "2. 根据当前能量/疲劳与昼夜相位，控制推理步数与细化程度。",
            "3. 借助高权重模块（如语言/控制/显著性/DMN）组织结构化输出。",
            "4. 给出可执行的建议或结论；如存在风险或不确定性，请标注提示。",
        ])
        return "\n".join([str(s) for s in lines if s is not None])

    def _start_webui(self):
        if self.webui_running:
            return
        config = uvicorn.Config(
            "astrbot_plugin_connectome.webui.run:app",
            host=self.webui_host,
            port=self.webui_port,
            log_level="info",
            reload=False,
        )
        self.webui_server = uvicorn.Server(config)
        self.webui_thread = threading.Thread(target=self.webui_server.run, daemon=True)
        self.webui_thread.start()
        self.webui_running = True

    def _stop_webui(self):
        try:
            if self.webui_server:
                self.webui_server.should_exit = True
            if self.webui_thread:
                self.webui_thread.join(timeout=3)
        except Exception:
            pass
        finally:
            self.webui_server = None
            self.webui_thread = None
            self.webui_running = False

    # ---- 指标输出 ----
    def _log_metrics(self):
        try:
            metrics = self.engine.get_metrics()
            logger.info("Connectome 指标: " + json.dumps(metrics, ensure_ascii=False))
        except Exception:
            pass

    def _metrics_loop(self):
        while not self.metrics_stop.is_set():
            try:
                self._log_metrics()
            except Exception:
                pass
            # 使用等待而不是 time.sleep 便于快速停止
            self.metrics_stop.wait(timeout=max(1, int(self.metrics_interval)))

    def _start_metrics(self):
        try:
            if self.metrics_thread and self.metrics_thread.is_alive():
                return
            self.metrics_stop.clear()
            self.metrics_thread = threading.Thread(target=self._metrics_loop, daemon=True)
            self.metrics_thread.start()
        except Exception:
            pass

    def _stop_metrics(self):
        try:
            self.metrics_stop.set()
            if self.metrics_thread:
                self.metrics_thread.join(timeout=3)
        except Exception:
            pass
        finally:
            self.metrics_thread = None

    # ---- LLM 请求钩子：自动注入系统提示 ----
    @filter.on_llm_request()
    async def _connectome_llm_prompt(self, event: AstrMessageEvent, req: ProviderRequest):
        if not self.llm_hook_enable:
            return
        try:
            prompt = self._compose_connectome_prompt()
            base = req.system_prompt if hasattr(req, "system_prompt") else ""
            new_prompt = (base or "") + ("\n" if base else "") + prompt
            # 更新 system_prompt
            try:
                req.system_prompt = new_prompt
            except Exception:
                pass

            # 若提供方不支持 system_prompt，尝试注入到消息数组
            injected_path = []
            try:
                msgs = getattr(req, "messages", None)
                if isinstance(msgs, list):
                    already_has = False
                    if len(msgs) > 0 and isinstance(msgs[0], dict):
                        c0 = str(msgs[0].get("content", ""))
                        r0 = str(msgs[0].get("role", ""))
                        if r0 == "system" and ("具备连接组与认知策略" in c0):
                            already_has = True
                    if not already_has:
                        msgs.insert(0, {"role": "system", "content": prompt})
                        injected_path.append("messages")
            except Exception:
                pass

            # 控制台提示：记录一次注入事件与关键状态
            if self.llm_hook_log_enable:
                try:
                    weights = self.engine.get_node_weights()
                    top_modules = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:3]
                    mod_str = ", ".join([f"{k}:{v:.2f}" for k, v in top_modules])
                    m = self.engine.get_metrics() or {}
                    homeo = (m.get("homeostasis") or {})
                    circ = (m.get("circadian") or {})
                    env = (m.get("env") or {})
                    energy = homeo.get("energy")
                    fatigue = homeo.get("fatigue")
                    phase = circ.get("circadian_phase")
                    if not self.perception_lock:
                        try:
                            from datetime import datetime
                            local_time = env.get("local_time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        except Exception:
                            local_time = env.get("local_time")
                    else:
                        local_time = env.get("local_time")
                    self.llm_req_count += 1
                    logger.info(
                        f"[DEBUG-ConnectomePrompt] 注入系统提示: req={self.llm_req_count}, mods={mod_str}, "
                        f"energy={energy}, fatigue={fatigue}, phase={phase}, time={local_time}, path={'system' if new_prompt else ''}{'|'+('|'.join(injected_path)) if injected_path else ''}"
                    )
                except Exception:
                    pass

            # 捕获最终（当前钩子时刻）system_prompt，便于回显
            if self.llm_hook_capture_enable:
                try:
                    self.last_system_prompt = req.system_prompt
                    try:
                        from datetime import datetime
                        self.last_prompt_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        self.last_prompt_time = None
                    try:
                        self.last_prompt_session = event.message_obj.session_id
                    except Exception:
                        self.last_prompt_session = None
                except Exception:
                    pass
        except Exception:
            # 安全兜底，不影响默认流程
            return

    @filter.command("prompt")
    async def prompt_cmd(self, event: AstrMessageEvent):
        """查看最近一次发送给 AI 的系统提示：/prompt [last|status|on|off|clear]
        - last: 显示最后一次捕获的系统提示
        - status: 查看捕获开关与最近一次捕获时间/会话
        - on/off: 开启或关闭提示捕获
        - clear: 清空已捕获的提示
        """
        try:
            parts = (event.message_str or "").strip().split()
            sub = parts[1].lower() if len(parts) > 1 else "last"
            if sub == "on":
                self.llm_hook_capture_enable = True
                yield event.plain_result("提示捕获功能已开启")
                return
            if sub == "off":
                self.llm_hook_capture_enable = False
                yield event.plain_result("提示捕获功能已关闭")
                return
            if sub == "clear":
                self.last_system_prompt = None
                self.last_prompt_time = None
                self.last_prompt_session = None
                yield event.plain_result("已清空最近提示记录")
                return
            if sub == "status":
                status = "开启" if self.llm_hook_capture_enable else "关闭"
                info = f"状态: {status}\n最近捕获时间: {self.last_prompt_time or '无'}\n最近会话: {self.last_prompt_session or '无'}"
                yield event.plain_result(info)
                return
            # 默认 last
            if not self.last_system_prompt:
                yield event.plain_result("暂无捕获的系统提示。请先与 AI 进行一次对话以生成提示。")
                return
            header = f"[最近系统提示] 时间={self.last_prompt_time or '未知'} 会话={self.last_prompt_session or '未知'}"
            yield event.plain_result(f"{header}\n\n{self.last_system_prompt}")
        except Exception as e:
            yield event.plain_result(f"执行失败: {e}")

    @filter.command("llmhook")
    async def llmhook_cmd(self, event: AstrMessageEvent):
        """管理提示注入钩子：/llmhook status|on|off|log on|off|capture on|off
        - status: 显示当前 enable/log/capture 状态
        - on/off: 开启或关闭系统提示注入
        - log on/off: 控制是否输出注入日志
        - capture on/off: 控制是否捕获最近一次系统提示
        """
        try:
            parts = (event.message_str or "").strip().split()
            sub = parts[1].lower() if len(parts) > 1 else "status"
            if sub == "status":
                status = (
                    f"enable={'on' if self.llm_hook_enable else 'off'} "
                    f"log={'on' if self.llm_hook_log_enable else 'off'} "
                    f"capture={'on' if self.llm_hook_capture_enable else 'off'}"
                )
                yield event.plain_result(f"LLM Hook 状态: {status}")
                return
            if sub == "on":
                self.llm_hook_enable = True
                yield event.plain_result("已开启系统提示注入")
                return
            if sub == "off":
                self.llm_hook_enable = False
                yield event.plain_result("已关闭系统提示注入")
                return
            if sub == "log" and len(parts) > 2:
                toggle = parts[2].lower()
                self.llm_hook_log_enable = (toggle == "on")
                yield event.plain_result(f"注入日志已{'开启' if self.llm_hook_log_enable else '关闭'}")
                return
            if sub == "capture" and len(parts) > 2:
                toggle = parts[2].lower()
                self.llm_hook_capture_enable = (toggle == "on")
                yield event.plain_result(f"提示捕获已{'开启' if self.llm_hook_capture_enable else '关闭'}")
                return
            yield event.plain_result("用法: /llmhook status|on|off|log on|off|capture on|off")
        except Exception as e:
            yield event.plain_result(f"执行失败: {e}")

    @filter.command("connectome")
    async def connectome(self, event: AstrMessageEvent):
        """启用/关闭/执行 Connectome 思考: /connectome on|off|status|think <内容>"""
        session_id = event.message_obj.session_id
        parts = (event.message_str or "").strip().split()
        subcmd = parts[1] if len(parts) > 1 else "status"

        if subcmd == "on":
            self.enabled_sessions.add(session_id)
            yield event.plain_result("Connectome 已在本会话启用")
            return
        if subcmd == "off":
            self.enabled_sessions.discard(session_id)
            yield event.plain_result("Connectome 已在本会话关闭")
            return
        if subcmd == "status":
            status = "启用" if session_id in self.enabled_sessions else "关闭"
            yield event.plain_result(f"Connectome 当前状态: {status}")
            return
        if subcmd == "think":
            query = " ".join(parts[2:]) if len(parts) > 2 else ""
            if not query:
                yield event.plain_result("用法: /connectome think <内容>")
                return
            try:
                # 思考前刷新时间/天气感知（若未锁定）
                if self.perception_enable and not self.perception_lock:
                    try:
                        self.engine.refresh_perception(self.time_zone, self.geo_city if (self.geo_lat is None or self.geo_lon is None) else "", self.geo_lat, self.geo_lon)
                    except Exception:
                        pass
                # 在思考前动态重载自适应参数，确保 WebUI/命令更新即时生效
                try:
                    saved_params = self.hippocampus.load_adaptive_params()
                except Exception:
                    saved_params = {}
                if saved_params:
                    self.engine.homeo.update(saved_params.get("homeostasis", {}))
                    self.engine.auto.update(saved_params.get("autonomic", {}))
                    self.engine.horm.update(saved_params.get("hormones", {}))
                    self.engine.circ.update(saved_params.get("circadian", {}))
                    self.engine.pain.update(saved_params.get("pain_immune", {}))
                    self.engine.dev.update(saved_params.get("development", {}))
                    self.engine.individual.update(saved_params.get("individual", {}))
                    self.engine.body.update(saved_params.get("body_schema", {}))
                    self.engine.norms.update(saved_params.get("norms", {}))
                    self.engine.ethics.update(saved_params.get("ethics", {}))
                    # 同步模块实例
                    try:
                        self.engine.norms_mod.update(self.engine.norms)
                        self.engine.ethics_mod.update(self.engine.ethics)
                    except Exception:
                        pass
                    # 守卫开关
                    gconf = saved_params.get("guardian", {})
                    if isinstance(gconf.get("enable"), bool):
                        self.guard_enabled = gconf.get("enable")
                self.hippocampus.add_memory(session_id, "user", query)
                self.hippocampus.prune_session(session_id, self.max_memory_per_session)
                memories = self.hippocampus.get_recent(session_id, limit=12)
                result = self.engine.think(query, memories)
                # 守护器评估与可能拦截
                if self.guard_enabled:
                    assess = self.engine.assess_compliance(query, result)
                    # 记录审计日志
                    audit_text = f"合规评估: 风险={assess.get('risk')} 动作={assess.get('action')} 原因={';'.join(assess.get('reasons', []))}"
                    self.hippocampus.add_memory(session_id, "audit", audit_text)
                    if assess.get("action") == "halt":
                        safe_msg = "触发伦理停机：内容涉及高风险/不合规。请调整目标或参数后重试。"
                        self.hippocampus.add_memory(session_id, "assistant", safe_msg)
                        yield event.plain_result(safe_msg)
                        return
                    elif assess.get("action") == "soft_guard":
                        safe_prefix = "合规提示：内容可能存在风险或不当。以下为更安全的建议重述。\n"
                        result = safe_prefix + result
                # 记录路径用于奖励
                self.last_paths[session_id] = list(self.engine.last_path)
                # 记录到回放缓冲由引擎内部完成
                # 自动奖励（关键词驱动）
                if self.rl_enable and self.auto_reward:
                    reward = 0.0
                    low = result.lower()
                    if any(k.lower() in low for k in self.rk_positive):
                        reward += 1.0
                    if any(k.lower() in low for k in self.rk_negative):
                        reward -= 1.0
                    if abs(reward) > 0.0:
                        weights = self.engine.apply_reward(self.last_paths[session_id], reward, self.rl_alpha, self.rl_gamma)
                        self.hippocampus.save_rl_weights(weights)
                self.hippocampus.add_memory(session_id, "assistant", result)
                # 在思考后按需输出指标（需开启 metrics.enable）
                if self.metrics_enable and self.metrics_on_think:
                    try:
                        self._log_metrics()
                    except Exception:
                        pass
                yield event.plain_result(result)
            except Exception as e:
                yield event.plain_result(f"执行失败: {e}")
            return

        if subcmd == "reward":
            # /connectome reward <正负数>
            if len(parts) < 3:
                yield event.plain_result("用法: /connectome reward <奖励值，如 1 或 -1>")
                return
            try:
                reward_val = float(parts[2])
                path = self.last_paths.get(session_id, [])
                if not path:
                    yield event.plain_result("没有可奖励的最近思考路径，请先执行 /connectome think")
                    return
                if not self.rl_enable:
                    yield event.plain_result("RL 未启用，请在配置中开启 rl_enable")
                    return
                weights = self.engine.apply_reward(path, reward_val, self.rl_alpha, self.rl_gamma)
                self.hippocampus.save_rl_weights(weights)
                yield event.plain_result(f"已应用奖励 {reward_val} 并更新权重。")
            except Exception as e:
                yield event.plain_result(f"奖励失败: {e}")
            return

    @filter.command("webui")
    async def webui_cmd(self, event: AstrMessageEvent):
        """控制 WebUI: /webui start|stop|status|open"""
        parts = (event.message_str or "").strip().split()
        subcmd = parts[1] if len(parts) > 1 else "status"

        if subcmd == "start":
            if not self.webui_running:
                try:
                    self._start_webui()
                    yield event.plain_result(f"WebUI 已启动: http://{self.webui_host}:{self.webui_port}/")
                except Exception as e:
                    yield event.plain_result(f"WebUI 启动失败: {e}")
            else:
                yield event.plain_result(f"WebUI 已在运行: http://{self.webui_host}:{self.webui_port}/")
            return

        if subcmd == "stop":
            if self.webui_running:
                self._stop_webui()
                yield event.plain_result("WebUI 已停止")
            else:
                yield event.plain_result("WebUI 当前未运行")
            return

        if subcmd == "open":
            yield event.plain_result(f"请访问: http://{self.webui_host}:{self.webui_port}/")
            return

        if subcmd == "status":
            status = "运行中" if self.webui_running else "未运行"
            yield event.plain_result(f"WebUI 状态: {status} @ http://{self.webui_host}:{self.webui_port}/")
            return

    @filter.command("metrics")
    async def metrics_cmd(self, event: AstrMessageEvent):
        """管理指标输出：/metrics status|start|stop|interval <秒>|once|on_think on|off"""
        parts = (event.message_str or "").strip().split()
        subcmd = parts[1] if len(parts) > 1 else "status"

        if subcmd == "status":
            running = bool(self.metrics_thread and self.metrics_thread.is_alive())
            yield event.plain_result(
                f"Metrics 状态: {'运行中' if running else '未运行'} 使能={self.metrics_enable} 间隔={self.metrics_interval}s 思考时输出={'开' if self.metrics_on_think else '关'}"
            )
            return

        if subcmd == "start":
            self.metrics_enable = True
            try:
                self._start_metrics()
                yield event.plain_result(f"Metrics 已启动，间隔 {self.metrics_interval}s")
            except Exception as e:
                yield event.plain_result(f"Metrics 启动失败: {e}")
            return

        if subcmd == "stop":
            self.metrics_enable = False
            try:
                self._stop_metrics()
                yield event.plain_result("Metrics 已停止")
            except Exception as e:
                yield event.plain_result(f"Metrics 停止失败: {e}")
            return

        if subcmd == "interval" and len(parts) >= 3:
            try:
                self.metrics_interval = max(1, int(parts[2]))
                # 若正在运行则重启以应用新间隔
                if self.metrics_thread and self.metrics_thread.is_alive():
                    self._stop_metrics()
                    self._start_metrics()
                yield event.plain_result(f"Metrics 间隔已设置为 {self.metrics_interval}s")
            except Exception:
                yield event.plain_result("间隔参数错误，用法: /metrics interval <秒>")
            return

        if subcmd == "once":
            try:
                self._log_metrics()
                yield event.plain_result("已输出一次指标到官方控制台")
            except Exception as e:
                yield event.plain_result(f"输出失败: {e}")
            return

        if subcmd == "on_think" and len(parts) >= 3:
            flag = parts[2].lower()
            if flag in ("on", "off"):
                self.metrics_on_think = (flag == "on")
                yield event.plain_result(f"思考时输出指标: {'开' if self.metrics_on_think else '关'}")
                return
            yield event.plain_result("用法: /metrics on_think on|off")
            return

        yield event.plain_result("用法: /metrics status|start|stop|interval <秒>|once|on_think on|off")

    @filter.command("perception")
    async def perception_cmd(self, event: AstrMessageEvent):
        """管理时间/天气感知: /perception status|on|off|lock on|off|refresh|tz <TZ>|city <NAME>|coord <lat> <lon>"""
        parts = (event.message_str or "").strip().split()
        subcmd = parts[1] if len(parts) > 1 else "status"

        if subcmd == "status":
            env = getattr(self.engine, "env", {})
            tz = env.get("time_zone", self.time_zone)
            tstr = env.get("local_time_str", "")
            desc = env.get("weather_desc", "未知")
            temp = env.get("weather_temp_c")
            lat = env.get("lat", self.geo_lat)
            lon = env.get("lon", self.geo_lon)
            yield event.plain_result(
                f"状态={'开' if self.perception_enable else '关'} 锁定={'开' if self.perception_lock else '关'}\n"
                f"时间={tstr}({tz}) 天气={desc}{f', 温度={temp}℃' if temp is not None else ''} 坐标={lat},{lon}"
            )
            return

        if subcmd == "on":
            self.perception_enable = True
            yield event.plain_result("已开启环境感知（自动刷新与派生）")
            return

        if subcmd == "off":
            self.perception_enable = False
            yield event.plain_result("已关闭环境感知（将不再自动刷新或派生）")
            return

        if subcmd == "lock" and len(parts) >= 3:
            toggle = parts[2].lower()
            self.perception_lock = (toggle == "on")
            yield event.plain_result(f"已{'开启' if self.perception_lock else '关闭'}感知锁定（{'禁用自动派生' if self.perception_lock else '允许自动派生'}）")
            return

        if subcmd == "refresh":
            try:
                if self.perception_lock:
                    yield event.plain_result("当前为锁定模式，已跳过自动派生，仅保留现有参数。")
                else:
                    self.engine.refresh_perception(self.time_zone, self.geo_city if (self.geo_lat is None or self.geo_lon is None) else "", self.geo_lat, self.geo_lon)
                    yield event.plain_result("已刷新时间/天气感知")
            except Exception as e:
                yield event.plain_result(f"刷新失败: {e}")
            return

        if subcmd == "tz" and len(parts) >= 3:
            self.time_zone = parts[2]
            yield event.plain_result(f"已设置时区: {self.time_zone}")
            return

        if subcmd == "city" and len(parts) >= 3:
            self.geo_city = " ".join(parts[2:])
            # 清除坐标以强制地理编码
            self.geo_lat = None
            self.geo_lon = None
            yield event.plain_result(f"已设置城市: {self.geo_city}")
            return

        if subcmd == "coord" and len(parts) >= 4:
            try:
                self.geo_lat = float(parts[2])
                self.geo_lon = float(parts[3])
                yield event.plain_result(f"已设置坐标: {self.geo_lat},{self.geo_lon}")
            except Exception:
                yield event.plain_result("坐标格式错误，用法: /perception coord <lat> <lon>")
            return
        
        yield event.plain_result("用法: /perception status|refresh|tz <TZ>|city <NAME>|coord <lat> <lon>")

        yield event.plain_result("未知子命令，用法: /connectome on|off|status|think <内容> 或 /connectome reward <值>")

    @filter.command("replay")
    async def replay(self, event: AstrMessageEvent):
        """重放近期路径以巩固：/replay [k]"""
        try:
            k = 5
            parts = (event.message_str or "").strip().split()
            if len(parts) > 1:
                k = max(1, int(parts[1]))
            weights = self.engine.replay(k=k, alpha=self.rl_alpha, gamma=self.rl_gamma)
            self.hippocampus.save_rl_weights(weights)
            yield event.plain_result(f"已重放 {k} 条路径并更新权重。")
        except Exception as e:
            yield event.plain_result(f"重放失败: {e}")

    @filter.command("sleep")
    async def sleep(self, event: AstrMessageEvent):
        """执行睡眠巩固（NREM/REM 简化）：/sleep"""
        try:
            weights = self.engine.sleep_consolidate()
            self.hippocampus.save_rl_weights(weights)
            yield event.plain_result("已完成一次睡眠巩固并更新权重。")
        except Exception as e:
            yield event.plain_result(f"睡眠失败: {e}")

    @filter.command("neuromod")
    async def neuromod(self, event: AstrMessageEvent):
        """设置神经调质水平：/neuromod da=1.2 ach=0.8 ne=1.1 5ht=1.0"""
        try:
            text = (event.message_str or "").strip()
            parts = text.split()[1:] if len(text.split()) > 1 else []
            updates = {}
            for p in parts:
                if "=" in p:
                    k, v = p.split("=", 1)
                    updates[k.strip().lower()] = float(v)
            if not updates:
                yield event.plain_result("用法: /neuromod da=... ach=... ne=... 5ht=...")
                return
            self.engine.set_neuromodulators(updates)
            # 持久化
            params = {
                "neuromodulators": updates
            }
            # 合并到已有自适应参数
            try:
                existing = self.hippocampus.load_adaptive_params()
            except Exception:
                existing = {}
            for k, val in params.items():
                base = existing.get(k, {})
                base.update(val)
                existing[k] = base
            self.hippocampus.save_adaptive_params(existing)
            yield event.plain_result(f"已更新神经调质: {updates}")
        except Exception as e:
            yield event.plain_result(f"更新失败: {e}")

    @filter.command("wm")
    async def wm(self, event: AstrMessageEvent):
        """设置工作记忆参数：/wm loop=7 sketch=4 buffer=8 refresh=1.0"""
        try:
            text = (event.message_str or "").strip()
            parts = text.split()[1:] if len(text.split()) > 1 else []
            updates = {}
            for p in parts:
                if "=" in p:
                    k, v = p.split("=", 1)
                    k = k.strip().lower()
                    if k in ["loop", "sketch", "buffer"]:
                        updates_map = {"loop_capacity": "loop", "sketchpad_capacity": "sketch", "buffer_capacity": "buffer"}
                        # 临时收集，后面映射
                        pass
            # 简化解析：支持 loop/sketch/buffer/refresh 四项
            updates = {}
            for p in parts:
                if "=" in p:
                    k, v = p.split("=", 1)
                    k = k.strip().lower()
                    v = v.strip()
                    if k == "loop":
                        updates["loop_capacity"] = int(v)
                    elif k == "sketch":
                        updates["sketchpad_capacity"] = int(v)
                    elif k == "buffer":
                        updates["buffer_capacity"] = int(v)
                    elif k == "refresh":
                        updates["refresh_rate"] = float(v)
            if not updates:
                yield event.plain_result("用法: /wm loop=7 sketch=4 buffer=8 refresh=1.0")
                return
            # 更新引擎
            self.engine.wm.update(updates)
            # 持久化
            try:
                existing = self.hippocampus.load_adaptive_params()
            except Exception:
                existing = {}
            base = existing.get("working_memory", {})
            base.update(updates)
            existing["working_memory"] = base
            self.hippocampus.save_adaptive_params(existing)
            yield event.plain_result(f"已更新工作记忆: {updates}")
        except Exception as e:
            yield event.plain_result(f"更新失败: {e}")

    @filter.command("policy")
    async def policy(self, event: AstrMessageEvent):
        """设置强化学习策略权重：/policy mf=0.7 mb=0.3"""
        try:
            text = (event.message_str or "").strip()
            parts = text.split()[1:] if len(text.split()) > 1 else []
            updates = {}
            for p in parts:
                if "=" in p:
                    k, v = p.split("=", 1)
                    k = k.strip().lower()
                    if k == "mf":
                        updates["rl_model_free_weight"] = float(v)
                    elif k == "mb":
                        updates["rl_model_based_weight"] = float(v)
            if not updates:
                yield event.plain_result("用法: /policy mf=0.7 mb=0.3")
                return
            self.engine.learning.update(updates)
            # 持久化
            try:
                existing = self.hippocampus.load_adaptive_params()
            except Exception:
                existing = {}
            base = existing.get("learning", {})
            base.update(updates)
            existing["learning"] = base
            self.hippocampus.save_adaptive_params(existing)
            yield event.plain_result(f"已更新策略权重: {updates}")
        except Exception as e:
            yield event.plain_result(f"更新失败: {e}")

    @filter.command("emotion")
    async def emotion(self, event: AstrMessageEvent):
        """设置情绪状态：/emotion valence=1.0 arousal=1.0"""
        try:
            text = (event.message_str or "").strip()
            parts = text.split()[1:] if len(text.split()) > 1 else []
            updates = {}
            for p in parts:
                if "=" in p:
                    k, v = p.split("=", 1)
                    k = k.strip().lower()
                    if k in ["valence", "arousal"]:
                        updates[k] = float(v)
            if not updates:
                yield event.plain_result("用法: /emotion valence=1.0 arousal=1.0")
                return
            self.engine.emotion.update(updates)
            # 持久化
            try:
                existing = self.hippocampus.load_adaptive_params()
            except Exception:
                existing = {}
            base = existing.get("emotion", {})
            base.update(updates)
            existing["emotion"] = base
            self.hippocampus.save_adaptive_params(existing)
            yield event.plain_result(f"已更新情绪: {updates}")
        except Exception as e:
            yield event.plain_result(f"更新失败: {e}")

    @filter.command("guard")
    async def guard(self, event: AstrMessageEvent):
        """启用/关闭守护器：/guard on|off|status"""
        try:
            parts = (event.message_str or "").strip().split()
            sub = parts[1].lower() if len(parts) > 1 else "status"
            if sub == "on":
                self.guard_enabled = True
                # 持久化
                try:
                    existing = self.hippocampus.load_adaptive_params()
                except Exception:
                    existing = {}
                base = existing.get("guardian", {})
                base.update({"enable": True})
                existing["guardian"] = base
                self.hippocampus.save_adaptive_params(existing)
                yield event.plain_result("守护器已启用")
                return
            if sub == "off":
                self.guard_enabled = False
                try:
                    existing = self.hippocampus.load_adaptive_params()
                except Exception:
                    existing = {}
                base = existing.get("guardian", {})
                base.update({"enable": False})
                existing["guardian"] = base
                self.hippocampus.save_adaptive_params(existing)
                yield event.plain_result("守护器已关闭")
                return
            status = "启用" if self.guard_enabled else "关闭"
            yield event.plain_result(f"守护器状态: {status}")
        except Exception as e:
            yield event.plain_result(f"更新失败: {e}")

    @filter.command("act")
    async def act(self, event: AstrMessageEvent):
        """行动评估：/act <计划描述>（依据身体/疼痛/能量等评估可行性）"""
        try:
            session_id = event.message_obj.session_id
            text = (event.message_str or "").strip().split(" ", 1)
            plan = text[1] if len(text) > 1 else ""
            if not plan:
                yield event.plain_result("用法: /act <计划描述>")
                return
            summary = self.engine.evaluate_action(plan)
            self.hippocampus.add_memory(session_id, "assistant", summary)
            yield event.plain_result(summary)
        except Exception as e:
            yield event.plain_result(f"执行失败: {e}")

    @filter.command("audit")
    async def audit(self, event: AstrMessageEvent):
        """查看审计日志：/audit [limit=10]"""
        try:
            parts = (event.message_str or "").strip().split()
            limit = 10
            if len(parts) > 1 and parts[1].startswith("limit="):
                try:
                    limit = int(parts[1].split("=", 1)[1])
                except Exception:
                    pass
            session_id = event.message_obj.session_id
            items = self.hippocampus.get_audit(session_id, limit=limit)
            if not items:
                yield event.plain_result("暂无审计日志")
                return
            lines = [f"[{i['created_at']}] {i['content']}" for i in items]
            yield event.plain_result("\n".join(lines))
        except Exception as e:
            yield event.plain_result(f"执行失败: {e}")

    @filter.command("sleep")
    async def sleep(self, event: AstrMessageEvent):
        """离线重放与睡眠巩固：/sleep [replay_k=5 alpha=0.1 gamma=0.9]"""
        try:
            # 解析可选参数
            parts = (event.message_str or "").strip().split()
            kv = {k.split('=')[0]: k.split('=')[1] for k in parts[1:] if '=' in k}
            k = int(kv.get("replay_k", 5))
            alpha = float(kv.get("alpha", 0.1))
            gamma = float(kv.get("gamma", 0.9))
            # 重放与巩固
            self.engine.replay(k=k, alpha=alpha, gamma=gamma)
            weights = self.engine.sleep_consolidate()
            # 简要摘要：展示几个关键节点权重
            keys = ["dmn", "salience", "control", "language", "limbic"]
            summary = "睡眠巩固完成。关键节点权重: " + ", ".join([f"{n}={weights.get(n, 1.0):.2f}" for n in keys])
            session_id = event.message_obj.session_id
            self.hippocampus.add_memory(session_id, "assistant", summary)
            yield event.plain_result(summary)
        except Exception as e:
            yield event.plain_result(f"执行失败: {e}")

    @filter.command("homeostasis")
    async def homeostasis_cmd(self, event: AstrMessageEvent):
        """设置体内平衡：/homeostasis energy=1.0 fatigue=0.5 body_temp=1.0"""
        try:
            text = (event.message_str or "").strip()
            parts = text.split()[1:] if len(text.split()) > 1 else []
            updates = {}
            allow = {"energy", "fatigue", "body_temp"}
            for p in parts:
                if "=" in p:
                    k, v = p.split("=", 1)
                    k = k.strip().lower()
                    if k in allow:
                        updates[k] = float(v)
            if not updates:
                yield event.plain_result("用法: /homeostasis energy=... fatigue=... body_temp=...")
                return
            self.engine.homeo.update(updates)
            try:
                existing = self.hippocampus.load_adaptive_params()
            except Exception:
                existing = {}
            base = existing.get("homeostasis", {})
            base.update(updates)
            existing["homeostasis"] = base
            self.hippocampus.save_adaptive_params(existing)
            yield event.plain_result(f"已更新体内平衡: {updates}")
        except Exception as e:
            yield event.plain_result(f"更新失败: {e}")

    @filter.command("autonomic")
    async def autonomic_cmd(self, event: AstrMessageEvent):
        """设置自主神经：/autonomic sympathetic=1.0 parasympathetic=1.0"""
        try:
            text = (event.message_str or "").strip()
            parts = text.split()[1:] if len(text.split()) > 1 else []
            updates = {}
            allow = {"sympathetic", "parasympathetic"}
            for p in parts:
                if "=" in p:
                    k, v = p.split("=", 1)
                    k = k.strip().lower()
                    if k in allow:
                        updates[k] = float(v)
            if not updates:
                yield event.plain_result("用法: /autonomic sympathetic=... parasympathetic=...")
                return
            self.engine.auto.update(updates)
            try:
                existing = self.hippocampus.load_adaptive_params()
            except Exception:
                existing = {}
            base = existing.get("autonomic", {})
            base.update(updates)
            existing["autonomic"] = base
            self.hippocampus.save_adaptive_params(existing)
            yield event.plain_result(f"已更新自主神经: {updates}")
        except Exception as e:
            yield event.plain_result(f"更新失败: {e}")

    @filter.command("hormone")
    async def hormone_cmd(self, event: AstrMessageEvent):
        """设置激素：/hormone cortisol=1.0 adrenaline=1.0 oxytocin=1.0"""
        try:
            text = (event.message_str or "").strip()
            parts = text.split()[1:] if len(text.split()) > 1 else []
            updates = {}
            allow = {"cortisol", "adrenaline", "oxytocin"}
            for p in parts:
                if "=" in p:
                    k, v = p.split("=", 1)
                    k = k.strip().lower()
                    if k in allow:
                        updates[k] = float(v)
            if not updates:
                yield event.plain_result("用法: /hormone cortisol=... adrenaline=... oxytocin=...")
                return
            self.engine.horm.update(updates)
            try:
                existing = self.hippocampus.load_adaptive_params()
            except Exception:
                existing = {}
            base = existing.get("hormones", {})
            base.update(updates)
            existing["hormones"] = base
            self.hippocampus.save_adaptive_params(existing)
            yield event.plain_result(f"已更新激素: {updates}")
        except Exception as e:
            yield event.plain_result(f"更新失败: {e}")

    @filter.command("circadian")
    async def circadian_cmd(self, event: AstrMessageEvent):
        """设置昼夜节律：/circadian phase=0.5 pressure=0.5"""
        try:
            text = (event.message_str or "").strip()
            parts = text.split()[1:] if len(text.split()) > 1 else []
            updates = {}
            mapping = {"phase": "circadian_phase", "pressure": "sleep_pressure"}
            for p in parts:
                if "=" in p:
                    k, v = p.split("=", 1)
                    k = k.strip().lower()
                    if k in mapping:
                        updates[mapping[k]] = float(v)
            if not updates:
                yield event.plain_result("用法: /circadian phase=... pressure=...")
                return
            self.engine.circ.update(updates)
            try:
                existing = self.hippocampus.load_adaptive_params()
            except Exception:
                existing = {}
            base = existing.get("circadian", {})
            base.update(updates)
            existing["circadian"] = base
            self.hippocampus.save_adaptive_params(existing)
            yield event.plain_result(f"已更新昼夜节律: {updates}")
        except Exception as e:
            yield event.plain_result(f"更新失败: {e}")

    @filter.command("modules")
    async def modules_cmd(self, event: AstrMessageEvent):
        """设置模块权重：/modules dmn=0 salience=0 control=0 ...（范围 0.0~2.0）"""
        try:
            text = (event.message_str or "").strip()
            parts = text.split()[1:] if len(text.split()) > 1 else []
            updates = {}
            allow = {
                "dmn",
                "salience",
                "control",
                "dorsal_attention",
                "ventral_attention",
                "language",
                "visual",
                "auditory",
                "sensorimotor",
                "limbic",
            }
            for p in parts:
                if "=" in p:
                    k, v = p.split("=", 1)
                    k = k.strip().lower()
                    if k in allow:
                        updates[k] = float(v)
            if not updates:
                yield event.plain_result("用法: /modules dmn=... salience=... control=...（支持上述 10 个模块）")
                return
            # 应用到引擎
            self.engine.set_weights(updates)
            # 持久化到 RL 权重，确保稳定覆盖
            try:
                self.hippocampus.save_rl_weights(self.engine.get_node_weights())
            except Exception:
                pass
            yield event.plain_result(f"已更新模块权重: {updates}")
        except Exception as e:
            yield event.plain_result(f"更新失败: {e}")

    @filter.command("pain")
    async def pain_cmd(self, event: AstrMessageEvent):
        """设置疼痛/免疫：/pain nociception=0.3 inflammation=0.2"""
        try:
            text = (event.message_str or "").strip()
            parts = text.split()[1:] if len(text.split()) > 1 else []
            updates = {}
            allow = {"nociception", "inflammation"}
            for p in parts:
                if "=" in p:
                    k, v = p.split("=", 1)
                    k = k.strip().lower()
                    if k in allow:
                        updates[k] = float(v)
            if not updates:
                yield event.plain_result("用法: /pain nociception=... inflammation=...")
                return
            self.engine.pain.update(updates)
            try:
                existing = self.hippocampus.load_adaptive_params()
            except Exception:
                existing = {}
            base = existing.get("pain_immune", {})
            base.update(updates)
            existing["pain_immune"] = base
            self.hippocampus.save_adaptive_params(existing)
            yield event.plain_result(f"已更新疼痛/免疫: {updates}")
        except Exception as e:
            yield event.plain_result(f"更新失败: {e}")

    @filter.command("development")
    async def development_cmd(self, event: AstrMessageEvent):
        """设置发育曲线：/development maturation=1.0 plasticity=1.0 senescence=0.0"""
        try:
            text = (event.message_str or "").strip()
            parts = text.split()[1:] if len(text.split()) > 1 else []
            updates = {}
            mapping = {"maturation": "maturation", "plasticity": "plasticity_curve", "senescence": "senescence"}
            for p in parts:
                if "=" in p:
                    k, v = p.split("=", 1)
                    k = k.strip().lower()
                    if k in mapping:
                        updates[mapping[k]] = float(v)
            if not updates:
                yield event.plain_result("用法: /development maturation=... plasticity=... senescence=...")
                return
            self.engine.dev.update(updates)
            try:
                existing = self.hippocampus.load_adaptive_params()
            except Exception:
                existing = {}
            base = existing.get("development", {})
            base.update(updates)
            existing["development"] = base
            self.hippocampus.save_adaptive_params(existing)
            yield event.plain_result(f"已更新发育曲线: {updates}")
        except Exception as e:
            yield event.plain_result(f"更新失败: {e}")

    @filter.command("agency")
    async def agency_cmd(self, event: AstrMessageEvent):
        """设置身体图式/代理：/agency agency=1.0 proprio_noise=0.5 motor_cost=1.0"""
        try:
            text = (event.message_str or "").strip()
            parts = text.split()[1:] if len(text.split()) > 1 else []
            updates = {}
            mapping = {"agency": "agency", "proprio_noise": "proprioception_noise", "motor_cost": "motor_cost"}
            for p in parts:
                if "=" in p:
                    k, v = p.split("=", 1)
                    k = k.strip().lower()
                    if k in mapping:
                        updates[mapping[k]] = float(v)
            if not updates:
                yield event.plain_result("用法: /agency agency=... proprio_noise=... motor_cost=...")
                return
            self.engine.body.update(updates)
            try:
                existing = self.hippocampus.load_adaptive_params()
            except Exception:
                existing = {}
            base = existing.get("body_schema", {})
            base.update(updates)
            existing["body_schema"] = base
            self.hippocampus.save_adaptive_params(existing)
            yield event.plain_result(f"已更新身体图式/代理: {updates}")
        except Exception as e:
            yield event.plain_result(f"更新失败: {e}")

    @filter.command("norms")
    async def norms_cmd(self, event: AstrMessageEvent):
        """设置规范敏感度：/norms legal=1.2 social=1.0 cultural=1.0"""
        try:
            text = (event.message_str or "").strip()
            parts = text.split()[1:] if len(text.split()) > 1 else []
            updates = {}
            allow = {"legal", "social", "cultural"}
            for p in parts:
                if "=" in p:
                    k, v = p.split("=", 1)
                    k = k.strip().lower()
                    if k in allow:
                        updates[k] = float(v)
            if not updates:
                yield event.plain_result("用法: /norms legal=... social=... cultural=...")
                return
            self.engine.norms.update(updates)
            try:
                existing = self.hippocampus.load_adaptive_params()
            except Exception:
                existing = {}
            base = existing.get("norms", {})
            base.update(updates)
            existing["norms"] = base
            self.hippocampus.save_adaptive_params(existing)
            yield event.plain_result(f"已更新规范敏感度: {updates}")
        except Exception as e:
            yield event.plain_result(f"更新失败: {e}")

    @filter.command("ethics")
    async def ethics_cmd(self, event: AstrMessageEvent):
        """设置伦理停机：/ethics guard=1.5 halt=1.5"""
        try:
            text = (event.message_str or "").strip()
            parts = text.split()[1:] if len(text.split()) > 1 else []
            updates = {}
            mapping = {"guard": "override_guard", "halt": "halt_threshold"}
            for p in parts:
                if "=" in p:
                    k, v = p.split("=", 1)
                    k = k.strip().lower()
                    if k in mapping:
                        updates[mapping[k]] = float(v)
            if not updates:
                yield event.plain_result("用法: /ethics guard=... halt=...")
                return
            self.engine.ethics.update(updates)
            try:
                existing = self.hippocampus.load_adaptive_params()
            except Exception:
                existing = {}
            base = existing.get("ethics", {})
            base.update(updates)
            existing["ethics"] = base
            self.hippocampus.save_adaptive_params(existing)
            yield event.plain_result(f"已更新伦理停机: {updates}")
        except Exception as e:
            yield event.plain_result(f"更新失败: {e}")

    @filter.command("identity")
    async def identity_cmd(self, event: AstrMessageEvent):
        """设置叙事身份：/identity consistency=1.0 goals=1.0"""
        try:
            text = (event.message_str or "").strip()
            parts = text.split()[1:] if len(text.split()) > 1 else []
            updates = {}
            mapping = {"consistency": "narrative_consistency", "goals": "long_term_goals"}
            for p in parts:
                if "=" in p:
                    k, v = p.split("=", 1)
                    k = k.strip().lower()
                    if k in mapping:
                        updates[mapping[k]] = float(v)
            if not updates:
                yield event.plain_result("用法: /identity consistency=... goals=...")
                return
            self.engine.identity.update(updates)
            try:
                existing = self.hippocampus.load_adaptive_params()
            except Exception:
                existing = {}
            base = existing.get("identity", {})
            base.update(updates)
            existing["identity"] = base
            self.hippocampus.save_adaptive_params(existing)
            yield event.plain_result(f"已更新叙事身份: {updates}")
        except Exception as e:
            yield event.plain_result(f"更新失败: {e}")

    @filter.command("remember")
    async def remember(self, event: AstrMessageEvent):
        """手动记忆当前文本: /remember <内容>"""
        session_id = event.message_obj.session_id
        text = (event.message_str or "").strip().split(" ", 1)
        content = text[1] if len(text) > 1 else ""
        if not content:
            yield event.plain_result("用法: /remember <内容>")
            return
        self.hippocampus.add_memory(session_id, "user", content)
        self.hippocampus.prune_session(session_id, self.max_memory_per_session)
        yield event.plain_result("已记录到海马体记忆库")

    async def terminate(self):
        # 插件卸载/退出时关闭 WebUI
        try:
            if self.webui_running:
                self._stop_webui()
        except Exception:
            pass
        # 关闭指标线程
        try:
            if self.metrics_thread and self.metrics_thread.is_alive():
                self._stop_metrics()
        except Exception:
            pass
