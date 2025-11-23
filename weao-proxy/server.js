const express = require('express');
const cors = require('cors');
const axios = require('axios');

const app = express();
app.use(cors());

const WEAO_HEADERS = {
  'User-Agent': 'WEAO-3PService',
  'Accept': 'application/json'
};

// все эксплойты
app.get('/api/status/exploits', async (req, res) => {
  try {
    const r = await axios.get('https://weao.xyz/api/status/exploits', {
      headers: WEAO_HEADERS,
      timeout: 10000
    });
    res.status(r.status).json(r.data);
  } catch (err) {
    console.error(err.message);
    res.status(500).json({ error: err.message || 'error fetching exploits' });
  }
});

// один эксплойт
app.get('/api/status/exploits/:exploit', async (req, res) => {
  try {
    const exploit = encodeURIComponent(req.params.exploit);
    const r = await axios.get(`https://weao.xyz/api/status/exploits/${exploit}`, {
      headers: WEAO_HEADERS,
      timeout: 10000
    });
    res.status(r.status).json(r.data);
  } catch (err) {
    console.error(err.message);
    res.status(500).json({ error: err.message || 'error fetching exploit' });
  }
});

const port = process.env.PORT || 25505;
app.listen(port, () => {
  console.log('Proxy listening on port', port);
});
