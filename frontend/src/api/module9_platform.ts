import client from "./client";

export const authApi = {
  login: (username: string, password: string) =>
    client.post("/auth/login", { username, password }),
  me: () => client.get("/auth/me"),
  changePassword: (old_password: string, new_password: string) =>
    client.post("/auth/change-password", { old_password, new_password }),
};

export const userApi = {
  list: (params?: { page?: number; page_size?: number; role?: string }) =>
    client.get("/users", { params }),
  create: (data: object) => client.post("/users", data),
  get: (id: string) => client.get(`/users/${id}`),
  update: (id: string, data: object) => client.put(`/users/${id}`, data),
  delete: (id: string) => client.delete(`/users/${id}`),
};

export const auditApi = {
  query: (params?: { page?: number; page_size?: number; user_id?: string; action?: string; resource_type?: string }) =>
    client.get("/audit", { params }),
};
