# Design System Strategy: The Digital Roastery

## 1. Overview & Creative North Star
**Creative North Star: "The Artisanal Alchemist"**

This design system rejects the sterile, "SaaS-blue" aesthetics of typical AI platforms. Instead, it leans into the tactile, sensory world of specialty coffee—combining the precision of technology with the warmth of a morning brew. 

We break the "template" look through **Intentional Asymmetry** and **Editorial Layering**. Rather than rigid, boxed-in sections, the UI should feel like a high-end lifestyle magazine: breathable, sophisticated, and deeply human. We use "Bento-style" layouts not as static grids, but as a series of nested, elevated trays that prioritize content through depth rather than lines.

---

## 2. Colors & Tonal Depth
Our palette transitions from the steam of a latte (`surface: #fff8f1`) to the depth of an espresso (`on_secondary_fixed: #2d1608`).

### The "No-Line" Rule
**Explicit Instruction:** Do not use 1px solid borders to define sections. To separate a navigation sidebar from a main feed, or a hero section from a feature grid, use a background shift. For example, place a `surface_container_low` section directly against a `surface` background. The boundary is felt through the change in value, not seen through a stroke.

### Surface Hierarchy & Nesting
Treat the interface as physical layers of fine paper and glass.
*   **Base Layer:** `surface` (#fff8f1) for the main canvas.
*   **Secondary Layer:** `surface_container_low` for subtle grouping.
*   **Action Layer:** `surface_container_highest` for interactive elements that need to pop.

### The "Glass & Gradient" Rule
To elevate the "AI" aspect of the platform, use Glassmorphism for floating overlays (e.g., AI suggestion prompts). Use `surface_container_lowest` at 70% opacity with a `20px` backdrop-blur. 

**Signature Gradients:** Apply a subtle linear gradient to Primary CTAs:
*   *From:* `primary` (#775838) 
*   *To:* `primary_container` (#c8a27c) 
This 15-degree tilt provides a "metallic" gold sheen that feels premium and tactile.

---

## 3. Typography: Editorial Authority
We utilize a pairing of **Plus Jakarta Sans** for character-rich displays and **Manrope** for high-performance utility.

*   **Display & Headlines (Plus Jakarta Sans):** These are the "voice" of the brand. Use `display-lg` (3.5rem) with tight letter-spacing (-0.02em) to create an authoritative, editorial feel.
*   **Body & Labels (Manrope):** Chosen for its geometric clarity. `body-md` (0.875rem) ensures that even dense marketing data remains legible.
*   **The Hierarchy Goal:** Use high contrast in scale. A `display-md` headline should sit closely to a `label-md` eyebrow text to create a sophisticated, asymmetrical tension typical of high-end fashion or architectural journals.

---

## 4. Elevation & Depth
We move away from the "flat" web by using light and physics.

*   **The Layering Principle:** Depth is achieved by stacking. Place a `surface_container_lowest` card on a `surface_container_low` background. This creates a "natural lift" that feels architectural.
*   **Ambient Shadows:** For floating 3D mascots or featured "Post Cards," use an extra-diffused shadow: `box-shadow: 0 20px 40px rgba(61, 35, 20, 0.08);`. Note the color: we use a tint of our Deep Cocoa Brown (`#3D2314`) rather than black, keeping the shadows "warm" and natural.
*   **The Ghost Border Fallback:** If a border is required for accessibility (e.g., search inputs), use `outline_variant` at **15% opacity**. It should be a suggestion of an edge, not a cage.

---

## 5. Components

### Primary Buttons
*   **Style:** `rounded-full` (pill-shaped) to contrast the bento-grid's geometry.
*   **Color:** The Signature Gradient (Primary to Primary-Container).
*   **Interaction:** On hover, a subtle `xl` elevation increase and a scale of 1.02.

### Bento Grid Cards
*   **Constraint:** No borders. 
*   **Separation:** Use `surface_container` with a `lg` (1rem) corner radius. 
*   **Content:** Large `headline-sm` titles paired with 3D mascots that "break the container"—partially overlapping the card edges to create 3D space.

### Input Fields
*   **Style:** Minimalist. No bottom line, no full border. Use `surface_container_low` as the field background with a `md` (0.75rem) radius. 
*   **Focus State:** The background shifts to `surface_container_highest` with a `primary` "Ghost Border" at 20% opacity.

### Comparison Tables
*   **Logic:** Forbid vertical and horizontal divider lines. 
*   **Alternative:** Use zebra-striping with `surface_container_low` and `surface_container_lowest`. The "Current Plan" column should be highlighted using a subtle `primary_fixed` background.

---

## 6. Do’s and Don'ts

### Do:
*   **Do** use white space as a structural element. The `spacing-12` (4rem) and `spacing-16` (5.5rem) tokens are your friends for section breaks.
*   **Do** lean into the "Warm Cream" (`#FFF8F0`) for light modes; pure white should only be used for the most elevated "top-tier" cards (`surface_container_lowest`).
*   **Do** allow 3D assets to overlap text and containers to break the "web box" feel.

### Don't:
*   **Don't** use standard #000000 for text. Always use `on_surface` (#1e1b17) or `on_secondary_container` (#795845) to maintain the "warm" aesthetic.
*   **Don't** use hard-edged shadows. If a shadow feels "noticeable," it is too heavy. It should feel like an ambient glow.
*   **Don't** use dividers. If two pieces of content feel cluttered, increase the `spacing` token rather than adding a line. 

---
*Director's Note: This system is not a set of constraints, but a foundation for craft. Every screen should feel like it was curated, not just generated.*