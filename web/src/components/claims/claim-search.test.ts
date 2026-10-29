import { describe, expect, it } from "vitest";
import { Queue, SortField } from "#/gen/cashflow/claim/v1/claim_pb";
import { advancedCount, effectiveSort, listRequest, validateClaimSearch } from "./claim-search";

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

describe("advanced filters", () => {
  it("keep valid values from the URL", () => {
    const search = validateClaimSearch({
      scc: "Internt",
      from: "2026-01-01",
      to: "not a date",
      pay: 12,
      attested: true,
      flagged: "yes",
    });
    expect(search).toMatchObject({ scc: "Internt", from: "2026-01-01", pay: 12, attested: true });
    expect(search.to).toBeUndefined();
    expect(search.flagged).toBeUndefined();
    expect(advancedCount(search)).toBe(4);
  });

  it("become the request's filter; a fixed owner wins over the URL's", () => {
    const request = listRequest({ owner: "anna" }, { owner: "bertil", line: "Fika", paid: false, pay: 7 });
    expect(request.filter).toMatchObject({ owner: "anna", budgetLine: "Fika", paid: false, paymentId: 7n });
  });
});
