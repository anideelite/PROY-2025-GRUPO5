from flask import Flask, redirect, request, render_template
from auth import sp_oauth, set_token_info
from bpm_handler import bpm_blueprint  
from spotipy import Spotify
import os

app = Flask(__name__)
app.register_blueprint(bpm_blueprint)

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login")
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    error = request.args.get("error")
    if error:
        return f"Error devuelto por Spotify: {error}", 400

    code = request.args.get("code")
    if not code:
        return "No se encontró el código de autorización.", 400

    token_info = sp_oauth.get_access_token(code, as_dict=True)
    set_token_info(token_info)

    sp = Spotify(auth=token_info['access_token'])
    user_profile = sp.current_user()
    user_id = user_profile.get("id", "desconocido")

    return render_template("dashboard.html", user_id=user_id)