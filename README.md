Bitcoin Dashboard
=================

Dashboard em Python para acompanhar o Bitcoin em USD usando dados da CoinGecko,
sentimento de mercado do Fear & Greed Index e metricas de ciclo como Mayer
Multiple e halving.

Tabelas geradas
---------------

- `btc_1semana`: ultimos 7 dias
- `btc_1mes`: ultimos 30 dias
- `btc_1ano`: ultimos 365 dias
- `btc_macro_10anos`: historico macro de ate 10 anos
- `btc_intraday`: preco medio por hora nas ultimas 24 horas
- `btc_halving_countdown`: progresso estimado do ciclo atual
- `btc_halving_analysis`: retornos de 90 dias antes/depois de halvings passados

Como executar
-------------

```bash
.venv/bin/python main.py
```

O pipeline atualiza o banco `database/bitcoin.db` e depois abre um menu para:

1. Ver o valor atual do Bitcoin
2. Abrir dashboards de preco por periodo
3. Abrir o dashboard intraday
4. Abrir log-retornos
5. Abrir Fear & Greed comparado ao preco
6. Abrir Mayer Multiple
7. Abrir painel de halving
8. Atualizar o banco novamente

Observacoes
-----------

- Os dashboards interativos sao gerados com Plotly.
- A base principal foi unificada em USD na coluna `price_USD`.
- O intraday mostra o preco medio por hora no fuso `America/Sao_Paulo`.
- O Fear & Greed vem da Alternative.me.
- A API Pro da CoinGecko pode ser usada se a variavel `COINGECKO_API_KEY`
  estiver configurada no ambiente.
