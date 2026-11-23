# SADAT – Student Career Intelligence & Skills Growth Portal
## 10. UI/UX Design System Specification

### 1. Visual Direction: Minimalistic Retro Grid + Calm Sea Palette
The platform design embodies an editorial academic aesthetic, combining clean technical grid patterns with restrained oceanic hues, clean sans-serif typography, and structured geometric compositions.

Generic AI tropes (purple neon gradients, floating glowing orbs, futuristic robot illustrations, excessive blur effects) are strictly avoided.

---

### 2. Design Tokens

#### 2.1 Color Palette
```css
:root {
  /* Primary & Brand */
  --color-navy-deep: #15354B;      /* Headers, Primary Buttons, Active Tabs */
  --color-ocean-blue: #286581;     /* Primary Accents, Brand Badges, Active Links */
  --color-sea-blue: #4E8298;       /* Subheadings, Secondary Actions, Progress Bars */
  
  /* Accents & Tints */
  --color-muted-teal: #76A9A6;     /* Indicators, Chart Series 2, Badges */
  --color-seafoam: #C5DFD9;        /* Soft Highlights, Pill Backgrounds, Light Borders */
  --color-ice-blue: #EAF3F5;       /* Card Backgrounds, Subnav, Subtle Panels */
  --color-off-white: #F8FAF9;      /* Global Background Canvas */
  
  /* Neutrals & Typography */
  --color-text-main: #13222B;      /* High-contrast readable body text */
  --color-slate: #637782;          /* Secondary meta text, labels, subtitles */
  --color-border: #D8E4E8;         /* Structural borders, grid accents */
  
  /* Status Colors */
  --color-status-strong: #1B7A58;  /* Strong Skill / High Compatibility / Free Cost */
  --color-status-developing: #D97706; /* Developing Skill / Partial Evidence / Paid Exam */
  --color-status-missing: #B91C1C; /* Missing Skill / Ineligible Experience */
}
```

#### 2.2 Retro Grid Pattern
A subtle, non-intrusive geometric grid applied to headers, metric cards, and dashboard sections:
```css
.bg-retro-grid {
  background-image: 
    linear-gradient(to right, rgba(216, 228, 232, 0.45) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(216, 228, 232, 0.45) 1px, transparent 1px);
  background-size: 24px 24px;
}
```

#### 2.3 Typography
- **English UI Font**: `Plus Jakarta Sans`, `Inter`, sans-serif.
- **Arabic UI Font**: `IBM Plex Sans Arabic`, `Noto Sans Arabic`, sans-serif.
- **Monospace Font**: `JetBrains Mono`, `Fira Code`, monospace (for course codes, test scores, formulas).

---

### 3. Component Design Guidelines

#### 3.1 Card-First Hierarchy
- The UI is built around modular cards with $1\text{px}$ solid borders (`var(--color-border)`), subtle drop shadows (`0 2px 8px rgba(21, 53, 75, 0.05)`), and 8px to 12px border radius.
- Cards host clear visual badges:
  - **Work Mode**: Remote (Indigo/Ice), Hybrid (Teal/Seafoam), On-site (Slate/Gray).
  - **Fit Percentage**: Prominently displayed circular or bold badge in top-right.
  - **Skill Chips**: Strong (Green-tinted), Partial (Amber-tinted), Missing (Red-tinted).

#### 3.2 Job Card Layout
```text
+-------------------------------------------------------------+
| [Rank #1] Junior Machine Learning Engineer      [ 76.6% Fit ]|
| ITWorx • Nasr City, Cairo • Remote • 0-1 Yrs Exp            |
+-------------------------------------------------------------+
| Strong Skills: [Python] [Machine Learning] [Deep Learning]  |
| Developing:    [TensorFlow] [PyTorch] [Git]                 |
+-------------------------------------------------------------+
| Growth Plan: Revisit Operating Systems (+11.1% Fit Gain)   |
| [View Job Details]                      [Apply on LinkedIn] |
+-------------------------------------------------------------+
```

#### 3.3 RTL Mirroring Architecture
- Every flex container using `justify-start`, `space-x-4`, `pl-4` must use directional logical properties (`ms-4`, `ps-4`, `pe-4`) or automated Tailwind RTL plugins.
- Icons indicating direction (e.g. `fa-chevron-right`, `fa-arrow-right`) must flip dynamically when `dir="rtl"`.
- Typography alignment flips from `text-left` to `text-right`.
