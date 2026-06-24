import axios from "axios";
const client = axios.create({ baseURL: "/api/v1", timeout: 30_000 });
client.interceptors.request.use((c) => {
  const t = localStorage.getItem("demo_token");
  if (t) c.headers.Authorization = `Bearer ${t}`;
  return c;
});
client.interceptors.response.use((r) => r, (e) => {
  if (e.response?.status === 401) { localStorage.removeItem("demo_token"); window.location.href = "/login"; }
  return Promise.reject(e);
});
export default client;
