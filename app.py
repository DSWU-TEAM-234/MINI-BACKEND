from flask import Flask, request, render_template, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'


@app.route('/')
def mainHome():
    return render_template('mainHome.html')



if __name__ == '__main__':
    app.run(port=5000, debug=True)