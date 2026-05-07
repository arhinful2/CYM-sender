import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.churchyouth.management',
  appName: 'CYM Sender',
  webDir: 'www',
  server: {
    // Loads your deployed Django app directly inside the Android shell.
    url: 'https://cym-sender.vercel.app',
    cleartext: false,
    androidScheme: 'https'
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 1200,
      launchAutoHide: true,
      backgroundColor: '#0d6efd',
      androidSplashResourceName: 'splash',
      showSpinner: false
    },
    StatusBar: {
      style: 'DARK',
      backgroundColor: '#0d6efd'
    }
  }
};

export default config;
