from locust import HttpUser, task, between
import random
import string


def random_alias(n=8):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


class ShortenerUser(HttpUser):
    wait_time = between(1, 2)

    @task(3)
    def create_link(self):
        alias = random_alias()
        self.client.post(
            "/links/shorten",
            json={
                "original_url": "https://www.python.org",
                "custom_alias": alias,
            },
        )

    @task(2)
    def redirect_missing_or_existing(self):
        self.client.get("/health", name="/health")