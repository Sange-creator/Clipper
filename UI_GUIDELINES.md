# AI Video Clipper Pro — UI Design System & Component Guidelines

This document defines the strict UI and design standards for the AI Video Clipper platform. All developers and AI coding assistants must adhere to these guidelines to ensure global consistency, responsive integrity, and a premium product experience.

---

## 1. Core Design Philosophy

* **Modern, Sleek, Professional**: Inspired by premium creator tools (Linear, Raycast, Vercel, Runway).
* **shadcn/ui First**: Always leverage standard shadcn/ui primitives (`Button`, `Card`, `Badge`, `Switch`, `Slider`, `Tabs`, `Dialog`, `Input`).
* **Zero-Emoji Policy in UI Controls**:
  * **STRICT RULE**: Never use emojis (`⚡️`, `📄`, `🗿`, `🎞️`, `🏛️`, `🔮`, `🤫`, `🔥`, `🤯`, `💀`, etc.) inside buttons, tabs, preset cards, labels, or badges.
  * Use crisp SVG icons from `lucide-react` instead (e.g. `Zap`, `FileText`, `Sparkles`, `Clock`, `BookOpen`, `MessageSquare`, `Type`, `Flame`, `Smile`, `Feather`).
  * Emojis should ONLY exist if a user explicitly enters them in an input field for video captions.

---

## 2. Color Palette & Dark Theme

* **Background Base**: `#07090E` (Deep space obsidian)
* **Surface Panels**: `zinc-950/60` with `backdrop-blur-xl` and `border border-white/10`
* **Card Hover**: `hover:bg-white/[0.04]` and `hover:border-white/20`
* **Brand Primary Accent**: `violet-500` (`#8B5CF6`) and `indigo-500` (`#6366F1`)
* **Secondary Accents**:
  * Amber / Creator: `amber-500` (`#F59E0B`)
  * Cyan / Delogo & Framing: `cyan-400` (`#22D3EE`)
  * Emerald / Enhancement: `emerald-400` (`#34D399`)
  * Rose / Rejection & Destructive: `rose-500` (`#F43F5E`)
* **Text Hierarchy**:
  * Primary: `text-white` (High contrast, clean sans-serif)
  * Secondary: `text-zinc-300` (Labels, active subtext)
  * Muted: `text-zinc-400` and `text-zinc-500` (Descriptions, helper text, timestamps)

---

## 3. Responsive Layout & Anti-Overcrowding Rules

### The Half-Width Rule
* When a component is placed inside a multi-column container (e.g., `grid grid-cols-1 md:grid-cols-2`):
  * **NEVER** use `grid-cols-4` or `grid-cols-3` for rich cards containing a title, badge, and description.
  * In half-width containers, rich cards must use **`grid-cols-1 sm:grid-cols-2`** with adequate gap (`gap-2.5` to `gap-3`).
  * For compact icon-only or simple text buttons, max **`grid-cols-3`**.

### Badge & Label Separation Rule
* **NEVER** float font badges with `absolute top-1.5 right-1.5` over text in narrow cards where text wrapping causes collisions.
* Always structure cards vertically:
  1. Header row: Icon + Title (`truncate` or sensible line break)
  2. Sub-row / Tag: Dedicated font badge (`text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-zinc-400`)
  3. Description row: Clean muted text (`text-[10px] text-zinc-500 line-clamp-1`)

---

## 4. Typography & Font Specifications

| Preset ID | Display Name | Font Family | Lucide Icon | Visual Characteristics |
| :--- | :--- | :--- | :--- | :--- |
| `tiktok_viral` | TikTok Viral | Arial Black | `Zap` | High-contrast yellow pop with dark outline |
| `meme` | Classic Meme | Impact | `MessageSquare` | Heavy all-caps white text with black stroke |
| `white_background` | White Card Box | Arial Black | `FileText` | Black text on crisp, solid white rectangular card |
| `nostalgic` | Nostalgic Vintage | Courier New | `Clock` | Monospace typewriter in warm retro amber |
| `old_history` | Old History | Georgia Serif | `BookOpen` | Antique parchment chronicle serif |
| `hormozi_bold` | Hormozi Bold | Impact | `Flame` | Neon green keyword highlights |
| `bold_yellow` | Bold Yellow | Arial Black | `Sun` | Active word pop with vibrant yellow fill |
| `clean_white` | Clean White | Arial | `Check` | Minimalist white karaoke subtitles |
| `podcast_box` | Podcast Box | Trebuchet MS | `Mic` | Dark translucent lower-third banner |
| `cinematic` | Cinematic Serif | Georgia | `Film` | Elegant italic letterbox typography |
| `playful_comic` | Playful Comic | Comic Sans MS | `Smile` | Rounded fun casual subtitles |
| `editorial_serif` | Editorial Luxury | Times New Roman | `Feather` | High-prestige luxury editorial font |
| `cyber_neon` | Cyber Neon | Arial Black | `Sparkles` | Vibrant cyan with magenta outer glow |

---

## 5. Hook Header Presets (Zero Emojis)

| Style ID | Label | Lucide Icon | Style Description |
| :--- | :--- | :--- | :--- |
| `viral_creator` | Viral Creator | `Zap` | Sans Bold in bright creator yellow |
| `white_box` | White Card Box | `FileText` | Bold black text on solid opaque white card |
| `meme` | Classic Meme | `MessageSquare` | Impact all-caps with heavy black stroke |
| `nostalgic` | Nostalgic Typewriter | `Clock` | Courier monospace typewriter in warm amber |
| `old_history` | Old History Serif | `BookOpen` | Georgia antique serif with parchment tones |
| `neon_cyber` | Cyber Neon | `Sparkles` | Neon cyan glow with magenta outline |

---

## 6. Component Checklist for Code Reviews

Before committing any UI changes:
- [ ] No emojis in UI buttons, tabs, preset names, or preview badges.
- [ ] No text or badge overlapping at standard viewports (375px mobile, 768px tablet, 1280px desktop).
- [ ] Uses shadcn/ui components (`Badge`, `Card`, `Button`, `Switch`, etc.) where applicable.
- [ ] Responsive grid columns adapt properly (`grid-cols-1 sm:grid-cols-2`).
- [ ] Verified build succeeds with `npm run build` with zero lint/type errors.
