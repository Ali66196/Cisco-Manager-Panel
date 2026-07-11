from flask import Flask, render_template, request, redirect, url_for, session
import switch_manager
from api_routes import api_blueprint

app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
    return response

@app.route('/api/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    return '', 204

app.secret_key = "cisco_panel_secret_2024"
app.register_blueprint(api_blueprint)


@app.route("/")
def index():
    if "switch_ip" in session and switch_manager.is_connected():
        return redirect(url_for("dashboard"))
    return redirect(url_for("connect"))


@app.route("/connect", methods=["GET", "POST"])
def connect():
    error = None

    if request.method == "POST":
        ip = request.form.get("switch_ip", "")
        port = int(request.form.get("ssh_port", 22))
        username = request.form.get("switch_user", "")
        password = request.form.get("switch_pass", "")

        success, message = switch_manager.connect_to_switch(ip, port, username, password)

        if success:
            session["switch_ip"] = ip
            return redirect(url_for("dashboard"))
        else:
            error = message

    return render_template("connect.html", error=error)


@app.route("/dashboard")
def dashboard():
    if "switch_ip" not in session:
        return redirect(url_for("connect"))

    switch_ip = session.get("switch_ip", "")
    return render_template("dashboard.html", switch_ip=switch_ip)


@app.route("/change-switch")
def change_switch():
    switch_manager.disconnect_switch()
    session.clear()
    return redirect(url_for("connect"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
