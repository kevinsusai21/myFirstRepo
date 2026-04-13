import { useState, useEffect, useCallback } from 'react'
import {
  ArrowBigUp,
  ArrowBigDown,
  MessageSquare,
  Plus,
  X,
  Send,
  Flame,
  Clock,
  TrendingUp,
  Reply,
  Trash2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface Post {
  id: number
  title: string
  content: string
  author: string
  score: number
  votes: Record<string, number>
  comment_count: number
  created_at: string
}

interface Comment {
  id: number
  post_id: number
  parent_comment_id: number | null
  content: string
  author: string
  score: number
  votes: Record<string, number>
  created_at: string
  replies: Comment[]
}

const CURRENT_USER = 'user123'

function timeAgo(dateStr: string): string {
  const now = new Date()
  const date = new Date(dateStr + 'Z')
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)
  if (seconds < 60) return 'just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}

function CommentItem({
  comment,
  postId,
  onRefresh,
}: {
  comment: Comment
  postId: number
  onRefresh: () => void
}) {
  const [showReply, setShowReply] = useState(false)
  const [replyContent, setReplyContent] = useState('')
  const [collapsed, setCollapsed] = useState(false)
  const userVote = comment.votes[CURRENT_USER] || 0

  const vote = async (direction: number) => {
    const newDir = userVote === direction ? 0 : direction
    await fetch(`${API_URL}/api/comments/${comment.id}/vote`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user: CURRENT_USER, direction: newDir }),
    })
    onRefresh()
  }

  const submitReply = async () => {
    if (!replyContent.trim()) return
    await fetch(`${API_URL}/api/posts/${postId}/comments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content: replyContent,
        author: CURRENT_USER,
        parent_comment_id: comment.id,
      }),
    })
    setReplyContent('')
    setShowReply(false)
    onRefresh()
  }

  const deleteComment = async () => {
    await fetch(`${API_URL}/api/comments/${comment.id}`, { method: 'DELETE' })
    onRefresh()
  }

  return (
    <div className="pl-4 border-l-2 border-zinc-700 mt-3">
      <div className="flex items-center gap-2 text-xs text-zinc-400">
        <button onClick={() => setCollapsed(!collapsed)} className="hover:text-zinc-200">
          {collapsed ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
        </button>
        <span className="font-semibold text-orange-400">{comment.author}</span>
        <span>·</span>
        <span>{timeAgo(comment.created_at)}</span>
        <span>·</span>
        <span>{comment.score} pts</span>
      </div>
      {!collapsed && (
        <>
          <p className="text-sm text-zinc-200 mt-1 ml-5">{comment.content}</p>
          <div className="flex items-center gap-3 mt-1 ml-5">
            <button
              onClick={() => vote(1)}
              className={`p-0.5 rounded hover:bg-zinc-700 ${userVote === 1 ? 'text-orange-500' : 'text-zinc-500'}`}
            >
              <ArrowBigUp size={16} />
            </button>
            <button
              onClick={() => vote(-1)}
              className={`p-0.5 rounded hover:bg-zinc-700 ${userVote === -1 ? 'text-blue-500' : 'text-zinc-500'}`}
            >
              <ArrowBigDown size={16} />
            </button>
            <button
              onClick={() => setShowReply(!showReply)}
              className="text-xs text-zinc-500 hover:text-zinc-300 flex items-center gap-1"
            >
              <Reply size={14} /> Reply
            </button>
            {comment.author === CURRENT_USER && (
              <button
                onClick={deleteComment}
                className="text-xs text-zinc-500 hover:text-red-400 flex items-center gap-1"
              >
                <Trash2 size={14} /> Delete
              </button>
            )}
          </div>
          {showReply && (
            <div className="ml-5 mt-2 flex gap-2">
              <input
                value={replyContent}
                onChange={(e) => setReplyContent(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && submitReply()}
                placeholder="Write a reply..."
                className="flex-1 bg-zinc-800 border border-zinc-600 rounded px-3 py-1.5 text-sm text-zinc-200 focus:outline-none focus:border-orange-500"
              />
              <button
                onClick={submitReply}
                className="bg-orange-600 hover:bg-orange-500 text-white px-3 py-1.5 rounded text-sm"
              >
                <Send size={14} />
              </button>
            </div>
          )}
          {comment.replies?.map((reply) => (
            <CommentItem
              key={reply.id}
              comment={reply}
              postId={postId}
              onRefresh={onRefresh}
            />
          ))}
        </>
      )}
    </div>
  )
}

function PostDetail({
  post,
  onBack,
  onRefresh,
}: {
  post: Post
  onBack: () => void
  onRefresh: () => void
}) {
  const [comments, setComments] = useState<Comment[]>([])
  const [newComment, setNewComment] = useState('')
  const userVote = post.votes[CURRENT_USER] || 0

  const fetchComments = useCallback(async () => {
    const res = await fetch(`${API_URL}/api/posts/${post.id}/comments`)
    setComments(await res.json())
  }, [post.id])

  useEffect(() => {
    fetchComments()
  }, [fetchComments])

  const vote = async (direction: number) => {
    const newDir = userVote === direction ? 0 : direction
    await fetch(`${API_URL}/api/posts/${post.id}/vote`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user: CURRENT_USER, direction: newDir }),
    })
    onRefresh()
  }

  const submitComment = async () => {
    if (!newComment.trim()) return
    await fetch(`${API_URL}/api/posts/${post.id}/comments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: newComment, author: CURRENT_USER }),
    })
    setNewComment('')
    fetchComments()
    onRefresh()
  }

  return (
    <div>
      <button
        onClick={onBack}
        className="text-sm text-zinc-400 hover:text-zinc-200 mb-4 flex items-center gap-1"
      >
        ← Back to feed
      </button>
      <div className="bg-zinc-800 rounded-lg border border-zinc-700 p-4">
        <div className="flex gap-3">
          <div className="flex flex-col items-center gap-1">
            <button
              onClick={() => vote(1)}
              className={`p-1 rounded hover:bg-zinc-700 ${userVote === 1 ? 'text-orange-500' : 'text-zinc-500'}`}
            >
              <ArrowBigUp size={22} />
            </button>
            <span className={`text-sm font-bold ${post.score > 0 ? 'text-orange-400' : post.score < 0 ? 'text-blue-400' : 'text-zinc-400'}`}>
              {post.score}
            </span>
            <button
              onClick={() => vote(-1)}
              className={`p-1 rounded hover:bg-zinc-700 ${userVote === -1 ? 'text-blue-500' : 'text-zinc-500'}`}
            >
              <ArrowBigDown size={22} />
            </button>
          </div>
          <div className="flex-1">
            <div className="text-xs text-zinc-400 mb-1">
              Posted by <span className="text-orange-400">{post.author}</span> · {timeAgo(post.created_at)}
            </div>
            <h2 className="text-xl font-semibold text-zinc-100 mb-2">{post.title}</h2>
            <p className="text-zinc-300 whitespace-pre-wrap">{post.content}</p>
          </div>
        </div>
      </div>

      <div className="mt-4">
        <div className="flex gap-2 mb-4">
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="What are your thoughts?"
            className="flex-1 bg-zinc-800 border border-zinc-600 rounded-lg px-4 py-3 text-sm text-zinc-200 focus:outline-none focus:border-orange-500 resize-none"
            rows={3}
          />
        </div>
        <button
          onClick={submitComment}
          disabled={!newComment.trim()}
          className="bg-orange-600 hover:bg-orange-500 disabled:bg-zinc-700 disabled:text-zinc-500 text-white px-4 py-2 rounded-lg text-sm font-medium"
        >
          Comment
        </button>
      </div>

      <div className="mt-6">
        <h3 className="text-sm font-semibold text-zinc-400 mb-3">
          {comments.length} Comment{comments.length !== 1 ? 's' : ''}
        </h3>
        {comments.map((c) => (
          <CommentItem key={c.id} comment={c} postId={post.id} onRefresh={() => { onRefresh(); fetchComments(); }} />
        ))}
        {comments.length === 0 && (
          <p className="text-sm text-zinc-500 italic">No comments yet. Be the first!</p>
        )}
      </div>
    </div>
  )
}

function App() {
  const [posts, setPosts] = useState<Post[]>([])
  const [selectedPost, setSelectedPost] = useState<Post | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newContent, setNewContent] = useState('')
  const [sortBy, setSortBy] = useState<'new' | 'top' | 'hot'>('new')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPosts = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/posts?sort=${sortBy}`)
      if (!res.ok) throw new Error('Failed to fetch posts')
      setPosts(await res.json())
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch posts')
    } finally {
      setLoading(false)
    }
  }, [sortBy])

  useEffect(() => {
    fetchPosts()
  }, [fetchPosts])

  const refreshAndUpdateSelected = async () => {
    const res = await fetch(`${API_URL}/api/posts?sort=${sortBy}`)
    const newPosts = await res.json()
    setPosts(newPosts)
    if (selectedPost) {
      const updated = newPosts.find((p: Post) => p.id === selectedPost.id)
      if (updated) setSelectedPost(updated)
    }
  }

  const createPost = async () => {
    if (!newTitle.trim() || !newContent.trim()) return
    await fetch(`${API_URL}/api/posts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: newTitle, content: newContent, author: CURRENT_USER }),
    })
    setNewTitle('')
    setNewContent('')
    setShowCreate(false)
    fetchPosts()
  }

  const vote = async (postId: number, direction: number) => {
    const post = posts.find((p) => p.id === postId)
    if (!post) return
    const currentVote = post.votes[CURRENT_USER] || 0
    const newDir = currentVote === direction ? 0 : direction
    await fetch(`${API_URL}/api/posts/${postId}/vote`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user: CURRENT_USER, direction: newDir }),
    })
    fetchPosts()
  }

  const deletePost = async (postId: number) => {
    await fetch(`${API_URL}/api/posts/${postId}`, { method: 'DELETE' })
    if (selectedPost?.id === postId) setSelectedPost(null)
    fetchPosts()
  }

  return (
    <div className="min-h-screen bg-zinc-900 text-zinc-100">
      {/* Header */}
      <header className="bg-zinc-800 border-b border-zinc-700 sticky top-0 z-50">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
          <div
            className="flex items-center gap-2 cursor-pointer"
            onClick={() => setSelectedPost(null)}
          >
            <div className="w-8 h-8 bg-orange-600 rounded-full flex items-center justify-center font-bold text-sm">
              F
            </div>
            <h1 className="text-lg font-bold">
              <span className="text-orange-500">r/</span>FoodieFinds
            </h1>
          </div>
          <button
            onClick={() => { setShowCreate(!showCreate); setSelectedPost(null); }}
            className="bg-orange-600 hover:bg-orange-500 text-white px-4 py-2 rounded-full text-sm font-medium flex items-center gap-1"
          >
            <Plus size={16} /> Create Post
          </button>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-6">
        {/* Create Post Form */}
        {showCreate && (
          <div className="bg-zinc-800 rounded-lg border border-zinc-700 p-4 mb-6">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold">Create a Post</h2>
              <button onClick={() => setShowCreate(false)} className="text-zinc-400 hover:text-zinc-200">
                <X size={20} />
              </button>
            </div>
            <input
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="Title"
              className="w-full bg-zinc-900 border border-zinc-600 rounded-lg px-4 py-2.5 text-sm text-zinc-200 focus:outline-none focus:border-orange-500 mb-3"
            />
            <textarea
              value={newContent}
              onChange={(e) => setNewContent(e.target.value)}
              placeholder="What's on your mind?"
              className="w-full bg-zinc-900 border border-zinc-600 rounded-lg px-4 py-2.5 text-sm text-zinc-200 focus:outline-none focus:border-orange-500 resize-none mb-3"
              rows={4}
            />
            <button
              onClick={createPost}
              disabled={!newTitle.trim() || !newContent.trim()}
              className="bg-orange-600 hover:bg-orange-500 disabled:bg-zinc-700 disabled:text-zinc-500 text-white px-6 py-2 rounded-full text-sm font-medium"
            >
              Post
            </button>
          </div>
        )}

        {/* Post Detail or Feed */}
        {selectedPost ? (
          <PostDetail
            post={selectedPost}
            onBack={() => setSelectedPost(null)}
            onRefresh={refreshAndUpdateSelected}
          />
        ) : (
          <>
            {/* Sort Tabs */}
            <div className="flex gap-2 mb-4">
              {[
                { key: 'hot' as const, icon: <Flame size={16} />, label: 'Hot' },
                { key: 'new' as const, icon: <Clock size={16} />, label: 'New' },
                { key: 'top' as const, icon: <TrendingUp size={16} />, label: 'Top' },
              ].map(({ key, icon, label }) => (
                <button
                  key={key}
                  onClick={() => setSortBy(key)}
                  className={`flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                    sortBy === key
                      ? 'bg-zinc-700 text-zinc-100'
                      : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
                  }`}
                >
                  {icon} {label}
                </button>
              ))}
            </div>

            {/* Loading / Error */}
            {loading && <p className="text-center text-zinc-400 py-8">Loading posts...</p>}
            {error && (
              <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 text-red-300 text-sm mb-4">
                {error}. Make sure the backend is running.
              </div>
            )}

            {/* Posts Feed */}
            {!loading && posts.length === 0 && !error && (
              <div className="text-center text-zinc-500 py-12">
                <p className="text-lg mb-2">No posts yet</p>
                <p className="text-sm">Be the first to create a post!</p>
              </div>
            )}
            {posts.map((post) => {
              const userVote = post.votes[CURRENT_USER] || 0
              return (
                <div
                  key={post.id}
                  className="bg-zinc-800 rounded-lg border border-zinc-700 mb-3 hover:border-zinc-500 transition-colors"
                >
                  <div className="flex gap-3 p-3">
                    <div className="flex flex-col items-center gap-0.5 pt-1">
                      <button
                        onClick={(e) => { e.stopPropagation(); vote(post.id, 1); }}
                        className={`p-0.5 rounded hover:bg-zinc-700 ${userVote === 1 ? 'text-orange-500' : 'text-zinc-500'}`}
                      >
                        <ArrowBigUp size={22} />
                      </button>
                      <span className={`text-xs font-bold ${post.score > 0 ? 'text-orange-400' : post.score < 0 ? 'text-blue-400' : 'text-zinc-400'}`}>
                        {post.score}
                      </span>
                      <button
                        onClick={(e) => { e.stopPropagation(); vote(post.id, -1); }}
                        className={`p-0.5 rounded hover:bg-zinc-700 ${userVote === -1 ? 'text-blue-500' : 'text-zinc-500'}`}
                      >
                        <ArrowBigDown size={22} />
                      </button>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs text-zinc-400 mb-0.5">
                        Posted by <span className="text-orange-400">{post.author}</span> · {timeAgo(post.created_at)}
                      </div>
                      <h3
                        onClick={() => setSelectedPost(post)}
                        className="text-base font-semibold text-zinc-100 cursor-pointer hover:text-orange-400 transition-colors mb-1"
                      >
                        {post.title}
                      </h3>
                      <p className="text-sm text-zinc-400 line-clamp-2">{post.content}</p>
                      <div className="flex items-center gap-3 mt-2">
                        <button
                          onClick={() => setSelectedPost(post)}
                          className="text-xs text-zinc-500 hover:text-zinc-300 flex items-center gap-1"
                        >
                          <MessageSquare size={14} /> {post.comment_count} Comments
                        </button>
                        {post.author === CURRENT_USER && (
                          <button
                            onClick={(e) => { e.stopPropagation(); deletePost(post.id); }}
                            className="text-xs text-zinc-500 hover:text-red-400 flex items-center gap-1"
                          >
                            <Trash2 size={14} /> Delete
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </>
        )}
      </main>
    </div>
  )
}

export default App
