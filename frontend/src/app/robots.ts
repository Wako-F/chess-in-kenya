import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: ["GPTBot", "CCBot", "ClaudeBot", "Bytespider", "Applebot-Extended"],
        disallow: "/",
      },
      {
        userAgent: "*",
        disallow: ["/api/", "/player/"],
        crawlDelay: 10,
      },
    ],
  };
}
