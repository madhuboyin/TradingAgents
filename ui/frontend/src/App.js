import React, { useCallback, useEffect, useMemo, useState } from 'react';
import FlowGraph from './components/FlowGraph';
import {
  Activity,
  AlertTriangle,
  ChevronRight,
  Info,
  Layout,
  PanelLeftClose,
  PanelLeftOpen,
  Target,
  TrendingUp,
  X,
} from 'lucide-react';

const ANALYST_OPTIONS = [
  { id: 'market', label: 'Market', helper: 'Trend and technical context' },
  { id: 'social', label: 'Sentiment', helper: 'Market mood and crowd signals' },
  { id: 'news', label: 'News', helper: 'Headlines, macro, and insider context' },
  { id: 'fundamentals', label: 'Fundamentals', helper: 'Financial quality and valuation base' },
  { id: 'industry', label: 'Industry / Peer', helper: 'Relative positioning and peer comparison' },
  { id: 'catalyst', label: 'Earnings / Catalyst', helper: 'Upcoming events, timing, and expectation risk' },
];

const ANALYST_REPORT_SECTIONS = [
  { key: 'market_report', title: 'Market Analyst', helper: 'Trend, momentum, and technical framing.' },
  { key: 'sentiment_report', title: 'Sentiment Analyst', helper: 'Retail, social, and narrative positioning.' },
  { key: 'news_report', title: 'News Analyst', helper: 'Macro headlines, company developments, and insider context.' },
  { key: 'fundamentals_report', title: 'Fundamentals Analyst', helper: 'Financial health, profitability, and balance-sheet quality.' },
  { key: 'industry_report', title: 'Industry / Peer Comparison Analyst', helper: 'Relative valuation, margins, growth, and peer quality.' },
  { key: 'catalyst_report', title: 'Earnings / Catalyst Analyst', helper: 'Upcoming events, expectation setup, and what-must-go-right / wrong.' },
];

const SURFACE = {
  appBg: '#020617',
  panel: '#0f172a',
  panelAlt: '#111c31',
  panelMuted: '#162033',
  border: '#1e293b',
  borderStrong: '#334155',
  text: '#f8fafc',
  textMuted: '#94a3b8',
  textSubtle: '#64748b',
  blue: '#3b82f6',
  blueSoft: '#60a5fa',
  green: '#10b981',
  amber: '#eab308',
  red: '#ef4444',
  purple: '#a855f7',
};

const formatStatusLabel = (status) => {
  if (!status) return 'Idle';
  if (status === 'in_progress') return 'In Progress';
  return status.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
};

const formatInvestmentHorizon = (horizon) => {
  if (!horizon) return 'Short term (<1 year)';
  const labels = {
    short_term: 'Short term (<1 year)',
    medium_term: 'Medium term (1-2 years)',
    long_term: 'Long term (3-5 years)',
  };
  return labels[horizon] || horizon;
};

const parseDecisionHeadline = (content) => {
  if (!content) return 'No decision yet';
  const firstMeaningfulLine = content
    .split('\n')
    .map((line) => line.replace(/\*\*/g, '').trim())
    .find(Boolean);

  return firstMeaningfulLine || 'No decision yet';
};

const getRatingColor = (headline) => {
  const text = (headline || '').toLowerCase();
  if (text.includes('sell')) return SURFACE.red;
  if (text.includes('buy') || text.includes('overweight')) return SURFACE.green;
  if (text.includes('hold') || text.includes('underweight')) return SURFACE.amber;
  return SURFACE.textMuted;
};

const MarkdownContent = ({ content, emptyMessage = 'No data available' }) => {
  if (!content) {
    return (
      <div
        style={{
          color: SURFACE.textMuted,
          fontStyle: 'italic',
          padding: '10px 0',
        }}
      >
        {emptyMessage}
      </div>
    );
  }

  const prepared = content.replace(/([^\n])(\*\*.*?\*\*):/g, '$1\n\n$2:');
  const chunks = prepared.split('\n\n').filter((chunk) => chunk.trim());

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {chunks.map((chunk, i) => {
        const headerMatch = chunk.match(/^\*\*(.*?)\*\*:\s*(.*)/s);

        if (headerMatch) {
          const [, header, body] = headerMatch;
          const isHighlight = ['Rating', 'Recommendation', 'Action'].some((token) => header.includes(token));
          const sentences = body.split(/(?<=[.!?])\s+/).filter((sentence) => sentence.trim().length > 5);

          return (
            <div
              key={i}
              style={{
                background: isHighlight ? SURFACE.panelMuted : 'transparent',
                borderRadius: '12px',
                padding: isHighlight ? '16px' : '0 2px',
                border: isHighlight ? `1px solid ${SURFACE.borderStrong}` : 'none',
                borderLeft: isHighlight
                  ? `4px solid ${header.includes('Action') ? SURFACE.green : SURFACE.blue}`
                  : 'none',
              }}
            >
              <div
                style={{
                  fontSize: '11px',
                  fontWeight: 800,
                  textTransform: 'uppercase',
                  color: isHighlight ? SURFACE.textMuted : SURFACE.blueSoft,
                  letterSpacing: '0.1em',
                  marginBottom: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                {header.includes('Rating') && <Target size={14} />}
                {header.includes('Action') && <AlertTriangle size={14} />}
                {header.includes('Rationale') && <Info size={14} />}
                {header}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {sentences.map((sentence, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      gap: '10px',
                      fontSize: '13px',
                      lineHeight: 1.6,
                      color: SURFACE.text,
                      fontWeight: header.includes('Rating') ? 700 : 400,
                    }}
                  >
                    <span style={{ color: SURFACE.blue, fontSize: '16px', lineHeight: 1.2 }}>•</span>
                    <span>
                      {sentence.split(/(\*\*.*?\*\*)/g).map((part, j) => {
                        if (part.startsWith('**') && part.endsWith('**')) {
                          return (
                            <strong key={j} style={{ color: SURFACE.blueSoft }}>
                              {part.slice(2, -2)}
                            </strong>
                          );
                        }
                        return part;
                      })}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          );
        }

        const paragraphSentences = chunk.split(/(?<=[.!?])\s+/).filter((sentence) => sentence.trim().length > 5);
        return (
          <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '0 2px' }}>
            {paragraphSentences.map((sentence, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  gap: '10px',
                  fontSize: '13px',
                  lineHeight: 1.7,
                  color: SURFACE.textMuted,
                }}
              >
                <span style={{ color: SURFACE.textSubtle }}>•</span>
                <span>
                  {sentence.split(/(\*\*.*?\*\*)/g).map((part, j) => {
                    if (part.startsWith('**') && part.endsWith('**')) {
                      return (
                        <strong key={j} style={{ color: SURFACE.text }}>
                          {part.slice(2, -2)}
                        </strong>
                      );
                    }
                    return part;
                  })}
                </span>
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );
};

const ProgressBar = ({ progress, status }) => {
  const isError = status === 'error';

  return (
    <div
      style={{
        width: '100%',
        height: '8px',
        background: SURFACE.panel,
        borderRadius: '999px',
        overflow: 'hidden',
        marginTop: '12px',
        position: 'relative',
        border: `1px solid ${SURFACE.border}`,
      }}
    >
      <div
        style={{
          width: `${progress}%`,
          height: '100%',
          background: isError ? SURFACE.red : `linear-gradient(90deg, ${SURFACE.blue}, ${SURFACE.blueSoft})`,
          transition: 'width 0.8s cubic-bezier(0.4, 0, 0.2, 1)',
          boxShadow: isError ? 'none' : '0 0 18px rgba(59, 130, 246, 0.45)',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {!isError && progress < 100 && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.16), transparent)',
              animation: 'pulse-scan 2s infinite',
            }}
          />
        )}
      </div>
    </div>
  );
};

const SectionCard = ({ title, subtitle, icon: Icon, children, accent = SURFACE.blue, collapsible = false, collapsed = false, onToggleCollapse }) => (
  <section
    style={{
      background: SURFACE.panel,
      border: `1px solid ${SURFACE.border}`,
      borderRadius: '16px',
      padding: '20px',
    }}
  >
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '12px',
        marginBottom: '16px',
        paddingBottom: '12px',
        borderBottom: `1px solid ${SURFACE.border}`,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
        {Icon && <Icon size={18} color={accent} />}
        <div style={{ minWidth: 0 }}>
          <div style={{ fontSize: '15px', fontWeight: 700, color: SURFACE.text }}>{title}</div>
          {subtitle && <div style={{ fontSize: '12px', color: SURFACE.textMuted, marginTop: '3px' }}>{subtitle}</div>}
        </div>
      </div>
      {collapsible && (
        <button
          type="button"
          onClick={onToggleCollapse}
          aria-expanded={!collapsed}
          aria-label={`${collapsed ? 'Expand' : 'Collapse'} ${title}`}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            border: `1px solid ${SURFACE.borderStrong}`,
            borderRadius: '999px',
            background: 'transparent',
            color: SURFACE.textMuted,
            padding: '8px 12px',
            cursor: 'pointer',
            fontSize: '12px',
            fontWeight: 700,
            flexShrink: 0,
          }}
        >
          <ChevronRight
            size={14}
            style={{
              transform: collapsed ? 'rotate(0deg)' : 'rotate(90deg)',
              transition: 'transform 0.2s ease',
            }}
          />
          {collapsed ? 'Show' : 'Hide'}
        </button>
      )}
    </div>
    {!collapsed && children}
  </section>
);

const EmptyState = ({ title, body }) => (
  <div
    style={{
      background: SURFACE.panel,
      border: `1px dashed ${SURFACE.borderStrong}`,
      borderRadius: '16px',
      padding: '28px',
      color: SURFACE.textMuted,
    }}
  >
    <div style={{ fontSize: '16px', fontWeight: 700, color: SURFACE.text, marginBottom: '8px' }}>{title}</div>
    <div style={{ fontSize: '13px', lineHeight: 1.6 }}>{body}</div>
  </div>
);

const AnalystToggle = ({ option, checked, onChange }) => (
  <label
    style={{
      display: 'flex',
      alignItems: 'flex-start',
      gap: '10px',
      padding: '10px 12px',
      borderRadius: '12px',
      border: `1px solid ${checked ? SURFACE.blue : SURFACE.border}`,
      background: checked ? 'rgba(59, 130, 246, 0.12)' : SURFACE.panel,
      cursor: 'pointer',
    }}
  >
    <input
      type="checkbox"
      checked={checked}
      onChange={() => onChange(option.id)}
      style={{ marginTop: '3px' }}
    />
    <div style={{ minWidth: 0 }}>
      <div style={{ fontSize: '13px', fontWeight: 700, color: SURFACE.text }}>{option.label}</div>
      <div style={{ fontSize: '11px', color: SURFACE.textMuted, marginTop: '4px', lineHeight: 1.5 }}>{option.helper}</div>
    </div>
  </label>
);

const StatusBanner = ({ items }) => (
  <div
    style={{
      display: 'flex',
      alignItems: 'stretch',
      marginTop: '16px',
      background: SURFACE.panel,
      border: `1px solid ${SURFACE.border}`,
      borderRadius: '12px',
      overflow: 'hidden',
    }}
  >
    {items.map((item, i) => (
      <div
        key={item.label}
        style={{
          flex: 1,
          padding: '10px 14px',
          borderRight: i < items.length - 1 ? `1px solid ${SURFACE.border}` : 'none',
          minWidth: 0,
        }}
      >
        <div style={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.08em', color: SURFACE.textSubtle, fontWeight: 700, marginBottom: '3px' }}>
          {item.label}
        </div>
        <div style={{ fontSize: '13px', fontWeight: 700, color: item.tone, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {item.value}
        </div>
      </div>
    ))}
  </div>
);

const AgentInspectorPanel = ({ agent, onClose }) => {
  React.useEffect(() => {
    const handleKey = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [onClose]);

  return (
    <>
      <div
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0,
          background: 'rgba(0,0,0,0.4)',
          backdropFilter: 'blur(2px)',
          zIndex: 40,
          cursor: 'pointer',
        }}
      />
      <div
        style={{
          position: 'fixed', right: 0, top: 0,
          height: '100vh', width: '360px',
          background: SURFACE.panel,
          borderLeft: `1px solid ${SURFACE.borderStrong}`,
          zIndex: 50,
          overflowY: 'auto',
          display: 'flex', flexDirection: 'column',
          boxShadow: '-12px 0 40px rgba(0,0,0,0.5)',
          animation: 'slideInRight 0.25s cubic-bezier(0.4,0,0.2,1)',
        }}
      >
        <div style={{
          padding: '20px 20px 16px',
          borderBottom: `1px solid ${SURFACE.border}`,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          background: SURFACE.panelAlt,
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TrendingUp size={16} color={SURFACE.amber} />
            <span style={{ fontSize: '11px', fontWeight: 700, color: SURFACE.textSubtle, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Agent Inspector
            </span>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent', border: 'none', cursor: 'pointer',
              color: SURFACE.textMuted, padding: '6px', borderRadius: '8px',
              display: 'flex', alignItems: 'center',
            }}
          >
            <X size={16} />
          </button>
        </div>

        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ background: SURFACE.panelAlt, border: `1px solid ${SURFACE.borderStrong}`, borderRadius: '14px', padding: '16px' }}>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.08em', color: SURFACE.textSubtle, fontWeight: 700, marginBottom: '8px' }}>
              Selected agent
            </div>
            <div style={{ fontSize: '20px', fontWeight: 800, marginBottom: '10px' }}>{agent.label}</div>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '6px 10px', borderRadius: '999px', background: 'rgba(59,130,246,0.12)', color: SURFACE.blueSoft, fontSize: '12px', fontWeight: 700 }}>
              <span>●</span>
              {agent.status || 'Waiting'}
            </div>
          </div>
          <div style={{ fontSize: '13px', color: SURFACE.textMuted, lineHeight: 1.7 }}>{agent.description}</div>
          <div style={{ background: SURFACE.panelAlt, border: `1px solid ${SURFACE.border}`, borderRadius: '14px', padding: '14px' }}>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.08em', color: SURFACE.textSubtle, fontWeight: 700, marginBottom: '8px' }}>
              Why this matters
            </div>
            <div style={{ fontSize: '13px', color: SURFACE.textMuted, lineHeight: 1.7 }}>
              This panel stays visible while you scan the graph, so you do not need to hover repeatedly to remember each stage's purpose.
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

const App = () => {
  const [runs, setRuns] = useState([]);
  const [stats, setStats] = useState(null);
  const [reflections, setReflections] = useState([]);
  const [activeStatus, setActiveStatus] = useState(null);
  const [activeRunId, setActiveRunId] = useState(null);
  const [lastValidProgress, setLastValidProgress] = useState(5);
  const [portfolio, setPortfolio] = useState('');
  const [investmentHorizon, setInvestmentHorizon] = useState('short_term');
  const [selectedAnalysts, setSelectedAnalysts] = useState(['market', 'social', 'news', 'fundamentals']);
  const [isSavingPortfolio, setIsSavingPortfolio] = useState(false);
  const [isTriggering, setIsTriggering] = useState(false);
  const [selectedRun, setSelectedRun] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [runDetail, setRunDetail] = useState(null);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [elapsed, setElapsed] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notification, setNotification] = useState(null);
  const [activeTab, setActiveTab] = useState('decision');
  const [viewportWidth, setViewportWidth] = useState(() => window.innerWidth);
  const [isWorkflowCollapsed, setIsWorkflowCollapsed] = useState(false);

  const isCompact = viewportWidth < 1180;
  const isNarrow = viewportWidth < 860;

  useEffect(() => {
    const handleResize = () => setViewportWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Auto-expand workflow when a live analysis starts; collapse when browsing history.
  useEffect(() => {
    if (activeRunId) setIsWorkflowCollapsed(false);
  }, [activeRunId]);

  useEffect(() => {
    setIsWorkflowCollapsed(true);
  }, [selectedRun]);

  useEffect(() => {
    if (!notification) return undefined;
    const timeout = setTimeout(() => setNotification(null), 4000);
    return () => clearTimeout(timeout);
  }, [notification]);

  useEffect(() => {
    let interval;

    const updateElapsed = () => {
      const activeStart = activeStatus?.start_time;
      const detailStart = runDetail?.start_time;
      const detailEnd = runDetail?.end_time;

      if (activeStatus && activeStart && activeStatus.status !== 'completed') {
        const start = new Date(activeStart);
        const now = new Date();
        const diff = Math.floor((now - start) / 1000);
        const mins = Math.max(0, Math.floor(diff / 60));
        const secs = Math.max(0, diff % 60);
        setElapsed(`${mins}m ${secs}s`);
      } else if (detailStart && detailEnd) {
        const start = new Date(detailStart);
        const end = new Date(detailEnd);
        const diff = Math.floor((end - start) / 1000);
        if (diff >= 0) {
          const mins = Math.floor(diff / 60);
          const secs = diff % 60;
          setElapsed(`${mins}m ${secs}s`);
        }
      } else {
        // Only clear elapsed when nothing is selected — preserve it while runDetail is loading
        // to prevent the "Runtime ↔ History" flicker during the null-loading gap.
        if (!selectedRun) setElapsed(null);
      }
    };

    updateElapsed();

    if (activeStatus && activeStatus.status !== 'completed' && activeStatus.status !== 'error') {
      interval = setInterval(updateElapsed, 1000);
    }

    return () => clearInterval(interval);
  }, [activeStatus, runDetail, selectedRun]);

  const commentary = useMemo(() => {
    if (!activeStatus) return null;
    const node = (activeStatus.active_node || '').toLowerCase();

    if (node.includes('market')) return 'Analyzing market trends and technical indicators.';
    if (node.includes('social') || node.includes('sentiment')) return 'Gauging market sentiment and social signals.';
    if (node.includes('news')) return 'Processing headlines, macro context, and insider activity.';
    if (node.includes('fundamental')) return 'Evaluating financial health and business fundamentals.';
    if (node.includes('industry')) return 'Comparing the target against peers and industry alternatives.';
    if (node.includes('synchronizer')) return 'Combining analyst output into a single shared picture.';
    if (node.includes('bull')) return 'Constructing the strongest bullish case.';
    if (node.includes('bear')) return 'Stress-testing the idea with bearish scenarios.';
    if (node.includes('research_manager') || node.includes('research manager')) return 'Turning the competing viewpoints into an investment plan.';
    if (node.includes('trader')) return 'Calculating execution levels and guardrails.';
    if (node.includes('portfolio_manager') || node.includes('portfolio manager') || node.includes('risk_management')) {
      return 'Running final risk review and portfolio sizing.';
    }
    if (node.includes('worker pod starting')) return 'Scheduling infrastructure and warming the workflow environment.';
    if (node.includes('launching analyst branches')) return 'Bootstrapping analyst branches and loading prior context.';
    if (node.includes('triggering') || node.includes('created') || node.includes('initializing')) {
      return 'Preparing the workflow to start.';
    }

    return 'Processing analysis.';
  }, [activeStatus]);

  const calculateProgress = (node) => {
    const normalized = (node || '').toLowerCase();

    const steps = {
      preparing: 5,
      'worker pod starting': 8,
      initializing: 10,
      'launching analyst branches': 12,
      market: 20,
      social: 30,
      sentiment: 30,
      news: 40,
      fundamental: 50,
      industry: 58,
      bull: 65,
      bear: 75,
      'research manager': 85,
      trader: 92,
      risk: 95,
      portfolio: 98,
      completed: 100,
    };

    let progress = lastValidProgress;
    for (const [key, value] of Object.entries(steps)) {
      if (normalized.includes(key)) {
        progress = value;
        break;
      }
    }

    if (progress > lastValidProgress) {
      setLastValidProgress(progress);
    }
    return progress;
  };

  const refreshRuns = useCallback((selectNewest = false) => {
    fetch('/api/runs')
      .then((res) => res.json())
      .then((data) => {
        setRuns(data);
        if (data.length > 0 && (selectNewest || !selectedRun)) {
          setSelectedRun(data[0]);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error refreshing runs:', err);
        setNotification({ type: 'error', message: 'Unable to refresh recent runs.' });
        setLoading(false);
      });
  }, [selectedRun]);

  useEffect(() => {
    let completionTimeout;
    refreshRuns();
    fetch('/api/stats').then((res) => res.json()).then(setStats).catch((err) => console.error('Error fetching stats:', err));
    fetch('/api/reflections').then((res) => res.json()).then(setReflections).catch((err) => console.error('Error fetching reflections:', err));
    fetch('/api/config/portfolio')
      .then((res) => res.json())
      .then((data) => setPortfolio(data.tickers))
      .catch((err) => console.error('Error fetching portfolio:', err));

    const statusInterval = setInterval(() => {
      const statusUrl = activeRunId ? `/api/status/${activeRunId}` : '/api/status';
      fetch(statusUrl)
        .then((res) => res.json())
        .then((data) => {
          if (data.status === 'in_progress' || data.status === 'triggered' || data.status === 'error') {
            setActiveStatus(data);
          } else if (data.status === 'completed' && activeRunId) {
            setActiveStatus(data);
            setSelectedRun({ ticker: data.ticker, date: data.date });
            clearTimeout(completionTimeout);
            completionTimeout = setTimeout(() => {
              refreshRuns(true);
              setActiveStatus(null);
              setActiveRunId(null);
            }, 5000);
          } else {
            setActiveStatus(null);
          }
        })
        .catch((err) => console.error('Error fetching status:', err));
    }, 3000);

    return () => {
      clearInterval(statusInterval);
      clearTimeout(completionTimeout);
    };
  }, [activeRunId, refreshRuns]);

  useEffect(() => {
    if (selectedRun) {
      setRunDetail(null);
      fetch(`/api/runs/${selectedRun.ticker}/${selectedRun.date}`)
        .then((res) => res.json())
        .then((data) => setRunDetail(data))
        .catch((err) => console.error('Error fetching run details:', err));
    }
  }, [selectedRun]);

  const savePortfolio = () => {
    setIsSavingPortfolio(true);
    fetch('/api/config/portfolio', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tickers: portfolio }),
    })
      .then((res) => {
        if (!res.ok) throw new Error('Failed to update portfolio');
        return res.json();
      })
      .then(() => {
        setIsSavingPortfolio(false);
        setNotification({ type: 'success', message: `Ticker list updated for future runs: ${portfolio}` });
      })
      .catch((err) => {
        console.error('Error updating portfolio:', err);
        setIsSavingPortfolio(false);
        setNotification({ type: 'error', message: err.message });
      });
  };

  const triggerAnalysis = () => {
    setIsTriggering(true);
    setElapsed('0m 0s');
    setLastValidProgress(5);
    setActiveTab('decision');
    setSelectedRun(null);
    setRunDetail(null);

    fetch('/api/jobs/trigger', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tickers: portfolio,
        investment_horizon: investmentHorizon,
        analysts: selectedAnalysts.join(','),
      }),
    })
      .then((res) => {
        if (!res.ok) {
          return res.json().then((err) => {
            throw new Error(err.detail || 'Failed to trigger job');
          });
        }
        return res.json();
      })
      .then((data) => {
        setIsTriggering(false);
        setNotification({ type: 'success', message: 'Analysis started. Live updates will appear below.' });
        if (data.run_id) {
          setActiveRunId(data.run_id);
        }
        const statusUrl = data.run_id ? `/api/status/${data.run_id}` : '/api/status';
        fetch(statusUrl)
          .then((res) => res.json())
          .then((statusData) => {
            if (statusData.status === 'triggered' || statusData.status === 'in_progress') {
              setActiveStatus(statusData);
            }
          });
      })
      .catch((err) => {
        console.error('Error triggering job:', err);
        setIsTriggering(false);
        setNotification({ type: 'error', message: `Trigger error: ${err.message}` });
      });
  };

  const liveRunDetail = activeStatus?.updates;
  const hasLiveCompletedRun = activeStatus?.status === 'completed' && !!liveRunDetail;
  const isRunActive = activeStatus && activeStatus.status !== 'completed' && activeStatus.status !== 'error';
  const currentHorizon = activeStatus?.investment_horizon || liveRunDetail?.investment_horizon || runDetail?.investment_horizon || selectedRun?.investment_horizon || investmentHorizon;
  const currentDecision = hasLiveCompletedRun
    ? liveRunDetail.final_trade_decision
    : isRunActive
      ? liveRunDetail?.final_trade_decision
      : (liveRunDetail?.final_trade_decision || runDetail?.final_trade_decision);
  const currentPlan = hasLiveCompletedRun
    ? liveRunDetail.investment_plan
    : isRunActive
      ? liveRunDetail?.investment_plan
      : (liveRunDetail?.investment_plan || runDetail?.investment_plan);
  const currentAnalystReports = useMemo(() => {
    const source = hasLiveCompletedRun
      ? liveRunDetail
      : isRunActive
        ? (liveRunDetail || {})
        : { ...(runDetail || {}), ...(liveRunDetail || {}) };

    return ANALYST_REPORT_SECTIONS.map((section) => ({
      ...section,
      content: source?.[section.key] || '',
    })).filter((section) => section.content);
  }, [hasLiveCompletedRun, isRunActive, liveRunDetail, runDetail]);
  const graphAnalystSelection = useMemo(() => {
    if (isRunActive) return selectedAnalysts;

    const source = liveRunDetail || runDetail || {};
    const derived = [];
    if (source.market_report) derived.push('market');
    if (source.sentiment_report) derived.push('social');
    if (source.news_report) derived.push('news');
    if (source.fundamentals_report) derived.push('fundamentals');
    if (source.industry_report) derived.push('industry');

    return derived.length > 0 ? derived : selectedAnalysts;
  }, [isRunActive, selectedAnalysts, liveRunDetail, runDetail]);
  const activeStep = activeStatus?.active_node || (selectedAgent ? selectedAgent.label : 'Awaiting selection');
  const heroTitle = activeStatus
    ? activeStatus.status === 'error'
      ? 'Analysis Failed'
      : activeStatus.status === 'completed'
        ? `${activeStatus.ticker} analysis`
        : `Analyzing ${activeStatus.ticker}`
    : selectedRun
      ? `${selectedRun.ticker} analysis`
      : 'Trading dashboard';

  const statusTone = activeStatus
    ? activeStatus.status === 'error'
      ? SURFACE.red
      : activeStatus.status === 'completed'
        ? SURFACE.green
        : SURFACE.blue
    : SURFACE.green;

  const decisionHeadline = parseDecisionHeadline(currentDecision);
  const ratingColor = getRatingColor(decisionHeadline);

  const detailTabs = [
    { id: 'decision', label: 'Decision' },
    { id: 'plan', label: 'Investment Plan' },
    { id: 'analysts', label: 'Analyst Reports' },
    { id: 'history', label: 'History' },
  ];

  const toggleAnalystSelection = (analystId) => {
    setSelectedAnalysts((current) => {
      if (current.includes(analystId)) {
        if (current.length === 1) return current;
        return current.filter((id) => id !== analystId);
      }
      return [...current, analystId];
    });
  };

  return (
    <div
      style={{
        display: 'flex',
        minHeight: '100vh',
        background: `radial-gradient(circle at top, #0f172a 0%, ${SURFACE.appBg} 45%)`,
        color: SURFACE.text,
        fontFamily: 'Inter, sans-serif',
        flexDirection: isNarrow ? 'column' : 'row',
      }}
    >
      <div
        style={{
          width: isNarrow ? '100%' : isSidebarCollapsed ? '72px' : '320px',
          borderRight: isNarrow ? 'none' : `1px solid ${SURFACE.border}`,
          borderBottom: isNarrow ? `1px solid ${SURFACE.border}` : 'none',
          display: 'flex',
          flexDirection: 'column',
          transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          overflow: 'hidden',
          position: 'relative',
          background: 'rgba(2, 6, 23, 0.82)',
          backdropFilter: 'blur(14px)',
          height: isNarrow ? 'auto' : '100vh',
        }}
      >
        <div
          style={{
            padding: '20px',
            borderBottom: `1px solid ${SURFACE.border}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: isSidebarCollapsed && !isNarrow ? 'center' : 'space-between',
            gap: '10px',
          }}
        >
          {(!isSidebarCollapsed || isNarrow) && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Activity color={SURFACE.blue} />
              <div>
                <h1 style={{ fontSize: '18px', fontWeight: 800, margin: 0 }}>TradingAgents</h1>
                <div style={{ fontSize: '12px', color: SURFACE.textMuted }}>Decision support dashboard</div>
              </div>
            </div>
          )}
          {!isNarrow && (
            <button
              onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
              style={{
                background: 'none',
                border: 'none',
                color: SURFACE.textSubtle,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                padding: '4px',
              }}
              aria-label={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {isSidebarCollapsed ? <PanelLeftOpen size={20} /> : <PanelLeftClose size={20} />}
            </button>
          )}
        </div>

        {(!isSidebarCollapsed || isNarrow) && (
          <>
            <div style={{ padding: '16px 18px', borderBottom: `1px solid ${SURFACE.border}` }}>
              <div style={{ fontSize: '12px', color: SURFACE.textSubtle, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '10px' }}>
                Performance
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div style={{ background: SURFACE.panel, border: `1px solid ${SURFACE.border}`, borderRadius: '12px', padding: '12px' }}>
                  <div style={{ fontSize: '11px', color: SURFACE.textMuted, marginBottom: '6px' }}>Total trades</div>
                  <div style={{ fontSize: '20px', fontWeight: 800 }}>{stats?.total_trades || 0}</div>
                </div>
                <div style={{ background: SURFACE.panel, border: `1px solid ${SURFACE.border}`, borderRadius: '12px', padding: '12px' }}>
                  <div style={{ fontSize: '11px', color: SURFACE.textMuted, marginBottom: '6px' }}>Win rate</div>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: stats?.win_rate >= 50 ? SURFACE.green : SURFACE.red }}>
                    {stats?.win_rate?.toFixed(1) || 0}%
                  </div>
                </div>
              </div>
            </div>

            <div style={{ padding: '18px', borderBottom: `1px solid ${SURFACE.border}`, background: 'rgba(15, 23, 42, 0.65)' }}>
              <div style={{ fontSize: '12px', color: SURFACE.textSubtle, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px' }}>
                Portfolio
              </div>
              <div style={{ fontSize: '12px', color: SURFACE.textMuted, lineHeight: 1.6, marginBottom: '10px' }}>
                Enter comma-separated tickers for the next analysis run.
              </div>
              <label style={{ display: 'block', fontSize: '12px', color: SURFACE.textMuted, marginBottom: '8px' }}>
                Investment horizon
              </label>
              <select
                value={investmentHorizon}
                onChange={(e) => setInvestmentHorizon(e.target.value)}
                style={{
                  width: '100%',
                  background: SURFACE.appBg,
                  border: `1px solid ${SURFACE.borderStrong}`,
                  borderRadius: '10px',
                  color: SURFACE.text,
                  fontSize: '13px',
                  padding: '10px 12px',
                  fontFamily: 'inherit',
                  boxSizing: 'border-box',
                  marginBottom: '10px',
                }}
              >
                <option value="short_term">Short term (&lt;1 year)</option>
                <option value="medium_term">Medium term (1-2 years)</option>
                <option value="long_term">Long term (3-5 years)</option>
              </select>
              <textarea
                value={portfolio}
                onChange={(e) => setPortfolio(e.target.value)}
                placeholder="AAPL, MSFT, NVDA"
                style={{
                  width: '100%',
                  background: SURFACE.appBg,
                  border: `1px solid ${SURFACE.borderStrong}`,
                  borderRadius: '10px',
                  color: SURFACE.text,
                  fontSize: '13px',
                  padding: '10px 12px',
                  minHeight: '72px',
                  resize: 'vertical',
                  fontFamily: 'inherit',
                  boxSizing: 'border-box',
                  marginBottom: '10px',
                }}
              />
              <button
                onClick={savePortfolio}
                disabled={isSavingPortfolio}
                style={{
                  width: '100%',
                  background: SURFACE.blue,
                  color: SURFACE.text,
                  border: 'none',
                  borderRadius: '10px',
                  padding: '10px 12px',
                  fontSize: '12px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  opacity: isSavingPortfolio ? 0.6 : 1,
                  marginBottom: '10px',
                }}
              >
                {isSavingPortfolio ? 'Saving portfolio...' : 'Save ticker list'}
              </button>

              <button
                onClick={triggerAnalysis}
                disabled={isTriggering || !!activeStatus}
                style={{
                  width: '100%',
                  background: activeStatus ? SURFACE.panelMuted : SURFACE.green,
                  color: SURFACE.text,
                  border: 'none',
                  borderRadius: '10px',
                  padding: '12px',
                  fontSize: '13px',
                  fontWeight: 800,
                  cursor: isTriggering || activeStatus ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  opacity: isTriggering ? 0.7 : 1,
                }}
              >
                <Activity size={14} />
                {activeStatus
                  ? activeStatus.status === 'triggered'
                    ? 'Job starting...'
                    : 'Analysis in progress...'
                  : isTriggering
                    ? 'Triggering...'
                    : 'Run analysis'}
              </button>

              <div style={{ fontSize: '12px', color: SURFACE.textMuted, marginTop: '16px', marginBottom: '8px' }}>
                Analyst lineup
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '8px', marginBottom: '12px' }}>
                {ANALYST_OPTIONS.map((option) => (
                  <AnalystToggle
                    key={option.id}
                    option={option}
                    checked={selectedAnalysts.includes(option.id)}
                    onChange={toggleAnalystSelection}
                  />
                ))}
              </div>
              <div style={{ fontSize: '11px', color: SURFACE.textSubtle, lineHeight: 1.5 }}>
                `Industry / Peer` is available on demand here, but not preselected by default so the dashboard preserves the current baseline recommendation path unless you opt in.
              </div>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', padding: '14px', minHeight: 0 }}>
              <div style={{ fontSize: '12px', color: SURFACE.textSubtle, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '10px', paddingLeft: '6px' }}>
                Recent runs
              </div>
              {runs.map((run, index) => {
                const isSelectedRun = selectedRun === run;
                return (
                  <button
                    key={`${run.ticker}-${run.date}-${index}`}
                    onClick={() => setSelectedRun(run)}
                    style={{
                      width: '100%',
                      padding: '14px',
                      borderRadius: '12px',
                      cursor: 'pointer',
                      background: isSelectedRun ? SURFACE.panelAlt : 'transparent',
                      marginBottom: '6px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      transition: 'background 0.2s',
                      border: isSelectedRun ? `1px solid ${SURFACE.blue}` : `1px solid transparent`,
                      color: SURFACE.text,
                      textAlign: 'left',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 700 }}>{run.ticker}</div>
                      <div style={{ fontSize: '12px', color: SURFACE.textMuted, marginTop: '4px' }}>
                        {run.date}
                      </div>
                      <div style={{ fontSize: '11px', color: SURFACE.textSubtle, marginTop: '2px' }}>
                        {formatInvestmentHorizon(run.investment_horizon)}
                      </div>
                    </div>
                    <ChevronRight size={14} color={SURFACE.textSubtle} />
                  </button>
                );
              })}
            </div>
          </>
        )}

        {isSidebarCollapsed && !isNarrow && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', paddingTop: '20px' }}>
            <Activity color={SURFACE.blue} />
            <div style={{ width: '30px', height: '1px', background: SURFACE.border }} />
            {runs.slice(0, 5).map((run, index) => (
              <button
                key={`${run.ticker}-${run.date}-${index}`}
                onClick={() => setSelectedRun(run)}
                title={`${run.ticker} - ${run.date}`}
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '21px',
                  background: selectedRun === run ? SURFACE.blue : SURFACE.panel,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '10px',
                  fontWeight: 800,
                  cursor: 'pointer',
                  color: SURFACE.text,
                  border: 'none',
                }}
              >
                {run.ticker.slice(0, 2)}
              </button>
            ))}
          </div>
        )}
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <header style={{ padding: '24px', borderBottom: `1px solid ${SURFACE.border}`, background: 'rgba(2, 6, 23, 0.72)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: isCompact ? 'flex-start' : 'center', gap: '16px', flexDirection: isCompact ? 'column' : 'row' }}>
            <div style={{ maxWidth: isCompact ? '100%' : 'none', minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                <span style={{ color: statusTone, fontSize: '18px' }}>●</span>
                <span style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.08em', color: SURFACE.textMuted, fontWeight: 700 }}>
                  {formatStatusLabel(activeStatus?.status || 'completed')}
                </span>
              </div>
              <h2 style={{ margin: 0, fontSize: isNarrow ? '28px' : '32px', lineHeight: 1.1 }}>{heroTitle}</h2>
              <div
                style={{
                  fontSize: '14px',
                  color: activeStatus?.status === 'error' ? SURFACE.red : SURFACE.textMuted,
                  marginTop: '10px',
                  lineHeight: 1.6,
                  whiteSpace: isCompact ? 'normal' : 'nowrap',
                  overflow: isCompact ? 'visible' : 'hidden',
                  textOverflow: isCompact ? 'clip' : 'ellipsis',
                }}
              >
                {activeStatus
                  ? activeStatus.status === 'error'
                    ? activeStatus.error
                    : activeStatus.status === 'completed'
                      ? `Trade date: ${activeStatus.date} · Horizon: ${formatInvestmentHorizon(activeStatus.investment_horizon)}`
                      : commentary
                  : selectedRun
                    ? `Reviewing the run from ${selectedRun.date} · Horizon: ${formatInvestmentHorizon(selectedRun.investment_horizon)}. Select a workflow node to inspect the reasoning path.`
                    : 'Choose a recent run or trigger a new analysis to inspect the workflow and final recommendation.'}
              </div>
            </div>

            {notification && (
              <div
                style={{
                  minWidth: isCompact ? '100%' : '320px',
                  maxWidth: '420px',
                  background: notification.type === 'error' ? 'rgba(239, 68, 68, 0.12)' : 'rgba(16, 185, 129, 0.12)',
                  border: `1px solid ${notification.type === 'error' ? SURFACE.red : SURFACE.green}`,
                  borderRadius: '14px',
                  padding: '14px 16px',
                  color: notification.type === 'error' ? '#fecaca' : '#bbf7d0',
                  fontSize: '13px',
                  lineHeight: 1.5,
                }}
              >
                {notification.message}
              </div>
            )}
          </div>

          <StatusBanner items={[
            { label: 'Status', value: formatStatusLabel(activeStatus?.status || 'completed'), tone: statusTone },
            { label: 'Decision', value: decisionHeadline, tone: ratingColor },
            { label: 'Horizon', value: formatInvestmentHorizon(currentHorizon), tone: SURFACE.purple },
            { label: 'Current Step', value: activeStatus && activeStatus.status !== 'completed' ? activeStep : selectedAgent?.label || 'Review decision', tone: SURFACE.amber },
            { label: elapsed ? 'Runtime' : 'History', value: elapsed || `${runs.length} runs`, tone: SURFACE.textMuted },
          ]} />

          {activeStatus && activeStatus.status !== 'error' && activeStatus.status !== 'completed' && (
            <div style={{ marginTop: '18px' }}>
              <ProgressBar progress={calculateProgress(activeStatus.active_node)} status={activeStatus.status} />
              <div style={{ fontSize: '12px', color: SURFACE.amber, marginTop: '8px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ animation: 'pulse 2s infinite' }}>●</span>
                Workflow progress is estimated from the current active node.
              </div>
            </div>
          )}
        </header>

        <style>{`
          @keyframes pulse {
            0% { opacity: 0.4; transform: scale(0.8); }
            50% { opacity: 1; transform: scale(1.1); }
            100% { opacity: 0.4; transform: scale(0.8); }
          }

          @keyframes pulse-scan {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
          }

          @keyframes slideInRight {
            from { transform: translateX(100%); }
            to   { transform: translateX(0); }
          }
        `}</style>

        <main style={{ flex: 1, overflowY: 'auto', padding: isNarrow ? '16px' : '24px' }}>
          {loading ? (
            <EmptyState title="Loading dashboard" body="Fetching recent runs, portfolio settings, and historical context." />
          ) : !selectedRun && !activeStatus ? (
            <EmptyState title="No analysis selected" body="Choose a recent run from the sidebar or trigger a fresh analysis to populate the dashboard." />
          ) : (
            <>
              <SectionCard
                title="Workflow overview"
                subtitle="Follow the analysis path and click any node to inspect what that agent contributes."
                icon={Layout}
                collapsible
                collapsed={isWorkflowCollapsed}
                onToggleCollapse={() => setIsWorkflowCollapsed((c) => !c)}
              >
                <FlowGraph
                  runData={runDetail}
                  activeStatus={activeStatus}
                  selectedAnalysts={graphAnalystSelection}
                  onNodeClick={setSelectedAgent}
                  selectedAgentId={selectedAgent?.id}
                />
              </SectionCard>

              {selectedAgent && (
                <AgentInspectorPanel
                  agent={selectedAgent}
                  onClose={() => setSelectedAgent(null)}
                />
              )}

              <div style={{ marginTop: '20px' }}>
              <SectionCard
                title="Decision workspace"
                subtitle="The most important output first, with the supporting plan, analyst reports, and historical context one click away."
                icon={Target}
                accent={SURFACE.blue}
              >
                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '18px' }}>
                    {detailTabs.map((tab) => {
                      const isActive = activeTab === tab.id;
                      return (
                        <button
                          key={tab.id}
                          onClick={() => setActiveTab(tab.id)}
                          style={{
                            border: `1px solid ${isActive ? SURFACE.blue : SURFACE.borderStrong}`,
                            background: isActive ? 'rgba(59, 130, 246, 0.14)' : 'transparent',
                            color: isActive ? SURFACE.blueSoft : SURFACE.textMuted,
                            borderRadius: '999px',
                            padding: '8px 14px',
                            fontSize: '12px',
                            fontWeight: 700,
                            cursor: 'pointer',
                          }}
                        >
                          {tab.label}
                        </button>
                      );
                    })}
                  </div>

                  {activeTab === 'decision' && (
                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns: isCompact ? '1fr' : 'minmax(260px, 0.8fr) minmax(0, 1.2fr)',
                        alignItems: 'start',
                        gap: '18px',
                      }}
                    >
                      <div style={{ background: SURFACE.panelAlt, border: `1px solid ${SURFACE.borderStrong}`, borderLeft: `4px solid ${ratingColor}`, borderRadius: '16px', padding: '18px' }}>
                        <div style={{ fontSize: '11px', color: SURFACE.textSubtle, textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 700, marginBottom: '10px' }}>
                          Key takeaway
                        </div>
                        <div style={{ fontSize: '24px', fontWeight: 800, lineHeight: 1.2, color: ratingColor }}>
                          {decisionHeadline}
                        </div>
                        <div style={{ fontSize: '13px', color: SURFACE.textMuted, lineHeight: 1.7, marginTop: '12px' }}>
                          This is the fastest way to understand the current run before diving into the full explanation.
                        </div>
                      </div>
                      <div>
                        <MarkdownContent
                          content={currentDecision}
                          emptyMessage="The final recommendation will appear here once a completed run is selected."
                        />
                      </div>
                    </div>
                  )}

                  {activeTab === 'plan' && (
                    <MarkdownContent
                      content={currentPlan}
                      emptyMessage="The investment plan will appear here once the run includes execution guidance."
                    />
                  )}

                  {activeTab === 'analysts' && (
                    <>
                      {currentAnalystReports.length > 0 ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                          {ANALYST_REPORT_SECTIONS.map((section) => {
                            const content = currentAnalystReports.find((report) => report.key === section.key)?.content || '';
                            if (!content) return null;

                            return (
                              <div
                                key={section.key}
                                style={{
                                  padding: '18px',
                                  background: SURFACE.panelAlt,
                                  borderRadius: '16px',
                                  border: `1px solid ${SURFACE.border}`,
                                }}
                              >
                                <div style={{ fontSize: '11px', color: SURFACE.textSubtle, textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 700, marginBottom: '6px' }}>
                                  {section.title}
                                </div>
                                <div style={{ fontSize: '12px', color: SURFACE.textMuted, lineHeight: 1.6, marginBottom: '14px' }}>
                                  {section.helper}
                                </div>
                                <MarkdownContent content={content} />
                              </div>
                            );
                          })}
                        </div>
                      ) : (
                        <EmptyState
                          title="No analyst reports available yet"
                          body="Analyst reports appear here as soon as the selected run includes them. If you want Industry / Peer output, include that analyst in the next triggered run."
                        />
                      )}
                    </>
                  )}

                  {activeTab === 'history' && (
                    <>
                      {reflections.length > 0 ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                          {reflections.slice(0, 5).map((ref, idx) => (
                            <div
                              key={`${ref.ticker}-${ref.date}-${idx}`}
                              style={{
                                padding: '16px',
                                background: SURFACE.panelAlt,
                                borderRadius: '14px',
                                border: `1px solid ${SURFACE.border}`,
                                borderLeft: `4px solid ${SURFACE.purple}`,
                              }}
                            >
                              <div style={{ fontSize: '11px', color: SURFACE.textMuted, marginBottom: '8px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                                {ref.ticker} • {ref.date} • {ref.alpha} alpha • {ref.holding} holding
                              </div>
                              <MarkdownContent content={ref.reflection} />
                            </div>
                          ))}
                        </div>
                      ) : (
                        <EmptyState title="No historical reflections yet" body="Completed run reflections will accumulate here so trends and mistakes are easier to spot over time." />
                      )}
                    </>
                  )}
                </SectionCard>
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
