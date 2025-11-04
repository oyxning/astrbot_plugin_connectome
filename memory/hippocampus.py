import os
import sqlite3
import time
from typing import List, Dict, Any
import json


class Hippocampus:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        # 确保目录存在
        dir_name = os.path.dirname(os.path.abspath(self.db_path))
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

        with sqlite3.connect(self.db_path, timeout=10) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    created_at INTEGER
                )
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memories_session
                ON memories(session_id, created_at DESC)
                """
            )
            # 强化学习权重表
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS rl_weights (
                    node TEXT PRIMARY KEY,
                    weight REAL
                )
                """
            )
            # 自适应参数持久化（JSON blob）
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS adaptive_params (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """
            )
            conn.commit()

    def add_memory(self, session_id: str, role: str, content: str):
        ts = int(time.time())
        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO memories(session_id, role, content, created_at) VALUES(?,?,?,?)",
                    (session_id, role, content, ts),
                )
                conn.commit()
        except Exception:
            # 静默失败，避免打断会话；可结合 astrbot.logger 进一步报告
            pass

    def get_recent(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT role, content, created_at FROM memories WHERE session_id=? ORDER BY created_at DESC LIMIT ?",
                (session_id, limit),
            )
            rows = cur.fetchall()
        return [
            {"role": r[0], "content": r[1], "created_at": r[2]} for r in rows
        ]

    def get_audit(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取审计日志（role='audit'）"""
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT role, content, created_at FROM memories WHERE session_id=? AND role='audit' ORDER BY created_at DESC LIMIT ?",
                (session_id, limit),
            )
            rows = cur.fetchall()
        return [{"role": r[0], "content": r[1], "created_at": r[2]} for r in rows]

    def prune_session(self, session_id: str, max_items: int):
        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT id FROM memories WHERE session_id=? ORDER BY created_at DESC",
                    (session_id,),
                )
                ids = [row[0] for row in cur.fetchall()]
                if len(ids) > max_items:
                    to_delete = ids[max_items:]
                    cur.executemany("DELETE FROM memories WHERE id=?", [(i,) for i in to_delete])
                    conn.commit()
        except Exception:
            pass

    # ---- RL 权重持久化 ----
    def load_rl_weights(self) -> Dict[str, float]:
        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                cur = conn.cursor()
                cur.execute("SELECT node, weight FROM rl_weights")
                rows = cur.fetchall()
                return {r[0]: float(r[1]) for r in rows}
        except Exception:
            return {}

    def save_rl_weights(self, weights: Dict[str, float]):
        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                cur = conn.cursor()
                for node, w in weights.items():
                    cur.execute(
                        """
                        INSERT INTO rl_weights(node, weight) VALUES(?,?)
                        ON CONFLICT(node) DO UPDATE SET weight=excluded.weight
                        """,
                        (node, float(w)),
                    )
                conn.commit()
        except Exception:
            pass

    # ---- 自适应参数持久化 ----
    def load_adaptive_params(self) -> Dict[str, Any]:
        try:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                cur = conn.cursor()
                cur.execute("SELECT value FROM adaptive_params WHERE key=?", ("global",))
                row = cur.fetchone()
                if not row:
                    return {}
                return json.loads(row[0])
        except Exception:
            return {}

    def save_adaptive_params(self, params: Dict[str, Any]):
        try:
            blob = json.dumps(params, ensure_ascii=False)
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO adaptive_params(key, value) VALUES(?,?)
                    ON CONFLICT(key) DO UPDATE SET value=excluded.value
                    """,
                    ("global", blob),
                )
                conn.commit()
        except Exception:
            pass
