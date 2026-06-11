# ₿ Bitcoin Quantitative Dashboard

Uma plataforma de análise quantitativa para o mercado de Bitcoin, desenvolvida em Python, com arquitetura ETL, armazenamento em SQLite e visualizações interativas para monitoramento de preço, volatilidade, sentimento de mercado e ciclos de halving.

O objetivo do projeto é centralizar indicadores relevantes do ecossistema Bitcoin em uma única aplicação, permitindo análises quantitativas, acompanhamento histórico e suporte à tomada de decisão baseada em dados.

---

## 📊 Funcionalidades

### Mercado

- Histórico diário do Bitcoin
- Histórico intraday (24 horas)
- Preço atual em USD
- Volume negociado
- Market Cap
- Variação percentual

### Indicadores Quantitativos

- Retornos Logarítmicos
- Volatilidade Anualizada
- Média Móvel de 200 dias
- Mayer Multiple
- Fear & Greed Index

### Ciclos de Mercado

- Contagem regressiva para o próximo Halving
- Histórico dos halvings
- Comparação entre ciclos

### Engenharia de Dados

- Pipeline ETL automatizado
- Coleta de dados via APIs
- Tratamento e transformação de dados
- Persistência em banco SQLite
- Atualização automática

### Visualização

- Dashboards interativos com Plotly
- Gráficos históricos
- Indicadores em tempo real
- Painéis executivos

---

## 🏗️ Arquitetura

```text
CoinGecko API
      │
Yahoo Finance
      │
Fear & Greed API
      │
      ▼
   Extract
      │
      ▼
 Transform
      │
      ├── Retornos
      ├── Volatilidade
      ├── Médias Móveis
      ├── Mayer Multiple
      └── Fear & Greed
      │
      ▼
     Load
      │
      ▼
   SQLite
      │
      ▼
 Dashboard
```

---

## 📁 Estrutura do Projeto

```text
bitcoin_dashboard/

├── analysis/
│   ├── __init__.py
│   ├── charts.py
│   └── metrics.py
│
├── database/
│   └── bitcoin.db
│
├── email/
│   ├── relatório.py
│   └── verificar_modelos.py
│
├── etl/
│   ├── __init__.py
│   ├── extract.py
│   ├── transform.py
│   └── load.py
│
├── .env
├── main.py
├── requirements.txt
└── README.md
```

---

## 📈 Indicadores Utilizados

### Retorno Logarítmico

O retorno logarítmico é calculado por:

```math
r_t = \ln\left(\frac{P_t}{P_{t-1}}\right)
```

onde:

- \(P_t\) = preço atual
- \(P_{t-1}\) = preço anterior

---

### Volatilidade Anualizada

A volatilidade anualizada é calculada por:

```math
\sigma_{anual} = \sigma_{diária} \times \sqrt{365}
```

Indicador amplamente utilizado para mensurar risco em ativos financeiros.

---

### Mayer Multiple

Métrica popular entre investidores de Bitcoin:

```math
Mayer = \frac{Preço Atual}{MM200}
```

onde:

- MM200 = Média móvel de 200 dias

Interpretação:

| Mayer Multiple | Interpretação |
|---------------|---------------|
| < 0.8 | Possível subvalorização |
| 0.8 – 2.4 | Faixa histórica normal |
| > 2.4 | Possível sobrevalorização |

---

### Fear & Greed Index

Indicador de sentimento de mercado que varia entre:

| Valor | Classificação |
|---------|---------------|
| 0 – 24 | Medo Extremo |
| 25 – 49 | Medo |
| 50 | Neutro |
| 51 – 74 | Ganância |
| 75 – 100 | Ganância Extrema |

---

## 🛠️ Tecnologias Utilizadas

### Linguagem

- Python 3.x

### Bibliotecas

- Pandas
- NumPy
- Plotly
- Requests
- SQLAlchemy
- SQLite3

### Fontes de Dados

- CoinGecko API
- Yahoo Finance
- Alternative.me Fear & Greed API

---

## ⚙️ Instalação

Clone o repositório:

```bash
git clone https://github.com/SEU-USUARIO/bitcoin-dashboard.git
```

Entre na pasta:

```bash
cd bitcoin-dashboard
```

Crie o ambiente virtual:

```bash
python -m venv .venv
```

Ative o ambiente:

### Linux / Mac

```bash
source .venv/bin/activate
```

### Windows

```bash
.venv\Scripts\activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

---

## ▶️ Executando o Projeto

```bash
python main.py
```

---

## 🗄️ Banco de Dados

O projeto utiliza SQLite para armazenamento local.

Exemplo:

```text
database/
└── bitcoin.db
```

As tabelas armazenam:

- Histórico de preços
- Dados intraday
- Métricas calculadas
- Indicadores de mercado

---

## 📸 Dashboard

### Visão Geral

- Preço atual
- Volume
- Market Cap
- Fear & Greed
- Mayer Multiple

### Análise Histórica

- Série temporal
- Retornos
- Volatilidade

### Ciclos de Mercado

- Histórico de Halvings
- Comparações entre ciclos

> Adicione screenshots nesta seção para melhorar a apresentação do projeto.

---

## 🚀 Próximas Melhorias

- [ ] Modelo Prophet para previsão de preços
- [ ] Modelo XGBoost
- [ ] LSTM para séries temporais
- [ ] Sharpe Ratio
- [ ] Sortino Ratio
- [ ] Value at Risk (VaR)
- [ ] Maximum Drawdown
- [ ] Alertas por Telegram
- [ ] Deploy em nuvem
- [ ] API própria para consulta dos indicadores

---

## 📚 Aprendizados

Este projeto foi desenvolvido com foco em:

- Ciência de Dados
- Engenharia de Dados
- Estatística Aplicada
- Séries Temporais
- Mercado Financeiro
- Criptomoedas
- Desenvolvimento de Dashboards

---

## 👨‍💻 Autor

**Marcos Salvador**

Graduando em Estatística e entusiasta de Ciência de Dados, Machine Learning, Modelos Probabilísticos e Análise Quantitativa.

GitHub:
https://github.com/MarcosSalvadorWeb

---

## 📄 Licença

Este projeto está licenciado sob a licença MIT.

Sinta-se livre para utilizar, modificar e contribuir.
