import { createClient } from "@connectrpc/connect";
import { Batcher } from "@tanstack/pacer";
import { useQuery } from "@tanstack/react-query";
import { UserService } from "#/gen/cashflow/user/v1/user_pb";
import { transport } from "#/lib/rpc";

type Request = { username: string; resolve: (url: string | null) => void };

const client = createClient(UserService, transport);

/**
 * Avatars across a page each ask for their own picture; the batcher gathers
 * those asks for a moment and sends one request for all of them.
 */
const batcher = new Batcher<Request>(
  (requests) => {
    const usernames = [...new Set(requests.map((r) => r.username))];
    client
      .getProfilePictures({ usernames })
      .then((res) => {
        for (const r of requests) r.resolve(res.urls[r.username] ?? null);
      })
      // No picture is fine: the avatar shows initials.
      .catch(() => {
        for (const r of requests) r.resolve(null);
      });
  },
  { wait: 20, maxSize: 100 },
);

/** A user's profile picture URL, or null; cached for the session. */
export function useProfilePicture(username: string | undefined) {
  return useQuery({
    queryKey: ["profile-picture", username],
    queryFn: () => new Promise<string | null>((resolve) => batcher.addItem({ username: username ?? "", resolve })),
    enabled: Boolean(username),
    staleTime: Number.POSITIVE_INFINITY,
    gcTime: 60 * 60 * 1000,
  }).data;
}
