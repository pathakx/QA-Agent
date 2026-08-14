import { useState, useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import {
  LogIn, UserPlus, Mail, Lock, User,
  Eye, EyeOff, CheckCircle, Zap, Shield,
  Activity, X, ArrowLeft, Send, KeyRound,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

/* ─────────────────────────────────────────────────────────────
   Animated floating orb
───────────────────────────────────────────────────────────── */
const FloatingOrb = ({ style }) => (
  <motion.div
    style={style}
    animate={{ y: [0, -20, 0], opacity: [0.3, 0.6, 0.3] }}
    transition={{ duration: 6 + Math.random() * 4, repeat: Infinity, ease: 'easeInOut' }}
    className="absolute rounded-full pointer-events-none"
  />
);

/* ─────────────────────────────────────────────────────────────
   Feature badge (left panel)
───────────────────────────────────────────────────────────── */
const FeatureBadge = ({ icon: Icon, label, delay }) => (
  <motion.div
    initial={{ opacity: 0, x: -20 }}
    animate={{ opacity: 1, x: 0 }}
    transition={{ delay, duration: 0.5 }}
    className="flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium"
    style={{
      background: 'rgba(99,102,241,0.15)',
      border: '1px solid rgba(99,102,241,0.3)',
      color: '#a5b4fc',
      backdropFilter: 'blur(8px)',
    }}
  >
    <Icon size={14} className="text-indigo-400" />
    {label}
  </motion.div>
);

/* ─────────────────────────────────────────────────────────────
   Left branding panel
───────────────────────────────────────────────────────────── */
const BrandPanel = () => (
  <div
    className="hidden lg:flex flex-col justify-between relative overflow-hidden"
    style={{ width: '50%', minHeight: '100vh', background: 'linear-gradient(135deg, #0a0d1a 0%, #0d1333 40%, #0f0a2e 100%)' }}
  >
    <div className="absolute inset-0 opacity-[0.04]"
      style={{
        backgroundImage: 'linear-gradient(rgba(99,102,241,1) 1px, transparent 1px), linear-gradient(90deg, rgba(99,102,241,1) 1px, transparent 1px)',
        backgroundSize: '40px 40px',
      }}
    />
    <FloatingOrb style={{ width: 300, height: 300, top: '10%', left: '-80px', background: 'radial-gradient(circle, rgba(99,102,241,0.25) 0%, transparent 70%)' }} />
    <FloatingOrb style={{ width: 200, height: 200, bottom: '20%', right: '-40px', background: 'radial-gradient(circle, rgba(139,92,246,0.2) 0%, transparent 70%)' }} />
    <FloatingOrb style={{ width: 150, height: 150, top: '60%', left: '20%', background: 'radial-gradient(circle, rgba(59,130,246,0.15) 0%, transparent 70%)' }} />

    <div className="relative z-10 p-10">
      <motion.div
        initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold tracking-wider uppercase"
        style={{ background: 'rgba(99,102,241,0.2)', border: '1px solid rgba(99,102,241,0.4)', color: '#818cf8' }}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
        Playwright Engine Active
      </motion.div>
    </div>

    <div className="relative z-10 flex flex-col items-center justify-center flex-1 px-10 py-8 text-center">
      <motion.div initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.7, type: 'spring' }} className="mb-8 relative">
        <div className="w-24 h-24 rounded-2xl flex items-center justify-center relative mx-auto"
          style={{
            background: 'linear-gradient(135deg, rgba(99,102,241,0.3) 0%, rgba(139,92,246,0.3) 100%)',
            border: '1px solid rgba(99,102,241,0.5)',
            boxShadow: '0 0 40px rgba(99,102,241,0.3), inset 0 1px 0 rgba(255,255,255,0.1)',
          }}
        >
          <motion.div animate={{ rotate: 360 }} transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
            className="absolute inset-0 rounded-2xl"
            style={{ background: 'conic-gradient(from 0deg, transparent 70%, rgba(99,102,241,0.6) 100%)' }}
          />
          <Shield size={40} className="text-indigo-300 relative z-10" />
        </div>
        <motion.div animate={{ scale: [1, 1.5], opacity: [0.4, 0] }} transition={{ duration: 2, repeat: Infinity }}
          className="absolute rounded-2xl"
          style={{ width: 96, height: 96, top: 0, left: '50%', transform: 'translateX(-50%)', background: 'rgba(99,102,241,0.2)' }}
        />
      </motion.div>

      <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2, duration: 0.6 }}
        className="text-5xl font-black mb-3 tracking-tight"
        style={{ background: 'linear-gradient(135deg, #ffffff 0%, #a5b4fc 60%, #818cf8 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}
      >
        QA Agent
      </motion.h1>
      <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3, duration: 0.6 }}
        className="text-lg mb-2 font-medium" style={{ color: '#94a3b8' }}>
        Intelligent Test Automation Platform
      </motion.p>
      <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4, duration: 0.6 }}
        className="text-sm mb-10 max-w-xs" style={{ color: '#64748b' }}>
        Generate, execute, and monitor browser tests — all powered by AI.
      </motion.p>
      <div className="flex flex-col gap-3 items-center">
        <FeatureBadge icon={Zap}         label="AI-Powered Generation" delay={0.5} />
        <FeatureBadge icon={Activity}    label="Playwright Engine"      delay={0.65} />
        <FeatureBadge icon={CheckCircle} label="Autonomous Testing"     delay={0.8} />
      </div>
    </div>

    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1 }} className="relative z-10 p-10 text-center">
      <p className="text-xs" style={{ color: '#334155' }}>© 2026 QA Agent · Powered by Supabase & Playwright</p>
    </motion.div>
  </div>
);

/* ─────────────────────────────────────────────────────────────
   Shared: polished input
───────────────────────────────────────────────────────────── */
const FormInput = ({ id, label, type, value, onChange, placeholder, icon: Icon, required, minLength, autoComplete, children }) => {
  const [focused, setFocused] = useState(false);
  return (
    <div>
      {label && (
        <label htmlFor={id} className="block text-sm font-medium mb-2" style={{ color: '#94a3b8' }}>
          {label}
        </label>
      )}
      <div className="relative">
        <Icon size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 transition-colors duration-200"
          style={{ color: focused ? '#818cf8' : '#475569' }} />
        <input
          id={id} type={type} value={value} onChange={onChange}
          onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
          placeholder={placeholder} required={required} minLength={minLength} autoComplete={autoComplete}
          style={{
            width: '100%',
            paddingLeft: '2.5rem',
            paddingRight: children ? '3rem' : '1rem',
            paddingTop: '0.75rem',
            paddingBottom: '0.75rem',
            borderRadius: '0.625rem',
            background: 'rgba(15,18,32,0.8)',
            border: focused ? '1px solid rgba(99,102,241,0.6)' : '1px solid rgba(51,65,85,0.8)',
            color: '#f1f5f9',
            outline: 'none',
            fontSize: '0.875rem',
            boxShadow: focused ? '0 0 0 3px rgba(99,102,241,0.15)' : 'none',
            transition: 'all 0.2s ease',
          }}
        />
        {children}
      </div>
    </div>
  );
};

/* ─────────────────────────────────────────────────────────────
   Shared: password field with show/hide toggle
───────────────────────────────────────────────────────────── */
const PasswordInput = ({ id, label, value, onChange, placeholder, required, minLength, autoComplete }) => {
  const [show, setShow] = useState(false);
  return (
    <FormInput id={id} label={label} type={show ? 'text' : 'password'}
      value={value} onChange={onChange} placeholder={placeholder || '••••••••'}
      icon={Lock} required={required} minLength={minLength} autoComplete={autoComplete}>
      <button type="button" onClick={() => setShow(!show)} tabIndex={-1}
        style={{ position: 'absolute', right: '0.875rem', top: '50%', transform: 'translateY(-50%)', color: '#475569', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
        {show ? <EyeOff size={16} /> : <Eye size={16} />}
      </button>
    </FormInput>
  );
};

/* ─────────────────────────────────────────────────────────────
   Shared: alert/feedback box
───────────────────────────────────────────────────────────── */
const AlertBox = ({ type, message }) => {
  const ok = type === 'success';
  return (
    <motion.div
      initial={{ opacity: 0, y: -8, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
      className="flex items-start gap-3 px-4 py-3 rounded-xl mb-5 text-sm"
      style={{
        background: ok ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)',
        border: ok ? '1px solid rgba(34,197,94,0.25)' : '1px solid rgba(239,68,68,0.25)',
        color: ok ? '#4ade80' : '#f87171',
      }}
    >
      {ok
        ? <CheckCircle size={15} className="mt-0.5 shrink-0" style={{ color: '#4ade80' }} />
        : <X           size={15} className="mt-0.5 shrink-0" style={{ color: '#f87171' }} />}
      {message}
    </motion.div>
  );
};

/* ─────────────────────────────────────────────────────────────
   Shared: primary submit button
───────────────────────────────────────────────────────────── */
const SubmitButton = ({ loading, label, loadingLabel, icon: Icon }) => (
  <motion.button type="submit" disabled={loading}
    whileHover={{ scale: loading ? 1 : 1.015 }} whileTap={{ scale: loading ? 1 : 0.985 }}
    className="w-full flex items-center justify-center gap-2.5 font-semibold text-sm"
    style={{
      padding: '0.875rem 1.5rem',
      borderRadius: '0.625rem',
      background: loading ? 'rgba(99,102,241,0.4)' : 'linear-gradient(135deg, #4f46e5 0%, #6d28d9 100%)',
      color: loading ? '#94a3b8' : '#ffffff',
      border: 'none',
      cursor: loading ? 'not-allowed' : 'pointer',
      boxShadow: loading ? 'none' : '0 4px 24px rgba(79,70,229,0.4)',
      transition: 'all 0.2s ease',
      letterSpacing: '0.01em',
    }}
  >
    {loading ? (
      <>
        <svg className="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeOpacity="0.3" />
          <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
        </svg>
        {loadingLabel}
      </>
    ) : (
      <>
        <Icon size={16} />
        {label}
      </>
    )}
  </motion.button>
);

/* ─────────────────────────────────────────────────────────────
   Shared: back link
───────────────────────────────────────────────────────────── */
const BackLink = ({ onClick, label = 'Back to Sign In' }) => (
  <button onClick={onClick}
    className="flex items-center gap-1.5 text-sm mb-7"
    style={{ color: '#64748b', background: 'none', border: 'none', cursor: 'pointer', padding: 0, transition: 'color 0.15s' }}
    onMouseEnter={(e) => (e.currentTarget.style.color = '#94a3b8')}
    onMouseLeave={(e) => (e.currentTarget.style.color = '#64748b')}
  >
    <ArrowLeft size={15} />
    {label}
  </button>
);

/* ─────────────────────────────────────────────────────────────
   VIEW 1: Login / Sign Up
───────────────────────────────────────────────────────────── */
const AuthFormView = ({ onForgotPassword }) => {
  const [isSignup, setIsSignup] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { signIn, signUp } = useContext(AuthContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isSignup) {
        if (!fullName.trim()) { setError('Please enter your full name'); setLoading(false); return; }
        await signUp(email, password, fullName);
      } else {
        await signIn(email, password);
      }
    } catch (err) {
      setError(err.message || 'Authentication failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div key="auth-form" initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -30 }} transition={{ duration: 0.3 }}>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white mb-1">{isSignup ? 'Create an account' : 'Welcome back'}</h2>
        <p className="text-sm" style={{ color: '#64748b' }}>
          {isSignup ? 'Start automating your QA workflows today' : 'Sign in to your QA Agent workspace'}
        </p>
      </div>

      <AnimatePresence>{error && <AlertBox type="error" message={error} />}</AnimatePresence>

      <form onSubmit={handleSubmit} className="space-y-5">
        <AnimatePresence>
          {isSignup && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.25 }} style={{ overflow: 'hidden' }}>
              <FormInput id="fullName" label="Full Name" type="text" value={fullName} onChange={(e) => setFullName(e.target.value)}
                placeholder="John Doe" icon={User} required={isSignup} autoComplete="name" />
            </motion.div>
          )}
        </AnimatePresence>

        <FormInput id="email" label="Email address" type="email" value={email} onChange={(e) => setEmail(e.target.value)}
          placeholder="you@company.com" icon={Mail} required autoComplete="email" />

        {/* Password with "Forgot password?" inline */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label htmlFor="password" className="block text-sm font-medium" style={{ color: '#94a3b8' }}>Password</label>
            {!isSignup && (
              <button type="button" onClick={onForgotPassword}
                className="text-xs font-medium"
                style={{ color: '#818cf8', background: 'none', border: 'none', cursor: 'pointer', padding: 0, transition: 'color 0.15s' }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#a5b4fc')}
                onMouseLeave={(e) => (e.currentTarget.style.color = '#818cf8')}
              >
                Forgot password?
              </button>
            )}
          </div>
          <PasswordInput id="password" value={password} onChange={(e) => setPassword(e.target.value)}
            required minLength={6} autoComplete={isSignup ? 'new-password' : 'current-password'} />
          {isSignup && <p className="mt-1.5 text-xs" style={{ color: '#475569' }}>Minimum 6 characters</p>}
        </div>

        <SubmitButton loading={loading}
          label={isSignup ? 'Create Account' : 'Sign In'}
          loadingLabel={isSignup ? 'Creating account…' : 'Signing in…'}
          icon={isSignup ? UserPlus : LogIn}
        />
      </form>

      <div className="flex items-center gap-3 my-6">
        <div className="flex-1 h-px" style={{ background: 'rgba(30,41,59,0.8)' }} />
        <span className="text-xs" style={{ color: '#334155' }}>or</span>
        <div className="flex-1 h-px" style={{ background: 'rgba(30,41,59,0.8)' }} />
      </div>

      <p className="text-center text-sm" style={{ color: '#64748b' }}>
        {isSignup ? 'Already have an account?' : "Don't have an account?"}{' '}
        <button onClick={() => { setIsSignup(!isSignup); setError(''); }}
          style={{ color: '#818cf8', background: 'none', border: 'none', cursor: 'pointer', padding: 0, fontWeight: 600, transition: 'color 0.15s' }}
          onMouseEnter={(e) => (e.currentTarget.style.color = '#a5b4fc')}
          onMouseLeave={(e) => (e.currentTarget.style.color = '#818cf8')}
        >
          {isSignup ? 'Sign in' : 'Sign up for free'}
        </button>
      </p>
    </motion.div>
  );
};

/* ─────────────────────────────────────────────────────────────
   VIEW 2: Forgot Password — send reset email
───────────────────────────────────────────────────────────── */
const ForgotPasswordView = ({ onBack }) => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [sent, setSent] = useState(false);
  const { resetPassword } = useContext(AuthContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFeedback(null);
    setLoading(true);
    try {
      await resetPassword(email);
      setSent(true);
      setFeedback({ type: 'success', message: `Reset link sent to ${email}. Check your inbox (and spam folder).` });
    } catch (err) {
      setFeedback({ type: 'error', message: err.message || 'Failed to send reset email. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div key="forgot" initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -30 }} transition={{ duration: 0.3 }}>
      <BackLink onClick={onBack} />

      <div className="mb-6">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-5"
          style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.2) 0%, rgba(139,92,246,0.2) 100%)', border: '1px solid rgba(99,102,241,0.3)' }}>
          <KeyRound size={26} className="text-indigo-400" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-1">Forgot password?</h2>
        <p className="text-sm" style={{ color: '#64748b' }}>Enter your email and we'll send you a secure reset link.</p>
      </div>

      <AnimatePresence>{feedback && <AlertBox type={feedback.type} message={feedback.message} />}</AnimatePresence>

      {!sent ? (
        <form onSubmit={handleSubmit} className="space-y-5">
          <FormInput id="reset-email" label="Email address" type="email" value={email} onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com" icon={Mail} required autoComplete="email" />
          <SubmitButton loading={loading} label="Send Reset Link" loadingLabel="Sending…" icon={Send} />
        </form>
      ) : (
        <div className="space-y-3">
          <button onClick={() => { setSent(false); setFeedback(null); setEmail(''); }}
            className="w-full text-sm font-medium"
            style={{ padding: '0.75rem', borderRadius: '0.625rem', background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.25)', color: '#818cf8', cursor: 'pointer', transition: 'background 0.15s' }}
            onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(99,102,241,0.18)')}
            onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(99,102,241,0.1)')}
          >
            Didn't receive it? Send again
          </button>
        </div>
      )}
    </motion.div>
  );
};

/* ─────────────────────────────────────────────────────────────
   VIEW 3: Reset Password — set new password after email link
   Shown automatically when Supabase fires PASSWORD_RECOVERY
───────────────────────────────────────────────────────────── */
const ResetPasswordView = () => {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [done, setDone] = useState(false);
  const { updatePassword } = useContext(AuthContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFeedback(null);

    // Client-side validation
    if (newPassword.length < 6) {
      setFeedback({ type: 'error', message: 'Password must be at least 6 characters.' });
      return;
    }
    if (newPassword !== confirmPassword) {
      setFeedback({ type: 'error', message: 'Passwords do not match. Please re-enter.' });
      return;
    }

    setLoading(true);
    try {
      await updatePassword(newPassword);
      setDone(true);
      setFeedback({ type: 'success', message: 'Password updated successfully! You can now sign in with your new password.' });
    } catch (err) {
      setFeedback({ type: 'error', message: err.message || 'Failed to update password. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  // Match indicator
  const bothFilled = newPassword.length > 0 && confirmPassword.length > 0;
  const passwordsMatch = newPassword === confirmPassword;

  return (
    <motion.div key="reset" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.35 }}>
      {/* Icon + header */}
      <div className="mb-7">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-5"
          style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.25) 0%, rgba(139,92,246,0.25) 100%)', border: '1px solid rgba(99,102,241,0.4)', boxShadow: '0 0 24px rgba(99,102,241,0.2)' }}>
          <Lock size={26} className="text-indigo-300" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-1">Set new password</h2>
        <p className="text-sm" style={{ color: '#64748b' }}>
          Choose a strong new password for your account.
        </p>
      </div>

      <AnimatePresence>{feedback && <AlertBox type={feedback.type} message={feedback.message} />}</AnimatePresence>

      {!done ? (
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* New password */}
          <PasswordInput
            id="new-password"
            label="New Password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="Minimum 6 characters"
            required
            minLength={6}
            autoComplete="new-password"
          />

          {/* Confirm password */}
          <div>
            <PasswordInput
              id="confirm-password"
              label="Re-type New Password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Same as above"
              required
              minLength={6}
              autoComplete="new-password"
            />
            {/* Live match indicator */}
            <AnimatePresence>
              {bothFilled && (
                <motion.p
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="mt-2 text-xs flex items-center gap-1.5"
                  style={{ color: passwordsMatch ? '#4ade80' : '#f87171' }}
                >
                  {passwordsMatch
                    ? <><CheckCircle size={12} /> Passwords match</>
                    : <><X size={12} /> Passwords do not match</>}
                </motion.p>
              )}
            </AnimatePresence>
          </div>

          {/* Password strength hint */}
          <div className="rounded-lg px-4 py-3" style={{ background: 'rgba(99,102,241,0.07)', border: '1px solid rgba(99,102,241,0.15)' }}>
            <p className="text-xs font-medium mb-2" style={{ color: '#818cf8' }}>Password requirements</p>
            <ul className="space-y-1">
              {[
                { ok: newPassword.length >= 6,  label: 'At least 6 characters' },
                { ok: /[A-Z]/.test(newPassword), label: 'One uppercase letter (recommended)' },
                { ok: /[0-9]/.test(newPassword), label: 'One number (recommended)' },
              ].map(({ ok, label }) => (
                <li key={label} className="flex items-center gap-2 text-xs" style={{ color: ok ? '#4ade80' : '#475569' }}>
                  {ok ? <CheckCircle size={11} /> : <div style={{ width: 11, height: 11, borderRadius: '50%', border: '1px solid #334155', display: 'inline-block' }} />}
                  {label}
                </li>
              ))}
            </ul>
          </div>

          <SubmitButton loading={loading} label="Update Password" loadingLabel="Updating…" icon={KeyRound} />
        </form>
      ) : (
        /* Success state */
        <div className="text-center py-4">
          <motion.div
            initial={{ scale: 0 }} animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 200, damping: 15 }}
            className="inline-flex items-center justify-center w-16 h-16 rounded-full mb-4"
            style={{ background: 'rgba(34,197,94,0.15)', border: '1px solid rgba(34,197,94,0.3)' }}
          >
            <CheckCircle size={32} style={{ color: '#4ade80' }} />
          </motion.div>
          <p className="text-sm" style={{ color: '#64748b' }}>
            You'll be signed in automatically in a moment…
          </p>
        </div>
      )}
    </motion.div>
  );
};

/* ─────────────────────────────────────────────────────────────
   Root AuthPage — orchestrates all three views
───────────────────────────────────────────────────────────── */
export const AuthPage = () => {
  const { isRecoveryMode } = useContext(AuthContext);
  const [view, setView] = useState('auth'); // 'auth' | 'forgot'

  // Supabase fired PASSWORD_RECOVERY → override to reset view
  const activeView = isRecoveryMode ? 'reset' : view;

  return (
    <div className="flex min-h-screen" style={{ background: '#070a14', fontFamily: "'Inter', 'Segoe UI', system-ui, sans-serif" }}>
      <BrandPanel />

      {/* Right panel */}
      <div className="flex flex-col items-center justify-center flex-1 relative px-6 py-12" style={{ background: '#0a0d1a' }}>
        {/* Glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] pointer-events-none"
          style={{ background: 'radial-gradient(circle, rgba(99,102,241,0.06) 0%, transparent 70%)' }} />

        {/* Mobile brand */}
        <div className="lg:hidden mb-10 text-center">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl mb-4"
            style={{ background: 'rgba(99,102,241,0.2)', border: '1px solid rgba(99,102,241,0.3)' }}>
            <Shield size={28} className="text-indigo-400" />
          </div>
          <h1 className="text-3xl font-black text-white">QA Agent</h1>
          <p className="text-sm mt-1" style={{ color: '#64748b' }}>Intelligent Test Automation</p>
        </div>

        {/* Card */}
        <div className="relative z-10 w-full max-w-md">
          <div style={{
            background: 'rgba(13,17,30,0.9)',
            border: '1px solid rgba(30,41,59,0.8)',
            borderRadius: '1.25rem',
            padding: '2.5rem',
            boxShadow: '0 24px 80px rgba(0,0,0,0.5), 0 0 0 1px rgba(99,102,241,0.05)',
            backdropFilter: 'blur(20px)',
          }}>
            <AnimatePresence mode="wait">
              {activeView === 'reset'  && <ResetPasswordView key="reset" />}
              {activeView === 'forgot' && <ForgotPasswordView key="forgot" onBack={() => setView('auth')} />}
              {activeView === 'auth'   && <AuthFormView key="auth" onForgotPassword={() => setView('forgot')} />}
            </AnimatePresence>
          </div>

          <p className="text-center text-xs mt-6" style={{ color: '#1e293b' }}>
            By continuing, you agree to our Terms of Service and Privacy Policy
          </p>
        </div>
      </div>
    </div>
  );
};
