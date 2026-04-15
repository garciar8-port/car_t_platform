import express from 'express';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = parseInt(process.env.PORT || '8080');
const ACCESS_CODE = process.env.DEMO_ACCESS_CODE || 'bioflow-demo-2026';

app.use(express.json());

app.post('/api/verify-code', (req, res) => {
  const { code } = req.body;
  if (code === ACCESS_CODE) {
    res.json({ ok: true });
  } else {
    res.status(401).json({ error: 'Invalid code' });
  }
});

app.use(express.static(join(__dirname, 'dist')));

// SPA fallback — serve index.html for all non-API, non-file routes
app.get('/{*splat}', (req, res) => {
  res.sendFile(join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
