import { QueryClient } from "@tanstack/react-query";
import { createRouter } from "@tanstack/react-router";
import { NotFound, RouteError } from "#/components/layout/states";
import { routeTree } from "./routeTree.gen";

export function getRouter() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
  });
  return createRouter({
    routeTree,
    context: { queryClient },
    scrollRestoration: true,
    // Loaders run on hover, so pages usually open with their data ready.
    defaultPreload: "intent",
    // Query's cache decides freshness, not the router's.
    defaultPreloadStaleTime: 0,
    defaultErrorComponent: RouteError,
    defaultNotFoundComponent: NotFound,
  });
}

declare module "@tanstack/react-router" {
  interface Register {
    router: ReturnType<typeof getRouter>;
  }
}
