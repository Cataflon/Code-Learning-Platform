import { useQueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import * as authApi from "../api/auth.js";
import { getToken, setToken, setUnauthorizedHandler } from "../api/client.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState(null);
  // "loading" while we check a stored token after a page refresh.
  const [status, setStatus] = useState(getToken() ? "loading" : "ready");

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    setStatus("ready");
    queryClient.clear(); // never show one user's cached data to the next one
  }, [queryClient]);

  useEffect(() => {
    setUnauthorizedHandler(logout);
  }, [logout]);

  // After a refresh the token is still in localStorage: load the profile it belongs to.
  useEffect(() => {
    if (!getToken()) return;
    let cancelled = false;
    authApi
      .getMe()
      .then((me) => {
        if (!cancelled) {
          setUser(me);
          setStatus("ready");
        }
      })
      .catch(() => {
        if (!cancelled) logout();
      });
    return () => {
      cancelled = true;
    };
  }, [logout]);

  const login = useCallback(async (email, password) => {
    const { access_token: token } = await authApi.login(email, password);
    setToken(token);
    const me = await authApi.getMe();
    setUser(me);
    setStatus("ready");
    return me;
  }, []);

  const value = useMemo(
    () => ({ user, status, login, logout, setUser }),
    [user, status, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside <AuthProvider>");
  return value;
}

/** Where each role lands after signing in. */
export function homePathFor(user) {
  return user?.role === "teacher" ? "/courses" : "/dashboard";
}

// Exported for tests that need to provide a fixed auth state.
export { AuthContext };
