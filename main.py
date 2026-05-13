import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Mentor Wealth Advisor", layout="wide", page_icon="🏦")

# --- DATABASE MERCATI ---
MAPPA_MONDIALE = {
    "EUROPA": {
        "Italia": ["RACE.MI", "ENI.MI", "ISP.MI", "UCG.MI", "ENEL.MI", "STMMI.MI"],
        "Germania": ["SAP", "SIE.DE", "VOW3.DE", "BMW.DE", "DBK.DE"],
        "Francia": ["MC.PA", "OR.PA", "TTE", "AIR.PA", "BNP.PA"]
    },
    "AMERICHE": {
        "USA Tech": ["AAPL", "NVDA", "MSFT", "TSLA", "AMD", "META", "GOOGL"],
        "USA Finance/Bio": ["JPM", "PFE", "JNJ", "GS", "V"]
    },
    "CRYPTO & COMMODITIES": {
        "Crypto": ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD"],
        "Materie Prime": ["GC=F", "CL=F", "SI=F", "HG=F"]
    }
}

# --- INIZIALIZZAZIONE SESSIONE ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []
if 'base_currency' not in st.session_state:
    st.session_state.base_currency = "EUR"
if 'budget' not in st.session_state:
    st.session_state.budget = 10000.0

# --- MOTORE DI CALCOLO ---
def get_fx(from_c, to_c):
    if from_c == to_c: return 1.0
    try: return yf.Ticker(f"{from_c}{to_c}=X").history(period="1d")['Close'].iloc[-1]
    except: return 1.0

def calcola_indicatori(df):
    # Medie Mobili
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()
    # Bollinger
    std = df['Close'].rolling(window=20).std()
    df['UB'] = df['SMA20'] + (std * 2)
    df['LB'] = df['SMA20'] - (std * 2)
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain/loss)))
    # MACD
    exp1 = df['Close'].ewm(span=12).mean()
    exp2 = df['Close'].ewm(span=26).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9).mean()
    return df

# --- SIDEBAR NAVIGAZIONE ---
st.sidebar.title("🛡️ Mentor Advisor")
scelta = st.sidebar.radio("Vai a:", ["Dashboard Top/Flop", "Analisi Ticker", "Il Mio Portfolio", "Impostazioni"])

# --- 1. DASHBOARD TOP/FLOP ---
if scelta == "Dashboard Top/Flop":
    st.title("🏆 Leader e Laggards del Mercato")
    area = st.selectbox("Seleziona Area Geografica", list(MAPPA_MONDIALE.keys()))
    
    tabs = st.tabs(list(MAPPA_MONDIALE[area].keys()))
    for i, nazione in enumerate(MAPPA_MONDIALE[area].keys()):
        with tabs[i]:
            tickers = MAPPA_MONDIALE[area][nazione]
            risultati = []
            for t in tickers:
                h = yf.Ticker(t).history(period="2d")
                if len(h) >= 2:
                    v = ((h['Close'].iloc[-1] - h['Close'].iloc[-2]) / h['Close'].iloc[-2]) * 100
                    risultati.append({"Ticker": t, "Prezzo": h['Close'].iloc[-1], "Var %": v})
            
            df_res = pd.DataFrame(risultati)
            if not df_res.empty:
                c1, c2 = st.columns(2)
                c1.success("🚀 MIGLIORI 5")
                c1.table(df_res.sort_values("Var %", ascending=False).head(5))
                c2.error("📉 PEGGIORI 5")
                c2.table(df_res.sort_values("Var %", ascending=True).head(5))

# --- 2. ANALISI TICKER ---
elif scelta == "Analisi Ticker":
    st.title("🔍 Terminale di Analisi Avanzata")
    t_search = st.text_input("Inserisci Ticker (es: NVDA, BTC-USD):").upper()
    
    if t_search:
        data = yf.download(t_search, period="1y", interval="1d", progress=False)
        if not data.empty:
            data = calcola_indicatori(data)
            
            # Grafico a 3 livelli
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.5, 0.25, 0.25])
            fig.add_trace(go.Scatter(x=data.index, y=data['UB'], line=dict(width=0), showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['LB'], fill='tonexty', fillcolor='rgba(173,216,230,0.1)', line=dict(width=0), showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name='Prezzo', line=dict(color='white')), row=1, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['SMA200'], name='Trend Lungo', line=dict(color='yellow', dash='dot')), row=1, col=1)
            fig.add_trace(go.Bar(x=data.index, y=data['MACD']-data['Signal'], name='MACD Hist'), row=2, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], name='RSI', line=dict(color='magenta')), row=3, col=1)
            fig.update_layout(height=800, template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
            
            # Report Tecnico
            st.subheader("📋 Verdetto Automatico")
            rsi_u = data['RSI'].iloc[-1]
            macd_u = data['MACD'].iloc[-1]
            sig_u = data['Signal'].iloc[-1]
            
            col_a, col_b = st.columns(2)
            if rsi_u > 70: col_a.warning(f"🔥 RSI {rsi_u:.1f}: Ipercomprato")
            elif rsi_u < 30: col_a.success(f"❄️ RSI {rsi_u:.1f}: Ipervenduto")
            else: col_a.info(f"⚖️ RSI {rsi_u:.1f}: Neutrale")
            
            if macd_u > sig_u: col_b.success("📈 MACD: Segnale Bullish")
            else: col_b.error("📉 MACD: Segnale Bearish")
            
            # Bottone Acquisto
            st.divider()
            quant = st.number_input("Quantità da aggiungere:", min_value=0.0, step=1.0)
            if st.button("Aggiungi al mio Portfolio"):
                valuta = yf.Ticker(t_search).info.get('currency', 'USD')
                st.session_state.portfolio.append({"Ticker": t_search, "Q": quant, "Valuta": valuta})
                st.balloons()

# --- 3. IL MIO PORTFOLIO ---
elif scelta == "Il Mio Portfolio":
    st.title("💰 Situazione Patrimoniale")
    if st.session_state.portfolio:
        rows = []
        tot_val = 0
        for p in st.session_state.portfolio:
            curr_p = yf.Ticker(p['Ticker']).history(period="1d")['Close'].iloc[-1]
            tasso = get_fx(p['Valuta'], st.session_state.base_currency)
            val_base = (p['Q'] * curr_p) * tasso
            tot_val += val_base
            rows.append({"Asset": p['Ticker'], "Quantità": p['Q'], f"Valore in {st.session_state.base_currency}": round(val_base, 2)})
        
        c1, c2 = st.columns(2)
        c1.metric("Totale Investito", f"{tot_val:,.2f} {st.session_state.base_currency}")
        c2.metric("Liquidità Rimasta", f"{(st.session_state.budget - tot_val):,.2f}")
        
        df_final = pd.DataFrame(rows)
        fig_pie = px.pie(df_final, values=df_final.columns[2], names='Asset', hole=0.5, title="Distribuzione Asset")
        st.plotly_chart(fig_pie)
        st.dataframe(df_final, use_container_width=True)
    else:
        st.info("Nessun asset nel portfolio.")

# --- 4. IMPOSTAZIONI ---
elif scelta == "Impostazioni":
    st.title("⚙️ Configurazione")
    st.session_state.base_currency = st.selectbox("Cambia Valuta Base", ["EUR", "USD", "GBP", "CHF"])
    st.session_state.budget = st.number_input("Imposta Budget Totale", value=st.session_state.budget)
    if st.button("🔴 CANCELLA TUTTI I DATI"):
        st.session_state.portfolio = []
        st.rerun()
