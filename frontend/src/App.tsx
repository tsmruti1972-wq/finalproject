import React, { useMemo, useState } from 'react';
import Papa from 'papaparse';

import StructuredOutput from './components/StructuredOutput';
import type { ChatMessage, ChatResponse, TaskType } from './types';

const TASK_OPTIONS: Array<{ label: string; value: TaskType }> = [
  { label: 'Variance explanation', value: 'variance_explanation' },
  { label: 'Executive narrative', value: 'executive_narrative' },
  { label: 'Assumption and risk check', value: 'assumption_risk_check' },
];

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/chat';
const DEMO_CONTEXT =
  'Month-end variance review for December. Cloud vendor credits are one-time and should be separated from recurring run-rate impacts. Use conservative CFO-ready language and call out assumptions clearly.';
const DEMO_PROMPT =
  'Explain the December revenue, COGS, and Opex variances versus budget in CFO-ready language. Separate one-time vs recurring impacts, state assumptions, and identify follow-up questions.';

function buildChatPreview(responseText: string): string {
  const lines = responseText
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);

  const contentLines = lines.filter((line) => {
    const lower = line.toLowerCase();
    return ![
      'key insights',
      'drivers and impacts',
      'assumptions made',
      'risks and uncertainties',
      'suggested follow up questions',
      'suggested follow-up questions',
      'sources used',
    ].includes(lower);
  });

  const firstPoint = contentLines.find((line) => line.startsWith('-')) ?? contentLines[0] ?? 'Response generated.';
  const secondPoint =
    contentLines.find((line, idx) => idx > 0 && line !== firstPoint && !line.startsWith('[Doc')) ??
    'I organized the full response into the required sections.';

  const clean = (text: string) => text.replace(/^\-\s*/, '').trim();

  return `${clean(firstPoint)} ${clean(secondPoint)} Please refer to the side panel for more details.`;
}

export default function App() {
  const [taskType, setTaskType] = useState<TaskType>('variance_explanation');
  const [contextAssumptions, setContextAssumptions] = useState('');
  const [message, setMessage] = useState('');
  const [chat, setChat] = useState<ChatMessage[]>([]);
  const [csvRows, setCsvRows] = useState<Record<string, unknown>[]>([]);
  const [csvName, setCsvName] = useState('No file uploaded');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [latestResponse, setLatestResponse] = useState('');
  const [demoCsvPreview, setDemoCsvPreview] = useState('');
  const [showDemoPreview, setShowDemoPreview] = useState(false);

  const canSubmit = useMemo(() => message.trim().length > 0 && !loading, [loading, message]);

  const loadDemoCsv = async () => {
    setError('');
    try {
      const demoCsvUrl = `${import.meta.env.BASE_URL}demo-finance-variance.csv?v=20260224-1`;
      const res = await fetch(demoCsvUrl, { cache: 'no-store' });
      if (!res.ok) {
        throw new Error('Could not load demo CSV.');
      }
      const csvText = await res.text();
      Papa.parse<Record<string, unknown>>(csvText, {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          if (!results.data || results.data.length === 0) {
            setError('Demo CSV is empty or invalid.');
            return;
          }
          setCsvRows(results.data);
          setCsvName(`Demo finance variance CSV (${results.data.length} rows)`);
          setTaskType('variance_explanation');
          setContextAssumptions(DEMO_CONTEXT);
          setMessage(DEMO_PROMPT);
        },
        error: () => setError('Could not parse demo CSV.'),
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load demo CSV.');
    }
  };

  const toggleDemoPreview = async () => {
    setError('');
    if (showDemoPreview) {
      setShowDemoPreview(false);
      return;
    }
    try {
      if (!demoCsvPreview) {
        const demoCsvUrl = `${import.meta.env.BASE_URL}demo-finance-variance.csv?v=20260224-1`;
        const res = await fetch(demoCsvUrl, { cache: 'no-store' });
        if (!res.ok) {
          throw new Error('Could not load demo CSV preview.');
        }
        setDemoCsvPreview(await res.text());
      }
      setShowDemoPreview(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load demo CSV preview.');
    }
  };

  const onFileUpload = (file: File | null) => {
    setError('');
    if (!file) {
      setCsvRows([]);
      setCsvName('No file uploaded');
      return;
    }

    Papa.parse<Record<string, unknown>>(file, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        if (!results.data || results.data.length === 0) {
          setError('Uploaded CSV is empty or invalid.');
          setCsvRows([]);
          setCsvName(file.name);
          return;
        }
        setCsvRows(results.data);
        setCsvName(`${file.name} (${results.data.length} rows)`);
      },
      error: () => {
        setError('Could not parse the CSV file.');
        setCsvRows([]);
        setCsvName(file.name);
      },
    });
  };

  const submit = async () => {
    setError('');
    if (!message.trim()) {
      setError('Please enter a request in the chat input.');
      return;
    }

    const userEntry: ChatMessage = {
      role: 'user',
      text: message,
      timestamp: new Date().toLocaleTimeString(),
    };

    setChat((prev) => [...prev, userEntry]);
    setLoading(true);

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_type: taskType,
          user_message: message,
          context_assumptions: contextAssumptions,
          csv_content: csvRows,
        }),
      });

      if (!res.ok) {
        const payload = await res.json().catch(() => ({}));
        throw new Error(payload.detail || 'Request failed');
      }

      const data: ChatResponse = await res.json();
      const assistantEntry: ChatMessage = {
        role: 'assistant',
        text: buildChatPreview(data.response_text),
        timestamp: new Date().toLocaleTimeString(),
      };

      setChat((prev) => [...prev, assistantEntry]);
      setLatestResponse(data.response_text);
      setMessage('');
    } catch (e) {
      const errMsg = e instanceof Error ? e.message : 'Unexpected error';
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <header className="topbar">
        <div className="topbar-content">
          <h1>Financial Decision Support Copilot</h1>
          <p>
            Turn financial data and business context into executive-ready, grounded decision support.
            This copilot helps explain variances, build CFO summaries, and identify assumptions and risks.
          </p>
          <div className="quick-steps">
            <span>1. Upload CSV</span>
            <span>2. Add context</span>
            <span>3. Ask for output</span>
          </div>
        </div>
      </header>
      <div className="layout">
        <aside className="panel">
          <h2>Inputs</h2>

          <label className="label">File upload for CSV</label>
          <input
            type="file"
            accept=".csv"
            onChange={(e) => onFileUpload(e.target.files?.[0] ?? null)}
          />
          <button type="button" className="secondary-btn" onClick={loadDemoCsv}>
            Load Demo CSV
          </button>
          <button type="button" className="secondary-btn" onClick={toggleDemoPreview}>
            {showDemoPreview ? 'Hide Demo Preview' : 'Preview Demo CSV'}
          </button>
          {showDemoPreview ? (
            <div className="demo-preview">
              <p className="demo-preview-title">Demo CSV preview</p>
              <pre>{demoCsvPreview}</pre>
            </div>
          ) : null}
          <p className="muted">{csvName}</p>

          <label className="label">Context and assumptions</label>
          <textarea
            value={contextAssumptions}
            onChange={(e) => setContextAssumptions(e.target.value)}
            placeholder="Example: Vendor credit is one-time, hiring ramp continues, materiality threshold is 5%"
            rows={14}
          />

          <label className="label">Task</label>
          <select value={taskType} onChange={(e) => setTaskType(e.target.value as TaskType)}>
            {TASK_OPTIONS.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </aside>

        <main className="panel">
          <h2>Copilot Chat</h2>
          <div className="chat-thread">
            {chat.length === 0 ? (
              <p className="muted">
                Start by uploading data or pasting context. Then ask a request like:
                &quot;Explain December revenue and margin variance in CFO-ready language.&quot;
              </p>
            ) : null}
            {chat.map((msg, idx) => (
              <div key={`${msg.timestamp}-${idx}`} className={`msg ${msg.role}`}>
                <div className="msg-head">
                  <strong>{msg.role === 'user' ? 'You' : 'Copilot'}</strong>
                  <span>{msg.timestamp}</span>
                </div>
                <pre>{msg.text}</pre>
              </div>
            ))}
            <div className="chat-input-row">
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                rows={4}
                placeholder="Enter your follow-up request for the selected task"
              />
              <button disabled={!canSubmit} onClick={submit}>
                {loading ? 'Submitting...' : 'Submit'}
              </button>
            </div>
          </div>
          {error ? <p className="error">{error}</p> : null}
        </main>

        <aside className="panel">
          <h2>Output</h2>
          <StructuredOutput responseText={latestResponse} />
        </aside>
      </div>
    </div>
  );
}
