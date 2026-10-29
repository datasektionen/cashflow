import { describe, expect, it } from "vitest";
import { formatOre, oreToInput, parseKronor } from "./money";

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

describe("parseKronor", () => {
  it("reads the ways people type amounts", () => {
    expect(parseKronor("1 234,50")).toBe(123450n);
    expect(parseKronor("1234.5")).toBe(123450n);
    expect(parseKronor("12 kr")).toBe(1200n);
    expect(parseKronor("0,05")).toBe(5n);
    expect(parseKronor("99")).toBe(9900n);
    expect(parseKronor(" 1 000")).toBe(100000n);
  });

  it("rejects anything that isn't an amount", () => {
    for (const bad of ["", "abc", "1,234,5", "1.005", "-5", "1e3"]) expect(parseKronor(bad)).toBeUndefined();
  });

  it("round-trips with oreToInput", () => {
    expect(oreToInput(123450n, "sv")).toBe("1234,50");
    expect(parseKronor(oreToInput(5n, "sv"))).toBe(5n);
  });
});
