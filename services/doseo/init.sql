create table if not exists public.users(
login varchar not null unique,
password_hash varchar not null);