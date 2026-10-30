import { useEffect, useState, type FormEvent } from 'react'

type Hackathon = {
  id: string
  name: string
  description: string
  status: string
  participants: number
  teams: number
  submissions: number
  start_date?: string
  end_date?: string
}

type Submission = {
  id: string
  project_name: string
  team_name: string
  status: string
  score: number | null
  risk: number | null
}
type Team = { id: string; name: string; description?: string; hackathon_id: string; invite_code?: string }
type LeaderboardEntry = {
  rank: number
  team: string
  project: string
  score: number
  risk: number | null
  status: string
}

type Analytics = {
  total_participants?: number
  total_teams?: number
  total_submissions?: number
  evaluated_projects?: number
  flagged_projects?: number
  average_score?: number
  evaluation_progress?: number
  assigned_submissions?: Submission[]
  pending_count?: number
  users?: number
  hackathons?: number
  teams?: number
  submissions?: number
  flagged_submissions?: number
  audit_events?: number
}

type Page = 'Overview' | 'Hackathons' | 'Submissions' | 'Leaderboard' | 'Analytics' | 'Settings'
type UserRole = 'PARTICIPANT' | 'ORGANIZER' | 'JUDGE' | 'ADMIN'
type AppView = 'app' | 'privacy' | 'terms'

const api = async <T,>(path: string, options?: RequestInit, token?: string): Promise<T> => {
  const headers = new Headers(options?.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}${path}`, { ...options, headers })
  if (!response.ok) {
    let detail = ''
    try {
      const body = await response.json() as { detail?: string | { msg?: string }[] }
      detail = typeof body.detail === 'string'
        ? body.detail
        : Array.isArray(body.detail)
          ? body.detail.map(item => item.msg).filter(Boolean).join('; ')
          : ''
    } catch {
      detail = ''
    }
    throw new Error(detail ? `API request failed (${response.status}): ${detail}` : `API request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

const EmptyState = ({ label }: { label: string }) => (
  <div className="empty-state">
    <div className="empty-icon">+</div>
    <h2>No {label} yet</h2>
    <p>Data will appear here once it has been created or uploaded.</p>
    <button className="secondary-button">Get started</button>
  </div>
)

/* ─── Legal Pages ──────────────────────────────────────────── */

const PrivacyPolicy = ({ onBack }: { onBack: () => void }) => (
  <div className="legal-shell">
    <nav className="legal-nav">
      <span className="legal-nav-brand">
        <span className="brand-mark">H</span>
        HackEval <b>AI</b>
      </span>
      <button className="legal-back" onClick={onBack}>Back to sign in</button>
    </nav>
    <div className="legal-content">
      <h1>Privacy Policy</h1>
      <span className="legal-date">Last updated: October 2025</span>

      <h2>1. What we collect</h2>
      <p>We collect the information you provide when you register and use HackEval. This includes your email address, name, and any project content you submit through the platform.</p>

      <h2>2. How we use it</h2>
      <p>We use your data solely to operate the HackEval platform. This means authenticating your account, displaying your submissions, and running automated evaluations on code you upload. We do not sell your data.</p>

      <h2>3. Code execution</h2>
      <p>Source code you submit for evaluation is run in an isolated sandbox environment. It is not stored beyond the evaluation period unless you have an active submission on the platform.</p>

      <h2>4. Data retention</h2>
      <p>Your account data is retained while your account is active. You may request deletion of your account and associated data by contacting us.</p>

      <h2>5. Third parties</h2>
      <p>We use Google Fonts (Inter, DM Mono) for typography, loaded from Google's CDN. No analytics trackers, advertising networks, or session-recording tools are used on this platform.</p>

      <h2>6. Security</h2>
      <p>All API communication is over HTTPS. Passwords are hashed and never stored in plain text. Access tokens expire and are not persisted server-side.</p>

      <h2>7. Contact</h2>
      <p>For privacy-related requests, email us at <a href="mailto:privacy@hackeval.ai">privacy@hackeval.ai</a>.</p>

      <div className="legal-footer">
        <p>HackEval AI — Automated Evaluation Engine</p>
      </div>
    </div>
  </div>
)

const TermsAndConditions = ({ onBack }: { onBack: () => void }) => (
  <div className="legal-shell">
    <nav className="legal-nav">
      <span className="legal-nav-brand">
        <span className="brand-mark">H</span>
        HackEval <b>AI</b>
      </span>
      <button className="legal-back" onClick={onBack}>Back to sign in</button>
    </nav>
    <div className="legal-content">
      <h1>Terms and Conditions</h1>
      <span className="legal-date">Last updated: October 2025</span>

      <h2>1. Acceptance</h2>
      <p>By creating an account or using HackEval, you agree to these terms. If you do not agree, do not use the platform.</p>

      <h2>2. Accounts</h2>
      <p>You are responsible for the security of your account. Do not share credentials. Accounts may only be used by the person they were created for.</p>

      <h2>3. Submissions</h2>
      <ul>
        <li>You retain ownership of the code and content you submit.</li>
        <li>By submitting, you grant HackEval a limited license to run, evaluate, and display your submission within the platform for the duration of the event.</li>
        <li>Submissions must be your own original work. Plagiarism is grounds for immediate disqualification.</li>
      </ul>

      <h2>4. Code execution</h2>
      <p>Submitted code runs in a restricted, sandboxed environment. You may not submit code designed to escape the sandbox, access the host network, or disrupt other users. Violations result in immediate account termination.</p>

      <h2>5. Prohibited conduct</h2>
      <ul>
        <li>Attempting to manipulate scores or leaderboard data</li>
        <li>Submitting malicious code or payloads</li>
        <li>Impersonating other participants or organizers</li>
        <li>Using the platform in any way that violates applicable law</li>
      </ul>

      <h2>6. Platform availability</h2>
      <p>HackEval is provided as-is. We do not guarantee uninterrupted access or that evaluations will complete within any specific time frame.</p>

      <h2>7. Termination</h2>
      <p>We reserve the right to suspend or terminate accounts that violate these terms, without prior notice.</p>

      <h2>8. Governing law</h2>
      <p>These terms are governed by the laws of India. Disputes shall be resolved in the courts of the jurisdiction in which HackEval operates.</p>

      <h2>9. Contact</h2>
      <p>Questions about these terms: <a href="mailto:legal@hackeval.ai">legal@hackeval.ai</a>.</p>

      <div className="legal-footer">
        <p>HackEval AI — Automated Evaluation Engine</p>
      </div>
    </div>
  </div>
)

/* ─── Login ────────────────────────────────────────────────── */

const Login = ({
  onLogin,
  onNavigate,
}: {
  onLogin: (role: UserRole, token: string, name: string) => void
  onNavigate: (view: AppView) => void
}) => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [role, setRole] = useState<UserRole>('PARTICIPANT')
  const [error, setError] = useState('')

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    try {
      const result = await api<{ access_token: string; role: UserRole }>('/api/auth/login', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: email.trim().toLowerCase(), password }),
      })
      onLogin(result.role, result.access_token, result.role === 'ORGANIZER' ? 'Admin Host' : 'Participant')
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to sign in')
    }
  }

  const fillDemo = (demoRole: UserRole) => {
    setRole(demoRole)
    const accounts = {
      PARTICIPANT: ['participant@hackeval.ai', 'Participant123!'],
      ORGANIZER: ['host@hackeval.ai', 'HostAdmin123!'],
      JUDGE: ['judge@hackeval.ai', 'Judge123!'],
      ADMIN: ['admin@hackeval.ai', 'Admin123!'],
    } as const
    setEmail(accounts[demoRole][0])
    setPassword(accounts[demoRole][1])
    setError('')
  }

  return (
    <div className="auth-shell">
      {/* Left panel */}
      <div className="auth-visual">
        <div className="auth-grid" />
        <div className="auth-brand">
          <span className="brand-mark">H</span>
          <span>HackEval <b>AI</b></span>
          <span className="brand-badge">BETA</span>
        </div>
        <div className="auth-hero-copy">
          <span className="eyebrow">AUTOMATED EVALUATION ENGINE</span>
          <h1>Run hackathons.<br /><strong>Score submissions automatically.</strong></h1>
          <p>
            HackEval handles registration, team formation, code submission, and
            AI-assisted evaluation in one platform. Organizers get a structured
            leaderboard. Participants get clear, consistent feedback.
          </p>
        </div>
        <div className="auth-visual-footer">
          <span>HACKEVAL.AI</span>
          <span>BETA</span>
        </div>
      </div>

      {/* Right panel */}
      <div className="auth-panel">
        <div className="auth-card">
          <span className="mobile-brand">
            <span className="brand-mark">H</span>
            HackEval <b>AI</b>
          </span>
          <div className="auth-card-header">
            <span className="auth-kicker">SIGN IN</span>
            <span className="online-status"><i />System online</span>
          </div>
          <h2>Welcome back</h2>
          <p className="auth-subtitle">Sign in to continue to your workspace.</p>

          <div className="role-switch">
            {(['PARTICIPANT', 'ORGANIZER', 'JUDGE', 'ADMIN'] as UserRole[]).map(item => (
              <button
                type="button"
                key={item}
                className={role === item ? 'selected' : ''}
                onClick={() => fillDemo(item)}
              >
                <span className="role-icon">{item === 'PARTICIPANT' ? '#' : item === 'ORGANIZER' ? '@' : item === 'JUDGE' ? '*' : '!'}</span>
                <span>{item === 'ORGANIZER' ? 'Admin Host' : item[0] + item.slice(1).toLowerCase()}</span>
                <small>{item === 'ORGANIZER' ? 'Create and manage events' : item === 'PARTICIPANT' ? 'Join and submit projects' : item === 'JUDGE' ? 'Review submissions' : 'Manage platform'}</small>
              </button>
            ))}
          </div>

          <form onSubmit={submit}>
            <label>
              Email address
              <input type="email" required value={email} onChange={event => setEmail(event.target.value)} placeholder="you@company.com" />
            </label>
            <label>
              Password
              <div className="password-field">
                <input type={showPassword ? 'text' : 'password'} required value={password} onChange={event => setPassword(event.target.value)} placeholder="Enter your password" />
                <button type="button" onClick={() => setShowPassword(current => !current)} aria-label={showPassword ? 'Hide password' : 'Show password'}>
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
            </label>
            {error && <div className="auth-error">{error}</div>}
            <button className="auth-submit">Sign in <span>→</span></button>
          </form>

          <div className="auth-divider"><span>or</span></div>
          <button type="button" className="demo-link" onClick={() => fillDemo(role)}>Use demo account <span>↗</span></button>

          <p className="auth-legal">
            By continuing, you agree to our{' '}
            <button type="button" className="demo-link" style={{ display: 'inline', margin: 0 }} onClick={() => onNavigate('terms')}>Terms and Conditions</button>
            {' '}and{' '}
            <button type="button" className="demo-link" style={{ display: 'inline', margin: 0 }} onClick={() => onNavigate('privacy')}>Privacy Policy</button>.
          </p>
        </div>
      </div>
    </div>
  )
}

/* ─── App shell ────────────────────────────────────────────── */

const App = () => {
  const [view, setView] = useState<AppView>('app')
  const [session, setSession] = useState<{ role: UserRole; token: string; name: string } | null>(null)
  const [page, setPage] = useState<Page>('Overview')
  const [hackathons, setHackathons] = useState<Hackathon[]>([])
  const [submissions, setSubmissions] = useState<Submission[]>([])
  const [teams, setTeams] = useState<Team[]>([])
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([])
  const [analytics, setAnalytics] = useState<Analytics | null>(null)
  const [leaderboardHackathonId, setLeaderboardHackathonId] = useState('')
  const [error, setError] = useState('')
  const [compactMode, setCompactMode] = useState(() => localStorage.getItem('hackeval-compact-mode') === 'true')
  const [emailUpdates, setEmailUpdates] = useState(() => localStorage.getItem('hackeval-email-updates') !== 'false')
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', start_date: '', end_date: '', registration_deadline: '' })
  const [showSubmit, setShowSubmit] = useState(false)
  const [showTeam, setShowTeam] = useState(false)
  const [teamForm, setTeamForm] = useState({ name: '', description: '', hackathon_id: '' })
  const [inviteCode, setInviteCode] = useState('')
  const [submissionForm, setSubmissionForm] = useState({ hackathon_id: '', team_id: '', project_name: '', project_description: '', problem_statement: '', solution: '', technologies: '', github_url: '', live_demo_url: '', artifact_ids: [] as string[] })
  const [uploading, setUploading] = useState(false)
  const [judgeForm, setJudgeForm] = useState({ submission_id: '', score: '80', comments: '' })
  const [sandboxForm, setSandboxForm] = useState({ source_archive_id: '', language: 'python', stdin: '', expected_stdout: '' })
  const [sandboxResult, setSandboxResult] = useState<{ passed?: boolean; tests?: { passed: boolean; stdout: string; stderr: string }[] } | null>(null)

  /* Legal views — shown before/without session */
  if (view === 'privacy') return <PrivacyPolicy onBack={() => setView('app')} />
  if (view === 'terms') return <TermsAndConditions onBack={() => setView('app')} />

  const loadLeaderboard = async (hackathonId: string) => {
    if (!session || !hackathonId) { setLeaderboard([]); return }
    const leaderboardData = await api<{ entries: LeaderboardEntry[] }>(`/api/leaderboard/${hackathonId}`, undefined, session.token)
    setLeaderboard(leaderboardData.entries)
  }

  const loadData = async () => {
    if (!session) return
    const currentSession = session
    try {
      const [hackathonData, submissionData, teamData] = await Promise.all([
        api<Hackathon[]>('/api/hackathons', undefined, session?.token),
        api<Submission[]>('/api/submissions', undefined, session?.token),
        api<Team[]>('/api/teams', undefined, session?.token),
      ])
      setHackathons(hackathonData)
      setSubmissions(submissionData)
      setTeams(teamData)
      const selectedHackathonId = hackathonData.some(item => item.id === leaderboardHackathonId)
        ? leaderboardHackathonId
        : hackathonData[0]?.id ?? ''
      setLeaderboardHackathonId(selectedHackathonId)
      await loadLeaderboard(selectedHackathonId)
      if (currentSession.role === 'ORGANIZER' || currentSession.role === 'ADMIN' || currentSession.role === 'JUDGE') {
        const dashboardPath = currentSession.role === 'ORGANIZER' ? '/api/dashboard/organizer' : currentSession.role === 'JUDGE' ? '/api/dashboard/judge' : '/api/dashboard/admin'
        setAnalytics(await api<Analytics>(dashboardPath, undefined, currentSession.token))
      } else {
        setAnalytics(null)
      }
      setError('')
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to load data')
    }
  }

  const updateCompactMode = (enabled: boolean) => {
    setCompactMode(enabled)
    localStorage.setItem('hackeval-compact-mode', String(enabled))
  }

  const updateEmailUpdates = (enabled: boolean) => {
    setEmailUpdates(enabled)
    localStorage.setItem('hackeval-email-updates', String(enabled))
  }

  const createSubmission = async (event: FormEvent) => {
    event.preventDefault()
    if (!session) return
    try {
      await api('/api/submissions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...submissionForm, technologies: submissionForm.technologies.split(',').map(item => item.trim()).filter(Boolean), live_demo_url: submissionForm.live_demo_url || null }) }, session.token)
      setShowSubmit(false)
      await loadData()
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'Unable to submit project') }
  }

  const submissionTeams = teams.filter(item => item.hackathon_id === submissionForm.hackathon_id)

  const createTeam = async (event: FormEvent) => {
    event.preventDefault()
    if (!session) return
    try {
      await api('/api/teams', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(teamForm) }, session.token)
      setShowTeam(false)
      setTeamForm({ name: '', description: '', hackathon_id: '' })
      await loadData()
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'Unable to create team') }
  }

  const joinTeam = async (event: FormEvent) => {
    event.preventDefault()
    if (!session) return
    try {
      await api('/api/teams/join', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ invite_code: inviteCode.trim() }) }, session.token)
      setInviteCode('')
      await loadData()
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'Unable to join team') }
  }

  const uploadArtifact = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file || !session) return
    setUploading(true)
    try {
      const body = new FormData()
      body.append('file', file)
      const artifact = await api<{ id: string }>('/api/uploads', { method: 'POST', body }, session.token)
      setSubmissionForm(current => ({ ...current, artifact_ids: [...current.artifact_ids, artifact.id] }))
      setError('')
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'Unable to upload artifact') }
    finally { setUploading(false) }
  }

  const evaluateSubmission = async (event: FormEvent) => {
    event.preventDefault()
    if (!session) return
    try {
      await api('/api/submissions/judges/evaluate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ submission_id: judgeForm.submission_id, score: Number(judgeForm.score), comments: judgeForm.comments, approved: true, criteria: {} }) }, session.token)
      await loadData()
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'Unable to save evaluation') }
  }

  const runSandbox = async (event: FormEvent) => {
    event.preventDefault()
    if (!session) return
    try {
      const result = await api<typeof sandboxResult>('/api/sandbox/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          language: sandboxForm.language,
          source_archive_id: sandboxForm.source_archive_id.trim(),
          tests: [{ stdin: sandboxForm.stdin, ...(sandboxForm.expected_stdout ? { expected_stdout: sandboxForm.expected_stdout } : {}) }],
        }),
      }, session.token)
      setSandboxResult(result)
      setError('')
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'Unable to run sandbox tests') }
  }

  // eslint-disable-next-line react-hooks/rules-of-hooks
  useEffect(() => {
    if (session) void loadData()
  }, [session])

  const createHackathon = async (event: FormEvent) => {
    event.preventDefault()
    if (!session) return
    try {
      await api('/api/hackathons', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form, start_date: new Date(form.start_date).toISOString(), end_date: new Date(form.end_date).toISOString(),
          registration_deadline: new Date(form.registration_deadline).toISOString(), max_participants: 500, max_team_size: 5,
          rules: 'Build an original project and document all external APIs.', rubric: [{ criterion: 'Innovation', weight: 25 }, { criterion: 'Functionality', weight: 25 }, { criterion: 'Impact', weight: 25 }, { criterion: 'Presentation', weight: 25 }],
        }),
      }, session.token)
      setShowCreate(false)
      setForm({ name: '', description: '', start_date: '', end_date: '', registration_deadline: '' })
      await loadData()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to create hackathon')
    }
  }

  if (!session) return <Login onLogin={(role, token, name) => setSession({ role, token, name })} onNavigate={setView} />

  const title = page === 'Overview' ? 'Workspace' : page
  const description = page === 'Overview'
    ? 'Showing data created or uploaded by you.'
    : `Manage your ${page.toLowerCase()}.`

  /* Nav labels — text only, no emoji or decorative symbols */
  const navItems: { label: Page; abbr: string }[] = [
    { label: 'Overview', abbr: 'OV' },
    { label: 'Hackathons', abbr: 'HK' },
    { label: 'Submissions', abbr: 'SB' },
    { label: 'Leaderboard', abbr: 'LB' },
    { label: 'Analytics', abbr: 'AN' },
    { label: 'Settings', abbr: 'ST' },
  ]

  return (
    <div className={compactMode ? 'app-shell compact-mode' : 'app-shell'}>
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark">H</div><span>HackEval <b>AI</b></span></div>
        <div className="workspace-label">{session.role === 'ORGANIZER' ? 'HOST CONSOLE' : session.role === 'PARTICIPANT' ? 'PARTICIPANT HUB' : `${session.role} CONSOLE`}</div>
        <div className="workspace-select">
          <span className="workspace-avatar">U</span>
          <span>My workspace</span>
          <span className="workspace-chevron">v</span>
        </div>
        <nav>
          {navItems.map(({ label, abbr }) => (
            <button key={label} onClick={() => setPage(label)} className={page === label ? 'nav-item active' : 'nav-item'}>
              <span className="nav-icon">{abbr}</span><span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-footer"><div className="status-dot" /> API connected</div>
      </aside>

      <main className="main-content">
        <header className="page-header">
          <div className="breadcrumb">Workspace <span>/</span> {title}</div>
          <div className="header-actions">
            <span className="role-badge">{session.role === 'ORGANIZER' ? 'Admin Host' : session.role[0] + session.role.slice(1).toLowerCase()}</span>
            <button className="icon-button" aria-label="Notifications">N</button>
            <button className="avatar-button">{session.name[0]}</button>
            <button className="primary-button" onClick={() => void loadData()}>Refresh</button>
            <button className="logout-button" onClick={() => setSession(null)}>Sign out</button>
          </div>
        </header>

        <div className="content-scroll">
          {error && <div className="card" style={{ padding: '14px 18px', color: '#b91c1c', marginBottom: '16px' }}>{error}</div>}

          {/* Overview */}
          {page === 'Overview' && (
            <>
              <section className="welcome-banner">
                <div>
                  <span className="eyebrow">{session.role === 'ORGANIZER' ? 'HOST CONSOLE' : session.role === 'PARTICIPANT' ? 'PARTICIPANT HUB' : `${session.role} CONSOLE`}</span>
                  <h1>{session.role === 'ORGANIZER' ? 'Manage your hackathons' : 'Your hackathon workspace'}</h1>
                  <p>{description}</p>
                  <button className="banner-action" onClick={() => session.role === 'ORGANIZER' ? setShowCreate(true) : setPage('Hackathons')}>
                    {session.role === 'ORGANIZER' ? '+ Create hackathon' : 'Browse hackathons'}
                  </button>
                </div>
              </section>

              <section className="metrics">
                <article className="metric-card">
                  <span className="metric-symbol blue-tag">HK</span>
                  <div className="metric-copy">
                    <span>Hackathons</span>
                    <strong>{hackathons.length}</strong>
                    <small>Created by you</small>
                  </div>
                </article>
                <article className="metric-card">
                  <span className="metric-symbol slate-tag">SB</span>
                  <div className="metric-copy">
                    <span>Submissions</span>
                    <strong>{submissions.length}</strong>
                    <small>Uploaded projects</small>
                  </div>
                </article>
                <article className="metric-card">
                  <span className="metric-symbol green-tag">TM</span>
                  <div className="metric-copy">
                    <span>Teams</span>
                    <strong>{hackathons.reduce((total, item) => total + item.teams, 0)}</strong>
                    <small>Registered teams</small>
                  </div>
                </article>
              </section>

              {hackathons.length === 0 && submissions.length === 0
                ? <EmptyState label="data" />
                : <div className="dashboard-grid">
                  <section className="card"><h2>Your hackathons</h2>{hackathons.map(item => <p key={item.id}><b>{item.name}</b> · {item.status}</p>)}</section>
                  <section className="card"><h2>Your submissions</h2>{submissions.map(item => <p key={item.id}><b>{item.project_name}</b> · {item.status}</p>)}</section>
                </div>}
            </>
          )}

          {/* Hackathons */}
          {page === 'Hackathons' && <>
            {session.role === 'ORGANIZER' && <button className="primary-button create-inline" onClick={() => setShowCreate(true)}>+ Create hackathon</button>}
            {session.role === 'PARTICIPANT' && <div className="action-row">
              <button className="primary-button" onClick={() => setShowTeam(true)}>+ Create team</button>
              <form onSubmit={joinTeam}>
                <input required placeholder="Invite code" value={inviteCode} onChange={event => setInviteCode(event.target.value)} />
                <button className="secondary-button">Join team</button>
              </form>
            </div>}
            {hackathons.length
              ? <section className="card">{hackathons.map(item => <div className="hackathon-row" key={item.id}><div><h2>{item.name}</h2><p>{item.description}</p><small>{item.status} · {item.participants} participants · {item.teams} teams</small></div><button className="secondary-button">Open</button></div>)}</section>
              : <EmptyState label="hackathons" />}
            {session.role === 'PARTICIPANT' && teams.length > 0 && <section className="card team-list"><h2>Your teams</h2>{teams.map(team => <div key={team.id}><b>{team.name}</b><small>{team.invite_code ? `Invite code: ${team.invite_code}` : ''}</small></div>)}</section>}
          </>}

          {/* Submissions */}
          {page === 'Submissions' && <>
            {session.role === 'PARTICIPANT' && <button className="primary-button create-inline" onClick={() => setShowSubmit(true)}>+ Submit project</button>}
            {submissions.length
              ? <section className="card">{submissions.map(item => <div key={item.id} className="hackathon-row"><div><h2>{item.project_name}</h2><p>{item.team_name} · {item.status}</p><small>Score: {item.score ?? 'Not evaluated'} · Risk: {item.risk ?? 'Not analyzed'}</small></div></div>)}</section>
              : <EmptyState label="submissions" />}
            {(session.role === 'JUDGE' || session.role === 'ADMIN') && <>
              <form className="card inline-form" onSubmit={evaluateSubmission}>
                <h2>Manual evaluation</h2>
                <select required value={judgeForm.submission_id} onChange={event => setJudgeForm({ ...judgeForm, submission_id: event.target.value })}>
                  <option value="">Select a submission</option>
                  {submissions.map(item => <option key={item.id} value={item.id}>{item.project_name}</option>)}
                </select>
                <input required type="number" min="0" max="100" value={judgeForm.score} onChange={event => setJudgeForm({ ...judgeForm, score: event.target.value })} />
                <textarea required placeholder="Judge comments" value={judgeForm.comments} onChange={event => setJudgeForm({ ...judgeForm, comments: event.target.value })} />
                <button className="primary-button">Save evaluation</button>
              </form>
              <form className="card sandbox-form" onSubmit={runSandbox}>
                <h2>Run isolated tests</h2>
                <p>Paste the uploaded source artifact ID. Code runs only in the restricted sandbox.</p>
                <input required placeholder="Source artifact ID" value={sandboxForm.source_archive_id} onChange={event => setSandboxForm({ ...sandboxForm, source_archive_id: event.target.value })} />
                <select value={sandboxForm.language} onChange={event => setSandboxForm({ ...sandboxForm, language: event.target.value })}>
                  <option value="python">Python</option>
                  <option value="javascript">JavaScript</option>
                  <option value="java">Java</option>
                  <option value="cpp">C++</option>
                </select>
                <textarea placeholder="Test stdin (optional)" value={sandboxForm.stdin} onChange={event => setSandboxForm({ ...sandboxForm, stdin: event.target.value })} />
                <input placeholder="Expected stdout (optional)" value={sandboxForm.expected_stdout} onChange={event => setSandboxForm({ ...sandboxForm, expected_stdout: event.target.value })} />
                <button className="primary-button">Run sandbox</button>
                {sandboxResult && <div className={sandboxResult.passed ? 'sandbox-success' : 'sandbox-failure'}>
                  {sandboxResult.passed ? 'All tests passed' : 'Test failed'}
                  {sandboxResult.tests?.map((test, index) => <small key={index}>Test {index + 1}: {test.passed ? 'passed' : test.stderr || 'failed'}{test.stdout ? ` · ${test.stdout}` : ''}</small>)}
                </div>}
              </form>
            </>}
          </>}

          {/* Leaderboard */}
          {page === 'Leaderboard' && <>
            {hackathons.length > 0 && <select value={leaderboardHackathonId} onChange={event => { setLeaderboardHackathonId(event.target.value); void loadLeaderboard(event.target.value) }}>
              <option value="">Select a hackathon</option>
              {hackathons.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>}
            {leaderboard.length
              ? <section className="card"><h2>{hackathons.find(item => item.id === leaderboardHackathonId)?.name ?? 'Leaderboard'}</h2>
                {leaderboard.map(item => <div className="hackathon-row" key={`${item.rank}-${item.project}`}>
                  <div><h2>#{item.rank} · {item.project}</h2><p>{item.team} · {item.status}</p><small>Risk: {item.risk ?? 'Not analyzed'}</small></div>
                  <strong>{item.score.toFixed(1)}</strong>
                </div>)}
              </section>
              : <EmptyState label="evaluated submissions" />}
          </>}

          {/* Analytics */}
          {page === 'Analytics' && (
            analytics
              ? <section className="analytics-grid">
                <article className="card analytics-card"><span>Total participants</span><strong>{analytics.total_participants ?? analytics.users ?? 0}</strong><small>Registered users in your workspace</small></article>
                <article className="card analytics-card"><span>Total teams</span><strong>{analytics.total_teams ?? analytics.teams ?? 0}</strong><small>Teams created for your events</small></article>
                <article className="card analytics-card"><span>Submissions</span><strong>{analytics.total_submissions ?? analytics.submissions ?? 0}</strong><small>Projects received</small></article>
                <article className="card analytics-card"><span>Average score</span><strong>{analytics.average_score ?? 0}</strong><small>Across evaluated projects</small></article>
                <article className="card analytics-card"><span>Evaluation progress</span><strong>{analytics.evaluation_progress ?? 0}%</strong><small>{analytics.pending_count ?? analytics.flagged_projects ?? analytics.flagged_submissions ?? 0} requiring attention</small></article>
                <article className="card analytics-card"><span>Audit events</span><strong>{analytics.audit_events ?? analytics.evaluated_projects ?? 0}</strong><small>Recorded review activity</small></article>
              </section>
              : <EmptyState label="analytics" />
          )}

          {/* Settings */}
          {page === 'Settings' && (
            <section className="card settings-card">
              <div className="settings-heading">
                <div>
                  <span className="eyebrow">WORKSPACE PREFERENCES</span>
                  <h2>Settings</h2>
                  <p>Control how this dashboard behaves on this device.</p>
                </div>
                <span className="settings-avatar">{session.name[0]}</span>
              </div>
              <label className="setting-row">
                <span><b>Compact dashboard</b><small>Reduce spacing in lists and cards.</small></span>
                <input type="checkbox" checked={compactMode} onChange={event => updateCompactMode(event.target.checked)} />
              </label>
              <label className="setting-row">
                <span><b>Email updates</b><small>Keep notification preferences ready for future workspace alerts.</small></span>
                <input type="checkbox" checked={emailUpdates} onChange={event => updateEmailUpdates(event.target.checked)} />
              </label>
              <div className="setting-row">
                <span><b>Signed in as</b><small>{session.name} · {session.role}</small></span>
                <button className="secondary-button" onClick={() => setSession(null)}>Sign out</button>
              </div>
              <div className="setting-row" style={{ cursor: 'default' }}>
                <span><b>Legal</b><small>Review platform policies</small></span>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button className="secondary-button" onClick={() => setView('privacy')}>Privacy Policy</button>
                  <button className="secondary-button" onClick={() => setView('terms')}>Terms</button>
                </div>
              </div>
            </section>
          )}

          {/* Create hackathon modal */}
          {showCreate && <div className="modal-backdrop"><form className="modal-card" onSubmit={createHackathon}>
            <button type="button" className="modal-close" onClick={() => setShowCreate(false)}>x</button>
            <span className="eyebrow">HOST CONSOLE</span>
            <h2>Create hackathon</h2>
            <p>Set up the event details participants will see.</p>
            <input required placeholder="Hackathon name" value={form.name} onChange={event => setForm({ ...form, name: event.target.value })} />
            <textarea required placeholder="Description" value={form.description} onChange={event => setForm({ ...form, description: event.target.value })} />
            <label>Registration deadline<input required type="datetime-local" value={form.registration_deadline} onChange={event => setForm({ ...form, registration_deadline: event.target.value })} /></label>
            <div className="modal-grid">
              <label>Starts<input required type="datetime-local" value={form.start_date} onChange={event => setForm({ ...form, start_date: event.target.value })} /></label>
              <label>Ends<input required type="datetime-local" value={form.end_date} onChange={event => setForm({ ...form, end_date: event.target.value })} /></label>
            </div>
            <button className="primary-button">Publish hackathon</button>
          </form></div>}

          {/* Submit project modal */}
          {showSubmit && <div className="modal-backdrop"><form className="modal-card" onSubmit={createSubmission}>
            <button type="button" className="modal-close" onClick={() => setShowSubmit(false)}>x</button>
            <span className="eyebrow">PARTICIPANT HUB</span>
            <h2>Submit your project</h2>
            <select required value={submissionForm.hackathon_id} onChange={event => setSubmissionForm({ ...submissionForm, hackathon_id: event.target.value, team_id: '' })}><option value="">Hackathon</option>{hackathons.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
            <select required value={submissionForm.team_id} onChange={event => setSubmissionForm({ ...submissionForm, team_id: event.target.value })} disabled={!submissionForm.hackathon_id}><option value="">Team</option>{submissionTeams.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
            <input required placeholder="Project name" value={submissionForm.project_name} onChange={event => setSubmissionForm({ ...submissionForm, project_name: event.target.value })} />
            <textarea required minLength={30} placeholder="Project description" value={submissionForm.project_description} onChange={event => setSubmissionForm({ ...submissionForm, project_description: event.target.value })} />
            <textarea required placeholder="Problem statement" value={submissionForm.problem_statement} onChange={event => setSubmissionForm({ ...submissionForm, problem_statement: event.target.value })} />
            <textarea required placeholder="Solution" value={submissionForm.solution} onChange={event => setSubmissionForm({ ...submissionForm, solution: event.target.value })} />
            <input required placeholder="Technologies (comma separated)" value={submissionForm.technologies} onChange={event => setSubmissionForm({ ...submissionForm, technologies: event.target.value })} />
            <input required type="url" placeholder="GitHub URL" value={submissionForm.github_url} onChange={event => setSubmissionForm({ ...submissionForm, github_url: event.target.value })} />
            <label>Artifact upload<input type="file" accept=".pdf,.ppt,.pptx,video/mp4,video/webm,video/quicktime" onChange={uploadArtifact} disabled={uploading} /></label>
            {submissionForm.artifact_ids.length > 0 && <small>{submissionForm.artifact_ids.length} artifact uploaded</small>}
            <button className="primary-button">Submit project</button>
          </form></div>}

          {/* Create team modal */}
          {showTeam && <div className="modal-backdrop"><form className="modal-card" onSubmit={createTeam}>
            <button type="button" className="modal-close" onClick={() => setShowTeam(false)}>x</button>
            <span className="eyebrow">PARTICIPANT HUB</span>
            <h2>Create a team</h2>
            <select required value={teamForm.hackathon_id} onChange={event => setTeamForm({ ...teamForm, hackathon_id: event.target.value })}><option value="">Hackathon</option>{hackathons.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select>
            <input required minLength={3} placeholder="Team name" value={teamForm.name} onChange={event => setTeamForm({ ...teamForm, name: event.target.value })} />
            <textarea required minLength={5} placeholder="Team description" value={teamForm.description} onChange={event => setTeamForm({ ...teamForm, description: event.target.value })} />
            <button className="primary-button">Create team</button>
          </form></div>}
        </div>
      </main>
    </div>
  )
}

export default App
