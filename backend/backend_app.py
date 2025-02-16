from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import json
from math import ceil
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Get the directory of the current script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to the .env file
env_file = os.path.join(BASE_DIR, '.env')

# Load environment variables from the .env file
load_dotenv(env_file)

# Access the API key
API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY is not set in the .env file.")

# Middleware to validate the API key
@app.before_request
def validate_api_key():
    if request.method != 'OPTIONS':  # Skip validation for preflight requests
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != API_KEY:
            abort(401, description="Unauthorized: Invalid or missing API key.")

# Configure rate limiting
limiter = Limiter(
    get_remote_address,  # Use the client's IP address for rate limiting
    app=app,
    default_limits=["10 per minute"],  # Default limit: 10 requests per minute
    storage_uri="memory://",  # Store rate-limiting data in memory (use Redis for production)
)

# Construct the path to the JSON file relative to the script's location
data_file = os.path.join(BASE_DIR, 'posts_storage.json')
print(data_file)

class PostManager:
    """Class to manage posts operations like load, save, delete, update, etc."""
    def __init__(self, data_file):
        self.data_file = data_file
        self.posts = self.load_posts()

    def load_posts(self):
        """Load posts from the JSON file."""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as file:
                print(f"Loading posts from {self.data_file}")
                data = json.load(file)
                print(f"Finished Loading from {self.data_file}")
                return data
        except FileNotFoundError:
            print(f"File {self.data_file} not found. Starting with an empty list.")
            return []
        except json.JSONDecodeError:
            print(f"Invalid JSON in {self.data_file}. Starting with an empty list.")
            return []

    def save_posts(self):
        """Save posts to the JSON file."""
        with open(self.data_file, 'w', encoding='utf-8') as file:
            json.dump(self.posts, file, indent=4, ensure_ascii=False)

    def add_post(self, title, content):
        """Add a new post."""
        new_id = max((post['id'] for post in self.posts), default=0) + 1
        new_post = {"id": new_id, "title": title, "content": content}
        self.posts.append(new_post)
        self.save_posts()
        return new_post

    def delete_post(self, post_id):
        """Delete a post by ID."""
        post_to_delete = next((post for post in self.posts if post["id"] == post_id), None)
        if not post_to_delete:
            return None
        self.posts = [post for post in self.posts if post["id"] != post_id]
        self.save_posts()
        return post_to_delete

    def update_post(self, post_id, title=None, content=None):
        """Update a post by ID."""
        post_to_update = next((post for post in self.posts if post["id"] == post_id), None)
        if not post_to_update:
            return None
        if title is not None:
            post_to_update['title'] = title.strip() or post_to_update['title']
        if content is not None:
            post_to_update['content'] = content.strip() or post_to_update['content']
        self.save_posts()
        return post_to_update

    def search_posts(self, title_query="", content_query=""):
        """Search posts by title or content."""
        return [
            post for post in self.posts
            if (not title_query or title_query in post['title'].lower()) and
               (not content_query or content_query in post['content'].lower())
        ]

# Initialize the PostManager with the data file
post_manager = PostManager(data_file)

# Version 1 Routes
@app.route('/api/v1/posts', methods=['GET'])
@limiter.limit("5 per minute")  # Custom rate limit for this endpoint
def get_posts_v1():
    """Endpoint to retrieve all posts with optional sorting and pagination."""
    page = int(request.args.get('page', 1))  # Default to page 1
    per_page = int(request.args.get('per_page', 5))  # Default to 5 posts per page
    sort_field = request.args.get('sort', '').strip().lower()
    direction = request.args.get('direction', '').strip().lower()

    # Validate sort field
    if sort_field and sort_field not in ['title', 'content']:
        return jsonify({"error": "Invalid sort field. Must be 'title' or 'content'."}), 400

    # Validate sort direction
    if direction and direction not in ['asc', 'desc']:
        return jsonify({"error": "Invalid sort direction. Must be 'asc' or 'desc'."}), 400

    # Apply sorting if valid parameters are provided
    if sort_field and direction:
        reverse = direction == 'desc'
        sorted_posts = sorted(post_manager.posts, key=lambda post: post[sort_field].lower(), reverse=reverse)
    else:
        sorted_posts = post_manager.posts

    # Paginate the results
    total_posts = len(sorted_posts)
    total_pages = ceil(total_posts / per_page)

    if total_posts == 0:
        return jsonify({
            "page": 1,
            "per_page": per_page,
            "total_posts": 0,
            "total_pages": 0,
            "posts": []
        }), 200

    if page < 1 or page > total_pages:
        return jsonify({"error": f"Invalid page number. Must be between 1 and {total_pages}."}), 400

    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    paginated_posts = sorted_posts[start_index:end_index]

    return jsonify({
        "page": page,
        "per_page": per_page,
        "total_posts": total_posts,
        "total_pages": total_pages,
        "posts": paginated_posts
    }), 200

@app.route('/api/v1/posts', methods=['POST'])
@limiter.limit("5 per minute")  # Custom rate limit for this endpoint
def add_post_v1():
    """Endpoint to add a new post."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided in the request body"}), 400

    missing_fields = []
    if 'title' not in data:
        missing_fields.append('title')
    if 'content' not in data:
        missing_fields.append('content')

    if missing_fields:
        return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400

    title = data['title'].strip()
    content = data['content'].strip()

    if not title or not content:
        return jsonify({"error": "Title and content must not be empty"}), 400

    new_post = post_manager.add_post(title, content)
    return jsonify(new_post), 201

@app.route('/api/v1/posts/<int:post_id>', methods=['DELETE'])
@limiter.limit("5 per minute")  # Custom rate limit for this endpoint
def delete_post_v1(post_id):
    """Endpoint to delete a post by its ID."""
    deleted_post = post_manager.delete_post(post_id)
    if not deleted_post:
        return jsonify({"error": f"Post with id {post_id} not found"}), 404
    return jsonify({"message": f"Post with id {post_id} has been deleted successfully."}), 200

@app.route('/api/v1/posts/<int:post_id>', methods=['PUT'])
@limiter.limit("5 per minute")  # Custom rate limit for this endpoint
def update_post_v1(post_id):
    """Endpoint to update a post by its ID."""
    data = request.get_json()
    title = data.get('title', None)
    content = data.get('content', None)
    updated_post = post_manager.update_post(post_id, title, content)
    if not updated_post:
        return jsonify({"error": f"Post with id {post_id} not found"}), 404
    return jsonify(updated_post), 200

@app.route('/api/v1/posts/search', methods=['GET'])
@limiter.limit("5 per minute")  # Custom rate limit for this endpoint
def search_posts_v1():
    title_query = request.args.get('title', '').strip().lower()
    content_query = request.args.get('content', '').strip().lower()
    matching_posts = post_manager.search_posts(title_query, content_query)
    return jsonify(matching_posts), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)