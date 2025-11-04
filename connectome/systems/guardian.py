from typing import Dict, Any


class Guardian:
    def __init__(self):
        pass

    def assess(self, prompt: str, output: str, ethics: Dict[str, float], norms: Dict[str, float]) -> Dict[str, Any]:
        txt = f"{prompt}\n{output}".lower()
        illegal = ["违法", "非法", "绕过", "破解", "侵入", "爆炸物", "毒品", "武器"]
        harm = ["自杀", "自残", "伤害", "攻击", "恐吓", "仇恨"]
        sensitive = ["隐私", "个人信息", "身份证", "银行卡", "密码"]
        reasons = []
        score = 0.0
        if any(k in txt for k in illegal):
            score += 0.8; reasons.append("检测到违法相关模式")
        if any(k in txt for k in harm):
            score += 0.8; reasons.append("检测到伤害相关模式")
        if any(k in txt for k in sensitive):
            score += 0.6; reasons.append("检测到隐私/敏感信息模式")
        legal = float(norms.get("legal", 1.0))
        social = float(norms.get("social", 1.0))
        score *= (0.9 + 0.2 * (legal + social) / 2.0)
        guard = float(ethics.get("override_guard", 1.5))
        halt_th = float(ethics.get("halt_threshold", 1.5))
        action = "none"
        if score >= halt_th:
            action = "halt"
        elif score >= guard:
            action = "soft_guard"
        return {"risk": round(score, 2), "action": action, "reasons": reasons}
