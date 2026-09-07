const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function request(path, options = {}, token) {
  const headers = new Headers(options.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || "Request failed");
  return body;
}

export const api = {
  async authenticate(mode, email, password) {
    const path = mode === "register" ? "/api/v1/auth/register" : "/api/v1/auth/login";
    return request(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
  },
  documents(token) {
    return request("/api/v1/documents", {}, token);
  },
  async upload(files, token) {
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));
    return request("/api/v1/documents/upload-multiple", { method: "POST", body: formData }, token);
  },
  deleteDocument(id, token) {
    return request(`/api/v1/documents/${id}`, { method: "DELETE" }, token);
  },
  chat(payload, token) {
    return request("/api/v1/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }, token);
  },
};
