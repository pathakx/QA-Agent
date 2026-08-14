import { createContext, useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import axios from 'axios';
import { api } from '../lib/api';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [session, setSession] = useState(null);
    const [loading, setLoading] = useState(true);
    // Set to true when Supabase fires PASSWORD_RECOVERY after user clicks the reset-link email
    const [isRecoveryMode, setIsRecoveryMode] = useState(false);

    useEffect(() => {
        // Get initial session
        supabase.auth.getSession().then(({ data: { session } }) => {
            setSession(session);
            setUser(session?.user ?? null);

            if (session) {
                axios.defaults.headers.common['Authorization'] = `Bearer ${session.access_token}`;
                api.defaults.headers.common['Authorization'] = `Bearer ${session.access_token}`;
            }

            setLoading(false);
        });

        // Listen for auth state changes — PASSWORD_RECOVERY fires when user
        // clicks the reset-link email and lands back on this app.
        const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
            setSession(session);
            setUser(session?.user ?? null);

            if (event === 'PASSWORD_RECOVERY') {
                // Don't navigate to the dashboard — keep on auth page with reset form
                setIsRecoveryMode(true);
            } else {
                setIsRecoveryMode(false);
            }

            if (session) {
                axios.defaults.headers.common['Authorization'] = `Bearer ${session.access_token}`;
                api.defaults.headers.common['Authorization'] = `Bearer ${session.access_token}`;
            } else {
                delete axios.defaults.headers.common['Authorization'];
                delete api.defaults.headers.common['Authorization'];
            }
        });

        return () => subscription.unsubscribe();
    }, []);

    const signUp = async (email, password, fullName) => {
        try {
            const { data, error } = await supabase.auth.signUp({
                email,
                password,
                options: {
                    data: { full_name: fullName },
                    emailRedirectTo: window.location.origin,
                },
            });

            if (error) throw error;

            // Email confirmation required
            if (data.user && !data.session) {
                throw new Error('Please check your email to confirm your account.');
            }

            return data;
        } catch (error) {
            throw error;
        }
    };

    const signIn = async (email, password) => {
        try {
            const { data, error } = await supabase.auth.signInWithPassword({ email, password });
            if (error) throw error;
            return data;
        } catch (error) {
            throw error;
        }
    };

    const signOut = async () => {
        try {
            const { error } = await supabase.auth.signOut();
            if (error) throw error;
        } catch (error) {
            throw error;
        }
    };

    /** Step 1 — sends the reset-link email */
    const resetPassword = async (email) => {
        try {
            const { error } = await supabase.auth.resetPasswordForEmail(email, {
                redirectTo: window.location.origin,
            });
            if (error) throw error;
        } catch (error) {
            throw error;
        }
    };

    /** Step 2 — called after the user lands back via the email link (recovery session active) */
    const updatePassword = async (newPassword) => {
        try {
            const { data, error } = await supabase.auth.updateUser({ password: newPassword });
            if (error) throw error;
            // Exit recovery mode after successful update
            setIsRecoveryMode(false);
            return data;
        } catch (error) {
            throw error;
        }
    };

    const value = {
        user,
        session,
        loading,
        isRecoveryMode,
        signUp,
        signIn,
        signOut,
        resetPassword,
        updatePassword,
    };

    return (
        <AuthContext.Provider value={value}>
            {!loading && children}
        </AuthContext.Provider>
    );
};
