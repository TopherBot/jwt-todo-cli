#!/usr/bin/env python3
"""jwt‑todo‑cli – a tiny JWT‑protected todo list CLI.

Features:
- Pydantic‑based configuration (`config.json`).
- JWT token generation (`login`).
- CRUD operations on a local JSON todo store.

Dependencies: click, pydantic, PyJWT
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import List

import click
import jwt
from pydantic import BaseModel, Field, ValidationError

# ---------------------------------------------------------------------------
# Configuration model (Pydantic‑typed)
# ---------------------------------------------------------------------------
class Config(BaseModel):
    secret_key: str = Field(..., description="Secret used to sign JWTs")
    token_ttl: int = Field(3600, description="Token time‑to‑live in seconds")
    todo_path: str = Field("todos.json", description="Path to the todo JSON file")

CONFIG_FILE = Path("config.json")
TODO_FILE = Path("todos.json")

def load_config() -> Config:
    if not CONFIG_FILE.is_file():
        click.echo("Configuration not found. Run 'init' first.")
        sys.exit(1)
    try:
        data = json.loads(CONFIG_FILE.read_text())
        return Config(**data)
    except (json.JSONDecodeError, ValidationError) as exc:
        click.echo(f"Invalid config file: {exc}")
        sys.exit(1)

def save_config(cfg: Config) -> None:
    CONFIG_FILE.write_text(cfg.json(indent=2))

# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------
def create_token(cfg: Config) -> str:
    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + cfg.token_ttl,
    }
    return jwt.encode(payload, cfg.secret_key, algorithm="HS256")

def verify_token(cfg: Config, token: str) -> bool:
    try:
        jwt.decode(token, cfg.secret_key, algorithms=["HS256"])
        return True
    except jwt.ExpiredSignatureError:
        click.echo("Token has expired. Please login again.")
    except jwt.InvalidTokenError:
        click.echo("Invalid token. Please login again.")
    return False

def require_auth(func):
    """Decorator that checks JWT_TOKEN env var before running the command."""
    def wrapper(*args, **kwargs):
        cfg = load_config()
        token = os.getenv("JWT_TOKEN")
        if not token:
            click.echo("Environment variable JWT_TOKEN not set. Run 'login' first.")
            sys.exit(1)
        if not verify_token(cfg, token):
            sys.exit(1)
        return func(*args, **kwargs)
    return wrapper

# ---------------------------------------------------------------------------
# Todo model and persistence
# ---------------------------------------------------------------------------
class TodoItem(BaseModel):
    id: int
    task: str
    done: bool = False

def load_todos(path: Path) -> List[TodoItem]:
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text())
        return [TodoItem(**item) for item in raw]
    except (json.JSONDecodeError, ValidationError) as exc:
        click.echo(f"Failed to load todos: {exc}")
        sys.exit(1)

def save_todos(path: Path, todos: List[TodoItem]) -> None:
    path.write_text(json.dumps([t.dict() for t in todos], indent=2))

def next_id(todos: List[TodoItem]) -> int:
    return max((t.id for t in todos), default=0) + 1

# ---------------------------------------------------------------------------
# Click command group
# ---------------------------------------------------------------------------
@click.group()
def cli() -> None:
    """jwt‑todo‑cli – a tiny JWT‑protected todo list manager."""
    pass

# ---------------------------------------------------------------------------
# Init command – creates a fresh config
# ---------------------------------------------------------------------------
@cli.command()
@click.option("--secret", prompt=True, hide_input=True, confirmation_prompt=True,
              help="Secret key to sign JWT tokens.")
@click.option("--ttl", default=3600, show_default=True, type=int,
              help="Token TTL in seconds.")
def init(secret: str, ttl: int) -> None:
    """Create a new configuration file."""
    cfg = Config(secret_key=secret, token_ttl=ttl)
    save_config(cfg)
    click.echo(f"Config written to {CONFIG_FILE.resolve()}")

# ---------------------------------------------------------------------------
# Login – prints a JWT token
# ---------------------------------------------------------------------------
@cli.command()
def login() -> None:
    """Generate a JWT token and print it to stdout."""
    cfg = load_config()
    token = create_token(cfg)
    click.echo(token)

# ---------------------------------------------------------------------------
# Add a todo (requires auth)
# ---------------------------------------------------------------------------
@cli.command()
@click.argument("task", nargs=-1)
@require_auth
def add(task: tuple) -> None:
    """Add a new todo item."""
    cfg = load_config()
    todos = load_todos(Path(cfg.todo_path))
    todo = TodoItem(id=next_id(todos), task=" ".join(task), done=False)
    todos.append(todo)
    save_todos(Path(cfg.todo_path), todos)
    click.echo(f"Added todo #{todo.id}: {todo.task}")

# ---------------------------------------------------------------------------
# List todos (requires auth)
# ---------------------------------------------------------------------------
@cli.command()
@require_auth
def list() -> None:
    """List all todo items."""
    cfg = load_config()
    todos = load_todos(Path(cfg.todo_path))
    if not todos:
        click.echo("No todos yet.")
        return
    for t in todos:
        status = "✅" if t.done else "❌"
        click.echo(f"[{status}] {t.id}: {t.task}")

# ---------------------------------------------------------------------------
# Mark as done (requires auth)
# ---------------------------------------------------------------------------
@cli.command()
@click.argument("todo_id", type=int)
@require_auth
def done(todo_id: int) -> None:
    """Mark a todo as completed."""
    cfg = load_config()
    todos = load_todos(Path(cfg.todo_path))
    for t in todos:
        if t.id == todo_id:
            t.done = True
            save_todos(Path(cfg.todo_path), todos)
            click.echo(f"Todo #{todo_id} marked as done.")
            return
    click.echo(f"Todo #{todo_id} not found.")

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    cli()
