import { TransportProvider } from "@connectrpc/connect-query";
import { HotkeysProvider } from "@tanstack/react-hotkeys";
import { type QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createRootRouteWithContext, HeadContent, Outlet, Scripts } from "@tanstack/react-router";
import { lazy, type ReactNode, Suspense } from "react";
import { Toaster } from "#/components/ui/sonner";
import { TooltipProvider } from "#/components/ui/tooltip";
import { transport } from "#/lib/rpc";
import styles from "#/styles.css?url";

// Runs before first paint so a dark-mode user never sees a white flash, and
// sets the document language. Mirrors lib/theme.ts and lib/i18n.
const BOOT_SCRIPT = `try{var t=localStorage.getItem("cashflow-theme");if(t==="dark"||(t!=="light"&&matchMedia("(prefers-color-scheme: dark)").matches))document.documentElement.classList.add("dark");var l=localStorage.getItem("cashflow-locale");document.documentElement.lang=l==="en"||(!l&&navigator.language.startsWith("en"))?"en":"sv"}catch(e){}`;

const Devtools = import.meta.env.DEV ? lazy(() => import("#/components/layout/devtools")) : () => null;

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { name: "theme-color", content: "#0f2a20" },
      { title: "Cashflow" },
    ],
    links: [
      { rel: "stylesheet", href: styles },
      { rel: "icon", href: "/favicon.svg", type: "image/svg+xml" },
    ],
  }),
  shellComponent: RootDocument,
  component: RootComponent,
});

function RootDocument({ children }: { children: ReactNode }) {
  return (
    <html lang="sv" suppressHydrationWarning>
      <head>
        {/* biome-ignore lint/security/noDangerouslySetInnerHtml: a static string, see BOOT_SCRIPT */}
        <script dangerouslySetInnerHTML={{ __html: BOOT_SCRIPT }} />
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();
  return (
    <TransportProvider transport={transport}>
      <QueryClientProvider client={queryClient}>
        <HotkeysProvider>
          <TooltipProvider>
            <Outlet />
            <Toaster richColors position="bottom-right" />
          </TooltipProvider>
        </HotkeysProvider>
        <Suspense>
          <Devtools />
        </Suspense>
      </QueryClientProvider>
    </TransportProvider>
  );
}
