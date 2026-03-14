import { useState, useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import { LogIn, UserPlus, Mail, Lock, User } from 'lucide-react';
import { motion } from 'framer-motion';

export const AuthPage = () => {
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
                if (!fullName.trim()) {
                    setError('Please enter your full name');
                    setLoading(false);
                    return;
                }
                await signUp(email, password, fullName);
            } else {
                await signIn(email, password);
            }
        } catch (err) {
            console.error('Auth error:', err);
            setError(err.message || 'Authentication failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-950 via-gray-900 to-indigo-950 p-4">
            {/* Background effects */}
            <div className="absolute inset-0 bg-grid-white/[0.02] bg-[size:50px_50px]"></div>
            <div className="absolute inset-0 bg-gradient-to-t from-transparent via-transparent to-indigo-500/10"></div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-panel p-8 rounded-2xl w-full max-w-md relative z-10 shadow-2xl border border-gray-800"
            >
                {/* Logo/Title */}
                <div className="text-center mb-8">
                    <div className="inline-block p-3 bg-indigo-600/20 rounded-xl mb-4">
                        <svg className="w-12 h-12 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <h1 className="text-3xl font-bold text-white mb-2">QA Agent</h1>
                    <p className="text-gray-400">
                        {isSignup ? 'Create your account' : 'Welcome back'}
                    </p>
                </div>

                {/* Error message */}
                {error && (
                    <motion.div
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg mb-6 text-sm"
                    >
                        {error}
                    </motion.div>
                )}

                {/* Form */}
                <form onSubmit={handleSubmit} className="space-y-4">
                    {isSignup && (
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Full Name
                            </label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500" size={18} />
                                <input
                                    type="text"
                                    value={fullName}
                                    onChange={(e) => setFullName(e.target.value)}
                                    placeholder="John Doe"
                                    className="w-full pl-10 pr-4 py-3 rounded-lg bg-gray-800/50 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                                    required={isSignup}
                                />
                            </div>
                        </div>
                    )}

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Email
                        </label>
                        <div className="relative">
                            <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500" size={18} />
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="you@example.com"
                                className="w-full pl-10 pr-4 py-3 rounded-lg bg-gray-800/50 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                                required
                            />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Password
                        </label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500" size={18} />
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                className="w-full pl-10 pr-4 py-3 rounded-lg bg-gray-800/50 border border-gray-700 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                                required
                                minLength={6}
                            />
                        </div>
                        {isSignup && (
                            <p className="mt-2 text-xs text-gray-500">
                                Password must be at least 6 characters
                            </p>
                        )}
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-800 disabled:cursor-not-allowed text-white py-3 rounded-lg font-medium shadow-lg flex justify-center items-center gap-2 transition transform hover:scale-[1.02] active:scale-[0.98]"
                    >
                        {loading ? (
                            <>
                                <span className="animate-spin">⌛</span>
                                {isSignup ? 'Creating account...' : 'Signing in...'}
                            </>
                        ) : (
                            <>
                                {isSignup ? <UserPlus size={18} /> : <LogIn size={18} />}
                                {isSignup ? 'Create Account' : 'Sign In'}
                            </>
                        )}
                    </button>
                </form>

                {/* Toggle between signup/login */}
                <div className="mt-6 text-center">
                    <p className="text-gray-400 text-sm">
                        {isSignup ? 'Already have an account?' : "Don't have an account?"}
                        {' '}
                        <button
                            onClick={() => {
                                setIsSignup(!isSignup);
                                setError('');
                            }}
                            className="text-indigo-400 hover:text-indigo-300 font-medium transition"
                        >
                            {isSignup ? 'Sign In' : 'Sign Up'}
                        </button>
                    </p>
                </div>

                {/* Footer */}
                <div className="mt-8 pt-6 border-t border-gray-800 text-center text-xs text-gray-500">
                    Powered by Supabase
                </div>
            </motion.div>
        </div>
    );
};
