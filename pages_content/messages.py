"""
Pagina Messaggi WhatsApp
Visualizza e gestisce i messaggi ricevuti dagli utenti
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.config import supabase  # <-- IMPORT CORRETTO

# ==================== FUNZIONI DATABASE ====================

@st.cache_data(ttl=30)  # Cache 30 secondi per messaggi più recenti
def get_messages(limit: int = 100, phone_filter: str = None, days_back: int = 7):
    """
    Recupera i messaggi WhatsApp dalla tabella
    
    Args:
        limit: Numero massimo di messaggi da recuperare
        phone_filter: Filtro opzionale per numero di telefono
        days_back: Giorni indietro da cui recuperare i messaggi
    """
    try:
        # Data limite
        date_limit = datetime.now() - timedelta(days=days_back)
        
        query = supabase.table('whatsapp_messages')\
            .select('*')\
            .gte('created_at', date_limit.isoformat())\
            .order('created_at', desc=True)\
            .limit(limit)
        
        # Applica filtro telefono se presente
        if phone_filter and phone_filter.strip():
            query = query.ilike('phone_number', f'%{phone_filter}%')
        
        response = query.execute()
        return response.data if response.data else []
    
    except Exception as e:
        st.error(f"❌ Errore nel recupero messaggi: {e}")
        return []


@st.cache_data(ttl=60)
def get_message_stats():
    """Recupera statistiche sui messaggi"""
    try:
        # Messaggi oggi
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        today_response = supabase.table('whatsapp_messages')\
            .select('id', count='exact')\
            .gte('created_at', today.isoformat())\
            .execute()
        
        # Messaggi ultima settimana
        week_ago = datetime.now() - timedelta(days=7)
        
        week_response = supabase.table('whatsapp_messages')\
            .select('id', count='exact')\
            .gte('created_at', week_ago.isoformat())\
            .execute()
        
        # Utenti unici ultima settimana
        unique_users_response = supabase.table('whatsapp_messages')\
            .select('phone_number')\
            .gte('created_at', week_ago.isoformat())\
            .execute()
        
        unique_users = len(set([m['phone_number'] for m in unique_users_response.data])) if unique_users_response.data else 0
        
        return {
            'today': today_response.count or 0,
            'week': week_response.count or 0,
            'unique_users': unique_users
        }
    
    except Exception as e:
        st.error(f"❌ Errore statistiche: {e}")
        return {'today': 0, 'week': 0, 'unique_users': 0}


@st.cache_data(ttl=60)
def get_unique_phone_numbers():
    """Recupera lista di numeri di telefono unici per il filtro"""
    try:
        response = supabase.table('whatsapp_messages')\
            .select('phone_number, pushname')\
            .order('created_at', desc=True)\
            .execute()
        
        if response.data:
            # Crea dizionario phone -> pushname (prende il più recente)
            phone_names = {}
            for msg in response.data:
                phone = msg['phone_number']
                if phone not in phone_names:
                    phone_names[phone] = msg.get('pushname') or phone
            return phone_names
        return {}
    
    except Exception as e:
        return {}


# ==================== FUNZIONI UI ====================

def format_phone_display(phone: str, pushname: str = None) -> str:
    """Formatta il numero di telefono per la visualizzazione"""
    if pushname and pushname.strip():
        return f"{pushname} ({phone})"
    return phone


def format_message_type_badge(msg_type: str) -> str:
    """Ritorna un badge colorato per il tipo di messaggio"""
    badges = {
        'text': '💬',
        'image': '🖼️',
        'audio': '🎵',
        'video': '🎬',
        'document': '📄',
        'sticker': '🏷️',
        'location': '📍',
        'contact': '👤',
    }
    return badges.get(msg_type.lower(), '📨') + f" {msg_type}"


def render_message_card(message: dict):
    """Renderizza una card per un singolo messaggio"""
    
    with st.container():
        # Header con info utente e timestamp
        col1, col2 = st.columns([3, 1])
        
        with col1:
            pushname = message.get('pushname') or 'Sconosciuto'
            phone = message.get('phone_number', 'N/A')
            st.markdown(f"**{pushname}** `{phone}`")
        
        with col2:
            created_at = message.get('created_at')
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    st.caption(dt.strftime("%d/%m/%Y %H:%M"))
                except:
                    st.caption(created_at)
        
        # Tipo messaggio
        msg_type = message.get('message_type', 'unknown')
        st.caption(format_message_type_badge(msg_type))
        
        # Contenuto messaggio
        body = message.get('body')
        if body:
            st.markdown(f"> {body}")
        
        # Media (se presente)
        media = message.get('media')
        if media:
            with st.expander("📎 Media allegato"):
                st.code(media, language=None)
        
        st.markdown("---")


# ==================== PAGINA PRINCIPALE ====================

def render():
    """Renderizza la pagina dei messaggi"""
    
    st.title("📨 Messaggi WhatsApp")
    st.markdown("Visualizza i messaggi ricevuti dagli utenti")
    
    # ===== STATISTICHE =====
    stats = get_message_stats()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="📬 Messaggi Oggi",
            value=stats['today']
        )
    
    with col2:
        st.metric(
            label="📊 Messaggi (7 giorni)",
            value=stats['week']
        )
    
    with col3:
        st.metric(
            label="👥 Utenti Unici",
            value=stats['unique_users']
        )
    
    st.markdown("---")
    
    # ===== FILTRI =====
    st.markdown("### 🔍 Filtri")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Filtro per numero di telefono
        phone_numbers = get_unique_phone_numbers()
        
        phone_options = ["Tutti"] + [
            format_phone_display(phone, name) 
            for phone, name in phone_numbers.items()
        ]
        
        selected_phone_display = st.selectbox(
            "📱 Filtra per utente",
            options=phone_options,
            index=0
        )
        
        # Estrai il numero dal display
        if selected_phone_display == "Tutti":
            phone_filter = None
        else:
            # Estrai il numero tra parentesi se presente, altrimenti usa tutto
            if '(' in selected_phone_display:
                phone_filter = selected_phone_display.split('(')[-1].replace(')', '')
            else:
                phone_filter = selected_phone_display
    
    with col2:
        days_back = st.selectbox(
            "📅 Periodo",
            options=[1, 3, 7, 14, 30],
            index=2,
            format_func=lambda x: f"Ultimi {x} giorni" if x > 1 else "Oggi"
        )
    
    with col3:
        limit = st.selectbox(
            "📊 Messaggi da mostrare",
            options=[50, 100, 200, 500],
            index=1
        )
    
    # Pulsante refresh
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Aggiorna", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    st.markdown("---")
    
    # ===== LISTA MESSAGGI =====
    st.markdown("### 📋 Messaggi Recenti")
    
    messages = get_messages(
        limit=limit,
        phone_filter=phone_filter,
        days_back=days_back
    )
    
    if not messages:
        st.info("📭 Nessun messaggio trovato per i filtri selezionati")
        return
    
    st.caption(f"Trovati {len(messages)} messaggi")
    
    # Toggle vista: Cards o Tabella
    view_mode = st.radio(
        "Modalità visualizzazione",
        options=["📋 Lista", "📊 Tabella"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if view_mode == "📋 Lista":
        # Vista a cards
        for message in messages:
            render_message_card(message)
    
    else:
        # Vista tabella
        df = pd.DataFrame(messages)
        
        # Riordina e rinomina colonne
        columns_order = ['created_at', 'pushname', 'phone_number', 'message_type', 'body']
        columns_names = {
            'created_at': '📅 Data',
            'pushname': '👤 Nome',
            'phone_number': '📱 Telefono',
            'message_type': '📨 Tipo',
            'body': '💬 Messaggio'
        }
        
        # Filtra solo colonne esistenti
        available_cols = [c for c in columns_order if c in df.columns]
        df_display = df[available_cols].rename(columns=columns_names)
        
        # Formatta data
        if '📅 Data' in df_display.columns:
            df_display['📅 Data'] = pd.to_datetime(df_display['📅 Data']).dt.strftime('%d/%m/%Y %H:%M')
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True
        )
    
    # ===== EXPORT =====
    st.markdown("---")
    
    with st.expander("📥 Esporta Dati"):
        df_export = pd.DataFrame(messages)
        
        csv = df_export.to_csv(index=False)
        st.download_button(
            label="⬇️ Scarica CSV",
            data=csv,
            file_name=f"messaggi_whatsapp_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )