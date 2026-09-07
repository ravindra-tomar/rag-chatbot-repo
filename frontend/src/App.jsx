import { useEffect, useRef, useState } from "react";
import { api } from "./api";

const initialMessages = [{
  role: "assistant",
  text: "Welcome to Atlas. Upload your policies or ask a question about the documents already in your workspace.",
  sources: [],
}];

function AuthScreen({ onAuth }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const result = await api.authenticate(mode, email, password);
      onAuth(result.access_token, email);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-visual">
        <div className="brand-mark">A</div>
        <p className="eyebrow">PRIVATE KNOWLEDGE WORKSPACE</p>
        <h1>Answers with a paper trail.</h1>
        <p className="hero-copy">Bring your team documents into one calm, searchable space and get grounded answers with sources attached.</p>
        <div className="signal-row"><span className="signal-dot" /> Gemini + Chroma retrieval online</div>
      </section>
      <section className="auth-card">
        <p className="eyebrow">ATLAS RAG</p>
        <h2>{mode === "login" ? "Welcome back" : "Create your workspace"}</h2>
        <p className="muted">{mode === "login" ? "Sign in to continue your research." : "Start with a secure personal workspace."}</p>
        <form onSubmit={submit} className="stack-form">
          <label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required placeholder="you@company.com" /></label>
          <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required minLength="8" placeholder="At least 8 characters" /></label>
          {error && <div className="error-banner">{error}</div>}
          <button className="primary-button" disabled={busy}>{busy ? "Connecting..." : mode === "login" ? "Sign in" : "Create account"}</button>
        </form>
        <button className="text-button" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}>
          {mode === "login" ? "Need an account? Create one" : "Already have an account? Sign in"}
        </button>
      </section>
    </main>
  );
}

function UploadPanel({ token, onUploaded }) {
  const inputRef = useRef(null);
  const [files, setFiles] = useState([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function upload(event) {
    event.preventDefault();
    if (!files.length) return;
    setBusy(true); setMessage(""); setError("");
    try {
      const result = await api.upload(files, token);
      const summary = result.documents.map((item) => `${item.filename}: ${item.status}`).join(" | ");
      setMessage(summary);
      setFiles([]);
      if (inputRef.current) inputRef.current.value = "";
      onUploaded();
    } catch (requestError) { setError(requestError.message); }
    finally { setBusy(false); }
  }

  return <form className="upload-panel" onSubmit={upload}>
    <div className="upload-copy"><span className="upload-icon">+</span><div><h3>Add knowledge</h3><p>Upload PDF or TXT files. Existing content is preserved, duplicates are skipped, and changed filenames are re-indexed.</p></div></div>
    <div className="upload-actions"><input ref={inputRef} type="file" accept=".pdf,.txt" multiple onChange={(event) => setFiles([...event.target.files])} /><button className="primary-button small" disabled={busy || !files.length}>{busy ? "Processing..." : `Upload ${files.length ? `(${files.length})` : "files"}`}</button></div>
    {message && <div className="success-banner">{message}</div>}
    {error && <div className="error-banner">{error}</div>}
  </form>;
}

function Documents({ token, documents, refresh }) {
  const [deleting, setDeleting] = useState("");
  async function remove(document) {
    if (!window.confirm(`Delete ${document.filename}?`)) return;
    setDeleting(document.doc_id);
    try { await api.deleteDocument(document.doc_id, token); await refresh(); }
    catch (error) { window.alert(error.message); }
    finally { setDeleting(""); }
  }
  return <section className="content-section"><div className="section-heading"><div><p className="eyebrow">LIBRARY</p><h2>Your documents</h2></div><span className="count-pill">{documents.length} files</span></div><div className="document-list">{documents.length ? documents.map((document) => <article className="document-row" key={document.doc_id}><div className="file-badge">{document.filename.toLowerCase().endsWith(".pdf") ? "PDF" : "TXT"}</div><div className="document-info"><strong>{document.filename}</strong><span>{document.chunk_count} chunks · {document.char_count.toLocaleString()} characters</span></div><button className="icon-button danger" onClick={() => remove(document)} disabled={deleting === document.doc_id} aria-label={`Delete ${document.filename}`}>{deleting === document.doc_id ? "..." : "Delete"}</button></article>) : <div className="empty-state"><strong>Your knowledge base is empty</strong><span>Upload a policy, handbook, or guide to start asking questions.</span></div>}</div></section>;
}

function Chat({ token }) {
  const [messages, setMessages] = useState(initialMessages);
  const [sessionId, setSessionId] = useState(null);
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function send(event) {
    event?.preventDefault();
    const message = value.trim();
    if (!message || busy) return;
    setValue(""); setError(""); setMessages((current) => [...current, { role: "user", text: message, sources: [] }]); setBusy(true);
    try { const result = await api.chat({ message, top_k: 4, session_id: sessionId }, token); setSessionId(result.session_id); setMessages((current) => [...current, { role: "assistant", text: result.answer, sources: result.sources || [] }]); }
    catch (requestError) { setError(requestError.message); }
    finally { setBusy(false); }
  }
  return <section className="chat-panel"><div className="chat-header"><div><p className="eyebrow">RESEARCH ASSISTANT</p><h2>Ask your workspace</h2></div><span className="live-pill"><span className="signal-dot" /> Live</span></div><div className="message-list">{messages.map((message, index) => <div className={`message ${message.role}`} key={`${message.role}-${index}`}><div className="message-label">{message.role === "assistant" ? "ATLAS" : "YOU"}</div><p>{message.text}</p>{message.sources?.length > 0 && <div className="sources"><span>Sources</span>{message.sources.map((source, sourceIndex) => <div className="source" key={`${source.doc_id}-${sourceIndex}`}><strong>{source.filename || "Document"}</strong><small>{source.preview || "Relevant retrieved passage"}</small></div>)}</div>}</div>)}{busy && <div className="message assistant"><div className="message-label">ATLAS</div><div className="typing"><i /><i /><i /></div></div>}</div><div className="prompt-area"><div className="suggestions"><button onClick={() => setValue("What does the WFH policy say?")}>WFH policy</button><button onClick={() => setValue("Summarize the security requirements")}>Security summary</button></div><form onSubmit={send} className="composer"><textarea value={value} onChange={(event) => setValue(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); send(event); } }} placeholder="Ask a question about your documents..." rows="2" /><button className="send-button" disabled={busy || !value.trim()} aria-label="Send message">Send</button></form>{error && <div className="error-banner">{error}</div>}</div></section>;
}

function App() {
  const [token, setToken] = useState(() => localStorage.getItem("atlas_token"));
  const [email, setEmail] = useState(() => localStorage.getItem("atlas_email") || "");
  const [view, setView] = useState("chat");
  const [documents, setDocuments] = useState([]);
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  async function refreshDocuments() { if (!token) return; setLoadingDocuments(true); try { const result = await api.documents(token); setDocuments(result.documents || []); } catch (error) { if (error.message.toLowerCase().includes("token")) logout(); } finally { setLoadingDocuments(false); } }
  function auth(nextToken, nextEmail) { localStorage.setItem("atlas_token", nextToken); localStorage.setItem("atlas_email", nextEmail); setToken(nextToken); setEmail(nextEmail); }
  function logout() { localStorage.removeItem("atlas_token"); localStorage.removeItem("atlas_email"); setToken(null); }
  useEffect(() => { refreshDocuments(); }, [token]);
  if (!token) return <AuthScreen onAuth={auth} />;
  return <div className="app-shell"><aside className="sidebar"><div className="sidebar-brand"><div className="brand-mark small-mark">A</div><span>ATLAS</span></div><div className="workspace-label">WORKSPACE</div><nav><button className={view === "chat" ? "nav-item active" : "nav-item"} onClick={() => setView("chat")}><span>+</span>Chat</button><button className={view === "documents" ? "nav-item active" : "nav-item"} onClick={() => setView("documents")}><span>▣</span>Documents <b>{documents.length}</b></button></nav><div className="sidebar-bottom"><div className="user-chip"><div className="avatar">{email[0]?.toUpperCase()}</div><div><strong>{email}</strong><span>Personal workspace</span></div></div><button className="logout-button" onClick={logout}>Log out</button></div></aside><main className="main-area"><header className="topbar"><div><span className="breadcrumb">Workspace / </span><strong>{view === "chat" ? "Chat" : "Documents"}</strong></div><div className="connection"><span className="signal-dot" /> Backend connected</div></header>{view === "chat" ? <div className="dashboard-grid"><Chat token={token} /><aside className="right-rail"><UploadPanel token={token} onUploaded={refreshDocuments} /><Documents token={token} documents={documents} refresh={refreshDocuments} /></aside></div> : <div className="documents-page"><UploadPanel token={token} onUploaded={refreshDocuments} /><Documents token={token} documents={documents} refresh={refreshDocuments} /></div>}{loadingDocuments && <div className="loading-bar" />}</main></div>;
}

export default App;
