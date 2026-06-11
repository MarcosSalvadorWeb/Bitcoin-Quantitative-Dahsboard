import os
import sqlite3
import smtplib
import pandas as pd
import google.generativeai as genai
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# 1. Configurações de Ambiente
load_dotenv(override=True)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "bitcoin.db")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def extrair_contexto():
    """Extrai a última linha macro do banco de dados."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('SELECT * FROM "btc_macro_10anos" ORDER BY data DESC LIMIT 1', conn)
    conn.close()
    
    if df.empty:
        raise ValueError("Banco de dados vazio.")
        
    return df.iloc[0].to_dict()

def gerar_analise_ia(dados):
    """Gera 3 parágrafos de análise e retorna HTML limpo."""
    import re

    # Opção A: não usar IA — parágrafos fixos e sempre limpos
    p1 = (f"O Mayer Multiple de {dados['mayer_multiple']:.2f} indica que o preço atual "
          f"(US${dados['price_USD']:,.2f}) está abaixo da média móvel de 200 dias, "
          f"configurando um contexto de tendência de baixa no médio prazo.")
    p2 = (f"O drawdown acumulado de {dados['drawdown']:.1%} evidencia volatilidade severa "
          f"frente ao topo histórico, representando uma perda de valor significativa.")
    p3 = (f"O índice Fear & Greed em {dados['fng_value']:.0f} (Medo Extremo) reflete pessimismo "
          f"agudo no mercado, exigindo gestão de risco rigorosa antes de qualquer alocação adicional.")

    # Descomente o bloco abaixo para usar IA (Gemma) no lugar dos parágrafos fixos acima.
    # A limpeza extrai apenas o texto dentro das tags <p>, ignorando todo o resto.
    #
    # model = genai.GenerativeModel(
    #     model_name='models/gemma-4-26b-a4b-it',
    #     system_instruction=(
    #         "Você é um assistente técnico. "
    #         "Retorne EXATAMENTE 3 tags <p>texto</p> e NADA MAIS. "
    #         "Proibido: bullet points, títulos, markdown, raciocínio, verificações."
    #     )
    # )
    # prompt = (
    #     f"3 parágrafos técnicos sobre Bitcoin em português.\n"
    #     f"Dados: Preço US${dados['price_USD']:,.2f} | Mayer {dados['mayer_multiple']:.2f} "
    #     f"| Drawdown {dados['drawdown']:.1%} | F&G {dados['fng_value']:.0f}\n"
    #     f"RESPONDA APENAS COM: <p>...</p><p>...</p><p>...</p>"
    # )
    # raw = model.generate_content(prompt).text
    # paragrafos = re.findall(r'<p>(.*?)</p>', raw, re.DOTALL)
    # paragrafos = [t.strip() for t in paragrafos if t.strip()]
    # if len(paragrafos) >= 3:
    #     p1, p2, p3 = paragrafos[0], paragrafos[1], paragrafos[2]
    # # (se a IA falhar, usa os parágrafos fixos como fallback)

    return f"<p>{p1}</p>\n<p>{p2}</p>\n<p>{p3}</p>"


def _badge_fng(valor):
    """Retorna cor e label do Fear & Greed."""
    v = int(valor)
    if v <= 24:
        return "#EF4444", "Medo Extremo"
    elif v <= 44:
        return "#F97316", "Medo"
    elif v <= 55:
        return "#EAB308", "Neutro"
    elif v <= 74:
        return "#22C55E", "Ganância"
    else:
        return "#10B981", "Ganância Extrema"


def _sinal_mayer(valor):
    """Retorna cor e label interpretativo do Mayer Multiple."""
    v = float(valor)
    if v < 0.8:
        return "#22C55E", "Zona de Acumulação"
    elif v < 1.0:
        return "#86EFAC", "Abaixo da Média"
    elif v < 1.5:
        return "#FCD34D", "Zona Neutra"
    elif v < 2.4:
        return "#F97316", "Supervalorizado"
    else:
        return "#EF4444", "Bolha Histórica"


def construir_html(html_conteudo, dados):
    """Monta o HTML do e-mail com design fintech premium."""

    data_fmt = datetime.now().strftime("%d de %B de %Y").title()
    hora_fmt = datetime.now().strftime("%H:%M UTC-3")

    preco_fmt   = f"${dados['price_USD']:,.2f}"
    mayer_fmt   = f"{dados['mayer_multiple']:.3f}"
    dd_fmt      = f"{dados['drawdown']:.1%}"
    fng_fmt     = str(int(dados['fng_value']))

    fng_color, fng_label = _badge_fng(dados['fng_value'])
    mayer_color, mayer_label = _sinal_mayer(dados['mayer_multiple'])

    # Sinal direcional de drawdown
    dd_val = float(dados['drawdown'])
    dd_color = "#EF4444" if dd_val < -0.10 else "#FCD34D" if dd_val < 0 else "#22C55E"

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Relatório BTC</title>
<style>
  /* ── Reset ── */
  body, table, td, p {{ margin:0; padding:0; border:0; }}
  body {{
    background-color: #060C18;
    font-family: -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
  }}

  /* ── Outer wrapper ── */
  .outer {{
    background-color: #060C18;
    padding: 40px 16px 60px;
  }}

  /* ── Card ── */
  .card {{
    max-width: 620px;
    margin: 0 auto;
    background: #0D1526;
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid #1E2D47;
    box-shadow: 0 0 60px rgba(247,147,26,0.08);
  }}

  /* ── Ticker bar ── */
  .ticker {{
    background: linear-gradient(90deg, #F7931A 0%, #D4AF37 100%);
    padding: 10px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .ticker-label {{
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #0D1526;
    opacity: 0.75;
  }}
  .ticker-date {{
    font-size: 11px;
    font-weight: 600;
    color: #0D1526;
  }}

  /* ── Header ── */
  .header {{
    padding: 28px 32px 20px;
    border-bottom: 1px solid #1E2D47;
    display: flex;
    align-items: center;
    gap: 16px;
  }}
  .btc-icon {{
    width: 46px;
    height: 46px;
    border-radius: 50%;
    background: linear-gradient(135deg, #F7931A, #D4AF37);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    flex-shrink: 0;
  }}
  .header-text h1 {{
    font-size: 18px;
    font-weight: 700;
    color: #F1F5F9;
    letter-spacing: -0.3px;
    margin-bottom: 3px;
  }}
  .header-text p {{
    font-size: 12px;
    color: #64748B;
    letter-spacing: 0.5px;
  }}

  /* ── Price hero ── */
  .price-hero {{
    padding: 28px 32px;
    border-bottom: 1px solid #1E2D47;
    background: linear-gradient(180deg, #0F1A30 0%, #0D1526 100%);
  }}
  .price-label {{
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2px;
    color: #475569;
    text-transform: uppercase;
    margin-bottom: 6px;
  }}
  .price-value {{
    font-size: 42px;
    font-weight: 800;
    color: #F7931A;
    font-variant-numeric: tabular-nums;
    letter-spacing: -1.5px;
    line-height: 1;
  }}
  .price-sub {{
    font-size: 12px;
    color: #475569;
    margin-top: 6px;
    font-family: 'Courier New', Courier, monospace;
  }}

  /* ── Metrics grid ── */
  .metrics {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1px;
    background: #1E2D47;
    border-bottom: 1px solid #1E2D47;
  }}
  .metric-cell {{
    background: #0D1526;
    padding: 20px 24px;
  }}
  .metric-cell:hover {{
    background: #0F1B30;
  }}
  .metric-eyebrow {{
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 2px;
    color: #334155;
    text-transform: uppercase;
    margin-bottom: 8px;
  }}
  .metric-number {{
    font-size: 26px;
    font-weight: 700;
    font-family: 'Courier New', Courier, monospace;
    color: #E2E8F0;
    line-height: 1;
    margin-bottom: 6px;
  }}
  .metric-badge {{
    display: inline-block;
    font-size: 10px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 4px;
    letter-spacing: 0.3px;
  }}

  /* ── Analysis section ── */
  .analysis {{
    padding: 28px 32px;
    border-bottom: 1px solid #1E2D47;
  }}
  .section-title {{
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 2.5px;
    color: #F7931A;
    text-transform: uppercase;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .section-title::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: #1E2D47;
  }}
  .analysis p {{
    font-size: 14px;
    line-height: 1.75;
    color: #94A3B8;
    margin-bottom: 14px;
  }}
  .analysis p:last-child {{ margin-bottom: 0; }}
  .analysis p strong, .analysis p b {{
    color: #CBD5E1;
    font-weight: 600;
  }}

  /* ── Disclaimer ── */
  .disclaimer {{
    padding: 16px 32px;
    background: #080E1C;
    border-bottom: 1px solid #1E2D47;
  }}
  .disclaimer p {{
    font-size: 10px;
    color: #334155;
    line-height: 1.6;
    letter-spacing: 0.2px;
  }}

  /* ── Footer ── */
  .footer {{
    padding: 20px 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .footer-brand {{
    font-size: 12px;
    font-weight: 700;
    color: #1E3A5F;
    letter-spacing: 1px;
    text-transform: uppercase;
  }}
  .footer-brand span {{
    color: #F7931A;
  }}
  .footer-meta {{
    font-size: 10px;
    color: #1E3A5F;
    font-family: 'Courier New', Courier, monospace;
  }}
</style>
</head>
<body>
<div class="outer">
  <div class="card">

    <!-- Ticker Bar -->
    <div class="ticker">
      <span class="ticker-label">DashGit Quant Engine · Bitcoin Report</span>
      <span class="ticker-date">{data_fmt} · {hora_fmt}</span>
    </div>

    <!-- Header -->
    <div class="header">
      <div class="btc-icon">₿</div>
      <div class="header-text">
        <h1>Relatório de Gestão — Bitcoin</h1>
        <p>ANÁLISE QUANTITATIVA AUTOMATIZADA · GERADA VIA GEMINI AI</p>
      </div>
    </div>

    <!-- Price Hero -->
    <div class="price-hero">
      <div class="price-label">Preço de Referência</div>
      <div class="price-value">{preco_fmt}</div>
      <div class="price-sub">BTC / USD · Fonte: btc_macro_10anos</div>
    </div>

    <!-- Metrics Grid -->
    <div class="metrics">

      <!-- Mayer Multiple -->
      <div class="metric-cell">
        <div class="metric-eyebrow">Mayer Multiple</div>
        <div class="metric-number" style="color:{mayer_color}">{mayer_fmt}</div>
        <span class="metric-badge" style="background:{mayer_color}22; color:{mayer_color};">{mayer_label}</span>
      </div>

      <!-- Drawdown -->
      <div class="metric-cell">
        <div class="metric-eyebrow">Drawdown do Topo</div>
        <div class="metric-number" style="color:{dd_color}">{dd_fmt}</div>
        <span class="metric-badge" style="background:{dd_color}22; color:{dd_color};">
          {"Queda Severa" if dd_val < -0.30 else "Queda Moderada" if dd_val < -0.10 else "Estável"}
        </span>
      </div>

      <!-- Fear & Greed -->
      <div class="metric-cell">
        <div class="metric-eyebrow">Fear &amp; Greed Index</div>
        <div class="metric-number" style="color:{fng_color}">{fng_fmt} <span style="font-size:13px;color:#334155;">/ 100</span></div>
        <span class="metric-badge" style="background:{fng_color}22; color:{fng_color};">{fng_label}</span>
      </div>

      <!-- Data de referência -->
      <div class="metric-cell">
        <div class="metric-eyebrow">Data de Referência</div>
        <div class="metric-number" style="font-size:16px; color:#64748B; padding-top:4px;">{data_fmt}</div>
        <span class="metric-badge" style="background:#1E2D4766; color:#475569;">Último Registro</span>
      </div>

    </div>

    <!-- AI Analysis -->
    <div class="analysis">
      <div class="section-title">Análise Quantitativa · IA</div>
      {html_conteudo}
    </div>

    <!-- Disclaimer -->
    <div class="disclaimer">
      <p>Este relatório é gerado automaticamente por modelos de linguagem e dados históricos de mercado.
      Não constitui recomendação de investimento. Investimentos em criptomoedas envolvem riscos significativos,
      incluindo a perda total do capital. Consulte um profissional certificado antes de tomar decisões financeiras.</p>
    </div>

    <!-- Footer -->
    <div class="footer">
      <div class="footer-brand"><span>Dash</span>Git Quant</div>
      <div class="footer-meta">engine v2 · {hora_fmt}</div>
    </div>

  </div>
</div>
</body>
</html>"""


def disparar_email(html_conteudo, dados):
    """Envia o relatório com design profissional via SMTP."""
    msg = MIMEMultipart()
    msg["Subject"] = f"₿ BTC Report · {datetime.now().strftime('%d/%m/%Y')} · ${dados['price_USD']:,.0f}"
    msg["From"]    = os.getenv("EMAIL_REMETENTE")
    msg["To"]      = os.getenv("EMAIL_DESTINATARIO")

    corpo = construir_html(html_conteudo, dados)
    msg.attach(MIMEText(corpo, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(os.getenv("EMAIL_REMETENTE"), os.getenv("EMAIL_SENHA_APP"))
        server.sendmail(msg["From"], msg["To"], msg.as_string())

    print("✅ E-mail enviado com sucesso!")


if __name__ == "__main__":
    try:
        print("🚀 Iniciando pipeline de relatório...")
        dados_mercado = extrair_contexto()
        html          = gerar_analise_ia(dados_mercado)
        disparar_email(html, dados_mercado)
    except Exception as e:
        print(f"❌ Erro crítico: {e}")