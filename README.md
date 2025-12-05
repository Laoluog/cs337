# BrainCast AI

> A multimodal AI system for generating longitudinal brain imaging reconstructions from clinical data        
> Demo Video: https://www.youtube.com/watch?v=MZBBhJiUcmc

[![Next.js](https://img.shields.io/badge/Next.js-15.3-black?logo=next.js)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org/)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-green?logo=supabase)](https://supabase.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue?logo=typescript)](https://www.typescriptlang.org/)

---

## Overview

**BrainCast AI** is a research platform that synthesizes multimodal clinical data—electronic health records (EHR), CT scans, and clinical context—into AI-generated brain imaging progressions across temporal horizons. Built for clinical research teams, this system demonstrates how modern generative AI can visualize potential disease trajectories and treatment outcomes over time.

The platform orchestrates three state-of-the-art AI models to transform raw clinical inputs into rich, longitudinal visual narratives:

1. **Gemini Pro** – Contextual prompt generation from multimodal clinical data
2. **Flux Kontext Pro** – High-fidelity medical image synthesis 
3. **Google Veo 3.1** – Cinematic 3D brain visualizations

### Key Capabilities

- **Multimodal Data Fusion**: Intelligently combines structured EHR data, unstructured clinical notes, and medical imaging
- **Longitudinal Visualization**: Generates brain states across multiple timepoints (baseline, 3-month, 6-month, 12-month)
- **Iterative Refinement**: Edit and reprompt functionality for exploring alternative clinical scenarios
- **Video Generation**: Synthesizes smooth 360° orbital views of generated brain states
- **Research-Grade Pipeline**: End-to-end reproducible workflow from data ingestion to visualization

---

## Architecture

### System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                          │
│  Next.js 15 + TypeScript + Tailwind CSS + Supabase Client      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┴─────────────┐
                │    API Gateway Layer      │
                │   (Flask + CORS)          │
                └────────────┬──────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼────────┐  ┌────────▼────────┐  ┌───────▼────────┐
│  Gemini Pro    │  │  Flux Kontext   │  │  Google Veo    │
│  (Prompting)   │  │  (Imaging)      │  │  (Video)       │
└────────────────┘  └─────────────────┘  └────────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                   ┌─────────▼─────────┐
                   │   Supabase DB     │
                   │   (PostgreSQL)    │
                   └───────────────────┘
```

### Technology Stack

#### Frontend
- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript 5.0
- **Styling**: Tailwind CSS 3.4 + Radix UI primitives
- **State Management**: React 19 hooks + Server Components
- **Database Client**: Supabase JS SDK with SSR support

#### Backend
- **Runtime**: Python 3.10+
- **Framework**: Flask with Flask-CORS
- **AI APIs**: 
  - Google Gemini API (multimodal understanding)
  - BFL Flux API (medical image generation)
  - Google Generative AI (video synthesis)
- **Data Processing**: Pillow for image handling

#### Infrastructure
- **Database**: Supabase (PostgreSQL with real-time capabilities)
- **Storage**: Supabase Storage (scalable file uploads)
- **Authentication**: Supabase Auth (currently disabled for development)

---

## Features Deep Dive

### 1. Intelligent Prompt Generation

The system employs **Gemini Pro** as a clinical reasoning engine that:

- Parses structured patient demographics (name, age, MRN, notes)
- Extracts and interprets unstructured EHR text (clinical notes, lab reports, medication lists)
- Analyzes uploaded CT scan images using multimodal understanding
- Synthesizes all inputs into detailed, clinically-grounded prompts optimized for downstream image generation

**Technical Implementation**: The prompt generator (`/model/prompt`) uses Gemini's multimodal API with custom temperature tuning (0.2) and sophisticated context assembly to maintain clinical accuracy while enabling creative visualization.

### 2. Temporal Image Generation

**Flux Kontext Pro** generates medically-plausible brain imaging sequences by:

- Accepting rich clinical prompts with patient-specific context
- Generating distinct images for four temporal horizons (now, 3M, 6M, 12M)
- Applying timepoint-specific augmentations to simulate disease progression or treatment response
- Maintaining anatomical consistency across the longitudinal sequence

**Performance**: Each image takes ~30-60 seconds to generate at medical-grade resolution with polling-based completion tracking.

### 3. Edit & Reprompt Workflow

Researchers can iteratively refine generated images through:

- **Prompt Augmentation**: Add specific clinical details or focus areas
- **Selective Regeneration**: Choose which timepoints to update
- **Real-time Feedback**: View updated images immediately upon generation
- **Version History**: All generations stored in Supabase for comparison

This enables hypothesis testing and scenario exploration critical for research applications.

### 4. Cinematic Video Synthesis

**Google Veo 3.1** transforms static brain images into dynamic 360° visualizations:

- **Reference-Driven Generation**: Uses generated brain images as visual anchors
- **Anatomically Accurate Motion**: Smooth orbital camera path with clinical realism
- **High-Fidelity Rendering**: Ultra-HD output with photorealistic lighting
- **Configurable Duration**: Adjustable video length (default: 7 seconds)

Videos are stored locally and served via Flask's static file serving, making them immediately viewable in the web interface.

---

## Installation & Setup

### Prerequisites

- **Node.js** 20+ (for Next.js)
- **Python** 3.10+ (for Flask backend)
- **Supabase Account** (for database and storage)

### Environment Variables

Create a `.env.local` file in the `my-app` directory:

```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_OR_ANON_KEY=your_supabase_anon_key

# Backend API
NEXT_PUBLIC_BACKEND_URL=http://localhost:5000
```

Create environment variables for the Flask backend (or a `.env` file):

```bash
# AI API Keys
export BFL_API_KEY=your_bfl_api_key              # Flux Kontext Pro
export GEMINI_API_KEY=your_gemini_api_key        # Gemini Pro
export GOOGLE_API_KEY=your_google_api_key        # Veo 3.1

# Optional: Model Configuration
export GEMINI_MODEL_NAME=gemini-pro-latest
```

### Database Schema

Run this SQL in your Supabase SQL editor:

```sql
create table if not exists public.cases (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  user_id uuid null,
  
  -- Patient Information
  patient_first_name text,
  patient_last_name text,
  patient_age int,
  patient_mrn text,
  patient_notes text,
  
  -- Prompts
  base_prompt text,
  generated_prompt text,
  
  -- File Metadata (JSON storage for flexibility)
  ehr_files jsonb,   -- [{ name, size, type, path }]
  ct_scans jsonb,    -- [{ name, size, type, path }]
  
  -- Generated Outputs
  images jsonb,      -- { "now": {url, timepoint, promptUsed}, "3m": {...}, ... }
  video_url text
);

-- Disable RLS for development (enable with proper policies in production)
alter table public.cases disable row level security;
```

### Installation

#### 1. Clone and Install Frontend

```bash
cd my-app
npm install
```

#### 2. Install Backend Dependencies

```bash
cd my-app/backend
pip install -r requirements.txt
```

---

## Running the Application

### Development Mode

**Terminal 1 - Backend:**

```bash
cd my-app/backend
python flask_app.py
```

The Flask server will start on `http://localhost:5000`

**Terminal 2 - Frontend:**

```bash
cd my-app
npm run dev
```

The Next.js app will be available at `http://localhost:3000`

### Production Build

```bash
cd my-app
npm run build
npm start
```

---

## Usage Guide

### Creating a New Case

1. Navigate to the home page at `http://localhost:3000`
2. Click **"Create Case"**
3. Fill in the patient information form:
   - Patient demographics (name, age, MRN)
   - Clinical notes/context
   - Upload EHR documents (text, JSON, CSV files)
   - Upload CT scan images
   - Provide a base prompt describing the clinical scenario
4. Submit the form

**Behind the Scenes:**
- Frontend sends multipart form data to Flask `/model/prompt`
- Gemini processes all inputs and generates an enhanced clinical prompt
- Case is created in Supabase with metadata
- Flux generates images for all four timepoints (2-4 minutes)
- User is redirected to the case detail page

### Viewing Cases

- Access the **"View Cases"** page to see all generated cases
- Cases display patient name, creation date, and preview thumbnails
- Click any case to view full longitudinal sequence and details

### Editing and Reprompting

On any case detail page:

1. Scroll to the **"Edit and Reprompt"** section
2. Enter additional clinical context or modifications
3. Select which timepoints to regenerate (checkboxes)
4. Click **"Reprompt Selected"**
5. Wait for new images to generate (30-60s per timepoint)
6. New images automatically update in the UI and database

### Generating Videos

1. On a case detail page, navigate to the video section
2. Click **"Generate Video"** for a specific timepoint
3. The system creates a 7-second 360° orbital view
4. Video player appears when generation completes (~30-60 seconds)

---

## API Documentation

### Endpoints

#### `POST /model/prompt`

Generates an enhanced clinical prompt using Gemini.

**Request:** `multipart/form-data`
- `base_prompt` (string): User-provided clinical prompt
- `patient` (JSON string): Patient demographics and notes
- `ehr_files` (files): Electronic health record documents
- `ct_scans` (files): CT scan images

**Response:**
```json
{
  "generated_prompt": "Detailed clinical prompt synthesized by Gemini..."
}
```

#### `POST /model/generate_images`

Generates brain images for specified timepoints.

**Request:** `application/json`
```json
{
  "prompt": "Clinical prompt text or object",
  "timepoints": ["now", "3m", "6m", "12m"]
}
```

**Response:**
```json
{
  "images": {
    "now": "https://...",
    "3m": "https://...",
    "6m": "https://...",
    "12m": "https://..."
  }
}
```

#### `POST /model/generate_video`

Creates a 360° video visualization of a brain image.

**Request:** `application/json`
```json
{
  "image_url": "https://...",
  "prompt": "Clinical context for video generation",
  "time_point": "now",
  "seconds": 7
}
```

**Response:**
```json
{
  "video_url": "http://localhost:5000/static/videos/brain_uuid.mp4"
}
```

---

## Project Structure

```
cs337project/
├── my-app/                          # Next.js application root
│   ├── app/                         # Next.js App Router pages
│   │   ├── page.tsx                 # Landing page with rotating brain
│   │   ├── layout.tsx               # Root layout with Supabase integration
│   │   ├── auth/                    # Authentication flows (sign-up, login, etc.)
│   │   └── protected/               # Authenticated routes
│   │       └── brain/
│   │           ├── input/           # Case creation form
│   │           ├── cases/           # Case listing page
│   │           └── [caseId]/        # Case detail view with edit/reprompt
│   │
│   ├── components/                  # React components
│   │   ├── brain/
│   │   │   └── home-landing.tsx     # Landing page component
│   │   └── ui/                      # Radix UI primitives (button, input, etc.)
│   │
│   ├── lib/                         # Library code and utilities
│   │   ├── brain/
│   │   │   ├── db.ts                # Supabase CRUD operations
│   │   │   ├── generator.ts         # Image generation API client
│   │   │   ├── model.ts             # Prompt generation API client
│   │   │   ├── video.ts             # Video generation API client
│   │   │   └── types.ts             # TypeScript type definitions
│   │   ├── supabase/                # Supabase client initialization
│   │   └── utils.ts                 # Utility functions
│   │
│   ├── backend/                     # Flask backend
│   │   ├── flask_app.py             # Main Flask application
│   │   ├── requirements.txt         # Python dependencies
│   │   ├── test_reprompt.py         # Backend test suite
│   │   ├── api_spec.yaml            # OpenAPI specification
│   │   ├── static/videos/           # Generated video storage
│   │   ├── README.md                # Backend documentation
│   │   ├── QUICK_START.md           # Quick start guide
│   │   └── REPROMPT_FLOW.md         # Reprompt feature documentation
│   │
│   └── package.json                 # Node.js dependencies
│
├── CHANGES_SUMMARY.md               # Development changelog
└── README.md                        # This file
```

---

## Key Implementation Details

### Multimodal Prompt Engineering

The system's prompt generation pipeline demonstrates sophisticated multimodal reasoning:

1. **Context Assembly**: Patient demographics, clinical notes, and imaging are structured into a coherent narrative
2. **EHR Text Extraction**: Intelligently parses text-like files (JSON, CSV, TXT) with graceful handling of binary formats
3. **Image Encoding**: CT scans are base64-encoded and embedded as inline data in Gemini API requests
4. **Few-Shot Instruction**: The prompt generator is instructed to act as a "clinical prompt generator for downstream CT scan generation," ensuring outputs are optimized for the image synthesis stage
5. **Temperature Tuning**: Low temperature (0.2) ensures clinical accuracy while allowing creative visual description

**Code Reference**: `backend/flask_app.py` lines 106-172

### Timepoint-Specific Generation

To create realistic disease progression or treatment response visualization:

1. Each timepoint receives a suffix modification to the base prompt:
   - `"now"` → "current brain state"
   - `"3m"` → "brain state in approximately 3 months"
   - `"6m"` → "brain state in approximately 6 months"
   - `"12m"` → "brain state in approximately 12 months"

2. Flux Kontext Pro interprets these temporal cues in context of the clinical scenario
3. The model naturally generates progressive changes (tumor growth, atrophy progression, treatment response, etc.)

**Code Reference**: `backend/flask_app.py` lines 379-399

### Polling-Based Completion Tracking

Both image and video generation use robust polling mechanisms:

- **Initial Request**: Submits prompt to API, receives `polling_url`
- **Status Checks**: Polls every 0.5 seconds with 90-second timeout
- **State Handling**: Detects `Ready`, `Error`, `Failed`, and timeout states
- **Error Recovery**: Graceful failures allow other timepoints to continue

This ensures reliability even with API latency variability.

**Code Reference**: `backend/flask_app.py` lines 363-377 (images), 312-316 (video)

### Frontend State Management

The case detail page employs sophisticated state synchronization:

- **Optimistic Updates**: UI updates immediately on user action
- **Background Regeneration**: New images are fetched without blocking interaction
- **Atomic Updates**: Supabase updates are transactional, preventing partial state
- **Error Boundaries**: Graceful fallbacks to placeholder images if backend is unavailable

**Code Reference**: `app/protected/brain/[caseId]/page.tsx` lines 96-116

---

## Testing

### Backend Endpoint Testing

```bash
cd my-app/backend
python test_reprompt.py
```

This automated test suite verifies:
- Flask server connectivity
- Image generation endpoint functionality
- BFL API integration
- Error handling and timeouts

### Manual API Testing

Test prompt generation:
```bash
curl -X POST http://localhost:5000/model/prompt \
  -F "base_prompt=CT scan of brain with tumor progression" \
  -F "patient={\"firstName\":\"John\",\"lastName\":\"Doe\",\"age\":45}"
```

Test image generation:
```bash
curl -X POST http://localhost:5000/model/generate_images \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Detailed CT scan of human brain showing early stage glioblastoma",
    "timepoints": ["now", "3m"]
  }'
```

---

## Performance Considerations

### Generation Times

| Operation | Duration | Bottleneck |
|-----------|----------|------------|
| Prompt Generation | 2-5 seconds | Gemini API latency |
| Single Image | 30-60 seconds | Flux rendering + polling |
| Full 4-Image Sequence | 2-4 minutes | Sequential generation |
| Video Generation | 30-90 seconds | Veo rendering + I/O |

### Optimization Strategies

1. **Parallel Generation**: Could parallelize timepoint generation (currently sequential)
2. **Caching**: Implement prompt/image caching for identical inputs
3. **Progressive Rendering**: Stream images to frontend as they complete
4. **Database Indexing**: Add indexes on `created_at` and `user_id` for fast case retrieval
5. **CDN Integration**: Serve generated images via CDN for global low-latency access

---

## Troubleshooting

### Common Issues

**Backend Connection Refused**
- Ensure Flask is running on port 5000: `python flask_app.py`
- Check `NEXT_PUBLIC_BACKEND_URL` in `.env.local`

**Missing API Keys**
- Verify all three API keys are exported: `BFL_API_KEY`, `GEMINI_API_KEY`, `GOOGLE_API_KEY`
- Restart Flask after setting environment variables

**Supabase 401 Errors**
- Check that RLS is disabled: `alter table public.cases disable row level security;`
- Verify Supabase credentials in `.env.local`

**Image Generation Timeout**
- Increase timeout in `flask_app.py` line 376 (default: 90 seconds)
- Check BFL API status and rate limits

**Placeholder Images Appearing**
- This is expected graceful fallback when backend is unreachable
- Check Flask logs for error details
- Verify network connectivity to BFL API

### Debug Mode

Enable verbose logging in Flask:

```python
# In flask_app.py
app.run(host="0.0.0.0", port=5000, debug=True)
```

Frontend debugging:
- Open browser DevTools → Console
- Check Network tab for failed API requests
- Verify Supabase queries in Application → Storage

---

## Roadmap & Future Enhancements

### Planned Features

- [ ] **Parallel Image Generation**: Generate all timepoints simultaneously for 4x speedup
- [ ] **Prompt Templates**: Pre-configured templates for common clinical scenarios
- [ ] **DICOM Support**: Native handling of medical imaging formats
- [ ] **Export Capabilities**: PDF reports with images, clinical context, and analysis
- [ ] **Collaborative Annotations**: Multi-user commenting and markup tools
- [ ] **Advanced Video Controls**: Custom camera paths, lighting, duration
- [ ] **Model Ensemble**: Aggregate predictions from multiple image generators
- [ ] **Authentication**: Enable Supabase Auth with role-based access control
- [ ] **Audit Trail**: Complete version history with diff visualization

### Research Extensions

- **Quantitative Analysis**: Extract volumetric metrics from generated images
- **Uncertainty Visualization**: Show confidence intervals for predicted states
- **Clinical Validation**: Compare generated progressions against real follow-up scans
- **Multi-Disease Support**: Expand beyond neuro-oncology to other pathologies

---

## Contributing

This is a research project developed for educational purposes. If you'd like to extend or adapt this work:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Guidelines

- **Code Style**: Use ESLint for TypeScript, Black for Python
- **Type Safety**: Maintain strict TypeScript checks
- **Documentation**: Update README and inline comments for significant changes
- **Testing**: Add test cases for new backend endpoints

---

## Citation

If you use BrainCast AI in academic research, please cite:

```bibtex
@software{braincast_ai_2025,
  title = {BrainCast AI: Multimodal Longitudinal Brain Imaging Synthesis},
  author = {HealthEp},
  year = {2025},
  url = {https://github.com/laoluog/BrainCast-AI}
}
```

---

## License

This project is licensed for educational and research purposes. Commercial use requires explicit permission. See license documentation for details.

---

## Acknowledgments

- **Black Forest Labs** for Flux Kontext Pro API access
- **Google AI** for Gemini and Veo 3.1 APIs
- **Supabase** for backend infrastructure
- **Vercel** for Next.js framework and tooling

---

## Technical Support

For questions, issues, or collaboration inquiries:

- **Issues**: Open a GitHub issue
- **Documentation**: See `backend/REPROMPT_FLOW.md` and `backend/QUICK_START.md`
- **API Reference**: See `backend/api_spec.yaml`

---

**Built with ❤️ for advancing clinical AI research**

