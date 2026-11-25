# NIL.ai Company Website — Product and Build Specification

## Purpose

Build a public, responsive website for Nepal Innovation Labs (brand: NIL.ai) with an advanced research-laboratory aesthetic. This is distinct from the NP.ai authenticated product application.

## Primary navigation

- Home
- About
- Products
- Research
- Responsible AI
- Contact
- Launch NP.ai (clearly labelled product link; destination configurable)

## Home page structure

1. Hero: "Born in Nepal. Built for the world." Explain that NIL.ai researches and engineers useful AI technology. Primary CTA: Explore NP.ai. Secondary CTA: Explore research.
2. Company mission: short, concrete and evidence-based.
3. Flagship product: NP.ai document intelligence and bilingual workspace; show only working capabilities.
4. Research areas: Nepali language intelligence, reliable knowledge AI, efficient AI and AI safety.
5. Engineering principles: privacy, security, evaluation, accessibility and human oversight.
6. Research / engineering updates: publish only verifiable work.
7. Contact: clear business and research inquiry path.
8. Footer: company identity, GitHub, privacy, terms and accessibility statement.

## Visual direction

- Advanced research laboratory, not cyberpunk.
- Dark graphite/navy base with high-contrast light content surfaces.
- Restrained cyan/blue accent, fine grid lines, technical diagrams and generous whitespace.
- Typography should be highly legible; avoid tiny all-caps body copy.
- Motion must be subtle and respect prefers-reduced-motion.
- Use real product captures and diagrams; no fabricated lab photos, metrics, partners or testimonials.

## Technical requirements

- Responsive mobile-first layout.
- Semantic HTML and accessible names.
- WCAG 2.2 AA target.
- Keyboard-operable navigation and visible focus.
- Reduced-motion support.
- Metadata, Open Graph and sitemap.
- Fast loading; optimize images and avoid unnecessary client JavaScript.
- Content should be editable without touching application logic.
- Security headers and a restrictive Content Security Policy appropriate to deployment.
- No analytics or tracking without an explicit privacy decision.
- Contact form must not be decorative: either connect a secured backend with spam protection or use a clearly displayed email/contact link.

## Proposed implementation

Use a separate company website repository or a clearly isolated `website/` app in a future monorepo. Do not mix public marketing pages with NP.ai authentication, chat or customer data routes.

Preferred stack: Next.js App Router + TypeScript, accessible component primitives, CSS variables/design tokens, lint/typecheck/build CI. Reuse existing deployment and package conventions only after auditing the current repository.

## Acceptance criteria

- All navigation links work.
- Mobile, tablet and desktop layouts are tested.
- Keyboard-only navigation works.
- Reduced-motion preference is respected.
- No fabricated claims, customer logos or metrics.
- Lighthouse-style performance and accessibility checks are documented.
- Production build and CI pass.
- Contact path is functional and privacy-reviewed.
