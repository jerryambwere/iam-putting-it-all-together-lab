#!/usr/bin/env python3

from flask import request, session, make_response
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe


class Signup(Resource):
    pass

    def post(self):
        data = request.get_json() if request.is_json else request.form
        if "username" not in data or "password" not in data:
            return {"error": "Missing required fields"}, 422
        try:
            user = User(
                username=data["username"],
                image_url=data["image_url"],
                bio=data["bio"],
            )
            user.password_hash = data["password"]
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            return make_response(user.to_dict(), 201)
        except IntegrityError:
            return {"error": "Username already exists"}, 422
        except Exception as e:
            print(e)
            return make_response({"error": str(e)}, 422)


class CheckSession(Resource):
    def get(self):
        if session["user_id"]:
            user = User.query.filter_by(id=session["user_id"]).first()
            return make_response(user.to_dict(), 200)
        else:
            return make_response({"error": "You are not logged in"}, 401)


class Login(Resource):
    def post(self):
        data = request.get_json() if request.is_json else request.form
        if "username" not in data or "password" not in data:
            return {"error": "Missing required fields"}, 422
        user = User.query.filter_by(username=data["username"]).first()
        if user and user.authenticate(data["password"]):
            session["user_id"] = user.id
            return make_response(user.to_dict(), 200)
        else:
            return make_response({"error": "Username or password incorrect"}, 401)


class Logout(Resource):
    def delete(self):
        if session["user_id"]:
            session["user_id"] = None
            return make_response({}, 204)
        else:
            return make_response({"error": "You are not logged in"}, 401)


class RecipeIndex(Resource):
    def get(self):
        if not session["user_id"]:
            return make_response({"error": "You are not logged in"}, 401)
        recipes = Recipe.query.all()
        return make_response([recipe.to_dict() for recipe in recipes], 200)

    def post(self):
        data = request.get_json() if request.is_json else request.form
        if not session["user_id"]:
            return make_response({"error": "You are not logged in"}, 401)
        if (
            not data["title"]
            or not data["instructions"]
            or not data["minutes_to_complete"]
        ):
            return {"error": "Data entered is invalid"}, 422
        try:
            recipe = Recipe(
                title=data["title"],
                instructions=data["instructions"],
                minutes_to_complete=data["minutes_to_complete"],
                user_id=session["user_id"],
            )
            db.session.add(recipe)
            db.session.commit()
            return make_response(recipe.to_dict(), 201)
        except Exception as e:
            print(e)
            return {"error": str(e)}, 422


api.add_resource(Signup, "/signup", endpoint="signup")
api.add_resource(CheckSession, "/check_session", endpoint="check_session")
api.add_resource(Login, "/login", endpoint="login")
api.add_resource(Logout, "/logout", endpoint="logout")
api.add_resource(RecipeIndex, "/recipes", endpoint="recipes")


if __name__ == "__main__":
    app.run(port=5555, debug=True)