import { useQuery } from "@tanstack/react-query";
import { useT } from "#/lib/i18n";

export function DemoBanner() {
  const t = useT();
  const { data } = useQuery({
    queryKey: ["demo-status"],
    queryFn: async () => {
      const response = await fetch("/demo/status");
      if (!response.ok) return { enabled: false };
      return response.json() as Promise<{ enabled: boolean }>;
    },
    staleTime: Number.POSITIVE_INFINITY,
    retry: false,
  });
  if (!data?.enabled) return null;
  return (
    <aside className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1 border-b bg-amber-50 px-4 py-2 text-xs text-amber-950 dark:bg-amber-950 dark:text-amber-100">
      <p>{t.demo.notice}</p>
      <a className="shrink-0 font-semibold underline underline-offset-2" href="/logout">
        {t.demo.switchUser}
      </a>
    </aside>
  );
}
