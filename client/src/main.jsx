import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.jsx";
import { BrowserRouter, useNavigate } from "react-router-dom";
import { store } from "./app/store.js";
import { Provider } from "react-redux";
import { ClerkProvider } from "@clerk/clerk-react";

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

if (!PUBLISHABLE_KEY) {
  throw new Error("Missing Publishable Key");
}

// Wrap ClerkProvider inside BrowserRouter so it can use React Router's
// navigate for internal routing (sign-in sub-steps, redirects, etc.)
const ClerkWithRouter = () => {
  const navigate = useNavigate();
  return (
    <ClerkProvider
      publishableKey={PUBLISHABLE_KEY}
      routerPush={(to) => navigate(to)}
      routerReplace={(to) => navigate(to, { replace: true })}
    >
      <Provider store={store}>
        <App />
      </Provider>
    </ClerkProvider>
  );
};

createRoot(document.getElementById("root")).render(
  <BrowserRouter>
    <ClerkWithRouter />
  </BrowserRouter>
);
