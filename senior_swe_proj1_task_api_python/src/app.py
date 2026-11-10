"""
Task Management REST API (Flask).

A small but realistic backend service: CRUD endpoints over an in-memory
task store, with input validation, proper HTTP status codes, structured
error responses, and pagination/filtering — the basics of a production
API surface, kept dependency-light on purpose.

Endpoints:
  POST   /tasks              create a task
  GET    /tasks               list tasks (supports ?status= and ?limit=/?offset=)
  GET    /tasks/<id>          get one task
  PATCH  /tasks/<id>          partially update a task
  DELETE /tasks/<id>          delete a task
  GET    /health              liveness check
"""
from __future__ import annotations

import itertools
import re
from datetime import datetime, timezone
from http import HTTPStatus

from flask import Flask, jsonify, request

app = Flask(__name__)

VALID_STATUSES = {"todo", "in_progress", "done"}
_id_counter = itertools.count(1)
_tasks: dict[int, dict] = {}


class ValidationError(Exception):
    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.message = message
        self.field = field


@app.errorhandler(ValidationError)
def handle_validation_error(err: ValidationError):
    body = {"error": "validation_error", "message": err.message}
    if err.field:
        body["field"] = err.field
    return jsonify(body), HTTPStatus.BAD_REQUEST


@app.errorhandler(404)
def handle_not_found(_err):
    return jsonify({"error": "not_found", "message": "Resource not found"}), HTTPStatus.NOT_FOUND


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_title(title) -> str:
    if not isinstance(title, str) or not title.strip():
        raise ValidationError("title is required and must be a non-empty string", field="title")
    if len(title) > 200:
        raise ValidationError("title must be 200 characters or fewer", field="title")
    return title.strip()


def _validate_status(status) -> str:
    if status not in VALID_STATUSES:
        raise ValidationError(
            f"status must be one of {sorted(VALID_STATUSES)}", field="status"
        )
    return status


def _validate_priority(priority) -> int:
    if priority is None:
        return 3
    if not isinstance(priority, int) or not (1 <= priority <= 5):
        raise ValidationError("priority must be an integer between 1 and 5", field="priority")
    return priority


@app.get("/health")
def health():
    return jsonify({"status": "ok", "time": _now()})


@app.post("/tasks")
def create_task():
    payload = request.get_json(silent=True) or {}

    title = _validate_title(payload.get("title"))
    status = _validate_status(payload.get("status", "todo"))
    priority = _validate_priority(payload.get("priority"))

    task_id = next(_id_counter)
    task = {
        "id": task_id,
        "title": title,
        "status": status,
        "priority": priority,
        "created_at": _now(),
        "updated_at": _now(),
    }
    _tasks[task_id] = task
    return jsonify(task), HTTPStatus.CREATED


@app.get("/tasks")
def list_tasks():
    status_filter = request.args.get("status")
    if status_filter is not None and status_filter not in VALID_STATUSES:
        raise ValidationError(f"status must be one of {sorted(VALID_STATUSES)}", field="status")

    items = list(_tasks.values())
    if status_filter:
        items = [t for t in items if t["status"] == status_filter]

    items.sort(key=lambda t: t["id"])

    limit = request.args.get("limit", default=50, type=int)
    offset = request.args.get("offset", default=0, type=int)
    if limit is None or limit < 1 or limit > 200:
        raise ValidationError("limit must be between 1 and 200", field="limit")
    if offset is None or offset < 0:
        raise ValidationError("offset must be >= 0", field="offset")

    page = items[offset: offset + limit]
    return jsonify({"items": page, "total": len(items), "limit": limit, "offset": offset})


@app.get("/tasks/<int:task_id>")
def get_task(task_id: int):
    task = _tasks.get(task_id)
    if task is None:
        return jsonify({"error": "not_found", "message": f"task {task_id} not found"}), HTTPStatus.NOT_FOUND
    return jsonify(task)


@app.patch("/tasks/<int:task_id>")
def update_task(task_id: int):
    task = _tasks.get(task_id)
    if task is None:
        return jsonify({"error": "not_found", "message": f"task {task_id} not found"}), HTTPStatus.NOT_FOUND

    payload = request.get_json(silent=True) or {}
    if not payload:
        raise ValidationError("request body must contain at least one field to update")

    if "title" in payload:
        task["title"] = _validate_title(payload["title"])
    if "status" in payload:
        task["status"] = _validate_status(payload["status"])
    if "priority" in payload:
        task["priority"] = _validate_priority(payload["priority"])

    task["updated_at"] = _now()
    return jsonify(task)


@app.delete("/tasks/<int:task_id>")
def delete_task(task_id: int):
    if task_id not in _tasks:
        return jsonify({"error": "not_found", "message": f"task {task_id} not found"}), HTTPStatus.NOT_FOUND
    del _tasks[task_id]
    return "", HTTPStatus.NO_CONTENT


def reset_store():
    """Test helper: clears in-memory state between test cases."""
    _tasks.clear()
    global _id_counter
    _id_counter = itertools.count(1)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
