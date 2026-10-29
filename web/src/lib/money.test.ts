import { describe, expect, it } from "vitest";
import { formatOre } from "./money";

// Intl uses a narrow no-break space as the Swedish thousands separator.
const nbsp = (s: string) => s.replace(/ /g, " ");

describe("formatOre", () => {
  it("formats Swedish kronor with comma decimals and grouped thousands", () => {
    expect(formatOre(123450n, "sv")).toBe(nbsp("1 234,50"));
  });

  it("formats English with a decimal point", () => {
    expect(formatOre(123450n, "en")).toBe("1,234.50");
  });

  it("pads single-digit öre", () => {
    expect(formatOre(1005n, "sv")).toBe("10,05");
    expect(formatOre(0n, "sv")).toBe("0,00");
  });

  it("keeps precision beyond floating point range", () => {
    expect(formatOre(900719925474099199n, "en")).toBe("9,007,199,254,740,991.99");
  });

  it("marks negative amounts with a minus sign", () => {
    expect(formatOre(-250n, "sv")).toBe("−2,50");
  });
});
