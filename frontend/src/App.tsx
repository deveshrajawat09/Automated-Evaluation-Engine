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
type Team = { id: string; name: string; hackathon_id: string }
type LeaderboardEntry = {
  rank: number
  team: string
  project: string
  score: number
  risk: number | null
  status: string
}

type Page = 'Overview' | 'Hackathons' | 'Submissions' | 'Leaderboard'
type UserRole = 'PARTICIPANT' | 'ORGANIZER' | 'JUDGE' | 'ADMIN'

const api = async <T,>(path: string, options?: RequestInit, token?: string): Promise<T> => {
  const headers = new Headers(options?.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`http://localhost:8000${path}`, { ...options, headers })
  if (!response.ok) throw new Error(`API request failed (${response.status})`)
  return response.json() as Promise<T>
}

const EmptyState = ({ label }: { label: string }) => (
  <div className="empty-state">
    <div className="empty-icon">+</div>
    <h2>No {label} yet</h2>
    <p>User-uploaded data will appear here after it is created.</p>
    <button className="secondary-button">Get started</button>
  </div>
)

const Login = ({ onLogin }: { onLogin: (role: UserRole, token: string, name: string) => void }) => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
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
    const accounts = { PARTICIPANT: ['participant@hackeval.ai', 'Participant123!'], ORGANIZER: ['host@hackeval.ai', 'HostAdmin123!'], JUDGE: ['judge@hackeval.ai', 'Judge123!'], ADMIN: ['admin@hackeval.ai', 'Admin123!'] } as const
    setEmail(accounts[demoRole][0])
    setPassword(accounts[demoRole][1])
    setError('')
  }
  return <div className="auth-shell">
    <div className="auth-visual"><div className="auth-brand"><span className="brand-mark">H</span> HackEval <b>AI</b></div><div><span className="eyebrow">THE HACKATHON OPERATING SYSTEM</span><h1>Build. Compete.<br /><em>Get recognized.</em></h1><p>One modern platform for every hackathon journey.</p></div><div className="auth-orbit">✦</div></div>
    <div className="auth-panel"><div className="auth-card"><span className="mobile-brand">HackEval <b>AI</b></span><h2>Welcome back</h2><p className="auth-subtitle">Sign in to continue to your hackathon workspace.</p><div className="role-switch">{(['PARTICIPANT', 'ORGANIZER', 'JUDGE', 'ADMIN'] as UserRole[]).map(item => <button type="button" key={item} className={role === item ? 'selected' : ''} onClick={() => fillDemo(item)}>{item === 'ORGANIZER' ? 'Admin Host' : item[0] + item.slice(1).toLowerCase()}<small>{item === 'ORGANIZER' ? 'Create & manage events' : item === 'PARTICIPANT' ? 'Join & submit projects' : item === 'JUDGE' ? 'Review submissions' : 'Manage platform'}</small></button>)}</div><form onSubmit={submit}><label>Email address<input type="email" required value={email} onChange={event => setEmail(event.target.value)} placeholder="Choose a role above" /></label><label>Password<input type="password" required value={password} onChange={event => setPassword(event.target.value)} placeholder="Enter your password" /></label>{error && <div className="auth-error">{error}</div>}<button className="auth-submit">Sign in <span>→</span></button></form><button type="button" className="demo-link" onClick={() => fillDemo(role)}>Use demo account</button></div></div>
  </div>
}

const App = () => {
  const [session, setSession] = useState<{ role: UserRole; token: string; name: string } | null>(null)
  const [page, setPage] = useState<Page>('Overview')
  const [hackathons, setHackathons] = useState<Hackathon[]>([])
  const [submissions, setSubmissions] = useState<Submission[]>([])
  const [teams, setTeams] = useState<Team[]>([])
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([])
  const [leaderboardHackathonId, setLeaderboardHackathonId] = useState('')
  const [error, setError] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', start_date: '', end_date: '', registration_deadline: '' })
  const [showSubmit, setShowSubmit] = useState(false)
  const [submissionForm, setSubmissionForm] = useState({ hackathon_id: '', team_id: '', project_name: '', project_description: '', problem_statement: '', solution: '', technologies: '', github_url: '', live_demo_url: '' })
  const [judgeForm, setJudgeForm] = useState({ submission_id: '', score: '80', comments: '' })

  const loadLeaderboard = async (hackathonId: string) => {
    if (!session || !hackathonId) {
      setLeaderboard([])
      return
    }
    const leaderboardData = await api<{ entries: LeaderboardEntry[] }>(`/api/leaderboard/${hackathonId}`, undefined, session.token)
    setLeaderboard(leaderboardData.entries)
  }

  const loadData = async () => {
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
      setError('')
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to load user data')
    }

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

  const evaluateSubmission = async (event: FormEvent) => {
    event.preventDefault()
    if (!session) return
    try {
      await api('/api/submissions/judges/evaluate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ submission_id: judgeForm.submission_id, score: Number(judgeForm.score), comments: judgeForm.comments, approved: true, criteria: {} }) }, session.token)
      await loadData()
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'Unable to save evaluation') }
  }

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

  if (!session) return <Login onLogin={(role, token, name) => setSession({ role, token, name })} />

  const title = page === 'Overview' ? 'Workspace' : page
  const description = page === 'Overview'
    ? 'Only data created or uploaded by users is shown.'
    : `Manage your user-created ${page.toLowerCase()}.`

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark">H</div><span>HackEval <b>AI</b></span></div>
        <div className="workspace-label">{session.role === 'ORGANIZER' ? 'HOST CONSOLE' : session.role === 'PARTICIPANT' ? 'PARTICIPANT HUB' : `${session.role} CONSOLE`}</div>
        <div className="workspace-select"><span className="workspace-avatar">U</span><span>My workspace</span><span className="workspace-chevron">⌄</span></div>
        <nav>
          {(['Overview', 'Hackathons', 'Submissions', 'Leaderboard'] as Page[]).map((item, index) => (
            <button key={item} onClick={() => setPage(item)} className={page === item ? 'nav-item active' : 'nav-item'}>
              <span className="nav-icon">{['⌂', '⚑', '▤', '♛'][index]}</span><span>{item}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-footer"><div className="status-dot" /> API connected</div>
      </aside>
      <main className="main-content">
        <header className="page-header">
          <div className="breadcrumb">Workspace <span>/</span> {title}</div>
          <div className="header-actions"><span className="role-pill">{session.role === 'ORGANIZER' ? 'Admin Host' : session.role[0] + session.role.slice(1).toLowerCase()}</span><button className="icon-button" aria-label="Notifications">◌</button><button className="avatar-button">{session.name[0]}</button><button className="primary-button" onClick={() => void loadData()}>↻&nbsp; Refresh data</button><button className="logout-button" onClick={() => setSession(null)}>Sign out</button></div>
        </header>
        <div className="content-scroll">
          {error && <div className="card" style={{ padding: '16px', color: '#b42318' }}>{error}</div>}
          {page === 'Overview' && (
            <>
              <section className="welcome-banner">
                <div><span className="eyebrow">{session.role === 'ORGANIZER' ? 'HOST CONSOLE' : session.role === 'PARTICIPANT' ? 'PARTICIPANT HUB' : `${session.role} CONSOLE`}</span><h1>{session.role === 'ORGANIZER' ? 'Run your next hackathon' : 'Find your next challenge'}</h1><p>{session.role === 'ORGANIZER' ? 'Create events, manage submissions, and discover standout teams.' : 'Explore events, build your team, and submit your best work.'}</p><button className="banner-action" onClick={() => session.role === 'ORGANIZER' ? setShowCreate(true) : setPage('Hackathons')}>{session.role === 'ORGANIZER' ? '+ Create hackathon' : 'Browse hackathons →'}</button></div>
                <div className="banner-orb">✦</div>
              </section>
              <section className="metrics">
                <article className="metric-card"><span className="metric-symbol purple">⚑</span><div className="metric-copy"><span>Hackathons</span><strong>{hackathons.length}</strong><small>Created by you</small></div></article>
                <article className="metric-card"><span className="metric-symbol blue">▤</span><div className="metric-copy"><span>Submissions</span><strong>{submissions.length}</strong><small>Uploaded projects</small></div></article>
                <article className="metric-card"><span className="metric-symbol green">♟</span><div className="metric-copy"><span>Teams</span><strong>{hackathons.reduce((total, item) => total + item.teams, 0)}</strong><small>Registered members</small></div></article>
              </section>
              {hackathons.length === 0 && submissions.length === 0
                ? <EmptyState label="user data" />
                : <div className="dashboard-grid">
                  <section className="card"><h2>Your hackathons</h2>{hackathons.map(item => <p key={item.id}><b>{item.name}</b> · {item.status}</p>)}</section>
                  <section className="card"><h2>Your submissions</h2>{submissions.map(item => <p key={item.id}><b>{item.project_name}</b> · {item.status}</p>)}</section>
                </div>}
            </>
          )}
          {page === 'Hackathons' && <>{session.role === 'ORGANIZER' && <button className="primary-button create-inline" onClick={() => setShowCreate(true)}>+ Create hackathon</button>}{hackathons.length ? <section className="card">{hackathons.map(item => <div className="hackathon-row" key={item.id}><div><h2>{item.name}</h2><p>{item.description}</p><small>{item.status} · {item.participants} participants · {item.teams} teams</small></div><button className="secondary-button">Open</button></div>)}</section> : <EmptyState label="hackathons" />}</>}
          {page === 'Submissions' && <>{session.role === 'PARTICIPANT' && <button className="primary-button create-inline" onClick={() => setShowSubmit(true)}>+ Submit project</button>}{submissions.length ? <section className="card">{submissions.map(item => <div key={item.id}><h2>{item.project_name}</h2><p>{item.team_name} · {item.status}</p><p>Score: {item.score ?? 'Not evaluated'} · Risk: {item.risk ?? 'Not analyzed'}</p></div>)}</section> : <EmptyState label="submissions" />}{(session.role === 'JUDGE' || session.role === 'ADMIN') && <form className="card inline-form" onSubmit={evaluateSubmission}><h2>Manual evaluation</h2><select required value={judgeForm.submission_id} onChange={event => setJudgeForm({ ...judgeForm, submission_id: event.target.value })}><option value="">Select a submission</option>{submissions.map(item => <option key={item.id} value={item.id}>{item.project_name}</option>)}</select><input required type="number" min="0" max="100" value={judgeForm.score} onChange={event => setJudgeForm({ ...judgeForm, score: event.target.value })} /><textarea required placeholder="Judge comments" value={judgeForm.comments} onChange={event => setJudgeForm({ ...judgeForm, comments: event.target.value })} /><button className="primary-button">Save evaluation</button></form>}</>}
          {page === 'Leaderboard' && <>{hackathons.length > 0 && <select value={leaderboardHackathonId} onChange={event => { setLeaderboardHackathonId(event.target.value); void loadLeaderboard(event.target.value) }}><option value="">Select a hackathon</option>{hackathons.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select>}{leaderboard.length ? <section className="card"><h2>{hackathons.find(item => item.id === leaderboardHackathonId)?.name ?? 'Leaderboard'}</h2>{leaderboard.map(item => <div className="hackathon-row" key={`${item.rank}-${item.project}`}><div><h2>#{item.rank} · {item.project}</h2><p>{item.team} · {item.status}</p><small>Risk: {item.risk ?? 'Not analyzed'}</small></div><strong>{item.score.toFixed(1)}</strong></div>)}</section> : <EmptyState label="evaluated submissions" />}</>}
          {showCreate && <div className="modal-backdrop"><form className="modal-card" onSubmit={createHackathon}><button type="button" className="modal-close" onClick={() => setShowCreate(false)}>×</button><span className="eyebrow">HOST CONSOLE</span><h2>Create hackathon</h2><p>Set up the event details participants will see.</p><input required placeholder="Hackathon name" value={form.name} onChange={event => setForm({ ...form, name: event.target.value })} /><textarea required placeholder="Description" value={form.description} onChange={event => setForm({ ...form, description: event.target.value })} /><label>Registration deadline<input required type="datetime-local" value={form.registration_deadline} onChange={event => setForm({ ...form, registration_deadline: event.target.value })} /></label><div className="modal-grid"><label>Starts<input required type="datetime-local" value={form.start_date} onChange={event => setForm({ ...form, start_date: event.target.value })} /></label><label>Ends<input required type="datetime-local" value={form.end_date} onChange={event => setForm({ ...form, end_date: event.target.value })} /></label></div><button className="primary-button">Publish hackathon</button></form></div>}
          {showSubmit && <div className="modal-backdrop"><form className="modal-card" onSubmit={createSubmission}><button type="button" className="modal-close" onClick={() => setShowSubmit(false)}>×</button><span className="eyebrow">PARTICIPANT HUB</span><h2>Submit your project</h2><select required value={submissionForm.hackathon_id} onChange={event => setSubmissionForm({ ...submissionForm, hackathon_id: event.target.value })}><option value="">Hackathon</option>{hackathons.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select><select required value={submissionForm.team_id} onChange={event => setSubmissionForm({ ...submissionForm, team_id: event.target.value })}><option value="">Team</option>{teams.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select><input required placeholder="Project name" value={submissionForm.project_name} onChange={event => setSubmissionForm({ ...submissionForm, project_name: event.target.value })} /><textarea required minLength={30} placeholder="Project description" value={submissionForm.project_description} onChange={event => setSubmissionForm({ ...submissionForm, project_description: event.target.value })} /><textarea required placeholder="Problem statement" value={submissionForm.problem_statement} onChange={event => setSubmissionForm({ ...submissionForm, problem_statement: event.target.value })} /><textarea required placeholder="Solution" value={submissionForm.solution} onChange={event => setSubmissionForm({ ...submissionForm, solution: event.target.value })} /><input required placeholder="Technologies (comma separated)" value={submissionForm.technologies} onChange={event => setSubmissionForm({ ...submissionForm, technologies: event.target.value })} /><input required type="url" placeholder="GitHub URL" value={submissionForm.github_url} onChange={event => setSubmissionForm({ ...submissionForm, github_url: event.target.value })} /><button className="primary-button">Submit project</button></form></div>}
        </div>
      </main>
    </div>
  )
}

export default App
