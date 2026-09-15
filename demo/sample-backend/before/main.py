"""
Sample backend — BEFORE (stale docs)
"""
from fastapi import FastAPI

app = FastAPI()

users = [{"id": 1, "name": "Navya"}]


@app.get("/users")
def get_users():
    return users


@app.post("/users")
def create_user(name: str):
    new_user = {"id": len(users) + 1, "name": name}
    users.append(new_user)
    return new_user
