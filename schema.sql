PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS events (
  id TEXT PRIMARY KEY, title TEXT NOT NULL, subtitle TEXT NOT NULL,
  category TEXT NOT NULL, starts_at TEXT NOT NULL, location TEXT NOT NULL,
  capacity INTEGER NOT NULL CHECK(capacity>0), description TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS registrations (
  id TEXT PRIMARY KEY, event_id TEXT NOT NULL REFERENCES events(id),
  display_name TEXT NOT NULL, email TEXT NOT NULL, created_at TEXT NOT NULL,
  UNIQUE(event_id,email)
);
CREATE TABLE IF NOT EXISTS sessions (
  token_hash TEXT PRIMARY KEY, user_id TEXT, csrf TEXT NOT NULL, expires INTEGER NOT NULL
);
