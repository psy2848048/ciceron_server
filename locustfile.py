from locust import HttpLocust, TaskSet, task
from ciceron_lib import *
import json

class UserBehavior(TaskSet):
    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        self.login()

    def login(self):
        response = self.client.get("/api/login", catch_response=True)
        salt = json.loads(response.content)['identifier']

        text_pass = 'amazingCiceron'
        hashed = get_hashed_password(text_pass)
        with_salt = get_hashed_password(hashed, salt=salt)
        self.client.post("/api/login", {"email":"admin@ciceron.me", "password":with_salt})

    @task(1)
    def index(self):
        self.client.get("/")

class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait=5000
    max_wait=9000
