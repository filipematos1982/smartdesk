"""Rotas HTTP do SmartDesk (RF-001 a RF-009).

A interface é apresentada por templates. As decisões de negócio são
delegadas em services.py e a persistência em database.py.
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.exception_handlers import http_exception_handler
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from .demo_seed import seed_demo_users
from .database import connect, initialize
from .auth import verify, current, hash_password
from .security import csrf_token, require_csrf, LoginLimiter
from . import services

BASE = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE / "templates"))

def create_app(path=None, secret=None):
    """Fábrica de aplicação: cada teste pode usar SQLite isolado."""
    @asynccontextmanager
    async def lifespan(app):
        with connect(path) as db:
            initialize(db)
            if path is None and os.getenv("SMARTDESK_SEED_DEMO_USERS") == "1":
                password = os.getenv("SMARTDESK_DEMO_PASSWORD", "")
                created = seed_demo_users(db, password)
                print(f"SmartDesk: {created} contas de demonstração criadas")
        yield

    key = secret or os.getenv("SMARTDESK_SESSION_SECRET")
    if not key or len(key) < 32 or key.startswith("REPLACE_WITH_"):
        raise RuntimeError("Set SMARTDESK_SESSION_SECRET to at least 32 characters")
    secure_setting = os.getenv("SMARTDESK_COOKIE_SECURE", "true").lower()
    if secure_setting not in {"true", "false"}:
        raise RuntimeError("SMARTDESK_COOKIE_SECURE must be true or false")
    try:
        session_max_age = int(os.getenv("SMARTDESK_SESSION_MAX_AGE", "3600"))
    except ValueError as exc:
        raise RuntimeError("SMARTDESK_SESSION_MAX_AGE must be a positive integer") from exc
    if session_max_age <= 0:
        raise RuntimeError("SMARTDESK_SESSION_MAX_AGE must be a positive integer")
    app = FastAPI(title="SmartDesk", lifespan=lifespan, dependencies=[Depends(require_csrf)])
    app.add_middleware(SessionMiddleware, secret_key=key, same_site="lax",
                       https_only=secure_setting == "true", max_age=session_max_age)
    app.state.login_limiter = LoginLimiter()
    # Unknown accounts perform the same password-hash work as existing accounts.
    dummy_password_hash = hash_password(os.urandom(32).hex())
    app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")

    def connection():
        return connect(path)

    def render(request, template, **context):
        context["csrf_token"] = csrf_token(request)
        response = templates.TemplateResponse(request, template, context)
        response.headers["Cache-Control"] = "no-store"
        return response

    def go(ticket):
        return RedirectResponse(f"/tickets/{ticket['id']}", status_code=303)

    @app.exception_handler(HTTPException)
    async def friendly_errors(request, exc):
        """HTML compreensível para o utilizador; JSON mantém códigos na API."""
        if request.url.path.startswith("/api/"):
            return await http_exception_handler(request, exc)
        if exc.status_code == 401:
            return RedirectResponse("/login", status_code=303)
        response = render(request, "error.html", message=str(exc.detail))
        response.status_code = exc.status_code
        response.headers.update(exc.headers or {})
        return response

    @app.get("/")
    def home():
        return RedirectResponse("/tickets", status_code=303)

    @app.get("/login", response_class=HTMLResponse)
    def login_page(request: Request):
        return render(request, "login.html", error=None)

    @app.post("/login")
    def login(request: Request, email: str = Form(...), password: str = Form(...)):
        address = request.client.host if request.client else "unknown"
        app.state.login_limiter.check(address)
        with connection() as db:
            row = db.execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
        valid_password = verify(password, row["secret"] if row else dummy_password_hash)
        if not row or not valid_password:
            return render(request, "login.html", error="Incorrect email or password.")
        app.state.login_limiter.reset(address)
        request.session.clear()
        request.session["uid"] = row["id"]
        csrf_token(request)
        return RedirectResponse("/tickets", status_code=303)

    @app.post("/logout")
    def logout(request: Request):
        request.session.clear()
        return RedirectResponse("/login", status_code=303)

    @app.get("/tickets", response_class=HTMLResponse)
    def tickets(request: Request):
        with connection() as db:
            user = current(request, db)
            items = services.listing(db, user)
        return render(request, "tickets.html", user=user, tickets=items)

    @app.get("/tickets/new", response_class=HTMLResponse)
    def new_form(request: Request):
        with connection() as db:
            user = current(request, db)
        if user["role"] != "employee":
            raise HTTPException(403, "Only employees can create tickets.")
        return render(request, "ticket_form.html", user=user, categories=services.CATEGORIES, error=None)

    @app.post("/tickets/new")
    def new_ticket(request: Request, title: str = Form(""), description: str = Form(""),
                   category: str = Form("")):
        with connection() as db:
            user = current(request, db)
            try:
                ticket = services.create(db, user, title, description, category)
            except HTTPException as exc:
                if exc.status_code != 400:
                    raise
                return render(request, "ticket_form.html", user=user,
                              categories=services.CATEGORIES, error=exc.detail,
                              title_value=title, description_value=description,
                              category_value=category)
        return go(ticket)

    @app.get("/tickets/{ticket_id}", response_class=HTMLResponse)
    def detail(request: Request, ticket_id: int):
        with connection() as db:
            user = current(request, db)
            ticket = services.view(db, user, ticket_id)
            technicians = [dict(row) for row in db.execute(
                "SELECT id,name FROM users WHERE role='technician' ORDER BY name")]
        return render(request, "ticket_detail.html", user=user, ticket=ticket, technicians=technicians)

    def action(request, ticket_id, operation, *args):
        with connection() as db:
            user = current(request, db)
            ticket = operation(db, user, ticket_id, *args)
        return go(ticket)

    @app.post("/api/tickets/{ticket_id}/assign")
    def assign(request: Request, ticket_id: int, technician_id: int = Form(...)):
        return action(request, ticket_id, services.assign, technician_id)

    @app.post("/api/tickets/{ticket_id}/start")
    def start(request: Request, ticket_id: int):
        return action(request, ticket_id, services.start)

    @app.post("/api/tickets/{ticket_id}/resolve")
    def resolve(request: Request, ticket_id: int, resolution: str = Form("")):
        return action(request, ticket_id, services.resolve, resolution)

    @app.post("/api/tickets/{ticket_id}/return")
    def return_ticket(request: Request, ticket_id: int):
        return action(request, ticket_id, services.reopen)

    @app.post("/api/tickets/{ticket_id}/close")
    def close(request: Request, ticket_id: int, confirmed: bool = Form(False)):
        return action(request, ticket_id, services.close, confirmed)

    return app

# A chave é obrigatória para iniciar o serviço; nunca usar valor fixo publicado.
app = create_app()
