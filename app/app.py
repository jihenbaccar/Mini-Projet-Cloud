from flask import Flask, request, jsonify
import psycopg2
import redis
import json
import time

app = Flask(__name__)
app.config['ALLOWED_HOSTS'] = ['*']

# attendre que PostgreSQL démarre
time.sleep(5)

def get_db():
    return psycopg2.connect(
        host="db",
        database="tasks",
        user="postgres",
        password="admin"
    )

# Connexion Redis
cache = redis.Redis(host='redis', port=6379)


# Initialisation DB
def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()

# GET
@app.route("/tasks", methods=["GET"])
def get_tasks():
    if cache.get("tasks"):
        return jsonify({
            "source": "cache",
            "data": json.loads(cache.get("tasks"))
        })

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks")
    rows = cur.fetchall()

    tasks = [{"id": r[0], "title": r[1]} for r in rows]

    cache.set("tasks", json.dumps(tasks), ex=10)

    return jsonify({"source": "db", "data": tasks})

# POST
@app.route("/tasks", methods=["POST"])
def add_task():

    data = request.json

    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (title) VALUES (%s)", (data["title"],))
    conn.commit()

    cache.delete("tasks")

    return jsonify({"message": "Task added"})

# DELETE
@app.route("/tasks/<int:id>", methods=["DELETE"])
def delete_task(id):


    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=%s", (id,))
    conn.commit()

    cache.delete("tasks")

    return jsonify({"message": "Task deleted"})


@app.route("/")
def home():
    return "Cloud Project Marche bien !"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)