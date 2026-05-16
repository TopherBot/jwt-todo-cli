# jwt‑todo‑cli

A **tiny** command‑line todo list manager that requires a JWT token for every operation. perfect for learning Pydantic models, JWT handling and Click‑based CLIs.

## Features
- Store todos in a local `todos.json` file.
- Authenticate with a short‑lived JWT token generated from a password.
- Pydantic‑validated configuration (`config.json`).
- Simple commands: `login`, `add`, `list`, `done`.

## Installation
```bash
# Clone the repo (or copy the single file)
git clone https://example.com/jwt-todo-cli.git
cd jwt-todo-cli

# Install dependencies in a virtualenv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # optional: the project is tiny, you can also install manually
```

If you only have the `todo_cli.py` file, just run:
```bash
pip install click pydantic PyJWT
```

## Usage
```bash
# First time: create a config (sets a secret key)
python3 todo_cli.py init

# Login – you will get a JWT token printed; store it in an env var
export JWT_TOKEN=$(python3 todo_cli.py login)

# Add a todo
python3 todo_cli.py add "Buy milk"

# List todos
python3 todo_cli.py list

# Mark as done (by ID)
python3 todo_cli.py done 1
```

All commands (except `init` and `login`) require the `JWT_TOKEN` environment variable.

## License
MIT – see the `LICENSE` file in the repository.
