import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)
db_drop_and_create_all()


def get_all_drinks(recipe_format):
    all_drinks = Drink.query.order_by(Drink.id).all()
    if recipe_format.lower() == 'short':
        all_drinks_formatted = [drink.short() for drink in all_drinks]
    elif recipe_format.lower() == 'long':
        all_drinks_formatted = [drink.long() for drink in all_drinks]
    else:
        return abort(500)

    if len(all_drinks_formatted) == 0:
        abort(404)

    return all_drinks_formatted


# implement endpoint GET /drinks

@app.route('/drinks', methods=['GET'])
def drinks():
    return jsonify({
        'success': True,
        'drinks': get_all_drinks('short')
    })


# implement endpoint /drinks-detail


@app.route('/drinks-detail',  methods=['GET'])
@requires_auth('get:drinks-detail')
def drinks_detail(payload):
    return jsonify({
        'success': True,
        'drinks': get_all_drinks('long')
    })


# implement endpoint POST /drinks


@app.route('/drinks',  methods=['POST'])
@requires_auth('post:drinks')
def create_drink(payload):
    body = request.get_json()
    new_drink = Drink(title=body['title'], recipe="""{}""".format(body['recipe']))
    new_drink.insert()
    new_drink.recipe = body['recipe']
    return jsonify({
        'success': True,
        'drinks': Drink.long(new_drink)
    })


# implement endpoint PATCH /drinks/<id>


@app.route('/drinks/<int:drink_id>',  methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, drink_id):
    body = request.get_json()

    if not body:
        abort(400)

    drink_to_update = Drink.query.filter(Drink.id == drink_id).one_or_none()

    updated_title = body.get('title', None)
    updated_recipe = body.get('recipe', None)

    if updated_title:
        drink_to_update.title = body['title']

    if updated_recipe:
        drink_to_update.recipe = """{}""".format(body['recipe'])

    drink_to_update.update()

    return jsonify({
        'success': True,
        'drinks': [Drink.long(drink_to_update)]
    })


# implement endpoint DELETE /drinks/<id>


@app.route('/drinks/<int:drink_id>',  methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(payload, drink_id):
    if not drink_id:
        abort(422)

    drink_to_delete = Drink.query.filter(Drink.id == drink_id).one_or_none()

    if not drink_to_delete:
        abort(404)

    drink_to_delete.delete()

    return jsonify({
        'success': True,
        'delete': drink_id
    })

# implement error handlers using the @app.errorhandler(error) decorator


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    }), 400

# implement error handler for 404


@app.errorhandler(404)
def ressource_not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


# implement error handler for AuthError


@app.errorhandler(AuthError)
def authentification_failed(AuthError):
    return jsonify({
        "success": False,
        "error": AuthError.status_code,
        "message": AuthError.error
    }), 401
