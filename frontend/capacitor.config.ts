import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.basketcompare.app",
  appName: "BasketCompare",
  webDir: ".next",
  server: {
    // Use CAP_SERVER_URL for a physical iPhone (e.g. http://192.168.1.20:3000).
    // Defaults to localhost so the iOS simulator can load your local Next.js app.
    url: process.env.CAP_SERVER_URL || "http://127.0.0.1:3000",
    cleartext: true,
  },
};

export default config;
