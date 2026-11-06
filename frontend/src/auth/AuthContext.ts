import { createContext } from "react";

export interface AuthContextType {
  authenticated: boolean;
  ready: boolean;
  username: string;
  error: string | null;
  refreshToken: () => Promise<string>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(
  undefined,
);
