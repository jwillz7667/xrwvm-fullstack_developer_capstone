import {useState} from 'react';
import {api} from '../../api.js';
export default function Register({onLogin}) {
  const [error,setError]=useState(''); const [busy,setBusy]=useState(false);
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError('');
    try {const data=Object.fromEntries(new FormData(event.currentTarget)); const result=await api('register',data); onLogin(result.userName); window.location.assign('/dealers');}
    catch(err){setError(err.message);} finally{setBusy(false);}
  }
  return <section className="form-panel"><p className="eyebrow">JOIN THE COMMUNITY</p><h1>Create your account</h1><p>Keep your experience useful for the next driver.</p><form onSubmit={submit}>
    <label>Username<input name="userName" autoComplete="username" required maxLength="150"/></label>
    <div className="form-row"><label>First Name<input name="firstName" autoComplete="given-name" required maxLength="150"/></label><label>Last Name<input name="lastName" autoComplete="family-name" required maxLength="150"/></label></div>
    <label>Email<input name="email" type="email" autoComplete="email" required maxLength="254"/></label>
    <label>Password<input name="password" type="password" autoComplete="new-password" minLength="8" maxLength="256" required/></label>
    <p className="muted">Use a unique password with at least eight characters. Avoid common passwords and personal information.</p>
    {error && <p role="alert" className="error">{error}</p>}<button disabled={busy}>{busy?'Creating account…':'Register'}</button>
  </form><p>Already a member? <a href="/login">Log in</a></p></section>;
}
