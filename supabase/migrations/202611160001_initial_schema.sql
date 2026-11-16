-- NP.ai Supabase schema. Apply with Supabase SQL Editor or Supabase CLI.
create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  avatar_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.conversations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null default 'New conversation',
  provider text not null check (provider in ('openai', 'anthropic', 'google')),
  model text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists conversations_user_updated_idx
  on public.conversations(user_id, updated_at desc);

create table if not exists public.messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  content text not null check (char_length(content) between 1 and 12000),
  created_at timestamptz not null default now()
);

create index if not exists messages_conversation_created_idx
  on public.messages(conversation_id, created_at);

create table if not exists public.chat_usage_events (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now()
);

create index if not exists chat_usage_user_created_idx
  on public.chat_usage_events(user_id, created_at desc);

alter table public.profiles enable row level security;
alter table public.conversations enable row level security;
alter table public.messages enable row level security;
alter table public.chat_usage_events enable row level security;

drop policy if exists "Users read own profile" on public.profiles;
create policy "Users read own profile" on public.profiles for select to authenticated using ((select auth.uid()) = id);
drop policy if exists "Users update own profile" on public.profiles;
create policy "Users update own profile" on public.profiles for update to authenticated using ((select auth.uid()) = id) with check ((select auth.uid()) = id);

drop policy if exists "Users manage own conversations" on public.conversations;
create policy "Users manage own conversations" on public.conversations for all to authenticated
  using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);

drop policy if exists "Users manage own messages" on public.messages;
create policy "Users manage own messages" on public.messages for all to authenticated
  using ((select auth.uid()) = user_id) with check (
    (select auth.uid()) = user_id and exists (
      select 1 from public.conversations c
      where c.id = conversation_id and c.user_id = (select auth.uid())
    )
  );

-- Usage events are private and may only be written by the quota function.
revoke all on public.chat_usage_events from anon, authenticated;
grant select on public.profiles, public.conversations, public.messages to authenticated;
grant insert, update, delete on public.conversations, public.messages to authenticated;
grant usage, select on all sequences in schema public to authenticated;

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.profiles (id, display_name)
  values (new.id, coalesce(new.raw_user_meta_data ->> 'display_name', split_part(new.email, '@', 1)))
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Atomically enforce 10 chats / 10 minutes and 100 chats / 24 hours per account.
create or replace function public.consume_chat_quota()
returns table (allowed boolean, short_remaining integer, daily_remaining integer, retry_after_seconds integer)
language plpgsql
security definer
set search_path = ''
as $$
declare
  current_user_id uuid := auth.uid();
  short_count integer;
  daily_count integer;
  oldest_short timestamptz;
  oldest_daily timestamptz;
  retry_seconds integer := 0;
begin
  if current_user_id is null then
    raise exception 'Authentication required' using errcode = '42501';
  end if;

  perform pg_advisory_xact_lock(hashtextextended(current_user_id::text, 0));

  select count(*)::integer, min(created_at)
    into short_count, oldest_short
    from public.chat_usage_events
    where user_id = current_user_id and created_at > now() - interval '10 minutes';

  select count(*)::integer, min(created_at)
    into daily_count, oldest_daily
    from public.chat_usage_events
    where user_id = current_user_id and created_at > now() - interval '24 hours';

  if short_count >= 10 or daily_count >= 100 then
    if short_count >= 10 and oldest_short is not null then
      retry_seconds := greatest(retry_seconds, ceil(extract(epoch from (oldest_short + interval '10 minutes' - now())))::integer);
    end if;
    if daily_count >= 100 and oldest_daily is not null then
      retry_seconds := greatest(retry_seconds, ceil(extract(epoch from (oldest_daily + interval '24 hours' - now())))::integer);
    end if;
    return query select false, greatest(0, 10 - short_count), greatest(0, 100 - daily_count), greatest(1, retry_seconds);
    return;
  end if;

  insert into public.chat_usage_events(user_id) values (current_user_id);
  return query select true, greatest(0, 9 - short_count), greatest(0, 99 - daily_count), 0;
end;
$$;

revoke all on function public.consume_chat_quota() from public, anon;
grant execute on function public.consume_chat_quota() to authenticated;
