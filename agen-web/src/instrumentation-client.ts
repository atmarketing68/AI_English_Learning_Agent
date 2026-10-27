// Runs before the app becomes interactive (Next.js client instrumentation).
import { initAnalytics } from './lib/analytics';
import { initPwa } from './lib/pwa';
import { captureSignupSource } from './lib/signupSource';

initAnalytics();
initPwa();
captureSignupSource();
