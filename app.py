# Import OS to get the port environment variable from the Procfile
import os # <-----
#Import the flask module
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    statement = 'Hello World!'
    return statement


#Calls the run method, runs the app on port 5005
if __name__ == "__main__":
    app.run(host='0.0.0.0')
# Create the main driver function
#port = int(os.environ.get("PORT", 5005)) # <-----  