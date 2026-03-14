import { createContext, useState, useEffect } from 'react';
import { supabase } from '../lib/supabase';
import axios from 'axios';
import { api } from '../lib/api';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [session, setSession] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Get initial session
        supabase.auth.getSession().then(({ data: { session } }) => {
            setSession(session);
            setUser(session?.user ?? null);

            // Set axios auth header
            if (session) {
                axios.defaults.headers.common['Authorization'] = `Bearer ${session.access_token}`;
                api.defaults.headers.common['Authorization'] = `Bearer ${session.access_token}`;
            }

            setLoading(false);
        });

        // Listen for auth changes
        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
            setSession(session);
            setUser(session?.user ?? null);

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
                    data: {
                        full_name: fullName
                    },
                    emailRedirectTo: window.location.origin
                }
            });

            if (error) throw error;

            // Check if email confirmation is required
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
            const { data, error } = await supabase.auth.signInWithPassword({
                email,
                password
            });

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

    const value = {
        user,
        session,
        loading,
        signUp,
        signIn,
        signOut
    };

    return (
        <AuthContext.Provider value={value}>
            {!loading && children}
        </AuthContext.Provider>
    );
};
