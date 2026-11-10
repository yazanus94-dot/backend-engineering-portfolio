"""
Test suite for the Task Management API, written against Python's built-in
unittest (no external test runner required to execute it — though the
tests are pytest-discoverable too, since pytest can run unittest.TestCase
classes directly if you have pytest installed).

Run: python -m unittest discover -s tests -v
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app import app, reset_store  # noqa: E402


class TaskApiTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        reset_store()

    # --- creation & validation ---

    def test_create_task_success(self):
        resp = self.client.post("/tasks", json={"title": "Write unit tests"})
        self.assertEqual(resp.status_code, 201)
        body = resp.get_json()
        self.assertEqual(body["title"], "Write unit tests")
        self.assertEqual(body["status"], "todo")
        self.assertEqual(body["priority"], 3)
        self.assertIn("id", body)

    def test_create_task_missing_title_rejected(self):
        resp = self.client.post("/tasks", json={})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json()["field"], "title")

    def test_create_task_blank_title_rejected(self):
        resp = self.client.post("/tasks", json={"title": "   "})
        self.assertEqual(resp.status_code, 400)

    def test_create_task_title_too_long_rejected(self):
        resp = self.client.post("/tasks", json={"title": "x" * 201})
        self.assertEqual(resp.status_code, 400)

    def test_create_task_invalid_status_rejected(self):
        resp = self.client.post("/tasks", json={"title": "A", "status": "bogus"})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json()["field"], "status")

    def test_create_task_invalid_priority_rejected(self):
        resp = self.client.post("/tasks", json={"title": "A", "priority": 99})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json()["field"], "priority")

    def test_create_task_title_whitespace_is_trimmed(self):
        resp = self.client.post("/tasks", json={"title": "  padded title  "})
        self.assertEqual(resp.get_json()["title"], "padded title")

    # --- retrieval ---

    def test_get_task_not_found(self):
        resp = self.client.get("/tasks/999")
        self.assertEqual(resp.status_code, 404)

    def test_get_task_found(self):
        created = self.client.post("/tasks", json={"title": "A"}).get_json()
        resp = self.client.get(f"/tasks/{created['id']}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["id"], created["id"])

    # --- listing, filtering, pagination ---

    def test_list_tasks_empty(self):
        resp = self.client.get("/tasks")
        body = resp.get_json()
        self.assertEqual(body["items"], [])
        self.assertEqual(body["total"], 0)

    def test_list_tasks_filter_by_status(self):
        self.client.post("/tasks", json={"title": "A", "status": "todo"})
        self.client.post("/tasks", json={"title": "B", "status": "done"})
        resp = self.client.get("/tasks?status=done")
        body = resp.get_json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["items"][0]["title"], "B")

    def test_list_tasks_invalid_status_filter_rejected(self):
        resp = self.client.get("/tasks?status=not_a_status")
        self.assertEqual(resp.status_code, 400)

    def test_list_tasks_pagination(self):
        for i in range(5):
            self.client.post("/tasks", json={"title": f"Task {i}"})
        resp = self.client.get("/tasks?limit=2&offset=1")
        body = resp.get_json()
        self.assertEqual(len(body["items"]), 2)
        self.assertEqual(body["total"], 5)
        self.assertEqual(body["items"][0]["title"], "Task 1")

    def test_list_tasks_limit_out_of_range_rejected(self):
        resp = self.client.get("/tasks?limit=0")
        self.assertEqual(resp.status_code, 400)
        resp2 = self.client.get("/tasks?limit=500")
        self.assertEqual(resp2.status_code, 400)

    def test_list_tasks_negative_offset_rejected(self):
        resp = self.client.get("/tasks?offset=-1")
        self.assertEqual(resp.status_code, 400)

    # --- update ---

    def test_update_task_partial(self):
        created = self.client.post("/tasks", json={"title": "A"}).get_json()
        resp = self.client.patch(f"/tasks/{created['id']}", json={"status": "in_progress"})
        body = resp.get_json()
        self.assertEqual(body["status"], "in_progress")
        self.assertEqual(body["title"], "A")  # unchanged
        self.assertNotEqual(body["updated_at"], body["created_at"])

    def test_update_task_not_found(self):
        resp = self.client.patch("/tasks/999", json={"status": "done"})
        self.assertEqual(resp.status_code, 404)

    def test_update_task_empty_body_rejected(self):
        created = self.client.post("/tasks", json={"title": "A"}).get_json()
        resp = self.client.patch(f"/tasks/{created['id']}", json={})
        self.assertEqual(resp.status_code, 400)

    def test_update_task_invalid_field_value_rejected(self):
        created = self.client.post("/tasks", json={"title": "A"}).get_json()
        resp = self.client.patch(f"/tasks/{created['id']}", json={"priority": -1})
        self.assertEqual(resp.status_code, 400)

    # --- deletion ---

    def test_delete_task(self):
        created = self.client.post("/tasks", json={"title": "A"}).get_json()
        resp = self.client.delete(f"/tasks/{created['id']}")
        self.assertEqual(resp.status_code, 204)
        resp2 = self.client.get(f"/tasks/{created['id']}")
        self.assertEqual(resp2.status_code, 404)

    def test_delete_task_not_found(self):
        resp = self.client.delete("/tasks/999")
        self.assertEqual(resp.status_code, 404)

    # --- misc ---

    def test_health_check(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["status"], "ok")


if __name__ == "__main__":
    unittest.main()
