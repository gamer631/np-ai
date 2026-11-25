begin;

select plan(7);

-- Isolated fixture users; the auth trigger also exercises profile creation.
insert into auth.users (
  id, aud, role, email, encrypted_password, email_confirmed_at, created_at, updated_at
) values
  ('11111111-1111-4111-8111-111111111111', 'authenticated', 'authenticated', 'rls-a@example.test', '', now(), now(), now()),
  ('22222222-2222-4222-8222-222222222222', 'authenticated', 'authenticated', 'rls-b@example.test', '', now(), now(), now())
on conflict (id) do nothing;

insert into public.conversations (id, user_id, title, provider, model) values
  ('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', '11111111-1111-4111-8111-111111111111', 'A private conversation', 'openai', 'gpt-4o-mini'),
  ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', '22222222-2222-4222-8222-222222222222', 'B private conversation', 'openai', 'gpt-4o-mini');

insert into public.messages (id, conversation_id, user_id, role, content) values
  ('aaaaaaaa-0000-4000-8000-000000000001', 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', '11111111-1111-4111-8111-111111111111', 'user', 'A private message'),
  ('bbbbbbbb-0000-4000-8000-000000000001', 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', '22222222-2222-4222-8222-222222222222', 'user', 'B private message');

set local role authenticated;
select set_config('request.jwt.claim.sub', '11111111-1111-4111-8111-111111111111', true);
select set_config('request.jwt.claim.role', 'authenticated', true);

select is(
  (select count(*)::integer from public.conversations),
  1,
  'User A can see only their own conversation'
);

select is(
  (select count(*)::integer from public.messages),
  1,
  'User A can see only their own messages'
);

select throws_ok(
  $$insert into public.conversations (user_id, title, provider, model)
    values ('22222222-2222-4222-8222-222222222222', 'forbidden', 'openai', 'gpt-4o-mini')$$,
  '42501',
  'User A cannot create a conversation owned by User B'
);

select throws_ok(
  $$insert into public.messages (conversation_id, user_id, role, content)
    values ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', '11111111-1111-4111-8111-111111111111', 'user', 'cross-account write')$$,
  '42501',
  'User A cannot write a message into User B conversation'
);

select throws_ok(
  $$select * from public.chat_usage_events$$,
  '42501',
  'Authenticated users cannot read the private quota ledger'
);

select is(
  (
    select count(*)::integer
    from generate_series(1, 10) as request_number
    cross join lateral public.consume_chat_quota() as quota
    where quota.allowed
  ),
  10,
  'The first ten quota requests are allowed'
);

select is(
  (select allowed from public.consume_chat_quota()),
  false,
  'The eleventh request is rejected by the ten-per-ten-minute quota'
);

reset role;
select * from finish();
rollback;
