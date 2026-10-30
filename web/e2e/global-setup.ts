import { execFileSync } from "node:child_process";

/** Every run starts from the seed: the same claims at every stage. */
export default function globalSetup() {
  execFileSync("go", ["run", "./cmd/seed", "-reset"], { cwd: "../server", stdio: "inherit" });
}
