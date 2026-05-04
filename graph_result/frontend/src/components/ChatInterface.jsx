import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, Terminal, AlertCircle, Table2, ChevronDown, ChevronUp } from 'lucide-react';

const backendUrl = 'http://localhost:8000';

// ── Inline result table component ──────────────────────────────────────────
const ResultTable = ({ table }) => {
  const [collapsed, setCollapsed] = useState(false);
  if (!table || table.length === 0) return null;

  const columns = Object.keys(table[0]);

  return (
    <div className="result-table-wrapper">
      <div className="result-table-header" onClick={() => setCollapsed(c => !c)}>
        <span>
          <Table2 size={13} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
          {table.length} record{table.length !== 1 ? 's' : ''} found
        </span>
        <span className="result-table-toggle">
          {collapsed ? <ChevronDown size={13} /> : <ChevronUp size={13} />}
        </span>
      </div>

      {!collapsed && (
        <div className="result-table-scroll">
          <table className="result-table">
            <thead>
              <tr>
                {columns.map(col => (
                  <th key={col} title={col}>{col.split('.').pop()}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {table.map((row, i) => (
                <tr key={i}>
                  {columns.map(col => (
                    <td key={col} title={String(row[col] ?? '')}>
                      {row[col] !== undefined && row[col] !== null
                        ? String(row[col]).length > 30
                          ? String(row[col]).slice(0, 30) + '…'
                          : String(row[col])
                        : '—'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

// ── Main chat component ─────────────────────────────────────────────────────
const ChatInterface = ({ onDataUpdate, setHighlightNodes }) => {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am your O2C Graph Assistant. Ask me about sales orders, deliveries, invoices, or customers.', type: 'welcome' }
  ]);
  const [inputUrl, setInputUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputUrl.trim() || loading) return;

    const query = inputUrl;
    setInputUrl('');
    setMessages(prev => [...prev, { role: 'user', content: query }]);
    setLoading(true);

    try {
      const res = await axios.post(`${backendUrl}/api/chat`, { query });
      const data = res.data;

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response,
        cypher: data.cypher,
        intent: data.intent,
        table: data.table,
        error: data.error
      }]);

      if (data.intent === 'domain_query' && !data.error) {
        onDataUpdate(data);
      }

    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Failed to connect to the backend server.',
        error: err.message
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="sidebar-container">
      <div className="sidebar-header">
        <h2>O2C Graph Query Explorer</h2>
      </div>

      <div className="chat-history" ref={scrollRef}>
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>

            {/* ── Table (raw data, shown first for provenance) ── */}
            {m.table && m.table.length > 0 && (
              <ResultTable table={m.table} />
            )}

            {/* ── LLM natural-language response ── */}
            <div className="message-bubble">
              {m.content}
            </div>

            {/* ── Cypher query block ── */}
            {m.cypher && (
              <div className="cypher-block">
                <div className="cypher-header">
                  <span><Terminal size={14} style={{ marginRight: '6px', verticalAlign: 'middle' }} />Cypher Generated</span>
                  <span style={{ color: '#6366f1', fontSize: '0.7rem' }}>{m.intent}</span>
                </div>
                <div className="cypher-body">
                  {m.cypher}
                </div>
              </div>
            )}

            {/* ── Execution error block ── */}
            {m.error && (
              <div className="cypher-block" style={{ borderColor: '#e06c75' }}>
                <div className="cypher-header" style={{ color: '#e06c75' }}>
                  <span><AlertCircle size={14} style={{ marginRight: '6px', verticalAlign: 'middle' }} />Execution Error</span>
                </div>
                <div className="cypher-body" style={{ color: '#e06c75' }}>
                  {m.error}
                </div>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="message assistant">
            <div className="typing-indicator">
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
            </div>
          </div>
        )}
      </div>

      <div className="chat-input-container">
        <form onSubmit={handleSubmit} className="chat-form">
          <input
            type="text"
            className="chat-input"
            placeholder="Ask about orders, invoices, customers…"
            value={inputUrl}
            onChange={e => setInputUrl(e.target.value)}
            disabled={loading}
          />
          <button type="submit" className="chat-submit-btn" disabled={loading || !inputUrl.trim()}>
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;
