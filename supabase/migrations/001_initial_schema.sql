-- =====================================================================
-- Analytics By Shanikwa — initial schema
-- Run this in the Supabase SQL editor or via `supabase db push`.
-- =====================================================================

-- ── Newsletter subscribers ──────────────────────────────────────────
create table if not exists public.newsletter_subscribers (
  id         uuid primary key default gen_random_uuid(),
  email      text not null,
  source     text,                        -- e.g. "homepage", "community"
  created_at timestamptz not null default now(),

  constraint newsletter_subscribers_email_unique unique (email)
);

alter table public.newsletter_subscribers enable row level security;

-- Anyone can subscribe (no account needed)
create policy "public_insert_newsletter"
  on public.newsletter_subscribers
  for insert
  to anon, authenticated
  with check (true);

-- Only the service-role / authenticated admin can read the list
create policy "service_select_newsletter"
  on public.newsletter_subscribers
  for select
  to authenticated
  using (true);


-- ── Contact messages ────────────────────────────────────────────────
create table if not exists public.contact_messages (
  id         uuid primary key default gen_random_uuid(),
  name       text not null,
  email      text not null,
  subject    text,
  message    text not null,
  created_at timestamptz not null default now()
);

alter table public.contact_messages enable row level security;

-- Anyone can submit a contact message
create policy "public_insert_contact"
  on public.contact_messages
  for insert
  to anon, authenticated
  with check (true);

-- Only authenticated users (admin) can read messages
create policy "service_select_contact"
  on public.contact_messages
  for select
  to authenticated
  using (true);
