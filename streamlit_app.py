"""
Entry Point Principale - Dashboard Oroscopi WhatsApp
Gestisce il routing tra le diverse pagine dell'applicazione
"""

import streamlit as st
from utils.config import apply_custom_css
from pages_content import dashboard, customers, horoscopes, customer_detail, statistics, messages

# ==================== CONFIGURAZIONE ====================

st.set_page_config(
    page_title="Dashboard Oroscopi WhatsApp",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Applica CSS personalizzato
apply_custom_css()

# ==================== SESSION STATE ====================

# Inizializza session state per la navigazione
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'dashboard'

if 'filter_type' not in st.session_state:
    st.session_state.filter_type = None

# ==================== SIDEBAR ====================

def render_sidebar():
    """Renderizza la sidebar con menu di navigazione"""
    
    with st.sidebar:
        # Logo/Header
        st.markdown("### 🌙 Oroscopi WhatsApp")
        st.markdown("---")
        
        # Menu navigazione principale
        st.markdown("#### 📍 Navigazione")
        
        # Dashboard
        if st.button(
            "🏠 Dashboard", 
            use_container_width=True, 
            type="primary" if st.session_state.current_page == 'dashboard' else "secondary"
        ):
            st.session_state.current_page = 'dashboard'
            st.session_state.filter_type = None
            st.rerun()
        
        # Clienti
        if st.button(
            "👥 Clienti", 
            use_container_width=True,
            type="primary" if st.session_state.current_page in ['customers', 'customer_detail'] else "secondary"
        ):
            st.session_state.current_page = 'customers'
            st.session_state.filter_type = 'totale'
            st.rerun()
        
        # Oroscopi
        if st.button(
            "📜 Oroscopi", 
            use_container_width=True,
            type="primary" if st.session_state.current_page == 'horoscopes' else "secondary"
        ):
            st.session_state.current_page = 'horoscopes'
            st.rerun()
        
        # Statistiche
        if st.button(
            "📊 Statistiche", 
            use_container_width=True,
            type="primary" if st.session_state.current_page == 'statistics' else "secondary"
        ):
            st.session_state.current_page = 'statistics'
            st.rerun()
        
        # Messaggi
        if st.button(
            "📨 Messaggi", 
            use_container_width=True,
            type="primary" if st.session_state.current_page == 'messages' else "secondary"
        ):
            st.session_state.current_page = 'messages'
            st.rerun()
        
        st.markdown("---")
        
        # Breadcrumb / Stato corrente
        if st.session_state.current_page != 'dashboard':
            st.markdown("#### 📌 Posizione Corrente")
            
            page_names = {
                'customers': '👥 Gestione Clienti',
                'customer_detail': '👤 Dettaglio Cliente',
                'horoscopes': '📜 Archivio Oroscopi',
                'statistics': '📊 Statistiche',
                'messages': '📨 Messaggi WhatsApp'

            }
            
            current_name = page_names.get(st.session_state.current_page, 'Sconosciuta')
            st.caption(f"📍 {current_name}")
            
            st.markdown("---")
        
        # Impostazioni
        st.markdown("#### ⚙️ Impostazioni")
        
        if st.button("🗑️ Pulisci Cache", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Cache pulita!")
            st.rerun()
        
        st.markdown("---")
        
        # Info
        st.caption("📊 Dashboard v1.0")
        st.caption("🔒 Connesso a Supabase")
        
        # Mostra pagina corrente per debug (opzionale, puoi rimuovere)
        if st.session_state.get('debug_mode', False):
            st.caption(f"🔧 Debug: {st.session_state.current_page}")

# ==================== ROUTING ====================

def main():
    """Funzione principale - gestisce il routing tra le pagine"""
    
    # Renderizza sidebar
    render_sidebar()
    
    # Routing verso la pagina corretta
    if st.session_state.current_page == 'dashboard':
        # Dashboard principale
        dashboard.render()
        render_footer()
    
    elif st.session_state.current_page == 'customers':
        # Lista clienti (con filtro)
        customers.render(st.session_state.filter_type or 'totale')
    
    elif st.session_state.current_page == 'customer_detail':
        # Dettaglio singolo cliente
        customer_id = st.session_state.filter_type
        if customer_id:
            customer_detail.render(customer_id)
        else:
            st.error("❌ ID cliente mancante")
            st.session_state.current_page = 'customers'
            st.session_state.filter_type = 'totale'
            st.rerun()
    
    elif st.session_state.current_page == 'horoscopes':
        # Archivio oroscopi
        horoscopes.render()
    
    elif st.session_state.current_page == 'statistics':
        # Pagina statistiche
        statistics.render()

    elif st.session_state.current_page == 'messages':
        # Pagina messaggi WhatsApp
        messages.render()
    
    else:
        # Fallback: pagina non trovata
        st.error(f"❌ Pagina '{st.session_state.current_page}' non trovata")
        st.info("Torno alla Dashboard...")
        st.session_state.current_page = 'dashboard'
        st.rerun()

def render_footer():
    """Renderizza il footer della dashboard"""
    st.markdown("---")
    st.caption("💡 **Nota**: I dati vengono aggiornati automaticamente ogni 60 secondi.")
    st.caption("🌙 Sistema Oroscopi WhatsApp - Powered by Streamlit & Supabase")

# ==================== AVVIO ====================

if __name__ == "__main__":
    main()