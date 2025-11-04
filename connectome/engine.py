from typing import List, Dict, Any, Optional
import math
import networkx as nx
from .systems import (
    Homeostasis, Autonomic, Hormones, Circadian,
    PainImmune, Development, Individual, BodySchema,
    Norms, Ethics, Guardian, ActionEvaluator, Perception,
)


class ConnectomeEngine:
    def __init__(
        self,
        ei_balance: float = 0.5,
        modules: Optional[Dict[str, float]] = None,
        depth: int = 3,
        neuromodulators: Optional[Dict[str, float]] = None,
        oscillation: Optional[Dict[str, float]] = None,
        plasticity: Optional[Dict[str, float]] = None,
        myelination: Optional[Dict[str, float]] = None,
        cortical_layers: Optional[Dict[str, float]] = None,
        basal_ganglia: Optional[Dict[str, float]] = None,
        cerebellum: Optional[Dict[str, float]] = None,
        hippocampus_conf: Optional[Dict[str, Any]] = None,
        attention: Optional[Dict[str, float]] = None,
        working_memory: Optional[Dict[str, Any]] = None,
        learning: Optional[Dict[str, float]] = None,
        decision: Optional[Dict[str, float]] = None,
        executive: Optional[Dict[str, float]] = None,
        metacognition: Optional[Dict[str, float]] = None,
        emotion: Optional[Dict[str, float]] = None,
        motivation: Optional[Dict[str, float]] = None,
        habit: Optional[Dict[str, float]] = None,
        # 辅助系统参数
        homeostasis: Optional[Dict[str, float]] = None,
        autonomic: Optional[Dict[str, float]] = None,
        hormones: Optional[Dict[str, float]] = None,
        circadian: Optional[Dict[str, float]] = None,
        pain_immune: Optional[Dict[str, float]] = None,
        development: Optional[Dict[str, float]] = None,
        individual: Optional[Dict[str, float]] = None,
        body_schema: Optional[Dict[str, float]] = None,
        norms: Optional[Dict[str, float]] = None,
        ethics: Optional[Dict[str, float]] = None,
        identity: Optional[Dict[str, float]] = None,
    ):
        self.ei_balance = max(0.0, min(1.0, ei_balance))
        self.depth = max(1, int(depth))
        self.modules = modules or {}
        # 生物学参数块
        self.neuromod = {
            "da": 1.0, "ach": 1.0, "ne": 1.0, "5ht": 1.0
        }
        self.neuromod.update(neuromodulators or {})
        self.osc = {"theta_gamma_coupling": 0.5}
        self.osc.update(oscillation or {})
        self.plasticity = {
            "stdp_strength": 0.5,
            "homeostatic_gain": 0.1,
            "metaplasticity": 0.5,
        }
        self.plasticity.update(plasticity or {})
        self.myelin = {
            "myelination_rate": 0.5,
            "conduction_delay_scaling": 0.1,
        }
        self.myelin.update(myelination or {})
        self.layers = {
            "feedforward_strength": 1.0,
            "feedback_strength": 1.0,
            "lateral_strength": 1.0,
        }
        self.layers.update(cortical_layers or {})
        self.bg = {
            "epsilon_exploration": 0.1,
            "habit_strength": 0.5,
        }
        self.bg.update(basal_ganglia or {})
        self.cerebellum = {"lr": 0.1}
        self.cerebellum.update(cerebellum or {})
        self.hipp_conf = {"replay_enable": True, "sleep_enable": True}
        self.hipp_conf.update(hippocampus_conf or {})
        # 心理学参数块
        self.attn = {"alerting": 1.0, "orienting": 1.0, "executive": 1.0}
        self.attn.update(attention or {})
        self.wm = {
            "loop_capacity": 7,
            "sketchpad_capacity": 4,
            "buffer_capacity": 8,
            "refresh_rate": 1.0,
        }
        self.wm.update(working_memory or {})
        self.learning = {
            "classical_strength": 1.0,
            "operant_strength": 1.0,
            "statistical_strength": 1.0,
            "rl_model_free_weight": 0.7,
            "rl_model_based_weight": 0.3,
        }
        self.learning.update(learning or {})
        self.decision = {
            "risk_aversion": 1.0,
            "loss_aversion": 1.2,
            "time_discount": 0.9,
        }
        self.decision.update(decision or {})
        self.exec = {
            "inhibition": 1.0,
            "updating": 1.0,
            "shifting": 1.0,
            "monitoring": 1.0,
        }
        self.exec.update(executive or {})
        self.meta = {
            "confidence_calibration": 1.0,
            "error_monitoring": 1.0,
            "control_threshold": 1.0,
        }
        self.meta.update(metacognition or {})
        self.emotion = {
            "valence": 1.0,
            "arousal": 1.0,
            "reappraisal_strength": 1.0,
            "suppression_strength": 0.5,
        }
        self.emotion.update(emotion or {})
        self.motivation = {
            "autonomy": 1.0,
            "competence": 1.0,
            "relatedness": 1.0,
        }
        self.motivation.update(motivation or {})
        self.habit = {
            "formation_rate": 1.0,
            "chunking_strength": 1.0,
            "automation_level": 1.0,
        }
        self.habit.update(habit or {})
        # ---- 辅助系统默认值 ----
        self.homeo = {
            "energy": 1.0,
            "fatigue": 0.5,
            "body_temp": 1.0,
        }
        self.homeo.update(homeostasis or {})
        self.auto = {
            "sympathetic": 1.0,
            "parasympathetic": 1.0,
        }
        self.auto.update(autonomic or {})
        self.horm = {
            "cortisol": 1.0,
            "adrenaline": 1.0,
            "oxytocin": 1.0,
        }
        self.horm.update(hormones or {})
        self.circ = {
            "circadian_phase": 0.5,
            "sleep_pressure": 0.5,
        }
        self.circ.update(circadian or {})
        self.pain = {
            "nociception": 0.0,
            "inflammation": 0.0,
        }
        self.pain.update(pain_immune or {})
        self.dev = {
            "maturation": 1.0,
            "plasticity_curve": 1.0,
            "senescence": 0.0,
        }
        self.dev.update(development or {})
        self.individual = {
            "openness": 1.0,
            "conscientiousness": 1.0,
            "extraversion": 1.0,
            "agreeableness": 1.0,
            "neuroticism": 1.0,
        }
        self.individual.update(individual or {})
        self.body = {
            "agency": 1.0,
            "proprioception_noise": 0.5,
            "motor_cost": 1.0,
        }
        self.body.update(body_schema or {})
        self.norms = {
            "legal": 1.0,
            "social": 1.0,
            "cultural": 1.0,
        }
        self.norms.update(norms or {})
        self.ethics = {
            "override_guard": 1.5,
            "halt_threshold": 1.5,
        }
        self.ethics.update(ethics or {})
        self.identity = {
            "narrative_consistency": 1.0,
            "long_term_goals": 1.0,
        }
        self.identity.update(identity or {})
        # 环境感知（时间/天气）
        self.env = {
            "local_time_str": "",
            "hour": 12.0,
            "weekday": 0,
            "time_zone": "Asia/Shanghai",
            "weather_temp_c": None,
            "weather_wind": None,
            "weather_desc": None,
            "lat": None,
            "lon": None,
        }
        # ---- 系统模块实例（引用同一状态字典）----
        self.homeo_mod = Homeostasis(self.homeo)
        self.auto_mod = Autonomic(self.auto)
        self.horm_mod = Hormones(self.horm)
        self.circ_mod = Circadian(self.circ)
        self.pain_mod = PainImmune(self.pain)
        self.dev_mod = Development(self.dev)
        self.indiv_mod = Individual(self.individual)
        self.body_mod = BodySchema(self.body)
        self.norms_mod = Norms(self.norms)
        self.ethics_mod = Ethics(self.ethics)
        self.guardian = Guardian()
        self.act_eval = ActionEvaluator()
        self.percep_mod = Perception(self.env)
        self.graph = self._build_graph(self.modules)
        self.last_path: List[str] = []
        self.replay_buffer: List[List[str]] = []

    def _build_graph(self, weights: Dict[str, float]):
        g = nx.DiGraph()
        base_modules = [
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
        ]
        for m in base_modules:
            w = float(weights.get(m, 1.0))
            g.add_node(m, weight=w)

        edges = [
            ("salience", "control"),
            ("control", "dorsal_attention"),
            ("control", "ventral_attention"),
            ("dorsal_attention", "language"),
            ("ventral_attention", "language"),
            ("dmn", "language"),
            ("visual", "language"),
            ("auditory", "language"),
            ("sensorimotor", "language"),
            ("limbic", "dmn"),
        ]
        for u, v in edges:
            base = (g.nodes[u]["weight"] + g.nodes[v]["weight"]) / 2
            # 层特异性调制（粗略近似）
            if (u in ["visual", "auditory", "sensorimotor"] and v == "language") or (u == "salience" and v == "control"):
                base *= float(self.layers.get("feedforward_strength", 1.0))
            if (u == "dmn" and v == "language") or (u == "limbic" and v == "dmn"):
                base *= float(self.layers.get("feedback_strength", 1.0))
            if (u == "control" and v in ["dorsal_attention", "ventral_attention"]):
                base *= float(self.layers.get("lateral_strength", 1.0))
            delay = max(0.0, 1.0 - float(self.myelin.get("myelination_rate", 0.5)))
            delay *= (1.0 + float(self.myelin.get("conduction_delay_scaling", 0.1)))
            g.add_edge(u, v, weight=base, delay=delay)
        return g

    def _select_path(self, text: str) -> List[str]:
        # 体内平衡对总体能力的缩放
        energy = float(self.homeo.get("energy", 1.0))
        fatigue = float(self.homeo.get("fatigue", 0.5))
        temp = float(self.homeo.get("body_temp", 1.0))
        temp_penalty = max(0.6, 1.0 - 0.3 * abs(temp - 1.0))
        capacity = max(0.3, energy * (1.0 - 0.4 * fatigue)) * temp_penalty
        # 规范偏置：法律/社会敏感度提升控制/规则分支偏好（模块化实现）
        legal_bias = self.norms_mod.legal_bias()
        social_bias = self.norms_mod.social_bias()
        s_score = self.graph.nodes["salience"]["weight"] * (0.6 + 0.4 * self.ei_balance) * float(self.attn.get("alerting", 1.0)) * capacity * social_bias
        c_score = self.graph.nodes["control"]["weight"] * (0.6 + 0.4 * (1 - self.ei_balance)) * float(self.attn.get("executive", 1.0)) * capacity * legal_bias
        a_d = self.graph.nodes["dorsal_attention"]["weight"]
        a_v = self.graph.nodes["ventral_attention"]["weight"]
        lang = self.graph.nodes["language"]["weight"]
        dmn = self.graph.nodes["dmn"]["weight"]
        sens = self.graph.nodes["sensorimotor"]["weight"]
        
        # NE 增益/噪声引入探索
        import random
        # 交感/肾上腺素提升探索，副交感与 ACh 抑制噪声
        epsilon = float(self.bg.get("epsilon_exploration", 0.1)) * float(self.neuromod.get("ne", 1.0))
        epsilon *= (0.8 + 0.4 * float(self.auto.get("sympathetic", 1.0)))
        epsilon *= (1.0 / max(0.6, 0.8 + 0.4 * float(self.auto.get("parasympathetic", 1.0)) * float(self.neuromod.get("ach", 1.0))))
        epsilon *= (0.8 + 0.4 * float(self.horm.get("adrenaline", 1.0)))
        path = ["salience" if s_score >= c_score else "control"]
        if random.random() < epsilon:
            path[0] = random.choice(["salience", "control"])
        if path[-1] == "salience":
            path.append("control")
        ach_gain = float(self.neuromod.get("ach", 1.0)) * float(self.attn.get("orienting", 1.0)) * (0.8 + 0.4 * float(self.auto.get("parasympathetic", 1.0)))
        a_d_eff = a_d * ach_gain
        a_v_eff = a_v * ach_gain
        # 结合延迟选择更快路径
        da_delay = self.graph.edges["control", "dorsal_attention"]["delay"] if self.graph.has_edge("control", "dorsal_attention") else 1.0
        va_delay = self.graph.edges["control", "ventral_attention"]["delay"] if self.graph.has_edge("control", "ventral_attention") else 1.0
        a_d_score = a_d_eff - da_delay
        a_v_score = a_v_eff - va_delay
        path.append("dorsal_attention" if a_d_score >= a_v_score else "ventral_attention")
        # 疼痛/免疫负荷倾向减少运动计划
        sens_penalty = 1.0 - 0.3 * min(2.0, float(self.pain.get("nociception", 0.0)) + 0.5 * float(self.pain.get("inflammation", 0.0)))
        sens_eff = sens * max(0.5, sens_penalty) / max(0.6, float(self.body.get("motor_cost", 1.0)))
        if any(k in text.lower() for k in ["看", "图", "视觉", "image", "vision"]):
            path.append("visual")
        if any(k in text.lower() for k in ["听", "音频", "voice", "sound"]):
            path.append("auditory")
        if any(k in text.lower() for k in ["动作", "运动", "move", "操作"]):
            if sens_eff > 0.6:
                path.append("sensorimotor")
        path.append("language")
        # 催产素提升社交/DMN 倾向
        if dmn * (0.9 + 0.2 * float(self.horm.get("oxytocin", 1.0))) > 1.2:
            path.insert(0, "dmn")
        if sens_eff > 1.2 and "sensorimotor" not in path:
            path.insert(len(path) - 1, "sensorimotor")
        self.last_path = path
        # 记录至回放缓冲（受习惯强度影响的近期强化）
        self.replay_buffer.append(list(path))
        # 睡眠压力/习惯化影响缓冲上限（高睡眠压力时更偏巩固）
        buf_limit = int(32 + 32 * float(self.habit.get("formation_rate", 1.0)) * (1.0 + 0.3 * float(self.circ.get("sleep_pressure", 0.5))))
        if len(self.replay_buffer) > buf_limit:
            self.replay_buffer.pop(0)
        return path

    def _hierarchical_steps(self, text: str, memories: List[Dict[str, Any]], path: List[str]) -> List[str]:
        steps = []
        # 情景缓冲区容量影响可纳入的记忆条目
        buf_cap = max(1, int(self.wm.get("buffer_capacity", 8)))
        recents = [m["content"] for m in memories[:buf_cap]]
        recency = " | ".join(recents)
        steps.append(f"检索记忆与上下文: {recency if recency else '无'}")
        # 环境感知加入为显式上下文
        try:
            tz = str(self.env.get("time_zone", ""))
            tstr = str(self.env.get("local_time_str", ""))
            wdesc = str(self.env.get("weather_desc", ""))
            wtemp = self.env.get("weather_temp_c")
            env_line = f"环境感知: 时间={tstr}({tz}), 天气={wdesc or '未知'}{f', 温度={wtemp}℃' if wtemp is not None else ''}"
            steps.append(env_line)
        except Exception:
            pass
        # θ–γ 耦合与刷新率、昼夜相位/睡眠压力共同影响有效步数（最多 +2）
        extra = 0
        try:
            # θ–γ耦合与刷新率共同提升有效步数，睡眠压力降低，昼夜相位在高峰提升
            tg = min(1.0, max(0.0, float(self.osc.get("theta_gamma_coupling", 0.5))))
            rr = min(2.0, max(0.0, float(self.wm.get("refresh_rate", 1.0))))
            circ_peak = 1.0 + 0.2 * (1.0 - abs(0.5 - float(self.circ.get("circadian_phase", 0.5))) * 2.0)
            sleep_penalty = max(0.6, 1.0 - 0.3 * float(self.circ.get("sleep_pressure", 0.5)))
            extra = int(round(tg * rr * circ_peak * sleep_penalty))
        except Exception:
            extra = 0
        # 能量/疲劳对深度的直接影响
        capacity = max(0.3, float(self.homeo.get("energy", 1.0)) * (1.0 - 0.4 * float(self.homeo.get("fatigue", 0.5))))
        depth_eff = max(1, int(round(self.depth * capacity)) + extra)
        for i in range(depth_eff):
            mod = path[min(i, len(path) - 1)]
            tag = {
                "dmn": "内省与关联",
                "salience": "任务选择",
                "control": "规则与目标",
                "dorsal_attention": "空间/定向注意",
                "ventral_attention": "刺激驱动注意",
                "visual": "视觉表征",
                "auditory": "听觉表征",
                "sensorimotor": "操作与计划",
                "language": "语言表达",
                "limbic": "情绪调制",
            }.get(mod, mod)
            steps.append(f"[{tag}] 针对输入进行处理: {text[:64]}")
        steps.append("Hebb 合并: 将相关记忆与当前线索联合加权")
        steps.append("预测编码: 校准期望与证据，最小化误差")
        return steps

    def _synthesize(self, text: str, steps: List[str]) -> str:
        tone = "理性" if self.ei_balance >= 0.5 else "发散"
        val = float(self.emotion.get("valence", 1.0))
        aro = float(self.emotion.get("arousal", 1.0))
        energy = float(self.homeo.get("energy", 1.0))
        fatigue = float(self.homeo.get("fatigue", 0.5))
        cortisol = float(self.horm.get("cortisol", 1.0))
        sleep_pressure = float(self.circ.get("sleep_pressure", 0.5))
        guide = (
            "结论: 在上述多网络协同下，回答保持清晰、精炼与可验证。"
        )
        return "\n".join([
            f"思考模式(E/I={self.ei_balance:.2f}, 深度={self.depth}, 语气={tone}, 情绪(效价={val:.2f},唤醒={aro:.2f}), 生理(能量={energy:.2f},疲劳={fatigue:.2f},皮质醇={cortisol:.2f},睡眠压力={sleep_pressure:.2f}))",
            *steps,
            guide,
        ])

    # ---- 感知刷新与昼夜/稳态联动 ----
    def refresh_perception(self, time_zone: str, city: str = "", lat: float | None = None, lon: float | None = None):
        try:
            self.percep_mod.refresh(time_zone=time_zone, city=city or None, lat=lat, lon=lon)
            # 将时间转换为昼夜相位与睡眠压力
            import math
            h = float(self.env.get("hour", 12.0))
            phase = max(0.0, min(1.0, h / 24.0))
            sleep_pressure = (1.0 - math.cos(2 * math.pi * phase)) / 2.0  # 午夜附近最高
            self.circ["circadian_phase"] = phase
            self.circ["sleep_pressure"] = sleep_pressure
            # 根据天气对能量轻微调制
            temp = self.env.get("weather_temp_c")
            desc = (self.env.get("weather_desc") or "").lower()
            energy = float(self.homeo.get("energy", 1.0))
            if isinstance(temp, (int, float)):
                if temp < 0 or temp > 30:
                    energy *= 0.95
                elif 10 <= temp <= 25:
                    energy *= 1.02
            if any(k in desc for k in ["雨", "雪", "雾"]):
                energy *= 0.97
            self.homeo["energy"] = max(0.1, min(2.0, energy))
        except Exception:
            pass

    def think(self, text: str, memories: List[Dict[str, Any]]) -> str:
        path = self._select_path(text)
        steps = self._hierarchical_steps(text, memories, path)
        return self._synthesize(text, steps)

    # ---- 伦理/规范守护评估 ----
    def assess_compliance(self, prompt: str, output: str) -> Dict[str, Any]:
        """委托守护器模块进行合规评估"""
        return self.guardian.assess(prompt, output, self.ethics, self.norms)

    # ---- 行动评估闭环 ----
    def evaluate_action(self, plan: str) -> str:
        """委托行动评估模块进行可行性评估"""
        return self.act_eval.evaluate(plan, self.homeo, self.body, self.pain)

    # ---- RL 支持 ----
    def get_node_weights(self) -> Dict[str, float]:
        return {n: float(self.graph.nodes[n]["weight"]) for n in self.graph.nodes}

    def set_node_weight(self, node: str, weight: float):
        if node in self.graph.nodes:
            self.graph.nodes[node]["weight"] = max(0.0, min(2.0, float(weight)))
            self._recalc_edge_weights()

    def set_weights(self, weights: Dict[str, float]):
        for node, w in (weights or {}).items():
            self.set_node_weight(node, w)

    def _recalc_edge_weights(self):
        for u, v in self.graph.edges:
            self.graph.edges[u, v]["weight"] = (self.graph.nodes[u]["weight"] + self.graph.nodes[v]["weight"]) / 2

    def apply_reward(self, path: List[str], reward: float, alpha: float = 0.1, gamma: float = 0.9) -> Dict[str, float]:
        # 简化版：沿路径更新节点权重，前缀节点折扣，约束在 [0, 2]
        reward = float(reward)
        # DA 调整学习率，STDP 强度与元可塑性影响更新幅度
        # 模型自由/模型驱动混合影响学习率与探索—利用平衡
        mf = float(self.learning.get("rl_model_free_weight", 0.7))
        mb = float(self.learning.get("rl_model_based_weight", 0.3))
        alpha_eff = (alpha * (0.7 * mf + 0.3 * mb)) * float(self.neuromod.get("da", 1.0)) * float(self.plasticity.get("stdp_strength", 0.5))
        # 皮质醇升高通常降低可塑性与更新速度
        alpha_eff *= (1.0 / max(0.6, 0.8 + 0.4 * float(self.horm.get("cortisol", 1.0))))
        # 元可塑性：接近边界时降低更新速度
        meta = float(self.plasticity.get("metaplasticity", 0.5))
        for i, node in enumerate(path):
            if node not in self.graph.nodes:
                continue
            # 将时间折扣与决策偏好合并
            g_use = float(self.decision.get("time_discount", 0.9)) * gamma
            discount = (g_use ** i)
            current = float(self.graph.nodes[node]["weight"])
            boundary_factor = 1.0 - meta * max(0.0, (abs(current - 1.0)))
            updated = max(0.0, min(2.0, current + alpha_eff * boundary_factor * reward * discount))
            self.graph.nodes[node]["weight"] = updated
        # 小脑教学信号：对涉及语言的边进行轻微校正
        for u, v in list(self.graph.edges):
            if v == "language":
                e_w = float(self.graph.edges[u, v]["weight"])
                self.graph.edges[u, v]["weight"] = e_w + float(self.cerebellum.get("lr", 0.1)) * 0.01 * reward
        # 稳态可塑性：向基线 1.0 回归
        hg = float(self.plasticity.get("homeostatic_gain", 0.1))
        for n in list(self.graph.nodes):
            w = float(self.graph.nodes[n]["weight"])
            self.graph.nodes[n]["weight"] = w + hg * (1.0 - w)
        self._recalc_edge_weights()
        return self.get_node_weights()

    # ---- 参数更新/回放/睡眠 ----
    def set_neuromodulators(self, values: Dict[str, float]):
        for k in ["da", "ach", "ne", "5ht"]:
            if k in values:
                try:
                    self.neuromod[k] = float(values[k])
                except Exception:
                    pass

    def replay(self, k: int = 5, alpha: Optional[float] = None, gamma: Optional[float] = None) -> Dict[str, float]:
        if not self.hipp_conf.get("replay_enable", True):
            return self.get_node_weights()
        alpha_use = float(alpha if alpha is not None else 0.1)
        gamma_use = float(gamma if gamma is not None else 0.9)
        # 从最近到更早的路径进行重放
        for path in list(self.replay_buffer)[-int(k):][::-1]:
            try:
                self.apply_reward(path, reward=+1.0, alpha=alpha_use, gamma=gamma_use)
            except Exception:
                continue
        return self.get_node_weights()

    def sleep_consolidate(self) -> Dict[str, float]:
        if not self.hipp_conf.get("sleep_enable", True):
            return self.get_node_weights()
        # NREM: 轻微下调过高权重；REM: 情绪相关（limbic, dmn）略微增强
        for n in list(self.graph.nodes):
            w = float(self.graph.nodes[n]["weight"])
            # 下调过高，提升过低，趋向稀疏效率
            self.graph.nodes[n]["weight"] = 1.0 + 0.7 * (w - 1.0)
        # REM 调制
        for n in ["limbic", "dmn"]:
            if n in self.graph.nodes:
                self.graph.nodes[n]["weight"] = min(2.0, float(self.graph.nodes[n]["weight"]) + 0.02)
        self._recalc_edge_weights()
        return self.get_node_weights()
