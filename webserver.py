from flask import Flask, request, render_template, redirect
from re import match
import time
import uuid
import bleach

VERSION = "1.0.0"


def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


def getWebServer(taskQueue):
    # create and configure the app
    app = Flask(__name__)

    @app.route("/", methods=['GET', 'POST'])
    def index():
        if request.method == "POST":
            url = request.form['url']
            if not url:
                return render_template('index.html', time=time.strftime("%H:%M"), status="Error: URL was not provided.", version=VERSION)
            if not match(r"(http|https):\/\/.*", url):
                return render_template('index.html', time=time.strftime("%H:%M"), status="Error: URL is invalid.", version=VERSION)
            task = taskQueue.add(url)
            return redirect(f'/tasks/{task.id}', 303)
        elif request.method == "GET":
            return render_template('index.html', time=time.strftime("%H:%M"), version=VERSION)

    @app.route("/status")
    def status():
        return render_template('status.html', version=VERSION)

    @app.route("/tasks/<taskID>")
    def taskStatus(taskID):
        if not is_valid_uuid(taskID):
            return redirect("/status", 302)
        status = taskQueue.status(taskID)
        if status == "not found":
            return redirect("/status", 302)
        return render_template('task.html', id=str(taskID), status=status.capitalize(), version=VERSION)
    
    @app.route("/api/tasks/status/<taskID>")
    def getTaskStatus(taskID):
        if not is_valid_uuid(taskID):
            return {"status": "error"}
        status = taskQueue.status(taskID)
        # Since the taskID is user input, we need to sanitize and escape it.
        # Auto escaping is turned on for jinja2 templates, but not for REST routes.
        return {
            "id": bleach.clean(taskID),
            "status": status
        }


    return app
