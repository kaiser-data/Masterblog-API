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


@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    """Endpoint to delete a post by its ID."""
    # Find the post with the given ID
    post_to_delete = next((post for post in POSTS if post["id"] == post_id), None)

    # If no post is found with the given ID, return a 404 Not Found response
    if not post_to_delete:
        return jsonify({"error": f"Post with id {post_id} not found"}), 404

    # Remove the post from the list
    POSTS[:] = [post for post in POSTS if post["id"] != post_id]

    # Return a success message with status code 200 OK
    return jsonify({"message": f"Post with id {post_id} has been deleted successfully."}), 200


@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    """Endpoint to update a post by its ID."""
    # Find the post with the given ID
    post_to_update = next((post for post in POSTS if post["id"] == post_id), None)

    # If no post is found with the given ID, return a 404 Not Found response
    if not post_to_update:
        return jsonify({"error": f"Post with id {post_id} not found"}), 404

    # Parse the JSON data from the request body
    data = request.get_json()

    # Update the title if provided, otherwise keep the current value
    if 'title' in data:
        post_to_update['title'] = data['title'].strip() or post_to_update['title']

    # Update the content if provided, otherwise keep the current value
    if 'content' in data:
        post_to_update['content'] = data['content'].strip() or post_to_update['content']

    # Return the updated post with status code 200 OK
    return jsonify({
        "id": post_to_update["id"],
        "title": post_to_update["title"],
        "content": post_to_update["content"]
    }), 200


@app.route('/api/posts/search', methods=['GET'])
def search_posts():
    """Endpoint to search for posts by title or content."""
    # Get query parameters from the request URL
    title_query = request.args.get('title', '').strip().lower()
    content_query = request.args.get('content', '').strip().lower()

    # Filter posts based on the search terms
    matching_posts = []
    for post in POSTS:
        # Check if the title contains the title_query (case-insensitive)
        title_match = title_query in post['title'].lower()
        # Check if the content contains the content_query (case-insensitive)
        content_match = content_query in post['content'].lower()

        # Include the post if it matches either the title or content query
        if title_match or content_match:
            matching_posts.append(post)

    # Return the list of matching posts
    return jsonify(matching_posts), 200


@app.route('/api/posts', methods=['GET'])
def get_posts():
    """Endpoint to retrieve all posts with optional sorting."""
    # Get query parameters for sorting
    sort_field = request.args.get('sort', '').strip().lower()  # Field to sort by (optional)
    direction = request.args.get('direction', '').strip().lower()  # Sort direction (optional)

    # Validate sort field
    if sort_field and sort_field not in ['title', 'content']:
        return jsonify({"error": "Invalid sort field. Must be 'title' or 'content'."}), 400

    # Validate sort direction
    if direction and direction not in ['asc', 'desc']:
        return jsonify({"error": "Invalid sort direction. Must be 'asc' or 'desc'."}), 400

    # Apply sorting if valid parameters are provided
    if sort_field and direction:
        reverse = direction == 'desc'  # Reverse order if direction is 'desc'
        sorted_posts = sorted(POSTS, key=lambda post: post[sort_field].lower(), reverse=reverse)
    else:
        # Return posts in their original order if no sorting parameters are provided
        sorted_posts = POSTS

    # Return the list of posts
    return jsonify(sorted_posts), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
