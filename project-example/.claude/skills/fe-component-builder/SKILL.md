---
name: fe-component-builder
description: Use when building React components from plain text descriptions, Figma specs, or mockups. Triggers on requests like "tạo component", "build a card component", "implement this UI", "create a button with these styles", or any task that involves translating a visual/text description into a React component. Always invoke this skill before writing any React component code.
---

# FE Component Builder

Build React components from plain text descriptions, Figma specs, or rough mockups.

## Process

### 1. Clarify before coding
Before writing any code, confirm:
- **Component name** — what is this called?
- **Props** — what data does it receive? What's optional vs required?
- **Variants** — does it have different states (loading, error, empty, disabled)?
- **Interactions** — hover, click, focus behaviors?

If the description is clear enough, skip asking and proceed — but call out any assumptions made.

### 2. Pick the right structure

| Scenario | Pattern |
|---|---|
| Pure display, no state | Functional component, no hooks |
| Has local UI state (open/close, hover) | useState inside component |
| Fetches data | Separate the fetch logic from the display component |
| Reused in many places | Export from `components/` with an index |

### 3. Component template

```tsx
interface ComponentNameProps {
  // required props first
  title: string
  // optional props last
  variant?: 'primary' | 'secondary'
  onClick?: () => void
}

export function ComponentName({ title, variant = 'primary', onClick }: ComponentNameProps) {
  return (
    <div>
      {/* implementation */}
    </div>
  )
}
```

### 4. Styling approach
- Default to **Tailwind CSS** unless the project uses something else
- Check existing components in the codebase for class patterns before inventing new ones
- Never inline styles unless dynamic (e.g., computed width/height)

### 5. Accessibility
Every component must have:
- Semantic HTML (`button` not `div` for clickable things)
- `aria-label` on icon-only buttons
- Keyboard navigation for interactive elements

## Output format

Always deliver:
1. The component file with correct path (e.g., `src/components/Card/Card.tsx`)
2. A usage example showing how to import and use it
3. List any assumptions made about props or behavior

## Example

**Input:** "tạo một Card component hiển thị tên sản phẩm, giá, và nút Add to Cart"

**Output:**
```tsx
// src/components/ProductCard/ProductCard.tsx
interface ProductCardProps {
  name: string
  price: number
  onAddToCart: () => void
}

export function ProductCard({ name, price, onAddToCart }: ProductCardProps) {
  return (
    <div className="rounded-lg border p-4 shadow-sm">
      <h3 className="font-semibold text-gray-900">{name}</h3>
      <p className="mt-1 text-lg font-bold">${price.toFixed(2)}</p>
      <button
        onClick={onAddToCart}
        className="mt-3 w-full rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
      >
        Add to Cart
      </button>
    </div>
  )
}
```

**Usage:**
```tsx
<ProductCard name="Wireless Headphones" price={99.99} onAddToCart={() => addItem(product)} />
```
