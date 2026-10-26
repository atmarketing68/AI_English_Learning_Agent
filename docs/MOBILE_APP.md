# Ứng dụng di động gốc (Android / iOS) từ PWA hiện có — Capacitor

Web app AI AGENT ENGLISH đã là PWA (cài được, offline, web push). Để lên **Google Play / App Store**, đóng gói
chính web app đó bằng [Capacitor](https://capacitorjs.com): app gốc mở WebView tới `https://<tên-miền>` (chế độ
*remote URL*), nên **không phải viết lại giao diện** và mọi bản deploy web đều tự có trên app.

Việc này cần máy có Android Studio (Android) và macOS + Xcode (iOS) nên chủ dự án chạy ở máy mình; môi trường
cloud không build được app gốc. Các bước đã được chuẩn bị sẵn:

## 1. Cài Capacitor (một lần, trong `agen-web/`)
```bash
cd agen-web
npm i @capacitor/core @capacitor/app @capacitor/push-notifications @capacitor/splash-screen
npm i -D @capacitor/cli
cp ../docs/mobile/capacitor.config.ts.example capacitor.config.ts   # sửa server.url = tên miền thật
npx cap add android          # cần Android Studio
npx cap add ios              # cần macOS + Xcode
```

## 2. Cấu hình
- `capacitor.config.ts`: `server.url` trỏ tới web production (ví dụ `https://aiagentenglish.com`), `appId`
  dạng ngược tên miền (`com.aiagentenglish.app`), `appName` "AI AGENT ENGLISH".
- Icon/splash: đặt `icon.png` (1024×1024) và `splash.png` (2732×2732) vào `agen-web/resources/` rồi chạy
  `npx @capacitor/assets generate` (tạo đủ kích thước cho hai nền tảng).
- Web push trên app gốc: iOS WebView không nhận Web Push → dùng `@capacitor/push-notifications` (APNs/FCM).
  Backend có thể thêm kênh FCM sau; hiện web push vẫn hoạt động trên Android (Chrome) và trên PWA iOS 16.4+.

## 3. Build & chạy thử
```bash
npx cap sync
npx cap open android    # Android Studio → Run
npx cap open ios        # Xcode → Run (cần Apple Developer để lên TestFlight)
```

## 4. Phát hành
- **Android**: Android Studio → Build → Generate Signed Bundle (AAB) → Google Play Console (phí 25 USD một lần).
- **iOS**: Xcode → Product → Archive → App Store Connect (Apple Developer 99 USD/năm).
- Vì app chỉ là WebView tới web production, review của Apple có thể yêu cầu "tính năng gốc": push gốc
  (bước 2), chia sẻ (Share API) và đăng nhập đã có sẵn thường là đủ; nếu bị từ chối, bật chế độ *bundled*
  (`npm run build` tĩnh + `webDir`) thay cho `server.url`.

## 5. Những gì đã có sẵn trong web app
- `public/manifest` (manifest.ts), service worker `public/sw.js`, trang offline, biểu tượng ứng dụng.
- Giao diện đáp ứng điện thoại (tab bar dưới), vùng an toàn (`env(safe-area-inset-bottom)`).
- Đăng nhập, học, nói, nghe đều chạy trong WebView; micro cần quyền `RECORD_AUDIO` (Android) và
  `NSMicrophoneUsageDescription` (iOS) — khai báo trong `AndroidManifest.xml` / `Info.plist`.
