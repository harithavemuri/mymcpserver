# React + TypeScript Coding Standards

> **Note**: These standards complement the project's [Global Development Rules](./GLOBAL_RULES.md). Please review them for additional guidelines on code modifications, version control, and other development practices.

## Table of Contents
1. [General Guidelines](#general-guidelines)
2. [TypeScript Usage](#typescript-usage)
3. [Component Structure](#component-structure)
4. [State Management](#state-management)
5. [Styling](#styling)
6. [Testing](#testing)
7. [Performance](#performance)

## General Guidelines
- Use functional components with React Hooks
- Follow the Single Responsibility Principle
- Keep components small and focused
- Use meaningful component and variable names
- Follow the DRY (Don't Repeat Yourself) principle
- Use ESLint and Prettier for code formatting
- Follow the [Code Modifications](./GLOBAL_RULES.md#code-modifications) guidelines in GLOBAL_RULES.md

## TypeScript Usage
- Enable `strict` mode in `tsconfig.json`
- Use interfaces for props and state types
- Prefer `type` over `interface` for React props and state
- Use TypeScript utility types (Partial, Pick, Omit, etc.)
- Avoid using `any` type
- Use `readonly` for immutable props and state
- Use enums or const assertions for fixed sets of values

## Component Structure
```typescript
// Component with props and state
type ComponentProps = {
  id: string;
  title: string;
  isActive: boolean;
  onAction: (id: string) => void;
};

const MyComponent: React.FC<ComponentProps> = ({
  id,
  title,
  isActive,
  onAction,
}) => {
  const [count, setCount] = useState<number>(0);

  const handleClick = useCallback(() => {
    onAction(id);
    setCount(prev => prev + 1);
  }, [id, onAction]);

  return (
    <div className={`my-component ${isActive ? 'active' : ''}`}>
      <h2>{title}</h2>
      <p>Count: {count}</p>
      <button onClick={handleClick}>
        Click me
      </button>
    </div>
  );
};

export default React.memo(MyComponent);
```

## State Management
- Use `useState` for local component state
- Use `useReducer` for complex state logic
- Use Context API for global state when appropriate
- Use Redux Toolkit for complex application state
- Memoize callbacks and values with `useCallback` and `useMemo`
- Use custom hooks for reusable logic

## Styling
- Use CSS Modules or styled-components with TypeScript
- Follow BEM naming convention for CSS classes
- Use CSS variables for theming
- Keep styles co-located with components
- Use responsive design principles

## Testing
- Write unit tests with Jest and React Testing Library
- Test user interactions, not implementation details
- Use `@testing-library/user-event` for user interactions
- Write integration tests for critical user flows
- Aim for at least 80% test coverage

## Performance
- Use `React.memo` for pure components
- Use `useCallback` and `useMemo` to prevent unnecessary re-renders
- Implement code splitting with React.lazy and Suspense
- Optimize images and assets
- Use the production build for performance testing

## File Structure
```
src/
  components/
    Common/
      Button/
        Button.tsx
        Button.module.css
        Button.test.tsx
        index.ts
  features/
    FeatureName/
      components/
      hooks/
      types.ts
      index.ts
  hooks/
    useCustomHook.ts
  utils/
    helpers.ts
    api.ts
  types/
    index.ts
  App.tsx
  index.tsx
```

## Naming Conventions
- Component files: `PascalCase.tsx`
- Non-component files: `camelCase.ts`
- Test files: `ComponentName.test.tsx`
- Custom hooks: `useFeatureName.ts`
- Type definitions: `types.ts` or `*.types.ts`

## Best Practices
- Keep components small and focused
- Extract logic into custom hooks
- Use TypeScript for all new code
- Write self-documenting code with meaningful names
- Keep the component API simple and predictable
- Handle loading and error states
- Implement proper error boundaries
- Use React DevTools for debugging
- Profile performance with React Profiler
