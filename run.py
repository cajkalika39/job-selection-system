from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Job Matching System работает!'

if __name__ == '__main__':
    app.run(debug=True)