# Money values

We want to avoid floating point errors when working with monetary amounts. Therefore
we use [dinero.js](https://www.dinerojs.com/) to represent all money values internally.

You can create a money value using the `dinero` function, which takes an object
parameter with

- `amount`, an integer representing the amount in the smallest units (for SEK
  this is öre)
- `currency`, a string representing the currency code, these can be imported as
  constants from `dinero.js/currencies` (e.g. `SEK`, `USD`, etc.).

Dinero objects are immutable, when using them you should use the built in
arithmetic functions and comparisons.

```ts
import { dinero, add, isZero } from "dinero.js";

const oneHundredSek = dinero({ amount: 10000, currency: SEK });
const fiftySek = dinero({ amount: 5000, currency: SEK });
const total = add(oneHundredSek, fiftySek);
console.log(isZero(total)); // false
```

To get a string representation of the money value, you can use the `toDecimal`
function, which will return a string with two decimal places.

```ts
import { dinero } from "dinero.js";
import { SEK } from "dinero.js/currencies";

const oneHundredSek = dinero({ amount: 10000, currency: SEK });

console.log(toDecimal(oneHundredSek)); // 100.00
```

In `$lib/money.ts` there are helper functions related to money, most importantly,
`fromDecimal` which takes a string representation and converts it to a dinero object.

```ts
import { fromDecimal, sumDinero, formatDineroAmount } from "$lib/money";

const oneHundredSek = fromDecimal("100.00", "SEK");
const fiftySek = fromDecimal("50.00", "SEK");
const total = sumDinero([oneHundredSek, fiftySek]);
console.log(formatDineroAmount(total)); // 150.00
```
