from flask import Blueprint, g, redirect, render_template, request, session as flask_session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database import Session as DBSession
import models


auth_bp = Blueprint("auth", __name__)


@auth_bp.before_app_request
def load_current_user():
	g.current_user = None
	user_id = flask_session.get("user_id")
	if not user_id:
		return

	db = DBSession()
	try:
		user = db.get(models.User, user_id)
		if user is None:
			flask_session.pop("user_id", None)
			return

		g.current_user = {
			"user_id": user.user_id,
			"username": user.username,
			"nickname": user.nickname,
			"email": user.email,
		}
	finally:
		db.close()


@auth_bp.app_context_processor
def inject_current_user():
	return {
		"current_user": g.current_user,
		"current_user_id": g.current_user["user_id"] if g.current_user else None,
	}


@auth_bp.route('/signin', methods=["GET", "POST"])
def signin():
	if g.current_user is not None:
		return redirect(url_for("index"))

	error = None
	if request.method == "POST":
		username = request.form.get("username", "").strip()
		password = request.form.get("password", "")

		if not username or not password:
			error = "Username and password are required."
		else:
			db = DBSession()
			try:
				user = db.query(models.User).filter(models.User.username == username).first()
				if user is None:
					error = "Invalid username or password."
				else:
					valid_password = check_password_hash(user.password_hash, password)

					# Backward-compatible fallback for existing plaintext records.
					if not valid_password and user.password_hash == password:
						valid_password = True
						user.password_hash = generate_password_hash(password)
						db.commit()

					if not valid_password:
						error = "Invalid username or password."
					else:
						flask_session["user_id"] = user.user_id
						return redirect(url_for("index"))
			finally:
				db.close()

	return render_template("Signin.html", error=error)


@auth_bp.route('/signup', methods=["GET", "POST"])
def signup():
	if g.current_user is not None:
		return redirect(url_for("index"))

	error = None
	if request.method == "POST":
		username = request.form.get("username", "").strip()
		nickname = request.form.get("nickname", "").strip() or None
		email = request.form.get("email", "").strip().lower() or None
		password = request.form.get("password", "")
		confirm_password = request.form.get("confirm_password", "")

		if not username or not password or not confirm_password:
			error = "Username, password, and confirmation are required."
		elif password != confirm_password:
			error = "Passwords do not match."
		else:
			db = DBSession()
			try:
				existing_username = db.query(models.User).filter(models.User.username == username).first()
				existing_email = None
				if email:
					existing_email = db.query(models.User).filter(models.User.email == email).first()

				if existing_username is not None:
					error = "That username is already taken."
				elif existing_email is not None:
					error = "That email is already registered."
				else:
					new_user = models.User(
						username=username,
						nickname=nickname,
						email=email,
						password_hash=generate_password_hash(password),
					)
					db.add(new_user)
					db.commit()
					db.refresh(new_user)

					flask_session["user_id"] = new_user.user_id
					return redirect(url_for("index"))
			finally:
				db.close()

	return render_template('Signup.html', error=error)


@auth_bp.route('/logout', methods=["POST"])
def logout():
	flask_session.clear()
	return redirect(url_for("auth.signin"))
