"""
Flask-based REST API for managing blog posts with rate limiting and Swagger documentation.

This module provides a RESTful API for creating, reading, updating, and deleting blog posts.
It includes features such as pagination, sorting, search, rate limiting, and API key authentication.
"""

from flask import Flask, jsonify, request, abort, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_swagger_ui import get_swaggerui_blueprint
from marshmallow import Schema, fields, ValidationError
import json
import logging
from math import ceil
from datetime import datetime
from config import Config


# Set up logging configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Initialize core application components
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Set up rate limiting with configured defaults
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=Config.RATE_LIMITS,
    storage_uri="memory://"
)


@app.route('/swagger.json', methods=['GET'])
def swagger_json():
    """Serve the Swagger JSON specification file."""
    return send_from_directory(Config.BASE_DIR / 'static', 'swagger.json')


# Configure Swagger UI endpoints
SWAGGER_URL = "/api/docs"
API_URL = "/swagger.json"

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL, API_URL, config={"app_name": "Masterblog API"}
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)


@app.before_request
def validate_api_key():
    """
    Validate the API key before processing any request.

    Checks for API key in headers or query parameters when not in debug mode.
    Raises 401 if the key is missing or invalid.
    """
    if app.config["DEBUG"]:
        return
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if not api_key or api_key != Config.API_KEY:
        abort(401, description="Unauthorized: Invalid or missing API key.")


@app.errorhandler(400)
def bad_request(error):
    """Handle bad request errors with a JSON response."""
    return jsonify({"error": "Bad Request", "message": str(error)}), 400


@app.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized access errors with a JSON response."""
    return jsonify({"error": "Unauthorized", "message": str(error)}), 401


@app.errorhandler(404)
def not_found(error):
    """Handle resource not found errors with a JSON response."""
    return jsonify({"error": "Not Found", "message": str(error)}), 404


class PostSchema(Schema):
    """
    Schema for validating blog post data.

    Defines required fields and their types for post creation and updates.
    """
    title = fields.Str(required=True)
    content = fields.Str(required=True)
    author = fields.Str(required=True)
    date = fields.Date(required=True, format="%Y-%m-%d")


post_schema = PostSchema()


class PostManager:
    """
    Manages blog post operations including CRUD and search functionality.

    Handles data persistence using JSON file storage and provides methods
    for creating, reading, updating, deleting, and searching blog posts.
    """

    def __init__(self, data_file):
        """Initialize PostManager with the path to the JSON storage file."""
        self.data_file = data_file
        self.posts = self.load_posts()

    def load_posts(self):
        """Load posts from the JSON storage file."""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as file:
                logger.info(f"Loading posts from {self.data_file}")
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning(f"Failed to load posts from {self.data_file}. Starting with an empty list.")
            return []

    def save_posts(self):
        """Save current posts to the JSON storage file."""
        with open(self.data_file, 'w', encoding='utf-8') as file:
            json.dump(self.posts, file, indent=4, ensure_ascii=False)

    def add_post(self, title, content, author, date):
        """
        Add a new blog post.

        Args:
            title (str): Post title
            content (str): Post content
            author (str): Post author
            date (datetime): Post date

        Returns:
            dict: The newly created post
        """
        new_id = max((post['id'] for post in self.posts), default=0) + 1
        new_post = {
            "id": new_id,
            "title": title.strip(),
            "content": content.strip(),
            "author": author.strip(),
            "date": date.strftime("%Y-%m-%d")
        }
        self.posts.append(new_post)
        self.save_posts()
        return new_post

    def delete_post(self, post_id):
        """
        Delete a blog post by ID.

        Args:
            post_id (int): ID of the post to delete

        Returns:
            dict: Success message or error if post not found
        """
        original_length = len(self.posts)
        self.posts = [post for post in self.posts if post["id"] != post_id]
        if len(self.posts) < original_length:
            self.save_posts()
            return {"message": f"Post with id {post_id} deleted successfully."}
        return {"error": f"Post with id {post_id} not found"}, 404

    def update_post(self, post_id, title=None, content=None, author=None, date=None):
        """
        Update an existing blog post.

        Args:
            post_id (int): ID of the post to update
            title (str, optional): New title
            content (str, optional): New content
            author (str, optional): New author
            date (datetime, optional): New date

        Returns:
            dict: Updated post or error if post not found
        """
        for post in self.posts:
            if post["id"] == post_id:
                if title: post["title"] = title.strip()
                if content: post["content"] = content.strip()
                if author: post["author"] = author.strip()
                if date: post["date"] = date.strftime("%Y-%m-%d")
                self.save_posts()
                return post
        return {"error": f"Post with id {post_id} not found"}, 404

    def search_posts(self, query="", title=None, content=None, author=None, date=None):
        """
        Search posts by various criteria.

        Args:
            query (str): General search query
            title (str, optional): Title search term
            content (str, optional): Content search term
            author (str, optional): Author search term
            date (str, optional): Date search term

        Returns:
            list: Matching posts
        """
        results = self.posts
        if query:
            results = [
                post for post in results
                if (query.lower() in post['title'].lower()) or
                   (query.lower() in post['content'].lower()) or
                   (query.lower() in post['author'].lower()) or
                   (query.lower() in post['date'].lower())
            ]
        if title:
            results = [post for post in results if title.lower() in post['title'].lower()]
        if content:
            results = [post for post in results if content.lower() in post['content'].lower()]
        if author:
            results = [post for post in results if author.lower() in post['author'].lower()]
        if date:
            results = [post for post in results if date.lower() in post['date'].lower()]
        return results


# Initialize the post manager with configured storage
post_manager = PostManager(Config.STORAGE_FILE)


@app.route('/api/v1/posts', methods=['GET'])
@limiter.limit("10 per minute")
def get_posts_v1():
    """
    Retrieve a paginated list of blog posts.

    Supports sorting by various fields and pagination parameters.

    Query Parameters:
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 5)
        sort (str): Sort field (title, content, author, date)
        direction (str): Sort direction (asc, desc)

    Returns:
        JSON response with paginated posts and metadata
    """
    page_num = int(request.args.get('page', 1))
    items_per_page = int(request.args.get('per_page', 5))
    sort_field = request.args.get('sort', '').strip().lower()
    sort_direction = request.args.get('direction', '').strip().lower()

    if sort_field and sort_field not in ['title', 'content', 'author', 'date']:
        return jsonify({"error": "Invalid sort field"}), 400
    if sort_direction and sort_direction not in ['asc', 'desc']:
        return jsonify({"error": "Invalid sort direction"}), 400

    sorted_posts = sorted(post_manager.posts,
                          key=lambda post: post.get(sort_field, ""),
                          reverse=(sort_direction == 'desc')) if sort_field else post_manager.posts

    total_posts = len(sorted_posts)
    total_pages = ceil(total_posts / items_per_page) or 1

    if page_num < 1 or page_num > total_pages:
        return jsonify({"error": f"Invalid page number. Choose between 1 and {total_pages}."}), 400

    start_index = (page_num - 1) * items_per_page
    end_index = start_index + items_per_page
    paginated_posts = sorted_posts[start_index:end_index]

    return jsonify({
        "page": page_num,
        "per_page": items_per_page,
        "total_posts": total_posts,
        "total_pages": total_pages,
        "posts": paginated_posts
    }), 200


@app.route('/api/v1/posts/<int:post_id>', methods=['GET'])
@limiter.limit("10 per minute")
def get_post_by_id(post_id):
    """
    Retrieve a single blog post by ID.

    Args:
        post_id (int): ID of the post to retrieve

    Returns:
        JSON response with the post data or an error if not found
    """
    logger.info(f"Fetching post with ID: {post_id}")
    post = next((post for post in post_manager.posts if post["id"] == post_id), None)
    if post:
        logger.info(f"Post found: {post}")
        return jsonify(post), 200
    logger.warning(f"Post with ID {post_id} not found.")
    return jsonify({"error": f"Post with id {post_id} not found"}), 404


@app.route('/api/v1/posts', methods=['POST'])
@limiter.limit("10 per minute")
def add_post_v1():
    """
    Create a new blog post.

    Expects JSON data matching the PostSchema.
    Returns the created post or validation errors.
    """
    try:
        post_data = post_schema.load(request.get_json())
        new_post = post_manager.add_post(**post_data)
        return jsonify(new_post), 201
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400


@app.route('/api/v1/posts/<int:post_id>', methods=['DELETE'])
@limiter.limit("10 per minute")
def delete_post_v1(post_id):
    """
    Delete a blog post by ID.

    Args:
        post_id (int): ID of the post to delete

    Returns:
        JSON response confirming deletion or error if not found
    """
    delete_result = post_manager.delete_post(post_id)
    if isinstance(delete_result, tuple):
        return jsonify(delete_result[0]), delete_result[1]
    return jsonify(delete_result), 200


@app.route('/api/v1/posts/<int:post_id>', methods=['PUT'])
@limiter.limit("10 per minute")
def update_post_v1(post_id):
    """
    Update an existing blog post.

    Args:
        post_id (int): ID of the post to update

    Expects JSON data matching PostSchema (partial updates allowed).
    Returns the updated post or validation errors.
    """
    try:
        update_data = post_schema.load(request.get_json(), partial=True)
        update_result = post_manager.update_post(post_id, **update_data)
        if isinstance(update_result, tuple):
            return jsonify(update_result[0]), update_result[1]
        return jsonify(update_result), 200
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400


@app.route('/api/v1/posts/search', methods=['GET'])
@limiter.limit("10 per minute")
def search_posts_v1():
    """
    Search for blog posts using various criteria.

    Query Parameters:
        query (str): General search term
        title (str): Title search term
        content (str): Content search term
        author (str): Author search term
        date (str): Date search term

    Returns:
        JSON list of matching posts
    """
    search_query = request.args.get('query', '').strip().lower()
    search_title = request.args.get('title', '').strip().lower()
    search_content = request.args.get('content', '').strip().lower()
    search_author = request.args.get('author', '').strip().lower()
    search_date = request.args.get('date', '').strip().lower()

    matching_posts = post_manager.search_posts(
        query=search_query,
        title=search_title,
        content=search_content,
        author=search_author,
        date=search_date
    )
    return jsonify(matching_posts), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=Config.DEBUG)