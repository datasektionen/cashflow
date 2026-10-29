/**
 * Swedish is the source of truth: its shape is the `Messages` type, so a key
 * missing from another language is a type error. Functions take parameters.
 */
export const sv = {
  nav: {
    groups: { mine: "Mitt", manage: "Hantera", insight: "Översikt" },
    overview: "Översikt",
    newExpense: "Nytt utlägg",
    newInvoice: "Ny faktura",
    attest: "Attestera",
    confirm: "Bekräfta kvitton",
    account: "Bokför",
    pay: "Betala",
    payments: "Utbetalningar",
    budget: "Budget",
    stats: "Statistik",
    fortnox: "Fortnox",
    profile: "Profil och bankuppgifter",
  },
  userMenu: {
    theme: "Tema",
    themes: { light: "Ljust", dark: "Mörkt", system: "System" },
    language: "Språk",
    shortcuts: "Kortkommandon",
    logout: "Logga ut",
  },
  overview: {
    greeting: (name: string) => `Hej ${name}`,
    title: "Dina utlägg",
    awaitingAttest: "Väntar på attest",
    awaitingPayment: "Väntar på utbetalning",
    paidThisYear: "Utbetalt i år",
    emptyTitle: "Inga utlägg än",
    emptyBody: "Ladda upp ett kvitto så sköter attestanter och kassör resten. Du ser varje steg här.",
    emptyAction: "Lägg till ett utlägg",
  },
  profile: {
    title: "Profil",
    bankTitle: "Bankuppgifter",
    bankDescription: "Hit betalas dina utlägg. Kassören ser uppgifterna när utbetalningen görs.",
    clearingNumber: "Clearingnummer",
    clearingHint: "4 eller 5 siffror, t.ex. 8327-9.",
    bankAccount: "Kontonummer",
    bankName: "Bank",
    save: "Spara",
    saved: "Bankuppgifterna sparades",
    missing: "Du har inga bankuppgifter än, så dina utlägg kan inte betalas ut.",
  },
  validation: {
    "clearing_number.digits": "Clearingnumret får bara innehålla siffror.",
    "clearing_number.required": "Fyll i clearingnummer.",
    "clearing_number.length": "Clearingnumret ska vara 4 eller 5 siffror.",
    "bank_account.digits": "Kontonumret får bara innehålla siffror.",
    "bank_account.required": "Fyll i kontonummer.",
    "bank_account.length": "Kontonumret får vara högst 13 siffror.",
    "bank_name.length": "Banknamnet får vara högst 30 tecken.",
    unknown: "Ogiltigt värde.",
  } as Record<string, string> & { unknown: string },
  shortcuts: {
    title: "Kortkommandon",
    description: "Tryck tangenterna efter varandra.",
    goTo: (page: string) => `Gå till ${page}`,
    help: "Visa kortkommandon",
    toggleSidebar: "Visa/dölj sidomenyn",
  },
  comingSoon: {
    title: "Inte klart än",
    body: "Den här sidan flyttas över från Cashflow 3 i en senare fas.",
  },
  errors: {
    title: "Något gick fel",
    retry: "Försök igen",
    notFoundTitle: "Sidan finns inte",
    notFoundBody: "Länken kan vara gammal, eller så har sidan flyttat.",
    home: "Till översikten",
    generic: "Något gick fel. Försök igen om en stund.",
  },
  money: { currency: "kr" },
};

export type Messages = typeof sv;
