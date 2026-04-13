from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from typing import Optional
from contextlib import asynccontextmanager

# --- In-memory data store ---
posts_db: dict[int, dict] = {}
comments_db: dict[int, dict] = {}
post_id_counter = 0
comment_id_counter = 0


def _seed_data() -> None:
    """Populate the in-memory store with food/steak themed content."""
    global post_id_counter, comment_id_counter

    now = datetime.now(timezone.utc)

    # --- Posts ---
    seed_posts = [
        {
            "title": "The Perfect Reverse Sear: A Step-by-Step Guide",
            "content": (
                "After years of experimenting, I've nailed the reverse sear method for thick-cut "
                "ribeyes. Here's what works for me:\n\n"
                "1. Season generously with salt and pepper, let it rest uncovered in the fridge overnight\n"
                "2. Bring to room temp for 45 min before cooking\n"
                "3. Oven at 250F until internal temp hits 120F (~45 min for a 1.5\" cut)\n"
                "4. Rest 10 min, then sear in a ripping hot cast iron with avocado oil\n"
                "5. 45 seconds per side, baste with butter, garlic, and thyme\n\n"
                "The crust you get is unreal. Medium-rare edge to edge with a perfect sear."
            ),
            "author": "grillmaster99",
            "votes": {"chef_julia": 1, "steaklover42": 1, "foodie_mike": 1, "BBQ_Dan": 1, "umami_queen": 1, "cast_iron_carl": 1},
            "created_at": (now - timedelta(hours=3)).isoformat(),
        },
        {
            "title": "Unpopular opinion: A5 Wagyu is overrated for a regular dinner",
            "content": (
                "Don't get me wrong, A5 Wagyu is an incredible experience. But I think people "
                "overhype it as the 'best steak ever.' It's so rich and fatty that you can only "
                "eat a few ounces before you're done. For a satisfying dinner-sized steak, give me "
                "a well-marbled USDA Prime ribeye any day.\n\n"
                "A5 is a luxury tasting experience, not an everyday steak. Anyone else feel this way?"
            ),
            "author": "foodie_mike",
            "votes": {"grillmaster99": 1, "steaklover42": -1, "BBQ_Dan": 1, "cast_iron_carl": 1},
            "created_at": (now - timedelta(hours=8)).isoformat(),
        },
        {
            "title": "Made my first dry-aged ribeye at home and I'm never going back",
            "content": (
                "Picked up a whole bone-in ribeye primal from my local butcher and dry-aged it in "
                "a dedicated mini fridge for 45 days. Used the Umai dry age bags.\n\n"
                "The flavor is insane -- nutty, beefy, almost cheese-like funk. Lost about 30% to "
                "trim and moisture loss but what's left is pure concentrated beef flavor.\n\n"
                "Total cost worked out to about $18/lb after trim, which is way cheaper than "
                "buying dry-aged steaks at a steakhouse. Highly recommend if you're patient!"
            ),
            "author": "steaklover42",
            "votes": {"grillmaster99": 1, "chef_julia": 1, "foodie_mike": 1, "umami_queen": 1},
            "created_at": (now - timedelta(hours=14)).isoformat(),
        },
        {
            "title": "Best steakhouses in NYC? Taking my partner for our anniversary",
            "content": (
                "Looking for recommendations for a special anniversary dinner in Manhattan. Budget "
                "isn't a huge concern but I'd like to stay under $300 for two.\n\n"
                "I've heard great things about Peter Luger, Keens, and Cote. Any favorites? "
                "Bonus points if they have a great wine list and a good atmosphere."
            ),
            "author": "umami_queen",
            "votes": {"chef_julia": 1, "foodie_mike": 1, "BBQ_Dan": 1},
            "created_at": (now - timedelta(hours=20)).isoformat(),
        },
        {
            "title": "Cast iron vs. grill -- which do you prefer for steaks?",
            "content": (
                "I've been going back and forth on this. Cast iron gives you an incredible crust "
                "and lets you baste with butter. But grilling over charcoal gives you that smoky "
                "flavor you can't replicate indoors.\n\n"
                "Lately I've been doing a hybrid: start on the grill for smoke, finish in cast "
                "iron for the sear. Best of both worlds?\n\n"
                "What's your go-to method?"
            ),
            "author": "BBQ_Dan",
            "votes": {"grillmaster99": 1, "steaklover42": 1, "chef_julia": 1, "foodie_mike": 1, "umami_queen": 1},
            "created_at": (now - timedelta(days=1, hours=2)).isoformat(),
        },
    ]

    for i, p in enumerate(seed_posts, start=1):
        score = sum(p["votes"].values())
        posts_db[i] = {
            "id": i,
            "title": p["title"],
            "content": p["content"],
            "author": p["author"],
            "score": score,
            "votes": p["votes"],
            "comment_count": 0,
            "created_at": p["created_at"],
        }
    post_id_counter = len(seed_posts)

    # --- Comments ---
    seed_comments = [
        # Post 1: Reverse Sear Guide
        {"post_id": 1, "parent": None, "author": "chef_julia", "content": "Great guide! One tip: try finishing with a blowtorch instead of the cast iron. You get an even more intense crust without overcooking the edges.", "votes": {"grillmaster99": 1, "steaklover42": 1}, "created_at": (now - timedelta(hours=2, minutes=30)).isoformat()},
        {"post_id": 1, "parent": 1, "author": "grillmaster99", "content": "I've tried the torch method! It works but I find the cast iron gives a more even crust. The torch can leave hot spots if you're not careful.", "votes": {"chef_julia": 1}, "created_at": (now - timedelta(hours=2, minutes=15)).isoformat()},
        {"post_id": 1, "parent": None, "author": "cast_iron_carl", "content": "250F is the sweet spot. I tried 225 once and it took forever. Also, don't skip the overnight salt -- it makes a huge difference for the crust.", "votes": {"grillmaster99": 1, "foodie_mike": 1, "BBQ_Dan": 1}, "created_at": (now - timedelta(hours=1, minutes=45)).isoformat()},
        {"post_id": 1, "parent": None, "author": "foodie_mike", "content": "What kind of cast iron do you use? I have a Lodge and it works great but wondering if there's something better.", "votes": {"grillmaster99": 1}, "created_at": (now - timedelta(hours=1)).isoformat()},
        {"post_id": 1, "parent": 4, "author": "grillmaster99", "content": "Lodge is perfect honestly. The key is getting it screaming hot -- I preheat mine in the oven at 500F for 30 min before the sear.", "votes": {"foodie_mike": 1, "cast_iron_carl": 1}, "created_at": (now - timedelta(minutes=45)).isoformat()},

        # Post 2: A5 Wagyu debate
        {"post_id": 2, "parent": None, "author": "steaklover42", "content": "Hard disagree. A5 Wagyu is a completely different category of food. Comparing it to Prime ribeye is like comparing champagne to beer -- both great, different purposes.", "votes": {"umami_queen": 1, "chef_julia": 1}, "created_at": (now - timedelta(hours=7)).isoformat()},
        {"post_id": 2, "parent": 6, "author": "foodie_mike", "content": "That's kind of my point though. You wouldn't drink champagne with every meal. For a regular Tuesday dinner steak, Prime is better.", "votes": {"BBQ_Dan": 1, "grillmaster99": 1}, "created_at": (now - timedelta(hours=6, minutes=30)).isoformat()},
        {"post_id": 2, "parent": None, "author": "chef_julia", "content": "As someone who's cooked A5 professionally, I think the issue is most people don't prepare it correctly. It should be served in thin slices, almost like sashimi. Not as a 16oz steak.", "votes": {"grillmaster99": 1, "steaklover42": 1, "umami_queen": 1}, "created_at": (now - timedelta(hours=5)).isoformat()},
        {"post_id": 2, "parent": 8, "author": "umami_queen", "content": "This is the real answer. When I had it at a proper yakiniku restaurant in Tokyo, they served maybe 3oz total. It was perfect.", "votes": {"chef_julia": 1, "steaklover42": 1}, "created_at": (now - timedelta(hours=4)).isoformat()},

        # Post 3: Dry-aged at home
        {"post_id": 3, "parent": None, "author": "grillmaster99", "content": "45 days is brave for a first attempt! I started at 28 days and worked my way up. How was the pellicle? Did you have any issues with off-flavors?", "votes": {"steaklover42": 1}, "created_at": (now - timedelta(hours=13)).isoformat()},
        {"post_id": 3, "parent": 10, "author": "steaklover42", "content": "The pellicle was thick and dark but trimmed off easily. No off-flavors at all -- the Umai bags really do prevent that. Honestly it was easier than I expected.", "votes": {"grillmaster99": 1, "chef_julia": 1}, "created_at": (now - timedelta(hours=12)).isoformat()},
        {"post_id": 3, "parent": None, "author": "BBQ_Dan", "content": "$18/lb for dry-aged ribeye is a steal. My local butcher charges $45/lb for 30-day aged. Definitely trying this.", "votes": {"steaklover42": 1, "foodie_mike": 1}, "created_at": (now - timedelta(hours=10)).isoformat()},

        # Post 4: NYC steakhouses
        {"post_id": 4, "parent": None, "author": "chef_julia", "content": "Cote is incredible -- it's Korean BBQ meets steakhouse. The Butcher's Feast is the move. You get like 5 different cuts plus all the banchan sides.", "votes": {"umami_queen": 1, "foodie_mike": 1, "steaklover42": 1}, "created_at": (now - timedelta(hours=19)).isoformat()},
        {"post_id": 4, "parent": None, "author": "cast_iron_carl", "content": "Keens for the mutton chop. It's unlike anything else in the city. The atmosphere is old-school NYC and the scotch list is legendary.", "votes": {"umami_queen": 1, "BBQ_Dan": 1}, "created_at": (now - timedelta(hours=18)).isoformat()},
        {"post_id": 4, "parent": 13, "author": "umami_queen", "content": "Cote is at the top of my list now! Is it easy to stay under $300 for two there?", "votes": {"chef_julia": 1}, "created_at": (now - timedelta(hours=17)).isoformat()},
        {"post_id": 4, "parent": 15, "author": "chef_julia", "content": "The Butcher's Feast is $65/person, so with drinks and tip you'd be right around $250-280. Very doable.", "votes": {"umami_queen": 1}, "created_at": (now - timedelta(hours=16)).isoformat()},

        # Post 5: Cast iron vs grill
        {"post_id": 5, "parent": None, "author": "grillmaster99", "content": "Your hybrid method is the way. I do the same thing -- 2 min per side over hot charcoal, then into a screaming cast iron with compound butter.", "votes": {"BBQ_Dan": 1, "steaklover42": 1, "cast_iron_carl": 1}, "created_at": (now - timedelta(days=1, hours=1)).isoformat()},
        {"post_id": 5, "parent": None, "author": "cast_iron_carl", "content": "Cast iron all day. You can control the heat better, the butter baste is essential, and I don't have to deal with flare-ups. Plus it works year-round regardless of weather.", "votes": {"chef_julia": 1, "umami_queen": 1}, "created_at": (now - timedelta(hours=23)).isoformat()},
        {"post_id": 5, "parent": 18, "author": "BBQ_Dan", "content": "Fair points but you're missing the charcoal flavor! That smokiness is irreplaceable. I'll take a few flare-ups for that taste.", "votes": {"grillmaster99": 1, "steaklover42": 1}, "created_at": (now - timedelta(hours=22)).isoformat()},
    ]

    for i, c in enumerate(seed_comments, start=1):
        score = sum(c["votes"].values())
        comments_db[i] = {
            "id": i,
            "post_id": c["post_id"],
            "parent_comment_id": c["parent"],
            "content": c["content"],
            "author": c["author"],
            "score": score,
            "votes": c["votes"],
            "created_at": c["created_at"],
        }
    comment_id_counter = len(seed_comments)

    # Update comment counts on posts
    for pid in posts_db:
        posts_db[pid]["comment_count"] = sum(
            1 for c in comments_db.values() if c["post_id"] == pid
        )


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    _seed_data()
    yield


app = FastAPI(title="r/FoodieFinds API", lifespan=lifespan)

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


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
        "created_at": datetime.now(timezone.utc).isoformat(),
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
        "created_at": datetime.now(timezone.utc).isoformat(),
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
