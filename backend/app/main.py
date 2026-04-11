from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

app = FastAPI(title="Reddit Clone API")

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- In-memory data store ---
posts_db: dict[int, dict] = {}
comments_db: dict[int, dict] = {}
post_id_counter = 0
comment_id_counter = 0


# --- Pydantic models ---
class PostCreate(BaseModel):
    title: str
    content: str
    author: str


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class CommentCreate(BaseModel):
    content: str
    author: str
    parent_comment_id: Optional[int] = None


class VoteRequest(BaseModel):
    user: str
    direction: int  # 1 for upvote, -1 for downvote, 0 to remove vote


# --- Health check ---
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


# --- Posts endpoints ---
@app.get("/api/posts")
async def list_posts(sort: str = "new"):
    posts = list(posts_db.values())
    if sort == "new":
        posts.sort(key=lambda p: p["created_at"], reverse=True)
    elif sort == "top":
        posts.sort(key=lambda p: p["score"], reverse=True)
    elif sort == "hot":
        posts.sort(key=lambda p: (p["score"], p["created_at"]), reverse=True)
    return posts


@app.get("/api/posts/{post_id}")
async def get_post(post_id: int):
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    return posts_db[post_id]


@app.post("/api/posts", status_code=201)
async def create_post(post: PostCreate):
    global post_id_counter
    post_id_counter += 1
    new_post = {
        "id": post_id_counter,
        "title": post.title,
        "content": post.content,
        "author": post.author,
        "score": 0,
        "votes": {},
        "comment_count": 0,
        "created_at": datetime.utcnow().isoformat(),
    }
    posts_db[post_id_counter] = new_post
    return new_post


@app.put("/api/posts/{post_id}")
async def update_post(post_id: int, post: PostUpdate):
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    existing = posts_db[post_id]
    if post.title is not None:
        existing["title"] = post.title
    if post.content is not None:
        existing["content"] = post.content
    return existing


@app.delete("/api/posts/{post_id}")
async def delete_post(post_id: int):
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    del posts_db[post_id]
    to_delete = [cid for cid, c in comments_db.items() if c["post_id"] == post_id]
    for cid in to_delete:
        del comments_db[cid]
    return {"detail": "Post deleted"}


# --- Voting ---
@app.post("/api/posts/{post_id}/vote")
async def vote_post(post_id: int, vote: VoteRequest):
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    if vote.direction not in (-1, 0, 1):
        raise HTTPException(status_code=400, detail="Direction must be -1, 0, or 1")
    post = posts_db[post_id]
    if vote.direction == 0:
        post["votes"].pop(vote.user, None)
    else:
        post["votes"][vote.user] = vote.direction
    post["score"] = sum(post["votes"].values())
    return {"score": post["score"], "user_vote": post["votes"].get(vote.user, 0)}


@app.post("/api/comments/{comment_id}/vote")
async def vote_comment(comment_id: int, vote: VoteRequest):
    if comment_id not in comments_db:
        raise HTTPException(status_code=404, detail="Comment not found")
    if vote.direction not in (-1, 0, 1):
        raise HTTPException(status_code=400, detail="Direction must be -1, 0, or 1")
    comment = comments_db[comment_id]
    if vote.direction == 0:
        comment["votes"].pop(vote.user, None)
    else:
        comment["votes"][vote.user] = vote.direction
    comment["score"] = sum(comment["votes"].values())
    return {"score": comment["score"], "user_vote": comment["votes"].get(vote.user, 0)}


# --- Comments endpoints ---
@app.get("/api/posts/{post_id}/comments")
async def list_comments(post_id: int):
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    comments = [c for c in comments_db.values() if c["post_id"] == post_id]
    comments.sort(key=lambda c: c["created_at"])
    comment_map = {c["id"]: {**c, "replies": []} for c in comments}
    roots = []
    for c in comment_map.values():
        if c["parent_comment_id"] and c["parent_comment_id"] in comment_map:
            comment_map[c["parent_comment_id"]]["replies"].append(c)
        else:
            roots.append(c)
    return roots


@app.post("/api/posts/{post_id}/comments", status_code=201)
async def create_comment(post_id: int, comment: CommentCreate):
    global comment_id_counter
    if post_id not in posts_db:
        raise HTTPException(status_code=404, detail="Post not found")
    if comment.parent_comment_id and comment.parent_comment_id not in comments_db:
        raise HTTPException(status_code=404, detail="Parent comment not found")
    comment_id_counter += 1
    new_comment = {
        "id": comment_id_counter,
        "post_id": post_id,
        "parent_comment_id": comment.parent_comment_id,
        "content": comment.content,
        "author": comment.author,
        "score": 0,
        "votes": {},
        "created_at": datetime.utcnow().isoformat(),
    }
    comments_db[comment_id_counter] = new_comment
    posts_db[post_id]["comment_count"] = sum(
        1 for c in comments_db.values() if c["post_id"] == post_id
    )
    return new_comment


@app.delete("/api/comments/{comment_id}")
async def delete_comment(comment_id: int):
    if comment_id not in comments_db:
        raise HTTPException(status_code=404, detail="Comment not found")
    comment = comments_db[comment_id]
    post_id = comment["post_id"]
    to_delete = [comment_id]
    queue = [comment_id]
    while queue:
        parent = queue.pop()
        children = [cid for cid, c in comments_db.items() if c["parent_comment_id"] == parent]
        to_delete.extend(children)
        queue.extend(children)
    for cid in to_delete:
        comments_db.pop(cid, None)
    if post_id in posts_db:
        posts_db[post_id]["comment_count"] = sum(
            1 for c in comments_db.values() if c["post_id"] == post_id
        )
    return {"detail": "Comment deleted"}
