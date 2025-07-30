from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello from Tech J"

@app.route('/health')
def health():
    # Health check endpoint returns 200 OK with simple json
    return jsonify(status="ok")

if __name__ == "__main__":
    # Development server with debug mode off for safety
    app.run(host="0.0.0.0", port=8080, debug=False)
