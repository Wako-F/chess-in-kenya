const message = process.env.VERCEL_GIT_COMMIT_MESSAGE || "";
const author = process.env.VERCEL_GIT_COMMIT_AUTHOR_LOGIN || "";

if (author === "github-actions[bot]" || message.startsWith("Auto-update: Data processing results")) {
  console.log("Skipping Vercel build for automated data-only commit.");
  process.exit(0);
}

process.exit(1);
