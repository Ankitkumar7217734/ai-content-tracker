-- Google OAuth profile support
-- Run in Supabase SQL Editor after enabling Google provider in Authentication → Providers

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
        coalesce(
            new.raw_user_meta_data ->> 'display_name',
            new.raw_user_meta_data ->> 'full_name',
            new.raw_user_meta_data ->> 'name',
            split_part(new.email, '@', 1)
        )
    );
    return new;
end;
$$;

-- Optional: store Google subject id for debugging / support (not required for email routing)
alter table public.profiles
    add column if not exists google_sub text;

create or replace function public.sync_google_identity()
returns trigger
language plpgsql
security definer set search_path = public
as $$
declare
    gsub text;
begin
    gsub := coalesce(
        new.raw_user_meta_data ->> 'sub',
        new.raw_user_meta_data ->> 'provider_id'
    );
    if gsub is not null then
        update public.profiles
        set google_sub = gsub
        where user_id = new.id;
    end if;
    return new;
end;
$$;

drop trigger if exists on_auth_user_google_sync on auth.users;
create trigger on_auth_user_google_sync
    after insert or update on auth.users
    for each row execute procedure public.sync_google_identity();
