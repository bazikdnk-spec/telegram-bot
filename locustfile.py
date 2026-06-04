"""Task 26: Load testing with Locust — 500 concurrent users."""
import random
from locust import HttpUser, task, between


class BotUser(HttpUser):
    """Simulates a Telegram bot user via the webhook HTTP endpoint."""
    wait_time = between(0.5, 2.0)
    host = "http://localhost:8443"

    QUESTIONS = [
        "Что такое машинное обучение?",
        "Напиши эссе о технологиях",
        "Расскажи о Казахстане",
        "Как работает Python?",
        "Что такое Docker?",
        "Объясни нейронные сети",
        "Помоги с задачей по математике",
        "Что такое REST API?",
    ]

    def _make_update(self, text: str, user_id: int = None) -> dict:
        uid = user_id or random.randint(100000, 999999)
        return {
            "update_id": random.randint(1, 9999999),
            "message": {
                "message_id": random.randint(1, 9999),
                "from": {
                    "id": uid, "first_name": "Test",
                    "username": f"user{uid}", "is_bot": False,
                },
                "chat": {"id": uid, "type": "private"},
                "date": 1700000000,
                "text": text,
            }
        }

    @task(70)
    def send_text_question(self):
        """70% — regular text questions."""
        question = random.choice(self.QUESTIONS)
        update = self._make_update(question)
        self.client.post("/webhook", json=update, name="text_question")

    @task(20)
    def send_start_command(self):
        """20% — /start command."""
        update = self._make_update("/start")
        self.client.post("/webhook", json=update, name="start_command")

    @task(10)
    def send_help_command(self):
        """10% — /help command."""
        update = self._make_update("/help")
        self.client.post("/webhook", json=update, name="help_command")
