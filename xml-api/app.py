import os

from flask import Flask
from flask import request, render_template
from flask import send_from_directory

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!";


@app.route('/aastra68xxi/<path:filename>', methods=['GET'])
def download(filename):
    return send_from_directory("aastra68xxi", filename, as_attachment=False)


@app.route('/firmware/<path:filename>', methods=['GET'])
def download_fw(filename):
    return send_from_directory("firmware", filename, as_attachment=False)


@app.route('/login', methods=['GET'])
def xml():
    extension = request.args.get("extension")
    password = request.args.get("password")
    return render_template("sip.xml", user=extension, passw=password)


@app.route('/input', methods=['GET'])
def login():
    return render_template("input.xml")


@app.route('/app', methods=['GET'])
def appl():
    up = os.popen("uptime").read().strip()
    return render_template("uptime.xml", uptime=up)


if __name__ == "__main__":
    app.run(debug = False, host = "0.0.0.0", port = 8888)

