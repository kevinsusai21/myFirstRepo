# Reddit Clone

A basic Reddit-style application where users can create posts, upvote/downvote, comment, and reply to comments.

## Project Structure

```
├── backend/          # FastAPI backend (Python)
│   ├── app/
│   │   └── main.py   # API endpoints
│   ├── pyproject.toml
│   └── poetry.lock
├── frontend/         # React frontend (TypeScript + Vite + Tailwind)
│   ├── src/
│   │   └── App.tsx    # Main app component
│   ├── package.json
│   └── vite.config.ts
└── index.html        # GitHub Issues Dashboard (separate tool)
```

## Features

- **Create posts** with title and content
- **Upvote / Downvote** posts and comments
- **Comment** on posts with nested replies
- **Sort** feed by Hot, New, or Top
- **Delete** your own posts and comments
- Dark theme (Reddit-inspired UI)

## Getting Started

### Backend

```bash
cd backend
poetry install
poetry run fastapi dev app/main.py
```

The API runs at `http://localhost:8000`. See docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app runs at `http://localhost:5173`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/posts` | List all posts (sort: new, top, hot) |
| POST | `/api/posts` | Create a new post |
| GET | `/api/posts/{id}` | Get a single post |
| PUT | `/api/posts/{id}` | Update a post |
| DELETE | `/api/posts/{id}` | Delete a post |
| POST | `/api/posts/{id}/vote` | Vote on a post |
| GET | `/api/posts/{id}/comments` | List comments (nested tree) |
| POST | `/api/posts/{id}/comments` | Create a comment |
| DELETE | `/api/comments/{id}` | Delete a comment |
| POST | `/api/comments/{id}/vote` | Vote on a comment |
