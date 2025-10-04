"""
Configurazione e inizializzazione connessione Supabase
"""

import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Carica variabili d'ambiente
load_dotenv()

def apply_custom_css():
    """Applica CSS personalizzato all'app"""
    st.markdown("""
        <style>
        .main {
            padding-top: 2rem;
        }
        .stMetric {
            background-color: #f0f2f6;
            padding: 15px;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .stMetric:hover {
            background-color: #e1e4e8;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }
        h1 {
            color: #1f77b4;
        }
        .stProgress > div > div > div > div {
            background-color: #1f77b4;
        }
        </style>
        """, unsafe_allow_html=True)

@st.cache_resource
def init_supabase() -> Client:
    """
    Inizializza e restituisce il client Supabase.
    Usa cache_resource per mantenere la connessione attiva.
    """
    # Prova prima con st.secrets (per Streamlit Cloud)
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except:
        # Fallback a variabili d'ambiente (per sviluppo locale)
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
    
    # Verifica che le credenziali esistano
    if not url or not key:
        st.error("⚠️ **Errore di Configurazione**")
        st.warning("""
        Credenziali Supabase mancanti! 
        
        Per configurare:
        1. Crea un file `.env` nella root del progetto
        2. Aggiungi le seguenti righe:
        SUPABASE_URL=https://tuo-progetto.supabase.co
        SUPABASE_KEY=tua-chiave-api-supabase
        3. Riavvia l'applicazione
        """)
        st.stop()
    
    # Crea e testa la connessione
    try:
        client = create_client(url, key)
        # Test connessione con una query semplice
        client.table('customers').select('id').limit(1).execute()
        return client
    except Exception as e:
        st.error(f"❌ Errore connessione a Supabase: {str(e)}")
        st.stop()

# Inizializza il client globale
supabase = init_supabase()