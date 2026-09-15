# DocGuard AI Frontend Implementation Plan

## 1. Component Structure

```
frontend/
  src/
    components/
      Navigation.jsx        # Liquid-metal pill navigation + mobile burger menu
      Hero.jsx              # Bottom-centered hero with video treatment
      DemoWorkflow.jsx      # Interactive demo state visualization (overlay)
      CTAButton.jsx         # Liquid-glass primary/secondary buttons
      StatItem.jsx          # Bottom stats display
      DemoIndicator.jsx     # Subtle DEMO MODE indicator
    data/
      demoData.js           # Deterministic demo workflow data
    utils/
      animationFallback.js  # Small IIFE — entrance-animation safety net
    styles/
      global.css            # Fonts, tokens, reset, grain, nav pills, CTAs, demo indicator
      hero.css              # Hero, badge, H1, lede, stats, entrance keyframes
      demo.css              # Demo workflow overlay, status pill, steps, connectors
      responsive.css        # Breakpoints, viewport locking, mobile behavior
    App.jsx                 # Main application component
    main.jsx                # React entry point
```

## 2. CSS Architecture

### CSS Variables
```css
:root {
  /* Color Palette */
  --color-bg-primary: #000000;
  --color-bg-secondary: #0a0a0a;
  --color-text-primary: #ffffff;
  --color-text-secondary: #a0a0a0;
  --color-accent: #3b82f6;
  --color-accent-glow: rgba(59, 130, 246, 0.4);
  
  /* Glass Effect */
  --glass-bg: rgba(255, 255, 255, 0.05);
  --glass-border: rgba(255, 255, 255, 0.1);
  --glass-blur: 20px;
  
  /* Liquid Metal */
  --metal-gradient: linear-gradient(135deg, #1a1a2e 0%, #0f0f23 100%);
  --metal-shine: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 100%);
  
  /* Typography */
  --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-serif: 'Instrument Serif', Georgia, serif;
  
  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  --spacing-2xl: 3rem;
  
  /* Animation Timing */
  --transition-fast: 150ms;
  --transition-normal: 300ms;
  --transition-slow: 500ms;
}
```

### Keyframe Animations
```css
/* Fade in up for entrance animations */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Liquid metal shimmer effect */
@keyframes liquidShimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

/* Pulse for CTA buttons */
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 var(--color-accent-glow); }
  50% { box-shadow: 0 0 20px 5px var(--color-accent-glow); }
}

/* Grain effect overlay */
@keyframes grain {
  0%, 100% { transform: translate(0, 0); }
  10% { transform: translate(-5%, -10%); }
  20% { transform: translate(-15%, 5%); }
  30% { transform: translate(7%, -25%); }
  40% { transform: translate(-5%, 25%); }
  50% { transform: translate(-15%, 10%); }
  60% { transform: translate(15%, 0%); }
  70% { transform: translate(0%, 15%); }
  80% { transform: translate(3%, 35%); }
  90% { transform: translate(-10%, 10%); }
}
```

## 3. Animation Architecture

### Entrance Animations
- Use CSS keyframes with `animation-fill-mode: both`
- Stagger animations using `animation-delay`
- Respect `prefers-reduced-motion` media query
- Fallback: No animations for reduced motion preference

### Implementation Pattern
```jsx
// Component with entrance animation
const Hero = () => {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  
  return (
    <div className={`hero ${prefersReducedMotion ? '' : 'animate-fade-in-up'}`}
         style={{ animationDelay: '0.2s' }}>
      {/* Content */}
    </div>
  );
};
```

### Reduced Motion Fallback
```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

## 4. Responsive Behavior

### Breakpoints
```css
/* Mobile first approach */
@media (min-width: 640px) { /* sm */ }
@media (min-width: 768px) { /* md */ }
@media (min-width: 1024px) { /* lg */ }
@media (min-width: 1280px) { /* xl */ }
```

### Desktop (1024px+)
- Locked to single viewport, no scrolling
- Full navigation pills
- Hero positioned bottom-center
- Full workflow visualization

### Tablet (768px - 1023px)
- Adapted navigation
- Condensed workflow steps
- Still single viewport

### Mobile (< 768px)
- Natural vertical scrolling allowed
- Burger menu navigation
- Stacked workflow visualization
- Touch-friendly interactions

## 5. DEMO MODE Behavior

### Demo Indicator
- Subtle "DEMO MODE" badge in top-right corner
- Semi-transparent with low opacity
- Does not obstruct main content

### Demo Data Structure
```javascript
export const demoWorkflow = [
  {
    id: 1,
    step: 'Git Repository',
    icon: 'git',
    status: 'completed',
    details: 'Scanning repository...'
  },
  // ... more steps
];
```

### Interaction
- "Analyze Repository" button triggers demo workflow
- Steps animate sequentially
- Each step shows completion status
- Final step displays "Documentation Synchronized"

### Backend Connection Placeholder
```javascript
// Future API integration point
export const analyzeRepository = async (repoUrl) => {
  // In demo mode, return deterministic data
  // In production, call FastAPI backend
  return demoWorkflow;
};
```

## 6. Backend Integration (Future)

### API Endpoints (FastAPI)
```python
# Backend structure (not implemented yet)
@router.post("/api/v1/analyze")
async def analyze_repository(repo_url: str):
    # 1. Clone repository
    # 2. Detect API routes
    # 3. Compare OpenAPI specs
    # 4. Generate documentation
    # 5. Validate and return
    pass

@router.get("/api/v1/status/{task_id}")
async def get_analysis_status(task_id: str):
    pass
```

### Frontend Integration Points
```javascript
// src/services/api.js (not implemented yet)
export const DocGuardAPI = {
  analyze: async (repoUrl) => {
    // POST /api/v1/analyze
  },
  getStatus: async (taskId) => {
    // GET /api/v1/status/{taskId}
  }
};
```

## 7. Technical Requirements Checklist

### Must Have
- [x] React + Vite setup
- [x] CSS-only animations (no Framer Motion)
- [x] Inline SVG icons
- [x] Liquid-metal navigation pills
- [x] Liquid-glass buttons
- [x] Black background with grain effect
- [x] Hero-video treatment (CSS gradient simulation)
- [x] Responsive breakpoints
- [x] Mobile burger menu
- [x] Reduced motion accessibility
- [x] No white flash on load
- [x] Single viewport desktop (no scroll)
- [x] Mobile vertical scrolling
- [x] @font-face definitions
- [x] DEMO MODE indicator
- [x] Deterministic demo data

### Must NOT Have
- [x] No Three.js, WebGL, or Lottie
- [x] No external image/video URLs
- [x] No extra sections/cards/forms/footer
- [x] No placeholder content
- [x] No unnecessary dependencies
