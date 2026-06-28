-- AI Content Tracker — Supabase schema
-- Run in Supabase SQL Editor: https://supabase.com/dashboard

-- Profiles (extends auth.users)
create table if not exists public.profiles (
    user_id uuid primary key references auth.users (id) on delete cascade,
    notification_email text,
    display_name text,
    created_at timestamptz default now()
);

-- YouTube channels to monitor
create table if not exists public.youtube_channels (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users (id) on delete cascade,
    channel_id text not null,
    channel_url text not null,
    channel_name text,
    created_at timestamptz default now(),
    unique (user_id, channel_id)
);

-- Website URLs to monitor (OpenAI News, Anthropic, etc.)
create table if not exists public.tracked_urls (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users (id) on delete cascade,
    site_name text not null,
    url text not null,
    url_type text default 'website',
    last_checked_at timestamptz,
    created_at timestamptz default now(),
    unique (user_id, url)
);

-- Videos already processed (avoid duplicate emails)
create table if not exists public.processed_videos (
    id uuid primary key default gen_random_uuid(),
    channel_id uuid not null references public.youtube_channels (id) on delete cascade,
    video_id text not null,
    title text,
    video_url text not null,
    processed_at timestamptz default now(),
    emailed_at timestamptz,
    unique (channel_id, video_id)
);

-- Articles/pages already processed
create table if not exists public.processed_articles (
    id uuid primary key default gen_random_uuid(),
    tracked_url_id uuid not null references public.tracked_urls (id) on delete cascade,
    content_hash text not null,
    title text,
    article_url text not null,
    processed_at timestamptz default now(),
    emailed_at timestamptz,
    unique (tracked_url_id, content_hash)
);

-- Generated reports
create table if not exists public.reports (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users (id) on delete cascade,
    source_type text not null check (source_type in ('youtube', 'website', 'manual')),
    source_url text,
    topic text,
    markdown text not null,
    storage_path text,
    created_at timestamptz default now()
);

-- Encrypted per-user OpenAI API keys (for scheduled automation)
create table if not exists public.user_secrets (
    user_id uuid primary key references auth.users (id) on delete cascade,
    openai_api_key_encrypted text not null,
    allow_scheduled_jobs boolean not null default true,
    updated_at timestamptz default now()
);

-- Auto-create profile on signup
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
    insert into public.profiles (user_id, notification_email, display_name)
    values (
        new.id,
        new.email,
        coalesce(new.raw_user_meta_data ->> 'display_name', split_part(new.email, '@', 1))
    );
    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute procedure public.handle_new_user();

revoke execute on function public.handle_new_user() from public;
revoke execute on function public.handle_new_user() from anon;
revoke execute on function public.handle_new_user() from authenticated;

-- Row Level Security
alter table public.profiles enable row level security;
alter table public.youtube_channels enable row level security;
alter table public.tracked_urls enable row level security;
alter table public.processed_videos enable row level security;
alter table public.processed_articles enable row level security;
alter table public.reports enable row level security;
alter table public.user_secrets enable row level security;

-- Profiles policies
create policy "Users read own profile" on public.profiles
    for select using (auth.uid() = user_id);
create policy "Users update own profile" on public.profiles
    for update using (auth.uid() = user_id);

-- YouTube channels policies
create policy "Users manage own channels" on public.youtube_channels
    for all using (auth.uid() = user_id);

-- Tracked URLs policies
create policy "Users manage own urls" on public.tracked_urls
    for all using (auth.uid() = user_id);

-- Processed videos (via channel ownership)
create policy "Users read own processed videos" on public.processed_videos
    for select using (
        exists (
            select 1 from public.youtube_channels c
            where c.id = processed_videos.channel_id and c.user_id = auth.uid()
        )
    );

-- Processed articles (via tracked url ownership)
create policy "Users read own processed articles" on public.processed_articles
    for select using (
        exists (
            select 1 from public.tracked_urls t
            where t.id = processed_articles.tracked_url_id and t.user_id = auth.uid()
        )
    );

-- Reports policies
create policy "Users manage own reports" on public.reports
    for all using (auth.uid() = user_id);

-- User secrets: users manage only their encrypted key row
create policy "Users manage own secrets" on public.user_secrets
    for all using (auth.uid() = user_id);

-- Service role bypasses RLS when using SUPABASE_SERVICE_ROLE_KEY in workers.
