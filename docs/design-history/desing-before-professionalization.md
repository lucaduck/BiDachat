# BIDACHAT — Design Guidelines

## 1. Design goals

BIDACHAT is a web application for managing and deploying analytical chatbots integrated with BI-DATA dashboards.

The interface should be:

- Clear and easy to understand.
- Consistent across screens and components.
- Visually aligned with BI-DATA.
- Oriented to data analysis and chatbot management.
- Simple, avoiding unnecessary visual complexity.
- Responsive across desktop, tablet and mobile devices.

The administration interface will use a dark visual base with the BI-DATA turquoise as the main identity color.

---

## 2. Visual identity

### 2.1. Product name

**BIDACHAT**

BIDACHAT must be presented as a **web application**, not as a platform.

### 2.2. Brand relationship

The visual identity must maintain a clear relationship with the BI-DATA research group.

The BIDACHAT logo should combine concepts related to:

- Chatbots.
- Artificial intelligence.
- Data analysis.
- Analytical dashboards.

### 2.3. Logo variants

The interface should support at least:

- Primary BIDACHAT logo.
- White BIDACHAT logo for dark backgrounds.
- Compact icon version for reduced spaces.

The logo should not be stretched, recolored arbitrarily or placed over backgrounds that reduce readability.

---

## 3. Color palette

### 3.1. Brand colors

| Token | Color | HEX | Main use |
|---|---|---|---|
| `primary` | BI-DATA Turquoise | `#14A8CE` | Main actions, active states, branding |
| `primary-dark` | Deep Navy | `#0B1F33` | Header, sidebar, dark areas |
| `secondary-dark` | Petroleum Blue | `#12324A` | Secondary dark surfaces |
| `secondary` | Institutional Blue | `#2459A4` | Links, charts, secondary actions |
| `primary-light` | Light Cyan | `#6CC1CF` | Soft accents and highlights |

### 3.2. Interface colors

| Token | Color | HEX | Main use |
|---|---|---|---|
| `background` | Dark Background | `#08111F` | Main application background |
| `surface` | Dark Surface | `#102033` | Cards, forms, panels |
| `border` | Blue Gray | `#1E3A52` | Borders and separators |
| `text` | Soft White | `#F8FAFC` | Main text |
| `text-muted` | Muted Blue Gray | `#94A3B8` | Secondary text |

### 3.3. Semantic colors

| Token | Color | HEX | Main use |
|---|---|---|---|
| `success` | Emerald Green | `#10B981` | Success and active states |
| `warning` | Orange | `#F07942` | Warnings |
| `error` | Red | `#DC2626` | Errors and destructive actions |

### 3.4. CSS variables

```css
:root {
  --color-primary: #14A8CE;
  --color-primary-dark: #0B1F33;
  --color-secondary-dark: #12324A;
  --color-secondary: #2459A4;
  --color-primary-light: #6CC1CF;

  --color-background: #08111F;
  --color-surface: #102033;
  --color-border: #1E3A52;

  --color-text: #F8FAFC;
  --color-text-muted: #94A3B8;

  --color-success: #10B981;
  --color-warning: #F07942;
  --color-error: #DC2626;
}
```

---

## 4. Typography

Use a single sans-serif family across the application.

### Recommended family

**Inter**

### Typography hierarchy

| Style | Size | Weight | Use |
|---|---:|---:|---|
| H1 | 32px | 700 | Main screen title |
| H2 | 24px | 700 | Main section title |
| H3 | 20px | 600 | Card or subsection title |
| Body | 16px | 400 | Main content |
| Small | 14px | 400 | Supporting text |
| Caption | 12px | 500 | Metadata and labels |

Avoid using multiple font families without a justified need.

---

## 5. Layout

### 5.1. Desktop structure

```text
+------------------------------------------------------+
| Header                                               |
+----------------+-------------------------------------+
|                |                                     |
| Sidebar        |          Main Content               |
|                |                                     |
| Chatbots       |   Cards / Forms / Metrics           |
| Documents      |                                     |
| Metrics        |                                     |
| Settings       |                                     |
|                |                                     |
+----------------+-------------------------------------+
```

### 5.2. Main layout rules

- Use a persistent sidebar on desktop.
- Keep the main content area visually clean.
- Use cards to group related information.
- Keep consistent horizontal and vertical spacing.
- Avoid deeply nested visual containers.

---

## 6. Navigation

Recommended main navigation:

```text
BIDACHAT
│
├── Dashboard
├── Chatbots
├── Documents
├── Metrics
└── Settings
```

The active navigation item must use the BIDACHAT primary color.

User-facing labels may be displayed in Spanish while internal technical identifiers remain in English.

---

## 7. Core components

The initial BIDACHAT interface should reuse a limited set of consistent components.

### Required components

- `Button`
- `Input`
- `Select`
- `Textarea`
- `Card`
- `Modal`
- `Table`
- `Badge`
- `Alert`
- `Sidebar`
- `Navbar`
- `MetricCard`
- `ChatbotCard`
- `FileUpload`
- `ChatWindow`
- `ChatMessage`
- `LoadingState`
- `EmptyState`

Do not create a new component when an existing component can solve the same need.

---

## 8. Buttons and forms

### 8.1. Primary button

```text
Background: #14A8CE
Text:       #FFFFFF
```

Use for the most important action on a screen.

Examples:

- Create chatbot.
- Save configuration.
- Upload document.
- Send message.

### 8.2. Secondary button

```text
Background: #102033
Border:     #1E3A52
Text:       #F8FAFC
```

### 8.3. Danger button

```text
Background: #DC2626
Text:       #FFFFFF
```

Use only for destructive actions.

### 8.4. Button states

Every interactive button should support:

- Default.
- Hover.
- Focus.
- Disabled.
- Loading.

### 8.5. Form fields

Form controls should include:

- Visible label.
- Clear placeholder when useful.
- Focus state.
- Validation error.
- Disabled state.
- Supporting text only when needed.

---

## 9. Cards and metrics

Cards will be used to display chatbots, metrics, documents and configuration groups.

### Card style

```text
Background:    #102033
Border:        #1E3A52
Border radius: 12px
```

### Chatbot card example

```text
+----------------------------------+
| ECDC 2024               ● Active |
|                                  |
| Assistant for dashboard queries  |
|                                  |
| Conversations        1,248       |
| Users                  892       |
|                                  |
| [ Edit ]        [ Test ]         |
+----------------------------------+
```

### Metric cards

Metric cards should prioritize:

1. Metric name.
2. Main value.
3. Optional variation or trend.
4. Supporting information.

Avoid decorative charts when they do not provide additional meaning.

---

## 10. System states

Use semantic colors consistently.

```text
Success     #10B981
Warning     #F07942
Error       #DC2626
Information #14A8CE
```

Common statuses:

- `Active`
- `Inactive`
- `Processing`
- `Ready`
- `Error`
- `Disabled`

Status colors should not be the only way of communicating meaning. Always include text.

---

## 11. Chat interface

The chatbot interface is one of the core elements of BIDACHAT.

### 11.1. Basic structure

```text
+--------------------------------+
| BIDACHAT                       |
| Dashboard assistant            |
+--------------------------------+
|                                |
| Bot: Hello, how can I help?    |
|                                |
|                    User: ...   |
|                                |
| Bot: ...                       |
|                                |
+--------------------------------+
| Ask a question...          >   |
+--------------------------------+
```

### 11.2. Required states

The chat interface should support:

- User message.
- Assistant message.
- Loading state.
- Error message.
- Empty conversation state.
- Message input.
- Send action.
- Optional references or sources when required by the response design.

### 11.3. Processing feedback

While the application processes a query, the user must receive visible feedback.

Example:

```text
Analyzing dashboard information...
```

---

## 12. Embedded widget

The chatbot widget will be integrated into BI-DATA dashboards.

```text
BI-DATA Dashboard
       │
       │ JavaScript Widget
       ▼
+--------------------+
| BIDACHAT           |
|                    |
| Conversation       |
|                    |
| Question...    >   |
+--------------------+
```

### Widget rules

- Must visually identify BIDACHAT.
- Must adapt to the available dashboard space.
- Must not depend on the host application framework.
- Must keep the conversation readable.
- Must provide loading and error feedback.
- Must preserve the visual identity without competing with dashboard content.

---

## 13. Responsive design

The interface should adapt to three main ranges.

```text
Desktop
>= 1024px

Tablet
768px - 1023px

Mobile
< 768px
```

### Desktop

- Sidebar visible.
- Multi-column cards when space allows.
- Full tables and metric layouts.

### Tablet

- Reduced sidebar.
- Fewer columns.
- Flexible card widths.

### Mobile

- Collapsible navigation.
- Single-column content.
- Full-width forms and cards.
- Horizontal scrolling only when unavoidable.

---

## 14. Spacing and borders

Use a limited spacing scale:

```text
4px
8px
12px
16px
24px
32px
```

Recommended border radii:

```text
8px  -> Inputs
10px -> Buttons
12px -> Cards
```

---

## 15. Iconography

Use a single icon style across the administration interface.

Recommended characteristics:

- Outline style.
- Simple geometry.
- Consistent stroke width.
- No unnecessary 3D effects.
- No mixed icon families within the same interface.

Icons must support text, not replace important labels.

---

## 16. User feedback

Every important asynchronous action should provide visible feedback.

Required cases:

```text
Document upload
Document processing
RAG processing
Chat response
Chatbot creation
Chatbot update
Chatbot deletion
```

General flow:

```text
User action
    |
    v
Loading / Processing
    |
    +------> Success
    |
    +------> Error
```

Success messages should be concise.

Error messages should explain what happened without exposing internal technical details.

---

## 17. Design rules

- Use BI-DATA turquoise as the main BIDACHAT identity color.
- Maintain the dark visual base of the administration interface.
- Keep typography, spacing and component behavior consistent.
- Avoid unnecessary decorative elements.
- Reuse existing components before creating new ones.
- Keep the interface simple and focused on project requirements.
- User-facing text may be displayed in Spanish.
- Technical identifiers must remain in English.
- Every asynchronous action must provide visual feedback.
- The embedded chatbot must adapt to the host dashboard.
- Do not introduce additional visual frameworks unless they solve a concrete project requirement.
- BIDACHAT must be referred to as a **web application**, not as a platform.

---

## 18. Initial implementation reference

The visual layer will be implemented with:

```text
Next.js
TypeScript
Tailwind CSS
```

This document defines the initial BIDACHAT visual rules and may be updated only when a new interface requirement is identified during development.
