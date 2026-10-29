import { Avatar, AvatarFallback, AvatarImage } from "#/components/ui/avatar";
import { useProfilePicture } from "#/lib/profile-pictures";
import { cn } from "#/lib/utils";

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

/** A person's rfinger picture, or their initials while it loads or if there is none. */
export function UserAvatar({
  name,
  username,
  className,
  size = "md",
}: {
  name: string;
  username?: string;
  className?: string;
  size?: "sm" | "md";
}) {
  const picture = useProfilePicture(username);
  return (
    <Avatar className={cn("rounded-lg", size === "sm" ? "size-6 text-[10px]" : "size-8")}>
      {picture && <AvatarImage src={picture} alt="" className="rounded-lg object-cover" />}
      <AvatarFallback className={cn("rounded-lg font-medium", className)}>{initials(name)}</AvatarFallback>
    </Avatar>
  );
}
