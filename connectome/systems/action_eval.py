class ActionEvaluator:
    def __init__(self):
        pass

    def evaluate(self, plan: str, homeo: dict, body: dict, pain: dict) -> str:
        energy = float(homeo.get("energy", 1.0))
        fatigue = float(homeo.get("fatigue", 0.5))
        motor_cost = float(body.get("motor_cost", 1.0))
        pain_load = min(2.0, float(pain.get("nociception", 0.0)) + 0.5 * float(pain.get("inflammation", 0.0)))
        agency = float(body.get("agency", 1.0))
        feasibility = energy * (1.0 - 0.4 * fatigue) * agency - 0.3 * motor_cost - 0.3 * pain_load
        decision = "批准" if feasibility >= 0.6 else ("谨慎执行" if feasibility >= 0.3 else "拒绝")
        lines = [
            f"行动评估: {plan}",
            f"状态(能量={energy:.2f}, 疲劳={fatigue:.2f}, 代价={motor_cost:.2f}, 疼痛负荷={pain_load:.2f}, 代理={agency:.2f})",
            f"可行性评分={feasibility:.2f} → 决策: {decision}",
            "建议: 若评分偏低，可降低动作代价或提升能量/降低疲劳。",
        ]
        return "\n".join(lines)
