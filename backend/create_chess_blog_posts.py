import json
from datetime import datetime, timedelta


# Function to generate chess-themed posts
def generate_chess_posts(num_posts=50):
    posts = []
    authors = ["Magnus Carlsen", "Garry Kasparov", "Bobby Fischer", "Anatoly Karpov", "Vishy Anand"]
    topics = [
        "Opening Strategies", "Endgame Techniques", "Tactical Masterpieces", "Chess Psychology",
        "Famous Games", "Chess History", "Pawn Structures", "Rook Endgames", "Knight Maneuvers",
        "Bishop Pair Advantage", "Queen Sacrifices", "Checkmate Patterns", "Blindfold Chess",
        "Time Management", "Chess Engines", "Online Chess Platforms", "Chess Books Review",
        "Women in Chess", "Chess for Beginners", "Advanced Tactics", "Chess Openings Explained"
    ]

    # Generate posts
    for i in range(1, num_posts + 1):
        title = f"Post #{i}: {topics[i % len(topics)]}"
        author = authors[i % len(authors)]
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        content = (
            f"This post explores the fascinating world of {title.lower()}. "
            f"{author} shares insights on how to improve your skills in this area. "
            "Whether you're a beginner or an advanced player, these tips will help you "
            "elevate your game. Stay tuned for more chess wisdom!"
        )
        post = {
            "id": i,
            "title": title,
            "content": content,
            "author": author,
            "date": date
        }
        posts.append(post)

    return posts


# Save posts to a JSON file
if __name__ == "__main__":
    posts = generate_chess_posts()
    with open("posts_storage.json", "w", encoding="utf-8") as file:
        json.dump(posts, file, indent=4, ensure_ascii=False)
    print("Generated 50 chess posts and saved them to 'posts_storage.json'.")