# Testing (Frontend)
The Svelte frontend mainly uses Vitest for testing, with test files typically being located next to their corresponding
components or files. To run the tests:
```bash
bun run test 
```
You can also run tests in a web UI by using:
```bash
bun run test:ui
```

> [!WARNING]
> It's easy to confuse `bun run test` with `bun test`, but they are not the same.
> `bun run test` executes the `test` script (Vitest), which loads `vite.config.ts`
> and the SvelteKit plugin, so `$app/*` imports, jsdom, and i18n all work.
> `bun test` is Bun's own test runner — it ignores the Vite config, so tests fail
> with errors like `Cannot find module '$app/environment'`. Always use `bun run test`.

## Utility functions
There are a few utility functions you can use in your tests, these exist in `src/lib/test/helpers.ts` (importable as `$lib/test/helpers`).

### i18n
If tests require internationalization (multiple languages) you need to initialize i18n; for this you can use the `setupI18n` function. For example:
```ts
import { afterEach, beforeAll, beforeEach, vi } from 'vitest';
import { setupI18n } from '$lib/test/helpers';

beforeAll(async () => {
	await setupI18n('sv');
});
```

> [!TIP]
> `beforeAll` runs once per file — ideal for one-time setup like i18n. Use
> `beforeEach` only when each test needs a fresh start. Remember to `await`.

### freezeTime
If your tests involve time-sensitive logic, you can use the `freezeTime` function to mock the current time. The
`freezeTime` function takes a date string as an argument and freezes time to that specific date. For example:
```ts
import { afterEach, beforeEach, vi } from 'vitest';
import { freezeTime } from '$lib/test/helpers';

beforeEach(() => {
    freezeTime('2026-05-29');
});
```