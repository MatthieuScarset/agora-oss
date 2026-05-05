# Dashboard

Next.js / React (widgets UI)

## Local Docker Service

The local stack runs a Node.js development container on port 3000.

- Path mounted in container: `apps/dashboard`
- Expected app entrypoint: `package.json`
- If no `package.json` exists yet, the container stays idle and logs a reminder.
