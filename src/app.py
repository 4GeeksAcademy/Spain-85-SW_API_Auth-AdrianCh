"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planet, Character, Favorite
from sqlalchemy import select
from flask_jwt_extended import create_access_token, JWTManager, get_jwt_identity, jwt_required
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.url_map.strict_slashes = False



db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Setup the Flask-JWT-Extended extension
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
jwt = JWTManager(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route("/login", methods=["POST"])
def login():
    try:
        email = request.json.get("email", None)
        password = request.json.get("password", None)
        result_email = db.session.execute(select(User).filter_by(email=email)).scalar_one_or_none()
        if result_email and bcrypt.check_password_hash(result_email.password, password):
            access_token = create_access_token(identity=email)
            return jsonify(access_token=access_token)
        return jsonify({"msg": "Bad username or password"}), 401
    except Exception as e:
        return jsonify({"msg": str(e)}), 500
@app.route("/profile", methods= ["GET"])
@jwt_required()
def get_profile():
    try:
        current_user = get_jwt_identity()
        return jsonify(logged_in_as=current_user), 200
    
    except Exception as e:
        return jsonify({"msg": str(e)}), 500
    
@app.route('/user', methods=['GET'])
def get_users():
    try:
        data = db.session.scalars(select(User)).all()
        results = list(map(lambda item: item.serialize(),data))
        response_body = {
            "results":results
        }
        return jsonify(response_body), 200
    except Exception as e:
        return jsonify({"msg": str(e)}), 500

@app.route('/user/<int:id>', methods=['GET'])
def get_user(id):
    try:
        user = db.session.execute(select(User).filter_by(id=id)).scalar_one()
        if user:
            response_body = {
                "result": user.serialize()
            }

            return jsonify(response_body), 200
        else:
            return jsonify({"msg": "User not found"}), 404
    except Exception as e:
        return jsonify({"msg": str(e)}), 500

@app.route('/user', methods=['POST'])
def create_user():
    request_data = request.json
    email = request_data["email"] 
    user_found = db.session.execute(select(User).filter_by(email=email)).scalar_one_or_none()
    try:
        if not user_found:
            user = User(email=email, password=bcrypt.generate_password_hash(request_data["password"])).decode('utf-8')
            db.session.add(user)
            db.session.commit()
            response_body = {
                "msg":"User created"
            }
            return jsonify(response_body), 201
        else:
            return jsonify({"msg": "User with this email already exists"}), 400
    except Exception as e:
        return jsonify({"msg": str(e)}), 500
    
@app.route('/user/<int:id>', methods=['DELETE'])
def delete_user(id):
    try:
        user = db.session.execute(db.select(User).filter_by(id=id)).scalar_one_or_none()
        if user:
            db.session.delete(user)
            db.session.commit()
            response_body = {
                "msg":"user deleted"
            }
            return jsonify(response_body), 200
        else:
            return jsonify({"msg": "User not found"}), 404
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


@app.route('/planet', methods=['GET'])
def get_planets():
    try:
        data = db.session.scalars(select(Planet)).all()
        results = list(map(lambda item: item.serialize(),data))
        response_body = {
            "results":results
        }
        return jsonify(response_body), 200
    except Exception as e:
        return jsonify({"msg": str(e)}), 500

@app.route('/planet/<int:id>', methods=['GET'])
def get_planet(id):
    try:
        planet = db.session.execute(select(Planet).filter_by(id=id)).scalar_one()
        if planet:
            response_body = {
                "result":planet.serialize()
            }
            return jsonify(response_body), 200
        else:
            return jsonify({"msg": "Planet not found"}), 404
    except Exception as e:
        return jsonify({"msg": str(e)}), 500



@app.route('/character', methods=['GET'])
def get_characters():
    try:
        data = db.session.scalars(select(Character)).all()
        results = list(map(lambda item: item.serialize(),data))
        response_body = {
            "results":results
        }
        return jsonify(response_body), 200
    except Exception as e:
        return jsonify({"msg": str(e)}), 500

@app.route('/character/<int:id>', methods=['GET'])
def get_character(id):
    try:
        character = db.session.execute(select(Character).filter_by(id=id)).scalar_one()
        if character:
            response_body = {
                "result":character.serialize()
            }
            return jsonify(response_body), 200
        else:
            return jsonify({"msg": "Character not found"}), 404
    except Exception as e:
        return jsonify({"msg": str(e)}), 500
    

@app.route('/favorite', methods=['GET'])
def get_favorites():
    try:
        data = db.session.scalars(select(Favorite)).all()
        results = list(map(lambda item: item.serialize(),data))
        response_body = {
            "results":results
        }
        return jsonify(response_body), 200
    except Exception as e:
        return jsonify({"msg": str(e)}), 500
    
@app.route('/user/<int:id>/favorites', methods=['GET'])
def get_user_favorites(id):
    try:
        user = db.session.execute(select(User).filter_by(id=id)).scalar_one()
        response_body = {
            "favorites": [favorite.serialize() for favorite in user.favorites]
        }
        return jsonify(response_body), 200
    except:
        return jsonify({"msg":"User has no favourites"}), 404

@app.route('/user/<int:id>/favorite', methods=['POST'])
def create_favourite(id):
    request_data = request.json
    try:
        user = db.session.execute(select(User).filter_by(id=id)).scalar_one()
        if user:
            favorite_type = request_data.get('type')
            favorite_id = request_data.get('id')
            if favorite_type == "planet":
                planet = db.session.execute(select(Planet).filter_by(id=favorite_id)).scalar_one_or_none()
                if planet:
                    new_favorite = Favorite(user_id=id, planet_id=favorite_id)
                    db.session.add(new_favorite)
                    db.session.commit()
                    return jsonify({"msg": "Planet added to favorites"}), 201
                else:
                    return jsonify({"msg": "Planet not found"}), 404
            elif favorite_type == 'character':
                character = db.session.execute(select(Character).filter_by(id=favorite_id)).scalar_one_or_none()
                if character:
                    new_favorite = Favorite(user_id=id, character_id=favorite_id)
                    db.session.add(new_favorite)
                    db.session.commit()
                    return jsonify({"msg": "Character added to favorites"}), 201
                else:
                    return jsonify({"msg": "Character not found"}), 404
            else:
                return jsonify({"msg": "favorite type needs to be planet or character"}), 400
        else:
            return jsonify({"msg": "User not found"}), 404
    except Exception as e:
        return jsonify({"msg": str(e)}), 500

# Request body of the function (planet OR character)
# {
#   "type": "planet",
#   "id": 1
# }

@app.route('/user/<int:user_find_id>/favorite/<int:favorite_id>', methods=['DELETE'])
def delete_user_favorite(user_find_id, favorite_id):
    try:
        user = db.session.execute(db.select(User).filter_by(id=user_find_id)).scalar_one_or_none()
        if user:
            user_favorite_character = db.session.execute(db.select(Favorite).filter_by(user_id=user_find_id, id=favorite_id)).scalar_one_or_none()
            if user_favorite_character:
                db.session.delete(user_favorite_character)
                db.session.commit()
                return jsonify({"msg": "Favorite deleted successfully"}), 200
            
            user_favorite_planet = db.session.execute(db.select(Favorite).filter_by(user_id=user_find_id, id=favorite_id)).scalar_one_or_none()
            if user_favorite_planet:
                db.session.delete(user_favorite_planet)
                db.session.commit()
                return jsonify({"msg": "Favorite deleted successfully"}), 200
            
            else:
                return jsonify(
                    {"msg": "Favorite not found",
                    "character": user_favorite_character,
                    "planet": user_favorite_planet,
                    }), 404
        else:
            return jsonify({"msg": "User not found"}), 404
    except Exception as e:
        return jsonify({"msg": str(e)}), 500


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
