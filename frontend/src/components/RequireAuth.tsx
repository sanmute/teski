import { useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { getOnboardingStatus } from "@/api/onboarding";
import { DEMO_MODE } from "@/config/demo";
import { demoUser } from "@/demo/demoUser";
import { setAuthToken } from "@/api/client";

type RequireAuthProps = {
  children: JSX.Element;
  allowNotOnboarded?: boolean;
};

export function RequireAuth({ children, allowNotOnboarded = false }: RequireAuthProps) {
  if (DEMO_MODE) {
    // In demo mode we present a permanent signed-in session.
    if (typeof window !== "undefined") {
      window.localStorage.setItem("teski_demo_user", JSON.stringify(demoUser));
      setAuthToken("demo");
    }
    return children;
  }
  const token = localStorage.getItem("teski_token");
  const location = useLocation();
  const [checking, setChecking] = useState<boolean>(!allowNotOnboarded);
  const [onboarded, setOnboarded] = useState<boolean | undefined>(allowNotOnboarded ? true : undefined);

  useEffect(() => {
    let cancelled = false;
    if (!token) return;
    if (allowNotOnboarded) {
      setChecking(false);
      return;
    }

    setChecking(true);
    getOnboardingStatus()
      .then((res) => {
        if (!cancelled) setOnboarded(res.onboarded);
      })
      .catch((err) => {
        if (import.meta.env.DEV) {
          // eslint-disable-next-line no-console
          console.warn("[onboarding] status fetch failed, allowing access", err);
        }
        if (!cancelled) setOnboarded(true); // fail-open to avoid blocking users
      })
      .finally(() => {
        if (!cancelled) setChecking(false);
      });

    return () => {
      cancelled = true;
    };
  }, [token, allowNotOnboarded]);

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  if (!allowNotOnboarded && !checking && onboarded === false && location.pathname !== "/onboarding") {
    return <Navigate to="/onboarding" state={{ from: location }} replace />;
  }
  if (checking) {
    return null;
  }
  return children;
}
