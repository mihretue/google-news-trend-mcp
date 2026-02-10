# Supabase Setup Guide

## Prerequisites

1. Create a Supabase account at https://supabase.com
2. Create a new project
3. Note your project credentials:
   - Project URL (SUPABASE_URL)
   - Anon Key (SUPABASE_KEY)
   - JWT Secret (SUPABASE_JWT_SECRET)

## Setup Steps

### 1. Create Tables and RLS Policies

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Create a new query
4. Copy the contents of `001_create_tables.sql`
5. Run the query

This will create:
- `conversations` table with user isolation
- `messages` table with user isolation
- Indexes for performance
- Row-Level Security (RLS) policies

### 2. Verify Setup

Run these queries to verify:

```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';

-- Check RLS is enabled
SELECT tablename, rowsecurity FROM pg_tables 
WHERE schemaname = 'public';

-- Check policies
SELECT * FROM pg_policies 
WHERE tablename IN ('conversations', 'messages');
```

### 3. Test RLS Policies

1. Create two test users via Supabase Auth
2. Get their JWT tokens
3. Test that User A cannot access User B's data:

```bash
# User A creates a conversation
curl -X POST http://localhost:8000/chat/conversations \
  -H "Authorization: Bearer USER_A_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Conversation"}'

# User B tries to access User A's conversations
curl http://localhost:8000/chat/conversations \
  -H "Authorization: Bearer USER_B_TOKEN"

# Should return empty list (User B's conversations only)
```

## Environment Variables

Add these to your `.env` file:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
```

## Troubleshooting

### RLS policies not working

1. Verify RLS is enabled: `ALTER TABLE table_name ENABLE ROW LEVEL SECURITY;`
2. Check policies exist: `SELECT * FROM pg_policies WHERE tablename = 'table_name';`
3. Verify auth.uid() is available in policies

### Cannot insert data

1. Check user is authenticated (has valid JWT)
2. Verify user_id in token matches auth.uid()
3. Check GRANT permissions are set correctly

### Performance issues

1. Verify indexes are created: `SELECT * FROM pg_indexes WHERE tablename IN ('conversations', 'messages');`
2. Consider adding more indexes if queries are slow
3. Monitor query performance in Supabase dashboard

## Data Model

### conversations table
- `id` (UUID): Primary key
- `user_id` (UUID): Foreign key to auth.users
- `title` (TEXT): Conversation title
- `created_at` (TIMESTAMP): Creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

### messages table
- `id` (UUID): Primary key
- `conversation_id` (UUID): Foreign key to conversations
- `user_id` (UUID): Foreign key to auth.users
- `role` (TEXT): 'user' or 'assistant'
- `content` (TEXT): Message content
- `tool_calls` (JSONB): Optional tool call metadata
- `created_at` (TIMESTAMP): Creation timestamp

## Next Steps

1. Update `.env` with your Supabase credentials
2. Run the backend to test database connectivity
3. Implement authentication endpoints
4. Implement chat endpoints
