<h1 align="center">Brain Imaging Studio</h1>

Create and explore brain image progressions across timepoints. Users input patient context (EHR + CT + base prompt). A backend model crafts a generated prompt, images are created, saved to Supabase, and displayed per case.

## Stack
- Next.js App Router (TypeScript, Tailwind)
- Supabase (Postgres, client SDK)
- Flask backend (`backend/flask_app.py`)
- BFL image generation API (Flux Kontext Pro)

Auth is disabled in `middleware.ts` for now; all routes are public. Re-enable later as needed.

## Environment variables
Frontend (`.env.local`):
```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_OR_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_BACKEND_URL=http://localhost:5001
```

Backend (shell or `.env` when running Flask):
```
BFL_API_KEY=your_bfl_api_key
```

## Supabase schema
Simple single-table design with JSON for files and images.

```sql
create table if not exists public.cases (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  user_id uuid null,

  -- patient info
  patient_first_name text,
  patient_last_name text,
  patient_age int,
  patient_mrn text,
  patient_notes text,

  -- prompts
  base_prompt text,
  generated_prompt text,

  -- file metadata (optional "path" for Supabase Storage)
  ehr_files jsonb,   -- [{ name, size, type, path }]
  ct_scans jsonb,    -- [{ name, size, type, path }]

  -- outputs
  images jsonb,      -- { "now": {url, timepoint, promptUsed}, "3m": {...}, ... }
  video_url text
);
```

RLS options:
- Development: disable RLS to avoid auth requirements while auth is off
```sql
alter table public.cases disable row level security;
```
- Production (later): enable RLS and add policies for per-user access.

## Run locally
1) Install frontend deps and run Next.js:
```bash
cd my-app
npm install
npm run dev
# http://localhost:3000
```

2) Run backend Flask app:
```bash
cd my-app/backend
pip install flask requests
export BFL_API_KEY=your_bfl_api_key
python flask_app.py
# http://localhost:5001
```

## Pipeline
1) User opens Home → “Create New Case” → `/protected/brain/input`
2) On submit:
   - Frontend sends multipart/form-data to `POST /model/prompt` (Flask) with:
     - `patient` JSON, `base_prompt`, and uploaded `ehr_files[]`, `ct_scans[]`
   - Flask returns `{ generated_prompt }`
   - Frontend inserts a case row in Supabase with:
     - `base_prompt`, `generated_prompt`, file metadata (add Storage paths later)
   - Frontend requests images via `POST /model/generate_images` (Flask) with:
     - `{ prompt: generated_prompt || base_prompt, timepoints: ["now","3m","6m","12m"] }`
   - Flask calls BFL API (hard-coded), polls until ready, returns image URLs
   - Frontend updates the case `images` in Supabase and routes to `/protected/brain/[caseId]`

3) The case page reads `images` from Supabase and displays the four timepoints.

Endpoints (Flask):
- `POST /model/prompt` → `{ generated_prompt }`
- `POST /model/generate_images` → `{ images: { now, 3m, 6m, 12m } }`

Key frontend files:
- `app/page.tsx`: landing with rotating brain and entry buttons
- `app/protected/brain/input/page.tsx`: input form and submission pipeline
- `app/protected/brain/cases/page.tsx`: list of all cases
- `app/protected/brain/[caseId]/page.tsx`: case detail page

Key libs:
- `lib/brain/model.ts`: calls Flask `/model/prompt`
- `lib/brain/generator.ts`: calls Flask `/model/generate_images`
- `lib/brain/db.ts`: Supabase CRUD and image updates
- `lib/brain/types.ts`: shared types

## Notes / Next steps
- Uploads: integrate Supabase Storage to upload `ehrFiles`/`ctScans`, then store `path` in JSON.
- Reprompt on case page: currently uses a placeholder generator in `db.ts`. Wire it to Flask `generate_images` for consistency.
- Auth: when enabled, add RLS policies and set `user_id` via `auth.uid()`.
- Normalization: you can split `images` and `files` into separate tables if you need stronger constraints or search.

## Troubleshooting
- 401/permission errors from Supabase when auth is disabled: disable RLS (see above) during development.
- Image generation timeouts: increase the poll timeout in `backend/flask_app.py` or handle retries.
