import { TanStackDevtools } from "@tanstack/react-devtools";
import { ReactQueryDevtoolsPanel } from "@tanstack/react-query-devtools";
import { TanStackRouterDevtoolsPanel } from "@tanstack/react-router-devtools";

/** Router and Query devtools in one panel. Loaded only in development (see __root.tsx). */
export default function Devtools() {
  return (
    <TanStackDevtools
      // Middle right keeps the trigger clear of the user menu and the toasts.
      config={{ position: "middle-right" }}
      plugins={[
        { name: "Router", render: <TanStackRouterDevtoolsPanel /> },
        { name: "Query", render: <ReactQueryDevtoolsPanel /> },
      ]}
    />
  );
}
