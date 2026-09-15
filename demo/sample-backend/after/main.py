"""
Sample backend — AFTER (new parametrized endpoint)
"""
from fastapi import FastAPI

app = FastAPI()

users = {1: {"id": 1, "name": "Navya"}}


@app.get("/users/{user_id}")
def get_user(user_id: int):
    return users.get(user_id, {"id": user_id, "name": "Navya"})


@app.post("/users")
def create_user(name: str):
    new_user = {"id": len(users) + 1, "name": name}
    users[len(users) + 1] = new_user
    return new_user
