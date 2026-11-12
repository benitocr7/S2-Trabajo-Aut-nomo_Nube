import os

import psycopg
from flask import Flask, jsonify, request
from psycopg.rows import dict_row

app = Flask(__name__)

TASK_COLUMNS = "id, title, description, done, created_at"


def get_connection():
    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=os.environ.get("DB_PORT", "5432"),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        row_factory=dict_row,
    )


def validate_task_fields(data, *, creating):
    if not isinstance(data, dict):
        return None, "A JSON object is required."

    allowed_fields = {"title", "description", "done"}
    unknown_fields = data.keys() - allowed_fields
    if unknown_fields:
        return None, f"Unknown field(s): {', '.join(sorted(unknown_fields))}."

    if creating and "title" not in data:
        return None, "The title field is required."
    if not creating and not data:
        return None, "Provide at least one field to update."

    if "title" in data and (
        not isinstance(data["title"], str) or not data["title"].strip()
    ):
        return None, "The title must be a non-empty string."
    if "description" in data and not isinstance(data["description"], str):
        return None, "The description must be a string."
    if "done" in data and not isinstance(data["done"], bool):
        return None, "The done field must be a boolean."

    return data, None


@app.get("/health")
def health():
    with get_connection() as connection:
        connection.execute("SELECT 1")
    return jsonify({"status": "ok", "database": "connected"})


@app.get("/api/tasks")
def list_tasks():
    with get_connection() as connection:
        tasks = connection.execute(
            f"SELECT {TASK_COLUMNS} FROM tasks ORDER BY id"
        ).fetchall()
    return jsonify(tasks)


@app.post("/api/tasks")
def create_task():
    data, error = validate_task_fields(request.get_json(silent=True), creating=True)
    if error:
        return jsonify({"error": error}), 400

    with get_connection() as connection:
        task = connection.execute(
            f"""INSERT INTO tasks (title, description, done)
                VALUES (%s, %s, %s)
                RETURNING {TASK_COLUMNS}""",
            (
                data["title"].strip(),
                data.get("description", ""),
                data.get("done", False),
            ),
        ).fetchone()
    return jsonify(task), 201


@app.get("/api/tasks/<int:task_id>")
def get_task(task_id):
    with get_connection() as connection:
        task = connection.execute(
            f"SELECT {TASK_COLUMNS} FROM tasks WHERE id = %s", (task_id,)
        ).fetchone()
    if task is None:
        return jsonify({"error": "Task not found."}), 404
    return jsonify(task)


@app.patch("/api/tasks/<int:task_id>")
def update_task(task_id):
    data, error = validate_task_fields(request.get_json(silent=True), creating=False)
    if error:
        return jsonify({"error": error}), 400

    with get_connection() as connection:
        current = connection.execute(
            f"SELECT {TASK_COLUMNS} FROM tasks WHERE id = %s", (task_id,)
        ).fetchone()
        if current is None:
            return jsonify({"error": "Task not found."}), 404

        updated = {
            "title": data.get("title", current["title"]),
            "description": data.get("description", current["description"]),
            "done": data.get("done", current["done"]),
        }
        task = connection.execute(
            f"""UPDATE tasks SET title = %s, description = %s, done = %s
                WHERE id = %s
                RETURNING {TASK_COLUMNS}""",
            (
                updated["title"].strip(),
                updated["description"],
                updated["done"],
                task_id,
            ),
        ).fetchone()
    return jsonify(task)


@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    with get_connection() as connection:
        deleted = connection.execute(
            "DELETE FROM tasks WHERE id = %s RETURNING id", (task_id,)
        ).fetchone()
    if deleted is None:
        return jsonify({"error": "Task not found."}), 404
    return "", 204
