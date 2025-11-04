import json
import os
from fastapi import FastAPI
from .app import build_app


def _load_config():
    base = os.path.dirname(__file__)
    cfg_path = os.path.join(base, "config.json")
    # 优先读取环境变量（由插件传入）
    env_db = os.getenv("CONNECTOME_DB_PATH")
    db_path = env_db or os.path.join(os.getcwd(), "connectome_memory.db")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            db_path = cfg.get("db_path", db_path)
        except Exception:
            pass
    return db_path


def create_app() -> FastAPI:
    db_path = _load_config()
    return build_app(db_path)


# for uvicorn entrypoint: uvicorn webui.run:app
app = create_app()
