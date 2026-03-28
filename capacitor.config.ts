import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.secuexam.mobile",
  appName: "SecuExam",
  webDir: "secuexam_app",
  server: {
    url: "http://10.107.134.59:5050",
    cleartext: true,
    allowNavigation: [
      "10.107.134.59",
      "*.loca.lt",
      "*.ngrok-free.app"
    ]
  },
  android: {
    allowMixedContent: true
  }
};

export default config;
