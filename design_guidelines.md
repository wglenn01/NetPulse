{
  "design_system_name": "NetPulse // CRT-HUD Green Console (Medium CRT)",
  "brand_attributes": [
    "instrument-grade readability (wallboard-first)",
    "futuristic console / sci-fi HUD chrome",
    "terminal-green primary actions",
    "cyan secondary telemetry",
    "calm, precise, operational (no playful gradients)"
  ],
  "visual_personality": {
    "style_fusion": [
      "CRT terminal (scanlines + phosphor glow, medium intensity)",
      "sci-fi HUD (corner brackets, technical grid, reticle dividers)",
      "NOC wallboard (large type, high contrast, low visual noise)"
    ],
    "do_not": [
      "No purple accents (explicitly prohibited for AI/console feel here)",
      "No heavy flicker/distortion; no readability loss",
      "No gradients on content surfaces; gradients only as subtle background accents under 20% viewport"
    ]
  },
  "typography": {
    "fonts": {
      "ui_sans": {
        "current": "IBM Plex Sans",
        "keep": true,
        "usage": "Body copy, tables, dialogs, forms. Keep for legibility at distance."
      },
      "mono": {
        "current": "JetBrains Mono",
        "keep": true,
        "usage": "Metrics, IPs, interface names, port labels, timestamps, HUD chrome headings.",
        "guidance": "Increase mono prominence: use mono for section headers, KPI labels, map overlays, and TV mode tickers."
      }
    },
    "scale_tailwind": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl",
      "h2": "text-base md:text-lg",
      "body": "text-sm md:text-base",
      "small": "text-xs text-muted-foreground",
      "kpi_number": "text-2xl md:text-3xl lg:text-4xl tabular font-semibold",
      "hud_label": "font-mono uppercase tracking-[0.18em] text-[11px] md:text-xs"
    },
    "text_rules": [
      "Use tabular numbers for all metrics: add class `tabular` (already defined) + `font-mono` for key counters.",
      "Prefer uppercase + wide tracking for HUD labels; keep sentence case for descriptions.",
      "Wallboard: minimum 14px equivalent for any persistent text in /tv mode."
    ]
  },
  "color_tokens_hsl": {
    "note": "REUSE existing token structure in /app/frontend/src/index.css; swap VALUES only + add a few new tokens below.",
    "base": {
      "--background": "210 30% 4%",
      "--foreground": "150 18% 92%",
      "--card": "210 26% 6%",
      "--card-foreground": "150 18% 92%",
      "--popover": "210 26% 6%",
      "--popover-foreground": "150 18% 92%",
      "--secondary": "210 18% 10%",
      "--secondary-foreground": "150 18% 92%",
      "--muted": "210 18% 10%",
      "--muted-foreground": "150 10% 68%",
      "--border": "150 18% 18%",
      "--input": "150 18% 18%",
      "--radius": "0.75rem"
    },
    "accents": {
      "--primary": "142 92% 52%",
      "--primary-foreground": "210 30% 4%",
      "--accent": "188 92% 52%",
      "--accent-foreground": "210 30% 4%",
      "--ring": "142 92% 52%",
      "--destructive": "0 84% 58%",
      "--destructive-foreground": "210 30% 4%"
    },
    "charts": {
      "--chart-1": "142 92% 52%",
      "--chart-2": "188 92% 52%",
      "--chart-3": "38 92% 56%",
      "--chart-4": "205 90% 60%",
      "--chart-5": "0 84% 58%"
    },
    "status": {
      "--status-ok": "142 92% 52%",
      "--status-warn": "38 92% 56%",
      "--status-crit": "0 84% 58%",
      "--status-down": "210 6% 52%",
      "--status-info": "188 92% 52%"
    },
    "traffic": {
      "--traffic-active": "188 92% 52%",
      "--traffic-idle": "210 10% 38%"
    },
    "vendor_accents": {
      "keep_existing_hues": true,
      "adjustment_guidance": "Keep vendor hues but slightly desaturate to avoid fighting primary green. Use vendor colors only as small badges/labels (<= 24px height) and never as large backgrounds.",
      "--vendor-mikrotik": "18 82% 56%",
      "--vendor-ubiquiti": "205 88% 58%",
      "--vendor-cambium": "142 70% 42%",
      "--vendor-mimosa": "38 88% 54%"
    },
    "new_tokens_to_add": {
      "--hud-grid": "150 30% 10%",
      "--hud-glow": "142 92% 52%",
      "--hud-glow-cyan": "188 92% 52%",
      "--tv-safe": "150 18% 94%",
      "--panel-tint": "142 92% 52%",
      "--panel-tint-2": "188 92% 52%"
    }
  },
  "global_css_recipes": {
    "crt_overlay_medium": {
      "where": "Apply to body via pseudo-elements or a top-level `.crt-shell` wrapper around the app. Must respect prefers-reduced-motion.",
      "css": "/* Add to index.css (new) */\n.crt-shell{position:relative;min-height:100%;}\n.crt-shell::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:50;\n  background:\n    /* scanlines */\n    repeating-linear-gradient(\n      to bottom,\n      rgba(0,0,0,0.18) 0px,\n      rgba(0,0,0,0.18) 1px,\n      rgba(0,0,0,0) 3px,\n      rgba(0,0,0,0) 4px\n    ),\n    /* subtle technical grid */\n    linear-gradient(to right, rgba(120,255,170,0.035) 1px, transparent 1px),\n    linear-gradient(to bottom, rgba(120,255,170,0.03) 1px, transparent 1px),\n    /* vignette */\n    radial-gradient(1200px circle at 50% 20%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%);\n  background-size: auto, 24px 24px, 24px 24px, auto;\n  mix-blend-mode: normal;\n  opacity: 0.55;\n}\n.crt-shell::after{content:'';position:fixed;inset:0;pointer-events:none;z-index:51;\n  background: radial-gradient(900px circle at 18% 8%, rgba(120,255,170,0.06), transparent 55%);\n  opacity: 0.9;\n}\n@media (prefers-reduced-motion: reduce){\n  .crt-shell::before{opacity:0.35;}\n}\n",
      "notes": [
        "Scanlines are subtle (1px dark line every 4px).",
        "Grid is faint and only visible on large screens; keep opacity low.",
        "No flicker animation by default; if you add any, gate behind prefers-reduced-motion and keep amplitude tiny."
      ]
    },
    "terminal_glow_treatment": {
      "usage": "Primary buttons, active nav item, focused inputs, status dots, active map edges.",
      "tailwind_patterns": [
        "shadow-[0_0_0_1px_hsl(var(--primary)/0.35),0_0_18px_hsl(var(--primary)/0.18)]",
        "drop-shadow-[0_0_10px_hsl(var(--primary)/0.25)]"
      ],
      "css_optional": ".glow-primary{box-shadow:0 0 0 1px hsl(var(--primary)/0.35),0 0 18px hsl(var(--primary)/0.18);}"
    },
    "selection_and_cursor": {
      "css": "::selection{background:hsl(var(--primary)/0.25);color:hsl(var(--foreground));}\n.cursor-block{position:relative;}\n.cursor-block::after{content:'';display:inline-block;width:0.6ch;height:1em;margin-left:0.2ch;background:hsl(var(--primary)/0.75);vertical-align:-0.15em;animation:blink 1.1s steps(1,end) infinite;}\n@keyframes blink{50%{opacity:0;}}\n@media (prefers-reduced-motion: reduce){.cursor-block::after{animation:none;opacity:0.65;}}"
    }
  },
  "layout_and_grid": {
    "app_shell": {
      "pattern": "Left rail navigation + main content + right device drawer overlay",
      "max_width": "Full-bleed; do not center the entire app",
      "spacing": "Use 2–3x more spacing than default; prefer `p-4 md:p-6 lg:p-8` and `gap-4 md:gap-6`",
      "wallboard": "In /tv mode, increase padding and font sizes; reduce secondary chrome."
    },
    "dashboard": {
      "kpi_row": "Bento KPI tiles (4–6 across on large screens, 2 across on tablet, 1 on mobile)",
      "grid": "react-grid-layout widgets: use clear widget headers with mono HUD labels + right-aligned actions"
    }
  },
  "components": {
    "component_path": {
      "button": "/app/frontend/src/components/ui/button.jsx",
      "card": "/app/frontend/src/components/ui/card.jsx",
      "badge": "/app/frontend/src/components/ui/badge.jsx",
      "tabs": "/app/frontend/src/components/ui/tabs.jsx",
      "table": "/app/frontend/src/components/ui/table.jsx",
      "dialog": "/app/frontend/src/components/ui/dialog.jsx",
      "drawer": "/app/frontend/src/components/ui/drawer.jsx",
      "sheet": "/app/frontend/src/components/ui/sheet.jsx",
      "scroll_area": "/app/frontend/src/components/ui/scroll-area.jsx",
      "select": "/app/frontend/src/components/ui/select.jsx",
      "switch": "/app/frontend/src/components/ui/switch.jsx",
      "slider": "/app/frontend/src/components/ui/slider.jsx",
      "calendar": "/app/frontend/src/components/ui/calendar.jsx",
      "sonner_toasts": "/app/frontend/src/components/ui/sonner.jsx"
    },
    "button_variants": {
      "primary": {
        "look": "Terminal-green fill with subtle glow; readable label",
        "tailwind": "bg-primary text-primary-foreground hover:bg-primary/90 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-0 shadow-[0_0_0_1px_hsl(var(--primary)/0.35),0_0_18px_hsl(var(--primary)/0.18)]",
        "data_testid_examples": [
          "data-testid=\"alerts-acknowledge-button\"",
          "data-testid=\"settings-save-button\""
        ]
      },
      "secondary": {
        "look": "Dark panel button with cyan outline on hover",
        "tailwind": "bg-secondary text-secondary-foreground border border-border hover:border-[hsl(var(--accent))] hover:shadow-[0_0_0_1px_hsl(var(--accent)/0.25),0_0_14px_hsl(var(--accent)/0.12)]"
      },
      "ghost": {
        "look": "HUD chrome action (icon buttons)",
        "tailwind": "bg-transparent hover:bg-white/5 text-foreground"
      }
    },
    "cards_and_panels": {
      "panel_style": "Use Card with a faint green tint + corner brackets (pseudo-elements) for key panels.",
      "tailwind_base": "bg-card/80 border border-border/80 backdrop-blur-[2px]",
      "corner_brackets_css": ".hud-panel{position:relative;}\n.hud-panel::before,.hud-panel::after{content:'';position:absolute;inset:10px;pointer-events:none;}\n.hud-panel::before{border-left:1px solid hsl(var(--primary)/0.35);border-top:1px solid hsl(var(--primary)/0.35);width:18px;height:18px;left:10px;top:10px;}\n.hud-panel::after{border-right:1px solid hsl(var(--accent)/0.28);border-bottom:1px solid hsl(var(--accent)/0.28);width:18px;height:18px;right:10px;bottom:10px;}"
    },
    "badges": {
      "status_badges": {
        "ok": "bg-[hsl(var(--status-ok)/0.12)] text-[hsl(var(--status-ok))] border border-[hsl(var(--status-ok)/0.25)]",
        "warn": "bg-[hsl(var(--status-warn)/0.12)] text-[hsl(var(--status-warn))] border border-[hsl(var(--status-warn)/0.25)]",
        "crit": "bg-[hsl(var(--status-crit)/0.12)] text-[hsl(var(--status-crit))] border border-[hsl(var(--status-crit)/0.25)]",
        "down": "bg-[hsl(var(--status-down)/0.10)] text-[hsl(var(--status-down))] border border-[hsl(var(--status-down)/0.22)]"
      },
      "vendor_badges": "Use vendor tokens only for small badges: `text-[hsl(var(--vendor-ubiquiti))] border-[hsl(var(--vendor-ubiquiti)/0.35)] bg-[hsl(var(--vendor-ubiquiti)/0.10)]`"
    },
    "tables": {
      "devices_table": {
        "rules": [
          "Sticky header with darker surface for wallboard scanning",
          "Use mono for IP/MAC/ifName columns",
          "Row hover: subtle green tint only"
        ],
        "tailwind": {
          "header": "bg-secondary/70 backdrop-blur border-b border-border",
          "row_hover": "hover:bg-[hsl(var(--primary)/0.06)]"
        }
      }
    },
    "forms": {
      "inputs": {
        "look": "Console input: dark surface, green focus ring + faint glow",
        "tailwind": "bg-secondary/60 border-border focus-visible:ring-2 focus-visible:ring-ring focus-visible:shadow-[0_0_0_1px_hsl(var(--primary)/0.25),0_0_16px_hsl(var(--primary)/0.12)]",
        "data_testid_examples": [
          "data-testid=\"settings-snmp-community-input\"",
          "data-testid=\"settings-discord-webhook-input\""
        ]
      },
      "switches_sliders": "Use shadcn Switch/Slider; active track should read as primary green; ensure focus-visible ring is present."
    },
    "toasts_and_alerts": {
      "toasts": "Use Sonner. Toast surfaces should be dark with green/cyan border accents; critical uses status-crit.",
      "alerts_feed": "Use Alert component for inline; for feed items use Card rows with left status bar (2px) colored by status token."
    }
  },
  "topology_map_xyflow": {
    "goal": "Futuristic schematic map: deep dark pane, green nodes, cyan animated traffic edges, readable labels.",
    "css_overrides_in_index_css": {
      "pane": "Update `.react-flow__pane` background to match new base: use subtle green/cyan radials but keep them extremely faint.",
      "edges": [
        "Keep existing `.np-edge` classes; swap glow colors to match new tokens.",
        "Active traffic: cyan dashed with drop-shadow; idle: muted gray-green.",
        "Warn/Crit: keep amber/red but reduce saturation slightly via opacity; do not glow excessively."
      ],
      "recommended_updates": "Change current pane base (#070B14) to near-black greenish: #050807 equivalent via tokens; keep radials <= 6% opacity."
    },
    "node_style": {
      "node_card": "bg-card/70 border border-[hsl(var(--primary)/0.22)] shadow-[0_0_0_1px_hsl(var(--primary)/0.18)]",
      "node_header": "font-mono uppercase tracking-[0.16em] text-xs text-[hsl(var(--primary))]",
      "status_dot": "w-2.5 h-2.5 rounded-full bg-[hsl(var(--status-ok))] shadow-[0_0_10px_hsl(var(--status-ok)/0.35)]",
      "port_labels": "font-mono text-[11px] text-[hsl(var(--foreground)/0.85)]"
    },
    "animated_dashed_lines": {
      "keep_existing": "Existing `@keyframes edgeDash` + `.np-edge.edge--active` is correct; just align colors to `--traffic-active` and reduce glow blur for wallboard clarity.",
      "dash_speed_tokens": "Use CSS var `--edge-dash-speed` per edge state (active 1.6s, warn 1.4s, crit 0.9s).",
      "reduced_motion": "Already present; keep it."
    },
    "map_interactions": [
      "Hover edge: increase stroke-width by +0.6 and show label pill (port/speed) with mono font.",
      "Drag-to-connect: show cyan preview line; on valid target, glow green.",
      "Selection: node outline becomes primary green with stronger glow; keep outline thickness 2px for visibility."
    ]
  },
  "tv_mode_route_tv": {
    "principles": [
      "TV-safe typography: increase contrast and size; reduce fine borders",
      "Auto-rotating panels: use a single consistent transition (fade + slight translateY)",
      "Persistent alert ticker at bottom with status color chips",
      "No dense tables; prefer top-N lists and big KPIs"
    ],
    "layout": {
      "grid": "12-col on desktop TV; typical: left 8 cols (map or KPIs), right 4 cols (alerts + top talkers)",
      "ticker": "fixed bottom bar height 56–64px; mono labels; scrolling marquee only if reduced-motion allows"
    },
    "motion": {
      "framer": "Use framer-motion for panel transitions; keep duration 0.35–0.5s; easeOut.",
      "reduced_motion": "If prefers-reduced-motion, disable marquee and use static paging."
    },
    "data_testids": [
      "tv-mode-root",
      "tv-alert-ticker",
      "tv-panel-rotation-indicator"
    ]
  },
  "micro_interactions": {
    "rules": [
      "No `transition: all` anywhere.",
      "Buttons: hover = slight brightness + glow; active = scale(0.98) with 120ms.",
      "Cards: hover = border tint + subtle lift (translateY -1px) only on desktop.",
      "Nav: active item has left 2px green bar + glow; hover shows cyan underline."
    ],
    "tailwind_snippets": {
      "button": "transition-colors duration-150 active:scale-[0.98]",
      "card_hover": "transition-colors duration-150 hover:border-[hsl(var(--primary)/0.35)]",
      "nav_active": "relative before:absolute before:left-0 before:top-2 before:bottom-2 before:w-[2px] before:bg-[hsl(var(--primary))] before:shadow-[0_0_12px_hsl(var(--primary)/0.35)]"
    }
  },
  "accessibility": {
    "contrast": [
      "Foreground text must remain readable on near-black; avoid low-opacity green for body text.",
      "Use green/cyan primarily for accents, borders, and key numbers; body text stays near-off-white."
    ],
    "focus": "All interactive elements must have visible focus ring: `focus-visible:ring-2 focus-visible:ring-ring`.",
    "reduced_motion": "Respect prefers-reduced-motion: disable edge dash animation (already), marquee tickers, and cursor blink if needed.",
    "hit_targets": "Minimum 40px height for primary controls in wallboard/desk mode."
  },
  "images": {
    "image_urls": [
      {
        "category": "background_texture",
        "description": "No external hero images needed; use CSS overlays (scanlines/grid/noise).",
        "urls": []
      }
    ]
  },
  "libraries_and_integrations": {
    "already_in_stack": [
      "@xyflow/react (topology)",
      "react-grid-layout (custom dashboards)",
      "recharts (throughput charts)",
      "framer-motion (panel transitions)",
      "lucide-react (icons)",
      "sonner (toasts)"
    ],
    "optional_additions": [
      {
        "name": "css-noise",
        "why": "If you want a subtle noise texture without images.",
        "how": "Prefer pure CSS gradients; avoid heavy noise that harms readability."
      }
    ]
  },
  "data_testid_policy": {
    "rule": "All interactive and key informational elements MUST include data-testid (kebab-case, role-based).",
    "examples": [
      "data-testid=\"topology-map-canvas\"",
      "data-testid=\"device-detail-drawer\"",
      "data-testid=\"alerts-feed-list\"",
      "data-testid=\"devices-table\"",
      "data-testid=\"dashboard-add-widget-button\"",
      "data-testid=\"settings-vendor-api-save-button\""
    ]
  },
  "instructions_to_main_agent": [
    "Overwrite token VALUES in /app/frontend/src/index.css :root using the HSL values above; keep token names unchanged.",
    "Add new tokens under :root: --hud-grid, --hud-glow, --hud-glow-cyan, --tv-safe, --panel-tint, --panel-tint-2.",
    "Wrap the app root with a `.crt-shell` div (or apply class to #root) to enable scanline/grid/vignette overlay; ensure overlay is pointer-events:none.",
    "Update ReactFlow pane background and edge glow colors to match green/cyan theme; keep existing `.np-edge` animation but reduce glow intensity slightly for wallboard clarity.",
    "Promote JetBrains Mono for HUD labels and KPI chrome (uppercase + tracking).",
    "Ensure /tv mode uses larger type, fewer borders, and a persistent alert ticker; respect prefers-reduced-motion.",
    "Do not introduce new gradients beyond subtle radials; keep gradients under 20% viewport and never on text-heavy surfaces.",
    "Ensure every button/input/link/menu item and key metric text includes a stable data-testid attribute."
  ],
  "general_ui_ux_design_guidelines_appendix": "<General UI UX Design Guidelines>  \n    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.\n</General UI UX Design Guidelines>"
}
