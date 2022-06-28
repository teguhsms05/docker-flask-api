# Import OS to get the port environment variable from the Procfile
import os, re, random, string
from datetime import datetime, timedelta
import jwt
from functools import wraps

#flask library
from flask import Flask, jsonify, request, make_response
from flask_sqlalchemy import SQLAlchemy
#from flask_caching import Cache
from werkzeug.security import generate_password_hash, check_password_hash
from flask_restful import Resource, Api
from decouple import config
#Import the flask module


app = Flask(__name__)

# inisiasai objek flask restful
api = Api(app)

app.config['SECRET_KEY'] = config('SECRET_KEY')
#app.config['SQLALCHEMY_DATABASE_URI'] =  'postgresql://postgres:postgres@db-container-bmg:5432/pg_backend'
app.config['SQLALCHEMY_DATABASE_URI'] = config('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
#cache = Cache(app)

# inisiasi class models
from models import *

# mencreate database
db.create_all()

#regex phrases for email
regex_mail = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

# decorator for verifying the JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # jwt is passed in the request header
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        # return 401 if token is not passed
        if not token:
            return jsonify({'message' : 'Token is missing !!'})
        try:
            # decoding the payload to fetch the stored details
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = db.session.query(Account).filter(Account.public_id==data['public_id']).first()
        except:
            return jsonify({
                'message' : 'invalid field information!!'
            })
        # returns the current logged in users contex to the routes
        return  f(current_user, *args, **kwargs)

    return decorated

@app.route('/')
def hello_world():
    statement = 'Hello World!'
    return statement

class Players(Resource):
    @token_required
    def get(self):
        query = db.session.query(Account).all()
        players = [
            {
                "id": data.id,
                "username": data.uname,
                "name": data.name,
                "email": data.email,
                "referal_code": data.ref_code

            }
            for data in query
        ]
        response = {
            "code" : 200, 
            "msg"  : "Query data sukses",
            "data" : players
        }

        return response, 200

    def post(self): 
        body        = request.get_json()
        uname       = body['username']
        passwd      = body['password']
        name        = body['name']
        email       = body['email']
        ref_code    = body['referral_code']

        #generate random referral code
        if ref_code == "":
            ref_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 10))
        
        #hashed password account
        hashed_password = generate_password_hash(passwd, method='sha256')

        if(re.fullmatch(regex_mail, email)):
            #checking for existing user by email
            if db.session.query(db.exists().where(Account.email == email)).scalar():
                return "invalid field information"
            #generate public_id
            gencode = ''.join(random.choices(string.ascii_uppercase + string.digits, k = 20))    
            account = Account(
                public_id = str(gencode),
                uname=uname, 
                passwd=hashed_password, 
                name=name, 
                email=email, 
                ref_code=ref_code
            )
            account.save()
            # db.session.add(account)
            # db.session.commit()

            response = {
                "msg" : "Data insert successful",
                "code": 200
            }

            return response, 200
            
        else:
            return "invalid field information"

class LoginPlayer(Resource):
    def post(self):
        auth    = request.get_json()
        uname   = auth['username']
        passwd  = auth['password']

        if not auth or not uname or not passwd:
            # returns Could not verify if any email or / and password is missing
            # return 'Login required !!'
            return make_response(
                'Could not verify',
                401,
                {'WWW-Authenticate' : 'Basic realm ="User does not exist !!"'}
            )
        user = db.session.query(Account).filter(Account.uname==uname).first()
        if not user:
            return make_response(
                f'Could not verify user {uname}',
                401,
                {'WWW-Authenticate' : f'Basic realm ="User {uname} does not exist !!"'}
            )
        player = []
        for item in db.session.query(Account).filter(Account.uname==uname):
            del item.__dict__['_sa_instance_state']
            player.append(item.__dict__)
        if check_password_hash(user.passwd, passwd):
            # generates the JWT Token
            token = jwt.encode({
                'public_id': user.public_id,
                'exp': datetime.utcnow() + timedelta(minutes=30)
                }, app.config['SECRET_KEY'], 'HS256')
            
            player.append({'token': token})
            return make_response(jsonify(player))
    
        # returns 403 if password is wrong
        return make_response(
            'Could not verify',
            403,
            {'WWW-Authenticate' : 'Basic realm ="Wrong Password !!"'}
        )

class CheckRefcode(Resource):
    @token_required
    def post(self, current_user):
        body        = request.get_json()
        ref_code    = body['referral_code']
        
        if db.session.query(Account).filter(Account.ref_code==ref_code).first():
            return 'ok'
        
# inisialisasi url / api 
# testing
api.add_resource(Players, "/player", methods=["GET", "POST"])
api.add_resource(LoginPlayer, "/player/login", methods=["POST"])
api.add_resource(CheckRefcode, "/player/checkRefCode", methods=["POST"])

#Calls the run method, runs the app on port 5005
if __name__ == "__main__":
    app.run(host='0.0.0.0')
# Create the main driver function
#port = int(os.environ.get("PORT", 5005)) # <-----  