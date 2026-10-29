import { Code, ConnectError, type Interceptor } from "@connectrpc/connect";
import { createConnectTransport } from "@connectrpc/connect-web";

/** Sends the browser through SSO and back to where it was. */
export function redirectToLogin() {
  const here = window.location.pathname + window.location.search;
  window.location.assign(`/login?return_to=${encodeURIComponent(here)}`);
}

// The session cookie is only checked by the server; an expired one surfaces as
// Unauthenticated on whatever call happens next.
const loginOnUnauthenticated: Interceptor = (next) => async (req) => {
  try {
    return await next(req);
  } catch (err) {
    if (ConnectError.from(err).code === Code.Unauthenticated) redirectToLogin();
    throw err;
  }
};

export const transport = createConnectTransport({
  baseUrl: "/api",
  useHttpGet: true,
  interceptors: [loginOnUnauthenticated],
});
