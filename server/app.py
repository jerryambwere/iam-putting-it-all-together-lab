#!/usr/bin/env python3

from flask import request, session, make_response
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe


class Signup(Resource):
    def post(self):
        data = request.get_json() if request.is_json else request.form
        if "username" not in data or "password" not in data:
            return {"error": "Missing required fields"}, 422
        try:
            user = User(
                username=data["username"],
                image_url=data.get("image_url", ""),  # Default empty string if not provided
                bio=data.get("bio", ""),  # Default empty string if not provided
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
        if "user_id" in session:  # Check if 'user_id' exists in the session
            user = User.query.filter_by(id=session["user_id"]).first()
            if user:
                return make_response(user.to_dict(), 200)
            else:
                return make_response({"error": "User not found"}, 404)
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
        if "user_id" in session:
            session["user_id"] = None
            return make_response({}, 204)
        else:
            return make_response({"error": "You are not logged in"}, 401)


class RecipeIndex(Resource):
    def get(self):
        if "user_id" not in session:
            return make_response({"error": "You are not logged in"}, 401)

        user = User.query.get(session["user_id"])
        if user:
            recipes = Recipe.query.filter_by(user_id=user.id).all()
            return make_response([recipe.to_dict() for recipe in recipes], 200)
        else:
            return make_response({"error": "User not found"}, 404)

    def post(self):
        data = request.get_json() if request.is_json else request.form
        if "user_id" not in session:
            return make_response({"error": "You are not logged in"}, 401)

        # Check if required fields are present
        if not data.get("title") or not data.get("instructions") or not data.get("minutes_to_complete"):
            return make_response({"error": "Data entered is invalid"}, 422)

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
            return make_response({"error": str(e)}, 422)


# Adding the resources to the API
api.add_resource(Signup, "/signup", endpoint="signup")
api.add_resource(CheckSession, "/check_session", endpoint="check_session")
api.add_resource(Login, "/login", endpoint="login")
api.add_resource(Logout, "/logout", endpoint="logout")
api.add_resource(RecipeIndex, "/recipes", endpoint="recipes")


if __name__ == "__main__":
    app.run(port=5555, debug=True)
