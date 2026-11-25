import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/" },
    // Replace with the verified production origin before launch.
    sitemap: "https://nil.ai/sitemap.xml",
  };
}
