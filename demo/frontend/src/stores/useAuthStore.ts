import { create } from "zustand";
interface User { id: string; username: string; display_name: string; role: string; }
interface AuthState { user: User | null; isAuthenticated: boolean; login: (token: string, user: User) => void; logout: () => void; }
export const useAuthStore = create<AuthState>((set) => ({
  user: null, isAuthenticated: !!localStorage.getItem("demo_token"),
  login: (token, user) => { localStorage.setItem("demo_token", token); set({ user, isAuthenticated: true }); },
  logout: () => { localStorage.removeItem("demo_token"); set({ user: null, isAuthenticated: false }); },
}));
