import { describe, expect, it } from "vitest";
import { Queue, SortField } from "#/gen/cashflow/claim/v1/claim_pb";
import { effectiveSort, listRequest, validateClaimSearch } from "./claim-search";

describe("validateClaimSearch", () => {
  it("keeps valid values and drops unknown or invalid ones", () => {
    expect(
      validateClaimSearch({ q: "pizza", kind: "invoice", sort: "amount", desc: true, page: 3, cc: "Ada", junk: 1 }),
    ).toEqual({ q: "pizza", kind: "invoice", sort: "amount", desc: true, page: 3, cc: "Ada" });
    expect(validateClaimSearch({ q: "  ", kind: "receipt", sort: "price", desc: "yes", page: 1.5 })).toEqual({
      q: undefined,
      kind: undefined,
      cc: undefined,
      sort: undefined,
      desc: undefined,
      page: undefined,
    });
  });

  it("treats page 1 as the default", () => {
    expect(validateClaimSearch({ page: 1 }).page).toBeUndefined();
  });
});

describe("effectiveSort", () => {
  it("lists queues oldest first and other lists newest first", () => {
    expect(effectiveSort({ queue: "attest" }, {})).toEqual({ sort: "date", desc: false });
    expect(effectiveSort({ mine: true }, {})).toEqual({ sort: "date", desc: true });
    expect(effectiveSort({ queue: "attest" }, { sort: "amount", desc: true })).toEqual({ sort: "amount", desc: true });
  });
});

describe("listRequest", () => {
  it("maps the URL state to the API request", () => {
    const req = listRequest({ queue: "pay" }, { q: "kaffe", sort: "owner", page: 2 });
    expect(req).toMatchObject({ queue: Queue.PAY, query: "kaffe", sort: SortField.OWNER, page: 2, mine: false });
  });
});
