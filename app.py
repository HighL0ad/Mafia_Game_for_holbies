# Monkey patching for gevent must be done before importing socket/flask modules
try:
    from gevent import monkey
    monkey.patch_all()
except ImportError:
    pass

from flask import Flask, render_template
from flask_socketio import join_room, leave_room

from config import Config
from database import db
from home.home import home_bp
from host.host import host_bp
from player.player import player_bp
from websock import socketio

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config.from_object(Config)

db.init_app(app)
socketio.init_app(app, cors_allowed_origins="*")

with app.app_context():
    db.create_all()
    # Ensure newly added columns exist in existing sqlite db
    with db.engine.connect() as conn:
        for col, col_type, default in [("phase", "VARCHAR(32)", "'day'"), ("day_number", "INTEGER", "1")]:
            try:
                conn.execute(db.text(f"ALTER TABLE rooms ADD COLUMN {col} {col_type} DEFAULT {default}"))
                conn.commit()
            except Exception:
                pass


app.register_blueprint(home_bp)
app.register_blueprint(host_bp)
app.register_blueprint(player_bp)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@socketio.on("connect")
def handle_connect():
    pass


@socketio.on("join_room")
def handle_join_room(data):
    room = str(data.get("room", ""))
    if room:
        join_room(room)


@socketio.on("leave_room")
def handle_leave_room(data):
    room = str(data.get("room", ""))
    if room:
        leave_room(room)


if __name__ == "__main__":
    print("Starting Mafia Game on http://0.0.0.0:8000 ...")
    socketio.run(app, host="0.0.0.0", port=8000, debug=Config.DEBUG, use_reloader=False)

