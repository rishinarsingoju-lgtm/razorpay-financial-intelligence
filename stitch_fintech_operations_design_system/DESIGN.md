---
name: Financial Intelligence Control Center
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#45464d'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#76777d'
  outline-variant: '#c6c6cd'
  surface-tint: '#565e74'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#131b2e'
  on-primary-container: '#7c839b'
  inverse-primary: '#bec6e0'
  secondary: '#0051d5'
  on-secondary: '#ffffff'
  secondary-container: '#316bf3'
  on-secondary-container: '#fefcff'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#0b1c30'
  on-tertiary-container: '#75859d'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#dbe1ff'
  secondary-fixed-dim: '#b4c5ff'
  on-secondary-fixed: '#00174b'
  on-secondary-fixed-variant: '#003ea8'
  tertiary-fixed: '#d3e4fe'
  tertiary-fixed-dim: '#b7c8e1'
  on-tertiary-fixed: '#0b1c30'
  on-tertiary-fixed-variant: '#38485d'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
  status-critical: '#DC2626'
  status-critical-bg: '#FEF2F2'
  status-critical-border: '#FECACA'
  status-warning: '#D97706'
  status-warning-bg: '#FFFBEB'
  status-warning-border: '#FDE68A'
  status-success: '#16A34A'
  status-success-bg: '#F0FDF4'
  status-success-border: '#BBF7D0'
  status-investigating: '#6366F1'
  status-investigating-bg: '#EEF2FF'
  status-investigating-border: '#C7D2FE'
  surface-subtle: '#F1F5F9'
  surface-card: '#FFFFFF'
  border-subtle: '#E2E8F0'
  border-strong: '#CBD5E1'
  text-primary: '#0F172A'
  text-secondary: '#475569'
  text-muted: '#94A3B8'
typography:
  headline-xl:
    fontFamily: Manrope
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Manrope
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Manrope
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Manrope
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.005em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  financial-metric-lg:
    fontFamily: Manrope
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.02em
  financial-metric-md:
    fontFamily: Manrope
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  label-reference:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-code:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 14px
  caption:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.01em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  layout-margin-desktop: 2rem
  layout-margin-tablet: 1.5rem
  layout-margin-mobile: 1rem
  grid-gutter: 1.5rem
  space-xxs: 0.25rem
  space-xs: 0.5rem
  space-sm: 0.75rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
  space-2xl: 3rem
  space-3xl: 4rem
---

# AI Financial Intelligence — Design Specification
## Product
AI-powered financial intelligence platform for businesses using Razorpay.
Core experience:
Order → Payment → Refund/Fee/Adjustment → Settlement → Bank Credit
The product automatically reconciles financial records, detects exceptions, provides settlement intelligence, traces transaction chains, and lets users investigate financial issues through an AI copilot.
Primary user: business owner or finance operator.
Core question:
"Where is my money, and what needs my attention?"
## Design Goals
Create a premium B2B fintech interface that feels:
- trustworthy
- intelligent
- calm
- precise
- professional
- data-rich but easy to scan
Avoid:
- generic SaaS dashboard aesthetics
- excessive cards
- clutter
- crypto/trading-terminal styling
- flashy AI visuals
- unnecessary gradients
- decorative elements that compete with financial information
Desktop-first web application.
## Visual Language
Use a clean modern fintech visual system with:
- strong typography hierarchy
- generous spacing
- restrained color usage
- subtle borders and surfaces
- clear status indicators
- highly readable financial numbers
- tables for dense financial records
- charts only where they communicate useful trends
Financial status colors should be semantic and restrained:
- positive/success
- warning/attention
- critical/problem
- neutral/information
Do not overuse color.
## Navigation
Primary navigation:
1. Overview
2. Reconciliation
3. Settlements
4. Transactions
5. AI Copilot
Keep navigation minimal.
## Screen 1 — Overview
Purpose: immediately answer:
- How much money is moving?
- How much is expected?
- How much has settled?
- What needs attention?
Show:
- payment volume
- expected settlement
- settled amount
- pending/delayed amount
- reconciliation health
- exceptions requiring attention
- recent settlement activity
- useful financial trend
Make "Needs Attention" prominent.
Example issues:
- ₹50,000 settlement missing
- ₹12,500 fee mismatch
- 3 delayed settlements
- 2 unmatched payments
The dashboard must prioritize actionable exceptions over decorative analytics.
## Screen 2 — Reconciliation
Show reconciliation status:
- Matched
- Unmatched
- Mismatched
- Investigating
- Resolved
Filters:
- date
- amount
- status
- exception type
- transaction/reference ID
Exception types:
- Missing settlement
- Partial settlement
- Duplicate
- Fee mismatch
- Bank-credit mismatch
- Delayed settlement
- Unmatched payment
Each exception should clearly expose:
Expected → Actual → Difference → Status
## Screen 3 — Investigation
Show the complete financial chain:
Order
↓
Payment
↓
Refund / Fee / Adjustment
↓
Settlement
↓
Bank Credit
Each stage shows:
- ID/reference
- amount
- timestamp
- status
- relevant metadata
Clearly highlight where the chain breaks.
Example:
Payment: ₹50,000 ✓
Expected settlement: ₹50,000
Actual settlement: ₹0
Bank credit: ₹0
Difference: ₹50,000
Provide an obvious "Ask AI about this issue" action.
## Screen 4 — Settlement Intelligence
Show:
- Expected settlements
- Processing
- Settled
- Delayed
- Held
- Bank credited
Settlement table:
- settlement ID
- expected amount
- actual amount
- difference
- expected date
- actual date
- status
Users should immediately understand:
What should have settled → what actually settled → what is missing → why.
## Screen 5 — AI Financial Copilot
Design the AI as a financial investigation assistant, not a generic chatbot.
Suggested questions:
- Why is today's settlement lower?
- Where is the missing ₹50,000?
- Show unreconciled payments above ₹10,000.
- Which settlements are delayed?
- What caused this discrepancy?
- What needs my attention today?
AI response structure:
1. Answer
2. Financial evidence
3. Records investigated
4. Recommended action
Show relevant transaction IDs, settlement IDs and amounts as evidence.
The AI should feel grounded in the financial system.
Do not make the AI visually dominate the financial product.
## Screen 6 — Transactions
Provide a searchable financial transaction view.
Allow users to inspect:
- payment
- refund
- fee
- settlement
- bank credit
Show status, amount, timestamps and references.
Provide navigation into the transaction chain.
## UX Principles
### Exception-first
Surface financial problems automatically.
### Traceability
Important numbers must be traceable to underlying records.
### Explainability
AI answers should visibly connect to financial evidence.
### Progressive disclosure
Overview is simple.
Investigation views contain detailed information.
### Financial clarity
Consistently use:
Expected
Actual
Difference
Matched
Unmatched
Delayed
Settled
Pending
Exception
## Demo Flow
The interface must support this exact story:
1. Open Overview.
2. See overall financial health.
3. Notice ₹50,000 requires attention.
4. Open Reconciliation.
5. Open the missing settlement.
6. Inspect Order → Payment → Settlement → Bank Credit.
7. Open AI Copilot.
8. Ask "Where is the missing ₹50,000?"
9. AI explains the broken financial chain.
10. Ask "Why is today's settlement lower?"
11. AI explains the settlement discrepancy.
12. User can visually verify the AI's numbers against the underlying records.
The experience should make this investigation feel fast and obvious.
## States
Design important states for:
- normal
- loading
- empty
- error
- exception
- AI response
- investigation
## Responsive
Desktop-first.
Support sensible tablet/mobile adaptation without compromising the desktop finance workflow.
## Product Character
The product should feel like:
"An intelligent financial control center that continuously understands where business money is, reconciles it, surfaces problems, and explains what happened."
It should NOT feel like:
"Another analytics dashboard with an AI chatbot."