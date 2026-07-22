# Internationalization (i18n)

Internationalization is a fancy word for providing support for multiple languages. Cashflow uses i18n to provide
swedish and english translations of the user interface.

Translations are defined in JSON files (one per language) as key-value pairs. These exist in the `src/lib/i18n`
directory.

## Initialization

i18n is initialized once in `src/lib/i18n/index.ts`, which registers the translation files and sets the starting
locale from the browser's language. This file is imported by the root layout so it runs before any page renders.

The root layout's `load` function (`src/routes/+layout.ts`) then calls `waitLocale()` to ensure the translation
JSON is fully loaded before SvelteKit renders anything — without this, `$_()` would return the raw key on first
render while the JSON was still being fetched.

You don't need to touch either file when adding new strings.

## Adding a new string

To add a new string, simply add a new key-value pair in both the `en.json` and `sv.json` files.
```json filename="en.json"
{
  "new_expense.form.description.label": "Description"
}
```
```json filename="sv.json"
{
  "new_expense.form.description.label": "Beskrivning"
}
```

## Using translations in code

The easiest way to use translations is to use the Svelte store provided by `i18n-svelte`:

```svelte
<script lang="ts">
    import { _ } from 'svelte-i18n';
</script>

<label>{$_('new_expense.form.description.label')}</label>
```

## Testing coverage
In `i18n.test.ts` there is a test that checks that all keys in `en.json` also exist in `sv.json` (and vice versa). By
running `bun run test` you can ensure that you have translated all keys.