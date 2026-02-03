import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";
import { loadAuthTokenFromStorage } from "./api/client";
import { DEMO_MODE } from "./config/demo";
import { AppErrorBoundary } from "./components/AppErrorBoundary";

loadAuthTokenFromStorage();

createRoot(document.getElementById("root")!).render(
  <AppErrorBoundary>
    <App />
  </AppErrorBoundary>,
);

if (
  "serviceWorker" in navigator &&
  (import.meta.env.PROD || window.location.hostname === "localhost")
) {
  const registerServiceWorker = () => {
    navigator.serviceWorker
      .register("/service-worker.js")
      .catch((error) => {
        console.error("Service worker registration failed", error);
      });
  };

  if (DEMO_MODE) {
    navigator.serviceWorker.getRegistrations().then((regs) => {
      regs.forEach((registration) => registration.unregister());
    });
  } else if (document.readyState === "complete") {
    registerServiceWorker();
  } else {
    window.addEventListener("load", registerServiceWorker, { once: true });
  }
}
