from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

POSTS = [
    {"id": 1, "title": "First post", "content": "This is the first post."},
    {"id": 2, "title": "Second post", "content": "This is the second post."},
    {"id": 3, "title": "Flask Tutorial", "content": "Learn Flask, a Python web framework."},
    {"id": 4, "title": "React Basics", "content": "Introduction to React for frontend development."},
    {"id": 5, "title": "Flask and React", "content": "Building full-stack apps with Flask and React."},
    {"id": 6, "title": "Django vs Flask", "content": "Comparison between Django and Flask frameworks."},
    {"id": 7, "title": "RESTful APIs", "content": "How to design RESTful APIs using Flask."},
    {"id": 8, "title": "Frontend Development", "content": "Mastering HTML, CSS, and JavaScript for modern web apps."},
    {"id": 9, "title": "Backend Development", "content": "Building scalable backends with Python and Flask."},
    {"id": 10, "title": "Database Design", "content": "Best practices for designing relational databases."},
    {"id": 11, "title": "Authentication in Flask", "content": "Implementing user authentication in Flask applications."},
    {"id": 12, "title": "Testing Flask Apps", "content": "Writing unit tests for Flask APIs."},
    {"id": 13, "title": "Deployment Guide", "content": "Deploying Flask apps to production servers."},
    {"id": 14, "title": "JavaScript Frameworks", "content": "Exploring popular JavaScript frameworks like React, Angular, and Vue."},
    {"id": 15, "title": "Python Tips and Tricks", "content": "Useful tips to improve your Python coding skills."},
]



@app.route('/api/posts', methods=['GET'])
def get_posts():
    return jsonify(POSTS)

@app.route('/api/posts', methods=['POST'])
def add_post():
    """Endpoint to add a new post."""
    # Parse the JSON data from the request body
    data = request.get_json()

    # Check if the request body is empty
    if not data:
        return jsonify({"error": "No data provided in the request body"}), 400

    # Validate that both 'title' and 'content' are provided
    missing_fields = []
    if 'title' not in data:
        missing_fields.append('title')
    if 'content' not in data:
        missing_fields.append('content')

    if missing_fields:
        return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400

    # Extract title and content from the request body
    title = data['title'].strip()
    content = data['content'].strip()

    # Ensure title and content are not empty strings
    if not title or not content:
        return jsonify({"error": "Title and content must not be empty"}), 400

    # Generate a unique ID for the new post
    new_id = max((post['id'] for post in POSTS), default=0) + 1

    # Create the new post object
    new_post = {
        "id": new_id,
        "title": title,
        "content": content
            }

    # Add the new post to the list of posts
    POSTS.append(new_post)

    # Return the newly created post with status code 201 Created
    return jsonify(new_post), 201


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
