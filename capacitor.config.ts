import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.secuexam.mobile",
  appName: "SecuExam",
  webDir: "secuexam_app",
  server: {
    url: "https://secuexam-backend-production.up.railway.app",
    cleartext: false,
    allowNavigation: [
      "secuexam-backend-production.up.railway.app"
    ]
  },
  android: {
    allowMixedContent: false
  }
};

export default config;
