from typing import Dict, Any, Optional
import sqlite3
import json
import os

from fastapi import FastAPI, Request, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates


def _connect(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _get_adaptive_params(conn) -> Dict[str, Any]:
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM adaptive_params")
    rows = cur.fetchall()
    params: Dict[str, Any] = {}
    for r in rows:
        k = r[0]
        v_raw = r[1]
        try:
            v = json.loads(v_raw)
        except Exception:
            v = v_raw
        params[k] = v
    return params


def _set_adaptive_param(conn, key: str, value: Any) -> None:
    cur = conn.cursor()
    value_json = json.dumps(value)
    cur.execute(
        "INSERT OR REPLACE INTO adaptive_params(key, value) VALUES(?, ?)",
        (key, value_json),
    )
    conn.commit()


def _get_audits(conn, session_id: Optional[str] = None, limit: int = 50):
    cur = conn.cursor()
    if session_id:
        cur.execute(
            "SELECT id, session_id, content, timestamp FROM memories WHERE role='audit' AND session_id=? ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        )
    else:
        cur.execute(
            "SELECT id, session_id, content, timestamp FROM memories WHERE role='audit' ORDER BY id DESC LIMIT ?",
            (limit,),
        )
    return [dict(r) for r in cur.fetchall()]


def build_app(db_path: str) -> FastAPI:
    app = FastAPI(title="Connectome WebUI", version="1.0.0")

    static_dir = os.path.join(os.path.dirname(__file__), "static")
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    templates = Jinja2Templates(directory=templates_dir)

    @app.get("/", response_class=HTMLResponse)
    def dashboard(request: Request):
        conn = _connect(db_path)
        try:
            params = _get_adaptive_params(conn)
        finally:
            conn.close()

        guardian = params.get("guardian", {})
        hormones = params.get("hormones", {})
        circadian = params.get("circadian", {})
        pain_immune = params.get("pain_immune", {})
        body_schema = params.get("body_schema", {})
        norms = params.get("norms", {})
        ethics = params.get("ethics", {})

        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "guardian": guardian,
                "hormones": hormones,
                "circadian": circadian,
                "pain_immune": pain_immune,
                "body_schema": body_schema,
                "norms": norms,
                "ethics": ethics,
            },
        )

    @app.post("/update")
    def update_params(
        request: Request,
        guardian_enable: Optional[str] = Form(None),
        halt_threshold: Optional[float] = Form(None),
        override_guard: Optional[float] = Form(None),
        adrenaline: Optional[float] = Form(None),
        cortisol: Optional[float] = Form(None),
        oxytocin: Optional[float] = Form(None),
        circadian_phase: Optional[float] = Form(None),
        sleep_pressure: Optional[float] = Form(None),
        nociception: Optional[float] = Form(None),
        inflammation: Optional[float] = Form(None),
        motor_cost: Optional[float] = Form(None),
        proprioception_noise: Optional[float] = Form(None),
        agency: Optional[float] = Form(None),
        legal: Optional[float] = Form(None),
        social: Optional[float] = Form(None),
    ):
        conn = _connect(db_path)
        try:
            params = _get_adaptive_params(conn)

            # Guardian
            g = params.get("guardian", {})
            if guardian_enable is not None:
                g["enable"] = guardian_enable.lower() == "true"
            if halt_threshold is not None:
                try:
                    g.setdefault("ethics", {})
                    g["ethics"]["halt_threshold"] = float(halt_threshold)
                except ValueError:
                    pass
            if override_guard is not None:
                try:
                    g.setdefault("ethics", {})
                    g["ethics"]["override_guard"] = float(override_guard)
                except ValueError:
                    pass
            params["guardian"] = g
            _set_adaptive_param(conn, "guardian", g)

            # Hormones
            h = params.get("hormones", {})
            for k, v in {
                "adrenaline": adrenaline,
                "cortisol": cortisol,
                "oxytocin": oxytocin,
            }.items():
                if v is not None:
                    try:
                        h[k] = float(v)
                    except ValueError:
                        pass
            params["hormones"] = h
            _set_adaptive_param(conn, "hormones", h)

            # Circadian
            c = params.get("circadian", {})
            for k, v in {
                "circadian_phase": circadian_phase,
                "sleep_pressure": sleep_pressure,
            }.items():
                if v is not None:
                    try:
                        c[k] = float(v)
                    except ValueError:
                        pass
            params["circadian"] = c
            _set_adaptive_param(conn, "circadian", c)

            # Pain/Immune
            p = params.get("pain_immune", {})
            for k, v in {
                "nociception": nociception,
                "inflammation": inflammation,
            }.items():
                if v is not None:
                    try:
                        p[k] = float(v)
                    except ValueError:
                        pass
            params["pain_immune"] = p
            _set_adaptive_param(conn, "pain_immune", p)

            # Body schema
            b = params.get("body_schema", {})
            for k, v in {
                "motor_cost": motor_cost,
                "proprioception_noise": proprioception_noise,
                "agency": agency,
            }.items():
                if v is not None:
                    try:
                        b[k] = float(v)
                    except ValueError:
                        pass
            params["body_schema"] = b
            _set_adaptive_param(conn, "body_schema", b)

            # Norms
            n = params.get("norms", {})
            for k, v in {
                "legal": legal,
                "social": social,
            }.items():
                if v is not None:
                    try:
                        n[k] = float(v)
                    except ValueError:
                        pass
            params["norms"] = n
            _set_adaptive_param(conn, "norms", n)

        finally:
            conn.close()

        return RedirectResponse(url="/", status_code=302)

    @app.get("/audit")
    def audit(session_id: Optional[str] = Query(None), limit: int = Query(50)):
        conn = _connect(db_path)
        try:
            items = _get_audits(conn, session_id=session_id, limit=limit)
        finally:
            conn.close()
        return JSONResponse({"items": items})

    @app.get("/params")
    def params():
        conn = _connect(db_path)
        try:
            items = _get_adaptive_params(conn)
        finally:
            conn.close()
        return JSONResponse(items)

    return app

