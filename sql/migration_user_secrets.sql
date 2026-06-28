-- Run this if you already applied schema.sql before user_secrets was added.

create table if not exists public.user_secrets (
    user_id uuid primary key references auth.users (id) on delete cascade,
    openai_api_key_encrypted text not null,
    allow_scheduled_jobs boolean not null default true,
    updated_at timestamptz default now()
);

alter table public.user_secrets enable row level security;

drop policy if exists "Users manage own secrets" on public.user_secrets;
create policy "Users manage own secrets" on public.user_secrets
    for all using (auth.uid() = user_id);
