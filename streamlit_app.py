import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
import os

# ==================== CONFIGURAZIONE ====================

st.set_page_config(
    page_title="Dashboard Oroscopi WhatsApp",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
    .clickable-metric {
        cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True)

# Carica variabili d'ambiente
load_dotenv()

# Inizializza session state per navigazione
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'dashboard'
if 'filter_type' not in st.session_state:
    st.session_state.filter_type = None

# ==================== CONNESSIONE SUPABASE ====================

@st.cache_resource
def init_supabase() -> Client:
    """Inizializza e restituisce il client Supabase"""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
    
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
    
    try:
        client = create_client(url, key)
        client.table('customers').select('id').limit(1).execute()
        return client
    except Exception as e:
        st.error(f"❌ Errore connessione a Supabase: {str(e)}")
        st.stop()

supabase = init_supabase()

# ==================== FUNZIONI QUERY DATABASE ====================

@st.cache_data(ttl=60)
def get_customer_stats():
    """Ottiene statistiche sui clienti"""
    try:
        all_customers = supabase.table('customers').select('id', count='exact').execute()
        total_customers = all_customers.count if hasattr(all_customers, 'count') else len(all_customers.data)
        
        active_subs = supabase.table('subscriptions')\
            .select('customer_id, service_plan_id, service_plans!inner(is_trial)')\
            .eq('is_active', True)\
            .eq('status', 'active')\
            .gte('end_date', datetime.now().date().isoformat())\
            .execute()
        
        trial_count = 0
        active_count = 0
        
        for sub in active_subs.data:
            service_plans = sub.get('service_plans')
            if service_plans and service_plans.get('is_trial'):
                trial_count += 1
            else:
                active_count += 1
        
        expired_subs = supabase.table('subscriptions')\
            .select('customer_id', count='exact')\
            .eq('status', 'expired')\
            .execute()
        
        expired_count = expired_subs.count if hasattr(expired_subs, 'count') else len(expired_subs.data)
        
        return {
            'totale_clienti': total_customers,
            'clienti_trial': trial_count,
            'clienti_attivi': active_count,
            'clienti_scaduti': expired_count
        }
        
    except Exception as e:
        st.error(f"Errore nel recupero statistiche clienti: {str(e)}")
        return {
            'totale_clienti': 0,
            'clienti_trial': 0,
            'clienti_attivi': 0,
            'clienti_scaduti': 0
        }

@st.cache_data(ttl=60)
def get_all_customers_details():
    """Ottiene tutti i clienti con dettagli completi"""
    try:
        response = supabase.table('customers')\
            .select('*, subscriptions(*, service_plans(*))')\
            .execute()
        
        customers_list = []
        for customer in response.data:
            # Prendi l'abbonamento più recente
            subs = customer.get('subscriptions', [])
            latest_sub = max(subs, key=lambda x: x.get('created_at', ''), default=None) if subs else None
            
            customers_list.append({
                'id': customer.get('id'),
                'nome': customer.get('name', 'N/A'),
                'telefono': customer.get('phone_number', 'N/A'),
                'data_nascita': customer.get('birth_date', 'N/A'),
                'segno': customer.get('zodiac_sign', 'N/A'),
                'ascendente': customer.get('ascendant', 'N/A'),
                'tipo_abbonamento': latest_sub.get('service_plans', {}).get('name', 'Nessuno') if latest_sub else 'Nessuno',
                'stato_abbonamento': latest_sub.get('status', 'Nessuno') if latest_sub else 'Nessuno',
                'is_trial': latest_sub.get('service_plans', {}).get('is_trial', False) if latest_sub else False,
                'data_inizio': latest_sub.get('start_date', 'N/A') if latest_sub else 'N/A',
                'data_scadenza': latest_sub.get('end_date', 'N/A') if latest_sub else 'N/A',
                'is_active': latest_sub.get('is_active', False) if latest_sub else False,
                'data_registrazione': customer.get('created_at', 'N/A')
            })
        
        return pd.DataFrame(customers_list)
        
    except Exception as e:
        st.error(f"Errore nel recupero dettagli clienti: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_filtered_customers(filter_type):
    """Ottiene clienti filtrati per tipo"""
    df = get_all_customers_details()
    
    if df.empty:
        return df
    
    today = datetime.now().date()
    
    if filter_type == 'totale':
        return df
    
    elif filter_type == 'attivi':
        # Clienti con abbonamento attivo NON trial
        filtered = df[
            (df['is_active'] == True) & 
            (df['stato_abbonamento'] == 'active') & 
            (df['is_trial'] == False)
        ].copy()
        
    elif filter_type == 'trial':
        # Clienti con abbonamento trial attivo
        filtered = df[
            (df['is_active'] == True) & 
            (df['stato_abbonamento'] == 'active') & 
            (df['is_trial'] == True)
        ].copy()
        
    elif filter_type == 'scaduti':
        # Clienti con abbonamento scaduto
        filtered = df[df['stato_abbonamento'] == 'expired'].copy()
    
    else:
        return df
    
    # Calcola giorni rimanenti per abbonamenti attivi
    if filter_type in ['attivi', 'trial']:
        filtered['giorni_rimanenti'] = filtered['data_scadenza'].apply(
            lambda x: (datetime.strptime(x, '%Y-%m-%d').date() - today).days if x != 'N/A' else 0
        )
    
    return filtered

@st.cache_data(ttl=60)
def get_horoscopes_today():
    """Ottiene statistiche oroscopi generati oggi"""
    today = datetime.now().date().isoformat()
    
    try:
        horoscopes = supabase.table('daily_horoscopes')\
            .select('*', count='exact')\
            .eq('data_oroscopo', today)\
            .execute()
        
        generated_count = horoscopes.count if hasattr(horoscopes, 'count') else len(horoscopes.data)
        
        try:
            active_combinations = supabase.table('active_customers_zodiac_combinations')\
                .select('*', count='exact')\
                .execute()
            
            total_needed = active_combinations.count if hasattr(active_combinations, 'count') else len(active_combinations.data)
        except:
            customers = supabase.table('customers')\
                .select('zodiac_sign, ascendant')\
                .not_.is_('ascendant', 'null')\
                .execute()
            
            combinations = set()
            for customer in customers.data:
                combo = (customer.get('zodiac_sign'), customer.get('ascendant'))
                if combo[0] and combo[1]:
                    combinations.add(combo)
            
            total_needed = len(combinations)
        
        success_rate = (generated_count / total_needed * 100) if total_needed > 0 else 0
        
        return {
            'generati': generated_count,
            'necessari': total_needed,
            'percentuale_successo': round(success_rate, 1)
        }
        
    except Exception as e:
        st.error(f"Errore nel recupero oroscopi: {str(e)}")
        return {
            'generati': 0,
            'necessari': 0,
            'percentuale_successo': 0
        }

@st.cache_data(ttl=60)
def get_expiring_subscriptions():
    """Ottiene abbonamenti in scadenza"""
    try:
        all_expiring = supabase.table('expiring_subscriptions_7_days')\
            .select('*')\
            .execute()
        
        if not all_expiring.data:
            return {
                'oggi': 0,
                'tre_giorni': 0,
                'sette_giorni': 0,
                'dettagli': []
            }
        
        df = pd.DataFrame(all_expiring.data)
        
        oggi = len(df[df['giorni_rimasti'] == 0]) if 'giorni_rimasti' in df.columns else 0
        tre_giorni = len(df[df['giorni_rimasti'] <= 3]) if 'giorni_rimasti' in df.columns else 0
        sette_giorni = len(df)
        
        return {
            'oggi': oggi,
            'tre_giorni': tre_giorni,
            'sette_giorni': sette_giorni,
            'dettagli': all_expiring.data
        }
        
    except Exception as e:
        try:
            today = datetime.now().date()
            seven_days = today + timedelta(days=7)
            
            expiring = supabase.table('subscriptions')\
                .select('*, customers(name, phone_number), service_plans(name)')\
                .eq('is_active', True)\
                .eq('status', 'active')\
                .gte('end_date', today.isoformat())\
                .lte('end_date', seven_days.isoformat())\
                .execute()
            
            details = []
            for sub in expiring.data:
                end_date = datetime.strptime(sub['end_date'], '%Y-%m-%d').date()
                days_left = (end_date - today).days
                
                details.append({
                    'name': sub.get('customers', {}).get('name', 'N/A'),
                    'numero': sub.get('customers', {}).get('phone_number', 'N/A'),
                    'end_date': sub['end_date'],
                    'tipo_subscription': sub.get('service_plans', {}).get('name', 'N/A'),
                    'giorni_rimasti': days_left
                })
            
            df = pd.DataFrame(details)
            
            return {
                'oggi': len(df[df['giorni_rimasti'] == 0]) if len(df) > 0 else 0,
                'tre_giorni': len(df[df['giorni_rimasti'] <= 3]) if len(df) > 0 else 0,
                'sette_giorni': len(df),
                'dettagli': details
            }
            
        except Exception as e2:
            st.error(f"Errore nel recupero scadenze: {str(e2)}")
            return {
                'oggi': 0,
                'tre_giorni': 0,
                'sette_giorni': 0,
                'dettagli': []
            }

# ==================== FUNZIONI NAVIGAZIONE ====================

def navigate_to(page, filter_type=None):
    """Cambia pagina e filtro"""
    st.session_state.current_page = page
    st.session_state.filter_type = filter_type
    st.rerun()

def go_back_to_dashboard():
    """Torna alla dashboard"""
    st.session_state.current_page = 'dashboard'
    st.session_state.filter_type = None
    st.rerun()

# ==================== LAYOUT DASHBOARD ====================

def render_header():
    """Renderizza l'header della dashboard"""
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.title("🌙 Dashboard Oroscopi WhatsApp")
        st.caption(f"📅 Ultimo aggiornamento: {datetime.now().strftime('%d/%m/%Y alle %H:%M:%S')}")
    
    with col2:
        if st.button("🔄 Aggiorna Dati", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.rerun()
    
    st.markdown("---")

def render_customer_stats():
    """Renderizza le statistiche dei clienti con link cliccabili"""
    st.subheader("👥 Statistiche Clienti")
    
    with st.spinner("Caricamento statistiche clienti..."):
        stats = get_customer_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📊 Totale Clienti",
            value=f"{stats['totale_clienti']:,}",
            help="Clicca per vedere tutti i clienti"
        )
        if st.button("🔍 Visualizza", key="btn_totale", use_container_width=True):
            navigate_to('customers', 'totale')
    
    with col2:
        st.metric(
            label="✅ Clienti Attivi",
            value=f"{stats['clienti_attivi']:,}",
            delta=f"{stats['clienti_attivi']} paganti",
            delta_color="normal",
            help="Clicca per vedere i clienti attivi"
        )
        if st.button("🔍 Visualizza", key="btn_attivi", use_container_width=True):
            navigate_to('customers', 'attivi')
    
    with col3:
        st.metric(
            label="🎁 Trial Attivi",
            value=f"{stats['clienti_trial']:,}",
            help="Clicca per vedere i trial attivi"
        )
        if st.button("🔍 Visualizza", key="btn_trial", use_container_width=True):
            navigate_to('customers', 'trial')
    
    with col4:
        st.metric(
            label="⏸️ Scaduti",
            value=f"{stats['clienti_scaduti']:,}",
            delta="Da riattivare",
            delta_color="inverse",
            help="Clicca per vedere i clienti scaduti"
        )
        if st.button("🔍 Visualizza", key="btn_scaduti", use_container_width=True):
            navigate_to('customers', 'scaduti')

def render_horoscope_stats():
    """Renderizza le statistiche degli oroscopi"""
    st.subheader("📜 Oroscopi di Oggi")
    
    with st.spinner("Caricamento statistiche oroscopi..."):
        stats = get_horoscopes_today()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="📝 Oroscopi Generati",
            value=f"{stats['generati']:,}",
            help="Numero di oroscopi già generati per oggi"
        )
    
    with col2:
        st.metric(
            label="🎯 Combinazioni Necessarie",
            value=f"{stats['necessari']:,}",
            help="Numero totale di combinazioni segno/ascendente da generare"
        )
    
    with col3:
        success_rate = stats['percentuale_successo']
        delta_text = "Completato ✓" if success_rate >= 100 else f"Mancano {stats['necessari'] - stats['generati']}"
        
        st.metric(
            label="📈 Completamento",
            value=f"{success_rate}%",
            delta=delta_text,
            delta_color="normal" if success_rate >= 100 else "inverse",
            help="Percentuale di oroscopi generati rispetto al totale necessario"
        )
    
    progress = min(success_rate / 100, 1.0)
    st.progress(progress, text=f"Progresso generazione: {success_rate}%")
    
    if success_rate < 100:
        st.warning(f"⚠️ Attenzione: Mancano ancora **{stats['necessari'] - stats['generati']} oroscopi** da generare per oggi")
    else:
        st.success("✅ Perfetto! Tutti gli oroscopi sono stati generati!")

def render_expiring_subscriptions():
    """Renderizza gli abbonamenti in scadenza"""
    st.subheader("⏰ Abbonamenti in Scadenza")
    
    with st.spinner("Caricamento scadenze..."):
        stats = get_expiring_subscriptions()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        urgency = "🔴 URGENTE!" if stats['oggi'] > 0 else ""
        st.metric(
            label="🚨 In Scadenza Oggi",
            value=f"{stats['oggi']:,}",
            delta=urgency,
            delta_color="inverse" if stats['oggi'] > 0 else "off",
            help="Abbonamenti che scadono oggi"
        )
    
    with col2:
        st.metric(
            label="⚠️ Entro 3 Giorni",
            value=f"{stats['tre_giorni']:,}",
            delta="Attenzione" if stats['tre_giorni'] > 0 else "Tutto ok",
            delta_color="inverse" if stats['tre_giorni'] > 0 else "off",
            help="Abbonamenti che scadono nei prossimi 3 giorni"
        )
    
    with col3:
        st.metric(
            label="📅 Entro 7 Giorni",
            value=f"{stats['sette_giorni']:,}",
            help="Abbonamenti che scadono nei prossimi 7 giorni"
        )
    
    if stats['dettagli']:
        st.markdown("#### 📋 Dettaglio Scadenze Imminenti")
        
        df = pd.DataFrame(stats['dettagli'])
        df_display = df[['name', 'numero', 'end_date', 'tipo_subscription', 'giorni_rimasti']].copy()
        df_display.columns = ['Nome', 'Telefono', 'Data Scadenza', 'Piano', 'Giorni Rimasti']
        df_display = df_display.sort_values('Giorni Rimasti')
        
        def highlight_urgency(row):
            if row['Giorni Rimasti'] == 0:
                return ['background-color: #ffcccc; font-weight: bold'] * len(row)
            elif row['Giorni Rimasti'] <= 3:
                return ['background-color: #fff4cc'] * len(row)
            else:
                return ['background-color: #e8f4f8'] * len(row)
        
        st.dataframe(
            df_display.style.apply(highlight_urgency, axis=1),
            use_container_width=True,
            height=400,
            hide_index=True
        )
        
        with st.expander("📊 Visualizza Grafico Distribuzione"):
            fig = px.bar(
                df.groupby('giorni_rimasti').size().reset_index(name='count'),
                x='giorni_rimasti',
                y='count',
                title='Distribuzione Abbonamenti per Giorni alla Scadenza',
                labels={'giorni_rimasti': 'Giorni alla Scadenza', 'count': 'Numero Abbonamenti'},
                color='count',
                color_continuous_scale='Reds_r'
            )
            
            fig.update_layout(
                xaxis_title="Giorni alla Scadenza",
                yaxis_title="Numero Abbonamenti",
                showlegend=False,
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("✅ Ottimo! Nessun abbonamento in scadenza nei prossimi 7 giorni")

# ==================== PAGINA DETTAGLIO CLIENTI ====================

def render_customers_page(filter_type):
    """Renderizza la pagina di dettaglio clienti"""
    
    # Header con pulsante indietro
    col1, col2 = st.columns([4, 1])
    with col1:
        titles = {
            'totale': '📊 Tutti i Clienti',
            'attivi': '✅ Clienti Attivi (Abbonamento Pagante)',
            'trial': '🎁 Clienti Trial (Periodo di Prova)',
            'scaduti': '⏸️ Clienti Scaduti'
        }
        st.title(titles.get(filter_type, 'Clienti'))
    
    with col2:
        if st.button("⬅️ Torna alla Dashboard", use_container_width=True, type="secondary"):
            go_back_to_dashboard()
    
    st.markdown("---")
    
    # Carica dati
    with st.spinner("Caricamento clienti..."):
        df = get_filtered_customers(filter_type)
    
    if df.empty:
        st.info("📭 Nessun cliente trovato con questi criteri")
        return
    
    # Statistiche riepilogo
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Totale Clienti", len(df))
    
    with col2:
        if 'giorni_rimanenti' in df.columns:
            avg_days = df['giorni_rimanenti'].mean()
            st.metric("📅 Media Giorni Rimanenti", f"{avg_days:.0f}")
        else:
            st.metric("📊 Segni Unici", df['segno'].nunique())
    
    with col3:
        st.metric("🌟 Ascendenti Definiti", df['ascendente'].notna().sum())
    
    with col4:
        if filter_type == 'scaduti':
            st.metric("⚠️ Da Riattivare", len(df), delta="Opportunità", delta_color="inverse")
        else:
            st.metric("📱 Con Telefono", df['telefono'].notna().sum())
    
    st.markdown("---")
    
    # Filtri
    st.subheader("🔍 Filtri e Ricerca")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_name = st.text_input("🔎 Cerca per nome", placeholder="Inserisci nome cliente...")
    
    with col2:
        if filter_type in ['attivi', 'trial']:
            signs = ['Tutti'] + sorted(df['segno'].dropna().unique().tolist())
            selected_sign = st.selectbox("♈ Filtra per Segno", signs)
        else:
            selected_sign = 'Tutti'
    
    with col3:
        if 'tipo_abbonamento' in df.columns:
            plans = ['Tutti'] + sorted(df['tipo_abbonamento'].dropna().unique().tolist())
            selected_plan = st.selectbox("💳 Filtra per Piano", plans)
        else:
            selected_plan = 'Tutti'
    
    # Applica filtri
    df_filtered = df.copy()
    
    if search_name:
        df_filtered = df_filtered[df_filtered['nome'].str.contains(search_name, case=False, na=False)]
    
    if selected_sign != 'Tutti':
        df_filtered = df_filtered[df_filtered['segno'] == selected_sign]
    
    if selected_plan != 'Tutti':
        df_filtered = df_filtered[df_filtered['tipo_abbonamento'] == selected_plan]
    
    st.info(f"📊 Visualizzati **{len(df_filtered)}** clienti su **{len(df)}** totali")
    
    st.markdown("---")
    
    # Tabella principale
    st.subheader("📋 Elenco Clienti")
    
    # Prepara colonne da mostrare
    if filter_type in ['attivi', 'trial']:
        columns_to_show = ['nome', 'telefono', 'segno', 'ascendente', 'tipo_abbonamento', 
                          'data_inizio', 'data_scadenza', 'giorni_rimanenti']
        column_names = ['Nome', 'Telefono', 'Segno', 'Ascendente', 'Piano', 
                       'Inizio', 'Scadenza', 'Giorni Rimasti']
    elif filter_type == 'scaduti':
        columns_to_show = ['nome', 'telefono', 'segno', 'ascendente', 'tipo_abbonamento', 
                          'data_scadenza', 'data_registrazione']
        column_names = ['Nome', 'Telefono', 'Segno', 'Ascendente', 'Piano', 
                       'Data Scadenza', 'Registrato il']
    else:  # totale
        columns_to_show = ['nome', 'telefono', 'segno', 'ascendente', 'tipo_abbonamento', 
                          'stato_abbonamento', 'data_registrazione']
        column_names = ['Nome', 'Telefono', 'Segno', 'Ascendente', 'Piano', 
                       'Stato', 'Registrato il']
    
    # Crea dataframe per visualizzazione
    df_display = df_filtered[columns_to_show].copy()
    df_display.columns = column_names
    
    # Formatta date
    for col in df_display.columns:
        if 'Data' in col or 'Inizio' in col or 'Scadenza' in col or 'Registrato' in col:
            df_display[col] = pd.to_datetime(df_display[col], errors='coerce').dt.strftime('%d/%m/%Y')
            df_display[col] = df_display[col].fillna('N/A')
    
    # Configurazione tabella interattiva
    st.dataframe(
        df_display,
        use_container_width=True,
        height=600,
        hide_index=True,
        column_config={
            "Giorni Rimasti": st.column_config.NumberColumn(
                "Giorni Rimasti",
                help="Giorni rimanenti all'abbonamento",
                format="%d giorni"
            ) if 'Giorni Rimasti' in column_names else None
        }
    )
    
    # Pulsanti azioni
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Esporta in CSV", use_container_width=True):
            csv = df_filtered.to_csv(index=False)
            st.download_button(
                label="⬇️ Scarica CSV",
                data=csv,
                file_name=f"clienti_{filter_type}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        if st.button("📊 Visualizza Statistiche", use_container_width=True):
            st.session_state.show_stats = True
    
    with col3:
        if st.button("🔄 Aggiorna Dati", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Statistiche dettagliate (opzionale)
    if st.session_state.get('show_stats', False):
        st.markdown("---")
        st.subheader("📈 Statistiche Dettagliate")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribuzione per segno
            if 'segno' in df_filtered.columns:
                st.markdown("#### Distribuzione per Segno Zodiacale")
                sign_counts = df_filtered['segno'].value_counts()
                fig = px.pie(
                    values=sign_counts.values,
                    names=sign_counts.index,
                    title='Distribuzione Segni Zodiacali'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Distribuzione per piano
            if 'tipo_abbonamento' in df_filtered.columns:
                st.markdown("#### Distribuzione per Piano")
                plan_counts = df_filtered['tipo_abbonamento'].value_counts()
                fig = px.bar(
                    x=plan_counts.index,
                    y=plan_counts.values,
                    title='Distribuzione Piani di Abbonamento',
                    labels={'x': 'Piano', 'y': 'Numero Clienti'}
                )
                st.plotly_chart(fig, use_container_width=True)

# ==================== LAYOUT PRINCIPALE ====================

def render_footer():
    """Renderizza il footer"""
    st.markdown("---")
    st.caption("💡 **Nota**: I dati vengono aggiornati automaticamente ogni 60 secondi.")
    st.caption("🔒 Connesso a Supabase | 🌙 Sistema Oroscopi WhatsApp v1.0")

def main():
    """Funzione principale dell'applicazione"""
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150x150.png?text=🌙", width=150)
        st.title("Menu")
        st.markdown("---")
        
        # Navigation
        if st.session_state.current_page != 'dashboard':
            if st.button("🏠 Torna alla Dashboard", use_container_width=True):
                go_back_to_dashboard()
            st.markdown("---")
        
        st.markdown("### ⚙️ Impostazioni")
        st.caption("Cache automatica: 60s")
        
        if st.button("🗑️ Pulisci Cache", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache pulita!")
            st.rerun()
        
        st.markdown("---")
        st.caption("📊 Dashboard v1.0")
    
    # Routing delle pagine
    if st.session_state.current_page == 'dashboard':
        render_header()
        render_customer_stats()
        st.markdown("---")
        render_horoscope_stats()
        st.markdown("---")
        render_expiring_subscriptions()
        render_footer()
    
    elif st.session_state.current_page == 'customers':
        render_customers_page(st.session_state.filter_type)

if __name__ == "__main__":
    main()