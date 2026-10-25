-- Run this once in the Supabase SQL Editor (Dashboard > SQL Editor > New query).

create table sessions (
  code       text primary key,
  admin_key  text not null,
  team_name  text not null,
  min_n      int  not null default 4,
  created_on date not null default current_date
);

create table responses (
  id           bigint generated always as identity primary key,
  session_code text  not null references sessions(code),
  answers      jsonb not null,
  submitted_on date  not null default current_date
  -- Deliberately NO name, email, IP, user agent or timestamp-of-day column:
  -- anonymity by design. Only the submission DATE is kept.
);

-- Lock the database: RLS on, no public policies. With no policies, the anon
-- key can read/write nothing. The app connects server-side with the service
-- role key, which bypasses RLS and lives only in Streamlit Cloud's secrets.
alter table sessions  enable row level security;
alter table responses enable row level security;
