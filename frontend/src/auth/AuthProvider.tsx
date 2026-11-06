import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

import keycloak, { initializeKeycloak } from "./keycloak";
import { AuthContext } from "./AuthContext";
import { setAccessToken } from "../api/client";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authenticated, setAuthenticated] = useState(false);
  const [ready, setReady] = useState(false);
  const [username, setUsername] = useState("");
  const [error, setError] = useState<string | null>(null);

  const active = useRef(true);

  useEffect(() => {
    active.current = true;

    keycloak.onAuthSuccess = () => {
      if (keycloak.token) {
        setAccessToken(keycloak.token);
      }
    };

    keycloak.onAuthRefreshSuccess = () => {
      if (keycloak.token) {
        setAccessToken(keycloak.token);
      }
    };

    keycloak.onAuthLogout = () => {
      setAccessToken(undefined);
      setAuthenticated(false);
    };

    initializeKeycloak()
      .then((isAuthenticated) => {
        if (!active.current) return;

        setAuthenticated(isAuthenticated);

        if (isAuthenticated) {
          setAccessToken(keycloak.token);
          setUsername(
            String(keycloak.tokenParsed?.preferred_username ?? ""),
          );
        }

        setReady(true);
      })
      .catch((err: unknown) => {
        if (!active.current) return;

        setError(
          err instanceof Error ? err.message : "Authentication failed",
        );
        setReady(true);
      });

    return () => {
      active.current = false;
    };
  }, []);

  const refreshToken = useCallback(async (): Promise<string> => {
    if (!keycloak.authenticated) {
      throw new Error("User is not authenticated");
    }

    await keycloak.updateToken(30);

    if (!keycloak.token) {
      throw new Error("Unable to obtain an access token");
    }

    setAccessToken(keycloak.token);
    return keycloak.token;
  }, []);

  const logout = useCallback(() => {
    setAccessToken(undefined);

    void keycloak.logout({
      redirectUri: window.location.origin,
    });
  }, []);

  return (
    <AuthContext.Provider
      value={{
        authenticated,
        ready,
        username,
        error,
        refreshToken,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
