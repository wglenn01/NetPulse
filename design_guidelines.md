{
  "design_system_name": "Nightwatch NOC (Dark Ops)",
  "brand_attributes": [
    "sleek",
    "instrument-grade",
    "low-eye-strain",
    "high-contrast",
    "real-time",
    "operator-first",
    "wallboard-readable"
  ],
  "visual_personality": {
    "style_fusion": [
      "Swiss grid discipline (dense, aligned, predictable)",
      "instrument panel / avionics UI (status lights, ticks, subtle scanlines)",
      "glass-lite panels (NOT transparent; use tonal surfaces + inner borders)",
      "bento dashboard tiles",
      "map/topology as the hero interaction surface"
    ],
    "do_not": [
      "No purple gradients or saturated neon gradients.",
      "No large gradients covering reading areas.",
      "No centered app container layouts.",
      "No transparent cards behind dark text (true dark surfaces only)."
    ]
  },
  "typography": {
    "google_fonts": {
      "sans": {
        "family": "IBM Plex Sans",
        "weights": [400, 500, 600, 700],
        "usage": "UI labels, navigation, headings"
      },
      "mono": {
        "family": "JetBrains Mono",
        "weights": [400, 500, 600],
        "usage": "IPs, interface names, metrics, timestamps"
      }
    },
    "tailwind_font_tokens": {
      "font-sans": "'IBM Plex Sans', ui-sans-serif, system-ui",
      "font-mono": "'JetBrains Mono', ui-monospace, SFMono-Regular"
    },
    "text_size_hierarchy": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl",
      "h2": "text-base md:text-lg",
      "body": "text-sm md:text-base",
      "small": "text-xs"
    },
    "numeric_readability": {
      "rules": [
        "Use tabular numerals for metrics: add `font-variant-numeric: tabular-nums;` on metric containers.",
        "Use mono for IPs/MACs/ifNames to reduce misreads at distance.",
        "Avoid rapid font-weight changes on live-updating numbers (prevents flicker)."
      ]
    }
  },
  "color_system": {
    "notes": [
      "FULL DARK THEME required: use deep blue-black base (not pure black) to reduce eye strain.",
      "Use semantic status colors consistently across tiles, map nodes, tables, and alerts.",
      "Traffic animation accent must be distinct from status colors."
    ],
    "css_variables_hsl": {
      "base": {
        "--background": "222 35% 6%",
        "--foreground": "210 20% 96%",
        "--card": "222 30% 8%",
        "--card-foreground": "210 20% 96%",
        "--popover": "222 30% 8%",
        "--popover-foreground": "210 20% 96%",
        "--muted": "222 22% 12%",
        "--muted-foreground": "215 14% 70%",
        "--border": "222 18% 16%",
        "--input": "222 18% 16%",
        "--ring": "190 95% 55%",
        "--radius": "0.75rem"
      },
      "brand": {
        "--primary": "190 95% 55%",
        "--primary-foreground": "222 35% 6%",
        "--secondary": "222 22% 12%",
        "--secondary-foreground": "210 20% 96%",
        "--accent": "198 85% 60%",
        "--accent-foreground": "222 35% 6%"
      },
      "semantic_status": {
        "--status-ok": "152 72% 48%",
        "--status-warn": "38 92% 56%",
        "--status-crit": "0 84% 58%",
        "--status-down": "0 0% 55%",
        "--status-info": "205 90% 60%"
      },
      "traffic": {
        "--traffic-active": "186 100% 55%",
        "--traffic-idle": "222 10% 35%",
        "--traffic-glow": "186 100% 55%"
      },
      "vendor_accents": {
        "--vendor-mikrotik": "12 85% 58%",
        "--vendor-ubiquiti": "205 90% 60%",
        "--vendor-cambium": "152 72% 48%",
        "--vendor-mimosa": "38 92% 56%"
      },
      "charts": {
        "--chart-1": "186 100% 55%",
        "--chart-2": "152 72% 48%",
        "--chart-3": "38 92% 56%",
        "--chart-4": "205 90% 60%",
        "--chart-5": "0 84% 58%"
      }
    },
    "hex_equivalents": {
      "bg": "#070B14",
      "surface": "#0B1220",
      "surface2": "#0F1A2E",
      "border": "#1B2A3D",
      "text": "#EAF0F7",
      "muted": "#A9B6C6",
      "primary_cyan": "#2FE6FF",
      "ok_green": "#2ED47A",
      "warn_amber": "#FFB020",
      "crit_red": "#FF4D4F",
      "traffic": "#22F0D6"
    },
    "gradient_policy": {
      "allowed": [
        "Hero/top header background only (max 20% viewport)",
        "Decorative overlays (noise + subtle radial)",
        "Large map background vignette"
      ],
      "recommended_gradients": [
        "radial-gradient(900px circle at 20% 10%, rgba(47,230,255,0.10), transparent 55%), radial-gradient(700px circle at 80% 0%, rgba(46,212,122,0.08), transparent 60%), linear-gradient(180deg, #070B14 0%, #070B14 100%)"
      ],
      "prohibited": [
        "blue-500 to purple-600",
        "purple-500 to pink-500",
        "green-500 to blue-500",
        "red to pink",
        "any saturated neon gradient on cards/tables"
      ]
    }
  },
  "design_tokens": {
    "spacing": {
      "page_padding": "px-4 sm:px-6 lg:px-8",
      "section_gap": "gap-4 sm:gap-6",
      "tile_padding": "p-4 sm:p-5",
      "dense_table_cell": "py-2 px-3"
    },
    "radii": {
      "card": "rounded-xl",
      "control": "rounded-lg",
      "pill": "rounded-full"
    },
    "shadows": {
      "panel": "shadow-[0_10px_30px_rgba(0,0,0,0.35)]",
      "panel_inner_border": "ring-1 ring-white/5",
      "focus": "focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))] focus-visible:ring-offset-0"
    },
    "borders": {
      "default": "border border-[hsl(var(--border))]",
      "hairline": "border border-white/5"
    }
  },
  "layout": {
    "app_shell": {
      "structure": [
        "Left sidebar (icon + label) collapsible",
        "Top bar with global status summary + live poll indicator + search",
        "Main content area with responsive grid",
        "Right-side drawer for device details (on map/table click)"
      ],
      "grid": {
        "dashboard": "grid grid-cols-1 lg:grid-cols-12 gap-4 sm:gap-6",
        "dashboard_left": "lg:col-span-8",
        "dashboard_right": "lg:col-span-4",
        "tiles": "grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4"
      },
      "noc_tv_mode": {
        "rules": [
          "Use 12-col grid but with fewer, larger tiles.",
          "Minimum font size for key numbers: 28–44px depending on tile.",
          "Avoid dense tables; use Top-N lists with 6–10 rows max.",
          "Auto-rotate panels every 20–40s with fade/slide transitions.",
          "Persistent alert ticker at bottom with severity color chips."
        ]
      }
    }
  },
  "components": {
    "component_path": {
      "navigation": [
        "/app/frontend/src/components/ui/navigation-menu.jsx",
        "/app/frontend/src/components/ui/tooltip.jsx",
        "/app/frontend/src/components/ui/separator.jsx",
        "/app/frontend/src/components/ui/scroll-area.jsx"
      ],
      "surfaces": [
        "/app/frontend/src/components/ui/card.jsx",
        "/app/frontend/src/components/ui/resizable.jsx"
      ],
      "forms": [
        "/app/frontend/src/components/ui/form.jsx",
        "/app/frontend/src/components/ui/input.jsx",
        "/app/frontend/src/components/ui/label.jsx",
        "/app/frontend/src/components/ui/select.jsx",
        "/app/frontend/src/components/ui/switch.jsx",
        "/app/frontend/src/components/ui/slider.jsx",
        "/app/frontend/src/components/ui/textarea.jsx"
      ],
      "feedback": [
        "/app/frontend/src/components/ui/sonner.jsx",
        "/app/frontend/src/components/ui/alert.jsx",
        "/app/frontend/src/components/ui/badge.jsx",
        "/app/frontend/src/components/ui/progress.jsx",
        "/app/frontend/src/components/ui/skeleton.jsx"
      ],
      "overlays": [
        "/app/frontend/src/components/ui/drawer.jsx",
        "/app/frontend/src/components/ui/dialog.jsx",
        "/app/frontend/src/components/ui/sheet.jsx",
        "/app/frontend/src/components/ui/popover.jsx",
        "/app/frontend/src/components/ui/hover-card.jsx"
      ],
      "data_display": [
        "/app/frontend/src/components/ui/table.jsx",
        "/app/frontend/src/components/ui/tabs.jsx",
        "/app/frontend/src/components/ui/pagination.jsx",
        "/app/frontend/src/components/ui/accordion.jsx"
      ]
    },
    "button_system": {
      "tone": "Professional / instrument panel",
      "variants": {
        "primary": {
          "use": "Main CTAs (Add device, Acknowledge, Save dashboard)",
          "tailwind": "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] hover:bg-[hsl(var(--primary))]/90 active:bg-[hsl(var(--primary))]/85",
          "radius": "rounded-lg",
          "motion": "transition-colors duration-150"
        },
        "secondary": {
          "use": "Secondary actions",
          "tailwind": "bg-[hsl(var(--secondary))] text-[hsl(var(--secondary-foreground))] border border-white/10 hover:bg-white/5",
          "motion": "transition-colors duration-150"
        },
        "ghost": {
          "use": "Toolbar icon buttons",
          "tailwind": "bg-transparent hover:bg-white/5 text-[hsl(var(--foreground))]",
          "motion": "transition-colors duration-150"
        },
        "danger": {
          "use": "Resolve/Delete",
          "tailwind": "bg-[hsl(var(--status-crit))] text-white hover:bg-[hsl(var(--status-crit))]/90",
          "motion": "transition-colors duration-150"
        }
      },
      "interaction_rules": [
        "No `transition-all`.",
        "Use `active:scale-[0.98]` only on primary CTAs (not on icon-only buttons).",
        "Always include visible focus ring using `focus-visible` utilities."
      ]
    },
    "cards_tiles": {
      "base_class": "rounded-xl bg-[hsl(var(--card))] text-[hsl(var(--card-foreground))] border border-white/5 shadow-[0_10px_30px_rgba(0,0,0,0.35)]",
      "header": "flex items-start justify-between gap-3",
      "title": "text-sm font-medium text-[hsl(var(--muted-foreground))]",
      "value": "mt-2 text-2xl sm:text-3xl font-semibold tracking-tight",
      "sub": "mt-1 text-xs text-[hsl(var(--muted-foreground))]",
      "status_chip": "inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-xs border border-white/10 bg-white/5"
    },
    "tables": {
      "style": [
        "Use sticky header for long device/interface tables.",
        "Use zebra rows with very subtle contrast (white/2–3%).",
        "Use mono for interface names and IPs.",
        "Use right-aligned numeric columns."
      ],
      "row_classes": {
        "base": "hover:bg-white/5 transition-colors duration-150",
        "critical": "bg-[rgba(255,77,79,0.08)]",
        "warning": "bg-[rgba(255,176,32,0.08)]"
      }
    },
    "alerts": {
      "feed_item": {
        "layout": "left severity bar + title + device + time + actions",
        "severity_bar": "w-1 rounded-full",
        "actions": "Acknowledge, Resolve, Open device"
      },
      "severity_colors": {
        "info": "bg-[hsl(var(--status-info))]",
        "warning": "bg-[hsl(var(--status-warn))]",
        "critical": "bg-[hsl(var(--status-crit))]",
        "ok": "bg-[hsl(var(--status-ok))]"
      }
    },
    "topology_map_xyflow": {
      "library": "@xyflow/react",
      "map_surface": {
        "container": "rounded-xl border border-white/5 bg-[#070B14] shadow-[0_10px_30px_rgba(0,0,0,0.35)] overflow-hidden",
        "background": "Use subtle vignette + grid dots (not bright).",
        "controls": "Place zoom/fit controls top-right; style as ghost buttons."
      },
      "node_design": {
        "shape": "rounded-xl device card with left vendor stripe + status dot",
        "content": [
          "Top row: device name (truncate) + status dot",
          "Second row: IP (mono) + vendor badge",
          "Bottom: 2 mini metrics (latency, util) with tiny sparkline"
        ],
        "status_dot": "Use `--status-*` colors; add subtle glow only when critical.",
        "vendor_stripe": "2–3px vertical stripe using vendor accent variables.",
        "hover": "Increase border to white/12 and lift shadow slightly (no transform on frequent updates)."
      },
      "edge_design": {
        "base": "stroke: rgba(169,182,198,0.35); stroke-width: 1.5",
        "active_traffic": {
          "stroke": "hsl(var(--traffic-active))",
          "dash": "stroke-dasharray: 6 8",
          "glow": "filter: drop-shadow(0 0 6px rgba(34,240,214,0.35))",
          "animation": "Animate dash offset; speed scales with utilization"
        },
        "utilization_to_speed": {
          "rule": "speed = clamp(0.6s, 2.4s - util*1.8s, 2.4s) where util is 0..1",
          "implementation": "Set CSS var `--edge-dash-speed` per edge style based on live util"
        }
      },
      "css_scaffold": {
        "file": "/app/frontend/src/index.css",
        "snippet": ".xyflow-dark { --xy-bg: #070B14; }\n.react-flow__pane { background: radial-gradient(900px circle at 20% 10%, rgba(47,230,255,0.08), transparent 55%), radial-gradient(700px circle at 80% 0%, rgba(46,212,122,0.06), transparent 60%), #070B14; }\n.react-flow__node { font-family: var(--font-sans); }\n@keyframes edgeDash { to { stroke-dashoffset: -28; } }\n.edge--active path { stroke: hsl(var(--traffic-active)); stroke-dasharray: 6 8; animation: edgeDash var(--edge-dash-speed, 1.6s) linear infinite; filter: drop-shadow(0 0 6px rgba(34,240,214,0.35)); }\n.edge--idle path { stroke: rgba(169,182,198,0.28); }\n.edge--warn path { stroke: hsl(var(--status-warn)); stroke-dasharray: 4 10; }\n.edge--crit path { stroke: hsl(var(--status-crit)); stroke-dasharray: 2 10; }"
      }
    },
    "dashboards_drag_drop": {
      "library": "react-grid-layout",
      "widget_shell": "Use Card with a compact header: title + time range + kebab menu (DropdownMenu).",
      "resize_handles": "Show only on hover; use subtle cyan handle dots.",
      "empty_state": "Use Skeleton + muted copy; provide 'Add widget' primary button."
    },
    "charts_recharts": {
      "rules": [
        "Use muted gridlines (white/6%).",
        "Use mono ticks for time/values.",
        "Avoid animated transitions on every poll update; prefer `isAnimationActive={false}` for high-frequency charts.",
        "Use gradient fills sparingly inside charts only (area fill at 10–14% opacity)."
      ],
      "palette": [
        "hsl(var(--chart-1))",
        "hsl(var(--chart-2))",
        "hsl(var(--chart-3))",
        "hsl(var(--chart-4))",
        "hsl(var(--chart-5))"
      ]
    }
  },
  "motion_microinteractions": {
    "principles": [
      "Motion communicates state changes; avoid decorative motion that competes with live data.",
      "Prefer opacity/color transitions over transforms for frequently updating tiles.",
      "Respect prefers-reduced-motion: disable edge dash animation and auto-rotate."
    ],
    "recommended_library": {
      "name": "framer-motion",
      "install": "npm i framer-motion",
      "usage": "Use for panel transitions (TV mode rotation), drawer entrance, alert ticker slide. Keep durations 180–260ms."
    },
    "interaction_specs": {
      "hover": "transition-colors duration-150 on buttons/rows; cards border brightens to white/10",
      "press": "primary buttons active:scale-[0.98]",
      "live_update": "Use `animate` only for severity changes (e.g., warn->crit pulse once)."
    }
  },
  "accessibility": {
    "rules": [
      "WCAG AA contrast: ensure muted text still readable on #070B14.",
      "Keyboard navigation: sidebar, tables, map nodes must be focusable.",
      "Focus ring must be visible on dark surfaces.",
      "Provide reduced motion mode: stop dashed animations and ticker movement.",
      "Use aria-labels for icon-only buttons."
    ]
  },
  "testing_attributes": {
    "data_testid_rules": [
      "All interactive and key informational elements MUST include data-testid.",
      "Use kebab-case describing role, not appearance.",
      "Examples: `data-testid=\"sidebar-nav-devices-link\"`, `data-testid=\"alerts-acknowledge-button\"`, `data-testid=\"topology-node-router-1\"`, `data-testid=\"noc-tv-mode-toggle\"`."
    ]
  },
  "pages": {
    "overview_dashboard": {
      "sections": [
        "Fleet health tiles (Up/Down/Warn/Crit)",
        "Active alerts feed (right column)",
        "Top interfaces by utilization (table)",
        "Latency/Loss sparklines (small cards)",
        "Mini topology embed (optional widget)"
      ]
    },
    "topology_map": {
      "ui": [
        "Map toolbar: Search device, Fit view, Layout (Dagre), Toggle labels",
        "Right drawer: device details with tabs (Interfaces, Charts, Events)",
        "Legend: status + vendor colors"
      ]
    },
    "devices": {
      "ui": [
        "Table with filters (vendor, status), search, add device",
        "CIDR discovery dialog with progress",
        "Device detail drawer/page with interface table + charts"
      ]
    },
    "alerts": {
      "ui": [
        "Active + History tabs",
        "Rules CRUD (forms)",
        "Discord webhook settings + test button (toast feedback)"
      ]
    },
    "custom_dashboards": {
      "ui": [
        "Dashboard list + create",
        "Drag/resize widgets",
        "Widget library drawer (add widgets)"
      ]
    },
    "noc_tv_mode": {
      "ui": [
        "Full-screen",
        "Auto-rotating panels",
        "Giant tiles",
        "Bottom alert ticker + clock",
        "Minimal chrome (hide sidebar)"
      ]
    },
    "settings": {
      "ui": [
        "SNMP defaults",
        "Poll intervals",
        "Discovery ranges",
        "Thresholds",
        "Discord webhook"
      ]
    }
  },
  "image_urls": [
    {
      "category": "login_or_empty_state_background_optional",
      "description": "Dark server-room photo for optional login/empty-state hero background (use heavy dark overlay; do not reduce readability).",
      "url": "https://images.unsplash.com/photo-1614508569207-3295ac89d75f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzl8MHwxfHNlYXJjaHwxfHxkYXJrJTIwc2VydmVyJTIwcm9vbXxlbnwwfHx8YmxhY2t8MTc4NjA3NTI2NXww&ixlib=rb-4.1.0&q=85"
    },
    {
      "category": "decorative_background_texture",
      "description": "Abstract circuit texture for subtle blurred background layer behind auth/settings pages (opacity 6–10%).",
      "url": "https://images.unsplash.com/photo-1582721691120-d1db3852893e?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2ODh8MHwxfHNlYXJjaHwzfHxhYnN0cmFjdCUyMGNpcmN1aXQlMjBib2FyZCUyMGRhcmt8ZW58MHx8fGJsdWV8MTc4NjA3NTI4MHww&ixlib=rb-4.1.0&q=85"
    },
    {
      "category": "decorative_background_texture",
      "description": "Bokeh lights texture for subtle depth in TV mode panel transitions (opacity 5–8%).",
      "url": "https://images.unsplash.com/photo-1604011237320-8e0506614fdf?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2ODh8MHwxfHNlYXJjaHw0fHxhYnN0cmFjdCUyMGNpcmN1aXQlMjBib2FyZCUyMGRhcmt8ZW58MHx8fGJsdWV8MTc4NjA3NTI4MHww&ixlib=rb-4.1.0&q=85"
    }
  ],
  "extra_libraries": [
    {
      "name": "@xyflow/react",
      "purpose": "Topology map with draggable nodes and custom animated edges",
      "notes": "Use custom edge classNames to toggle active dash animation based on utilization"
    },
    {
      "name": "react-grid-layout",
      "purpose": "Custom dashboards drag/resize widgets",
      "notes": "Persist layouts per dashboard; show resize handles only on hover"
    },
    {
      "name": "recharts",
      "purpose": "Time-series charts, sparklines, gauges",
      "notes": "Disable per-update animations for high-frequency polling"
    },
    {
      "name": "framer-motion",
      "purpose": "TV mode panel transitions + alert ticker motion",
      "install": "npm i framer-motion"
    }
  ],
  "instructions_to_main_agent": {
    "global_css_updates": [
      "Update /app/frontend/src/index.css : replace current :root and .dark tokens with the provided dark-first tokens (keep shadcn structure).",
      "Set default theme to dark by applying `class=\"dark\"` on the html/body root in React entry (or Tailwind dark mode strategy).",
      "Add scanline/noise overlay as a pseudo-element on body (very subtle).",
      "Do NOT use `transition: all` anywhere."
    ],
    "app_css_cleanup": [
      "Remove CRA demo styles in /app/frontend/src/App.css (App-header centering etc). Keep file minimal or delete if unused."
    ],
    "topology_edge_implementation_hint_js": [
      "When building ReactFlow edges, set `className` based on live metrics: `edge--active`, `edge--idle`, `edge--warn`, `edge--crit`.",
      "Set inline style var for speed: `style={{ '--edge-dash-speed': `${speed}s` }}` (JS object key must be string).",
      "Respect reduced motion: if `window.matchMedia('(prefers-reduced-motion: reduce)').matches`, do not apply `edge--active` animation class."
    ],
    "data_testid_coverage": [
      "Add data-testid to: sidebar links, topbar controls, map toolbar buttons, node wrappers, edge labels (if clickable), device table rows, alert actions, dashboard widget menus, settings save/test buttons, and key KPI numbers."
    ],
    "tv_mode": [
      "Implement a dedicated route `/tv` that hides sidebar/topbar chrome and uses larger typography + fewer widgets.",
      "Add auto-rotate with Framer Motion; include pause on hover and pause when user interacts."
    ]
  },
  "inspiration_sources": {
    "references": [
      {
        "title": "Elastic Observability Labs - APM service map migration to React Flow",
        "url": "https://www.elastic.co/observability-labs/blog/apm-service-map-react-flow-migration"
      },
      {
        "title": "Watchtower NOC dashboard (project inspiration)",
        "url": "https://solomonneas.dev/projects/watchtower-noc-dashboard"
      },
      {
        "title": "Zabbix map animation (animated links concept)",
        "url": "https://github.com/venkateshr9/zabbix-map-animation"
      }
    ]
  },
  "general_ui_ux_design_guidelines_appendix": "- You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n- You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n- NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals."
}
