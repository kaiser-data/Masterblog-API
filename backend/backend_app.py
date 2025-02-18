from flask import Flask, jsonify, request, abort, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_swagger_ui import get_swaggerui_blueprint
import json
from math import ceil
import os
from dotenv import load_dotenv
from pathlib import Path
import logging
from datetime import datetime

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get the directory of the current script
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Access the API key
API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY is not set in the .env file.")

# Configure rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["10 per minute"],
    storage_uri="memory://"
)

# Serve swagger.json as a static resource
@app.route('/swagger.json', methods=['GET'])
def swagger_json():
    return send_from_directory(BASE_DIR / 'static', 'swagger.json')

# Swagger UI configuration
SWAGGER_URL = "/api/docs"
API_URL = "/swagger.json"  # Served by the route above

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={"app_name": "Masterblog API"}
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)


# Before request: Validate API key
@app.before_request
def validate_api_key():
    if app.debug:
        return
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if not api_key or api_key != API_KEY:
        abort(401, description="Unauthorized: Invalid or missing API key.")


# PostManager class
class PostManager:
    def __init__(self, data_file):
        self.data_file = data_file
        self.posts = self.load_posts()

    def load_posts(self):
        try:
            with open(self.data_file, 'r', encoding='utf-8') as file:
                logging.info(f"Loading posts from {self.data_file}")
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            logging.warning(f"Failed to load posts from {self.data_file}. Starting with an empty list.")
            return []

    def save_posts(self):
        with open(self.data_file, 'w', encoding='utf-8') as file:
            json.dump(self.posts, file, indent=4, ensure_ascii=False)

    def add_post(self, title, content, author, date):
        """Add a new post with author and date."""
        new_id = max((post['id'] for post in self.posts), default=0) + 1
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Use 'YYYY-MM-DD'.")
        new_post = {
            "id": new_id,
            "title": title.strip(),
            "content": content.strip(),
            "author": author.strip(),
            "date": str(date_obj)
        }
        self.posts.append(new_post)
        self.save_posts()
        return new_post

    def delete_post(self, post_id):
        self.posts = [post for post in self.posts if post["id"] != post_id]
        deleted = any(post["id"] == post_id for post in self.posts)
        if deleted:
            self.save_posts()
            return {"message": f"Post with id {post_id} has been deleted successfully."}
        return {"error": f"Post with id {post_id} not found"}, 404

    def update_post(self, post_id, title=None, content=None, author=None, date=None):
        """Update a post by ID with optional fields."""
        for post in self.posts:
            if post["id"] == post_id:
                if title is not None:
                    post["title"] = title.strip() or post["title"]
                if content is not None:
                    post["content"] = content.strip() or post["content"]
                if author is not None:
                    post["author"] = author.strip() or post["author"]
                if date is not None:
                    try:
                        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
                        post["date"] = str(date_obj)
                    except ValueError:
                        raise ValueError("Invalid date format. Use 'YYYY-MM-DD'.")
                self.save_posts()
                return post
        return {"error": f"Post with id {post_id} not found"}, 404

    def search_posts(self, query=""):
        """Search posts by title, content, author, or date."""
        return [
            post for post in self.posts
            if (query.lower() in post['title'].lower()) or
               (query.lower() in post['content'].lower()) or
               (query.lower() in post['author'].lower()) or
               (query.lower() in post['date'].lower())
        ]


# Initialize PostManager
data_file = BASE_DIR / 'posts_storage.json'
post_manager = PostManager(data_file)


# Routes
@app.route('/api/v1/posts', methods=['GET'])
@limiter.limit("5 per minute")
def get_posts_v1():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 5))
    sort_field = request.args.get('sort', '').strip().lower()
    direction = request.args.get('direction', '').strip().lower()

    if sort_field and sort_field not in ['title', 'content', 'author', 'date']:
        return jsonify({"error": "Invalid sort field. Must be 'title', 'content', 'author', or 'date'."}), 400
    if direction and direction not in ['asc', 'desc']:
        return jsonify({"error": "Invalid sort direction. Must be 'asc' or 'desc'."}), 400

    sorted_posts = (
        sorted(
            post_manager.posts,
            key=lambda post: (
                datetime.strptime(post[sort_field], "%Y-%m-%d").date() if sort_field == 'date' else post[sort_field].lower()
            ),
            reverse=(direction == 'desc')
        )
        if sort_field and direction else post_manager.posts
    )

    total_posts = len(sorted_posts)
    total_pages = ceil(total_posts / per_page)
    if page < 1 or page > total_pages:
        return jsonify({"error": f"Invalid page number. Must be between 1 and {total_pages}."}), 400

    paginated_posts = sorted_posts[(page - 1) * per_page:page * per_page]
    return jsonify({
        "page": page,
        "per_page": per_page,
        "total_posts": total_posts,
        "total_pages": total_pages,
        "posts": paginated_posts
    }), 200


@app.route('/api/v1/posts', methods=['POST'])
@limiter.limit("5 per minute")
def add_post_v1():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided in the request body"}), 400

    required_fields = ['title', 'content', 'author', 'date']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400

    title = data['title'].strip()
    content = data['content'].strip()
    author = data['author'].strip()
    date = data['date'].strip()

    if not all([title, content, author, date]):
        return jsonify({"error": "All fields (title, content, author, date) must not be empty"}), 400

    try:
        new_post = post_manager.add_post(title, content, author, date)
        return jsonify(new_post), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/v1/posts/<int:post_id>', methods=['DELETE'])
@limiter.limit("5 per minute")
def delete_post_v1(post_id):
    result = post_manager.delete_post(post_id)
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result), 200


@app.route('/api/v1/posts/<int:post_id>', methods=['PUT'])
@limiter.limit("5 per minute")
def update_post_v1(post_id):
    data = request.get_json()
    title = data.get('title', None)
    content = data.get('content', None)
    author = data.get('author', None)
    date = data.get('date', None)

    try:
        updated_post = post_manager.update_post(post_id, title, content, author, date)
        if isinstance(updated_post, tuple):
            return jsonify(updated_post[0]), updated_post[1]
        return jsonify(updated_post), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/v1/posts/search', methods=['GET'])
@limiter.limit("5 per minute")
def search_posts_v1():
    query = request.args.get('query', '').strip().lower()
    matching_posts = post_manager.search_posts(query)
    return jsonify(matching_posts), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)