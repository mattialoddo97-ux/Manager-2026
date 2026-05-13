import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Mentor Advisor - Portfolio", layout="wide")

# Inizializziamo il portafoglio nella memoria della sessione se non esiste
if 'portafoglio' not in st.session_state:
    st.session_state.portafoglio = []

# --- SIDEBAR (GESTIONE PORTAFOGLIO) ---
st.sidebar.header("💰 Gestisci Portafoglio")

with st.sidebar.expander("➕ Aggiungi Titolo"):
    nuovo_ticker = st.text_input("Ticker (es: NVDA):").upper()
    capitale_investito = st.number_input("Capitale Investito ($):", min_value=0.0, step=100.0)
    prezzo_ingresso = st.number_input("Prezzo di Ingresso ($):", min_value=0.0, step=0.1)
    
    if st.button("Aggiungi al Portafoglio"):
        if nuovo_ticker and capitale_investito > 0:
            st.session_state.portafoglio.append({
                "ticker": nuovo_ticker,
                "investito": capitale_investito,
                "ingresso": prezzo_ingresso
            })
            st.success(f"Aggiunto {nuovo_ticker}!")

if st.sidebar.button("Svuota Portafoglio"):
    st.session_state.portafoglio = []
    st.rerun()

# --- ANALISI TITOLO SINGOLO (La tua dashboard precedente) ---
st.sidebar.header("🔍 Analisi Mercato")
ticker_scelto = st.sidebar.text_input("Cerca Titolo:", "AAPL").upper()

try:
    data_azione = yf.Ticker(ticker_scelto)
    prezzo_live = data_azione.history(period="1d")['Close'].iloc[-1]
    
    st.title(f"📈 Dashboard {ticker_scelto}")
    st.metric("Prezzo Live", f"${prezzo_live:,.2f}")

    # --- SEZIONE PORTAFOGLIO ---
    st.divider()
    st.header("💼 Il Mio Portafoglio")

    if st.session_state.portafoglio:
        dati_tabella = []
        totale_investito = 0
        totale_attuale = 0

        for item in st.session_state.portafoglio:
            t = yf.Ticker(item['ticker'])
            p_attuale = t.history(period="1d")['Close'].iloc[-1]
            
            # Calcolo rendimento
            quantita = item['investito'] / item['ingresso'] if item['ingresso'] > 0 else 0
            valore_attuale = quantita * p_attuale
            guadagno_assoluto = valore_attuale - item['investito']
            guadagno_perc = ((p_attuale - item['ingresso']) / item['ingresso']) * 100 if item['ingresso'] > 0 else 0
            
            totale_investito += item['investito']
            totale_attuale += valore_attuale

            dati_tabella.append({
                "Titolo": item['ticker'],
                "Investito ($)": f"{item['investito']:,.2f}",
                "Prezzo Ingresso": f"{item['ingresso']:,.2f}",
                "Prezzo Attuale": f"{p_attuale:,.2f}",
                "Valore Attuale ($)": f"{valore_attuale:,.2f}",
                "P/L (%)": f"{guadagno_perc:+.2f}%",
                "P/L ($)": f"{guadagno_assoluto:+.2f}"
            })

        # Visualizzazione Tabella Portafoglio
        df_portfolio = pd.DataFrame(dati_tabella)
        st.table(df_portfolio)

        # Riepilogo Totale
        c1, c2 = st.columns(2)
        profitto_totale = totale_attuale - totale_investito
        perc_totale = (profitto_totale / totale_investito) * 100 if totale_investito > 0 else 0
        
        c1.metric("Totale Investito", f"${totale_investito:,.2f}")
        c2.metric("Profitto/Perdita Totale", f"${profitto_totale:,.2f}", f"{perc_totale:+.2f}%")
    else:
        st.info("Il tuo portafoglio è vuoto. Aggiungi un titolo dalla barra laterale!")

except Exception as e:
    st.error(f"Errore nel caricamento: {e}")
