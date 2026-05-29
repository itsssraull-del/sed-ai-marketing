'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import { authApi } from '@/lib/api';
import toast from 'react-hot-toast';
import { Loader2, Zap } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await authApi.login(email, password);
      Cookies.set('access_token', res.data.access_token, { expires: 1 });
      router.push('/dashboard');
    } catch {
      toast.error('Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ background: "#0F0F0F" }}>
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full pointer-events-none"
        style={{ background: "radial-gradient(circle, rgba(242,101,34,0.06) 0%, transparent 70%)" }} />

      <div className="w-full max-w-sm relative">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-5"
            style={{ background: "linear-gradient(135deg, #F26522, #D4521A)", boxShadow: "0 0 32px rgba(242,101,34,0.25)" }}>
            <Zap size={24} className="text-white" fill="white" />
          </div>
          <div className="flex items-baseline justify-center gap-[3px] mb-1">
            <span className="text-2xl font-black tracking-tight" style={{ color: "#F26522" }}>SED</span>
            <span className="text-2xl font-black tracking-tight text-white/80"> ENERGY</span>
          </div>
          <p className="text-white/30 text-[11px] tracking-widest uppercase mt-1">AI Marketing System</p>
        </div>

        <div className="rounded-2xl p-8 border border-[#222]" style={{ background: "#141414" }}>
          <h2 className="text-white font-semibold text-base mb-6">Sign in to your account</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-white/40 mb-2">Email address</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder:text-white/20 outline-none transition-all"
                style={{ background: "#1C1C1C", border: "1px solid #2A2A2A" }}
                onFocus={e => (e.currentTarget.style.borderColor = "#F26522")}
                onBlur={e => (e.currentTarget.style.borderColor = "#2A2A2A")}
                placeholder="you@sed.energy"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-white/40 mb-2">Password</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder:text-white/20 outline-none transition-all"
                style={{ background: "#1C1C1C", border: "1px solid #2A2A2A" }}
                onFocus={e => (e.currentTarget.style.borderColor = "#F26522")}
                onBlur={e => (e.currentTarget.style.borderColor = "#2A2A2A")}
                placeholder="••••••••"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl font-semibold text-sm text-white flex items-center justify-center gap-2 transition-all mt-2 disabled:opacity-50"
              style={{ background: "linear-gradient(135deg, #F26522, #D4521A)", boxShadow: "0 0 20px rgba(242,101,34,0.2)" }}
            >
              {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Signing in...</> : 'Sign in'}
            </button>
          </form>
        </div>

        <p className="text-center text-white/15 text-xs mt-6">
          SED Energy · South Africa&apos;s Tier 1 Solar Distributor
        </p>
      </div>
    </div>
  );
}
