const BLOCKED_USER_AGENTS = [
  "ahrefsbot",
  "amazonbot",
  "applebot-extended",
  "baiduspider",
  "blexbot",
  "bytespider",
  "ccbot",
  "claudebot",
  "dataforseobot",
  "dotbot",
  "facebookexternalhit",
  "gptbot",
  "mj12bot",
  "petalbot",
  "semrushbot",
  "serpstatbot",
  "yandexbot",
];

const SCAN_PATH_PATTERNS = [
  /^\/\.env/i,
  /^\/\.git/i,
  /^\/admin/i,
  /^\/cgi-bin/i,
  /^\/phpmyadmin/i,
  /^\/vendor\//i,
  /^\/wp-/i,
  /^\/wordpress/i,
  /^\/xmlrpc\.php/i,
];

const STATIC_PATH_PATTERN = /\.(css|js|map|svg|png|jpg|jpeg|gif|webp|ico|txt|woff|woff2)$/i;

function blockedResponse(status = 403) {
  return new Response("Forbidden", {
    status,
    headers: {
      "Cache-Control": "public, max-age=3600",
      "X-Robots-Tag": "noindex, nofollow, noarchive",
    },
  });
}

async function botGuard(request, context) {
  const url = new URL(request.url);
  const pathname = url.pathname;
  const userAgent = request.headers.get("user-agent")?.toLowerCase() ?? "";

  if (
    pathname === "/robots.txt" ||
    pathname === "/sitemap.xml" ||
    pathname.startsWith("/_next/static/") ||
    pathname.startsWith("/_next/image") ||
    STATIC_PATH_PATTERN.test(pathname)
  ) {
    return context.next();
  }

  if (SCAN_PATH_PATTERNS.some((pattern) => pattern.test(pathname))) {
    return blockedResponse(404);
  }

  if (BLOCKED_USER_AGENTS.some((bot) => userAgent.includes(bot))) {
    return blockedResponse();
  }

  const response = await context.next();

  if (pathname.startsWith("/api/") || pathname.startsWith("/player/")) {
    const headers = new Headers(response.headers);
    headers.set("X-Robots-Tag", "noindex, nofollow, noarchive");
    return new Response(response.body, {
      headers,
      status: response.status,
      statusText: response.statusText,
    });
  }

  return response;
}

export default botGuard;
