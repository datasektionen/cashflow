import { Avatar, AvatarFallback } from "#/components/ui/avatar";
import { cn } from "#/lib/utils";

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

/** Initials for now; rfinger profile pictures arrive with the claims pages. */
export function UserAvatar({ name, className }: { name: string; className?: string }) {
  return (
    <Avatar className="size-8 rounded-lg">
      <AvatarFallback className={cn("rounded-lg font-medium", className)}>{initials(name)}</AvatarFallback>
    </Avatar>
  );
}
