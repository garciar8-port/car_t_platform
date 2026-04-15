import { useState, useEffect, useRef } from 'react';
import { Activity, Lock } from 'lucide-react';

interface AccessGatePageProps {
  onAuthenticated: () => void;
}

function FlowingLines() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const lineCount = 12;
    const lines = Array.from({ length: lineCount }, (_, i) => ({
      y: (canvas.height / (lineCount + 1)) * (i + 1),
      speed: 0.3 + Math.random() * 0.4,
      amplitude: 20 + Math.random() * 40,
      wavelength: 300 + Math.random() * 200,
      phase: Math.random() * Math.PI * 2,
      opacity: 0.04 + Math.random() * 0.06,
    }));

    const animate = (time: number) => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      for (const line of lines) {
        ctx.beginPath();
        ctx.strokeStyle = `rgba(30, 39, 97, ${line.opacity})`;
        ctx.lineWidth = 1.5;

        for (let x = 0; x <= canvas.width; x += 4) {
          const y =
            line.y +
            Math.sin((x / line.wavelength) * Math.PI * 2 + time * 0.001 * line.speed + line.phase) *
              line.amplitude +
            Math.sin((x / (line.wavelength * 1.7)) * Math.PI * 2 - time * 0.0007 * line.speed) *
              (line.amplitude * 0.5);

          if (x === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }
        ctx.stroke();
      }

      animationId = requestAnimationFrame(animate);
    };

    animationId = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full"
      style={{ pointerEvents: 'none' }}
    />
  );
}

export default function AccessGatePage({ onAuthenticated }: AccessGatePageProps) {
  const [code, setCode] = useState('');
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(false);

    try {
      const res = await fetch('/api/verify-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      });

      if (res.ok) {
        sessionStorage.setItem('demo_authenticated', 'true');
        onAuthenticated();
      } else {
        setError(true);
      }
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen bg-neutral-50 flex items-center justify-center overflow-hidden">
      <FlowingLines />

      <div className="relative z-10 w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Activity className="w-10 h-10 text-primary" />
            <span className="text-3xl font-semibold text-primary">BioFlow</span>
          </div>
          <p className="text-neutral-500">Manufacturing Scheduler</p>
        </div>

        <div className="bg-white/90 backdrop-blur-sm border border-neutral-200 rounded-xl p-8 shadow-sm">
          <div className="flex items-center justify-center gap-2 mb-6">
            <Lock className="w-5 h-5 text-neutral-400" />
            <p className="text-sm text-neutral-600 font-medium">Demo Access</p>
          </div>

          <form onSubmit={handleSubmit}>
            <input
              type="text"
              value={code}
              onChange={(e) => { setCode(e.target.value); setError(false); }}
              placeholder="Enter access code"
              autoFocus
              className={`w-full px-4 py-3 border rounded-lg text-center text-lg tracking-widest font-mono focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors ${
                error ? 'border-danger bg-danger/5' : 'border-neutral-200'
              }`}
            />

            {error && (
              <p className="text-danger text-sm text-center mt-2">
                Invalid access code
              </p>
            )}

            <button
              type="submit"
              disabled={!code.trim() || loading}
              className="w-full mt-4 bg-primary text-white font-medium py-3 px-4 rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Verifying...' : 'Enter Demo'}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-neutral-400 mt-6">
          Request access at crestlinepartners.io
        </p>
      </div>
    </div>
  );
}
