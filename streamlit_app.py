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

# Custom CSS per migliorare l'aspetto
st.markdown("""
    <style>
    .main {
        padding-top: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
    }
    h1 {
        color: #1f77b4;
    }
    .stProgress > div > div > div > div {
        background-color: #1f77b4;
    }
    </style>
    """, unsafe_allow_html=True)

# Carica variabili d'ambiente
load_dotenv()

# ==================== CONNESSIONE SUPABASE ====================

@st.cache_resource
def init_supabase() -> Client:
    """Inizializza e restituisce il client Supabase"""
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
        # Test connessione
        client.table('customers').select('id').limit(1).execute()
        return client
    except Exception as e:
        st.error(f"❌ Errore connessione a Supabase: {str(e)}")
        st.stop()

supabase = init_supabase()

# ==================== FUNZIONI QUERY DATABASE ====================

@st.cache_data(ttl=60)
def get_customer_stats():
    """Ottiene statistiche sui clienti (attivi, trial, scaduti)"""
    try:
        # Query tutti i clienti
        all_customers = supabase.table('customers').select('id', count='exact').execute()
        total_customers = all_customers.count if hasattr(all_customers, 'count') else len(all_customers.data)
        
        # Query abbonamenti attivi
        active_subs = supabase.table('subscriptions')\
            .select('customer_id, service_plan_id, service_plans!inner(is_trial)')\
            .eq('is_active', True)\
            .eq('status', 'active')\
            .gte('end_date', datetime.now().date().isoformat())\
            .execute()
        
        # Conta trial vs attivi
        trial_count = 0
        active_count = 0
        
        for sub in active_subs.data:
            service_plans = sub.get('service_plans')
            if service_plans and service_plans.get('is_trial'):
                trial_count += 1
            else:
                active_count += 1
        
        # Query abbonamenti scaduti
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
def get_horoscopes_today():
    """Ottiene statistiche oroscopi generati oggi"""
    today = datetime.now().date().isoformat()
    
    try:
        # Oroscopi generati oggi
        horoscopes = supabase.table('daily_horoscopes')\
            .select('*', count='exact')\
            .eq('data_oroscopo', today)\
            .execute()
        
        generated_count = horoscopes.count if hasattr(horoscopes, 'count') else len(horoscopes.data)
        
        # Combinazioni attive necessarie (dalla vista)
        try:
            active_combinations = supabase.table('active_customers_zodiac_combinations')\
                .select('*', count='exact')\
                .execute()
            
            total_needed = active_combinations.count if hasattr(active_combinations, 'count') else len(active_combinations.data)
        except:
            # Se la vista non esiste, stima dalle combinazioni uniche nei clienti attivi
            customers = supabase.table('customers')\
                .select('zodiac_sign, ascendant')\
                .not_.is_('ascendant', 'null')\
                .execute()
            
            # Conta combinazioni uniche
            combinations = set()
            for customer in customers.data:
                combo = (customer.get('zodiac_sign'), customer.get('ascendant'))
                if combo[0] and combo[1]:
                    combinations.add(combo)
            
            total_needed = len(combinations)
        
        # Calcola percentuale successo
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
    """Ottiene abbonamenti in scadenza per fasce temporali"""
    try:
        # Prova a usare la vista esistente
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
        
        # Conta per fasce
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
        # Fallback: calcola manualmente
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
    """Renderizza le statistiche dei clienti"""
    st.subheader("👥 Statistiche Clienti")
    
    with st.spinner("Caricamento statistiche clienti..."):
        stats = get_customer_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📊 Totale Clienti",
            value=f"{stats['totale_clienti']:,}",
            help="Numero totale di clienti registrati nel sistema"
        )
    
    with col2:
        st.metric(
            label="✅ Clienti Attivi",
            value=f"{stats['clienti_attivi']:,}",
            delta=f"{stats['clienti_attivi']} paganti",
            delta_color="normal",
            help="Clienti con abbonamento a pagamento attivo"
        )
    
    with col3:
        st.metric(
            label="🎁 Trial Attivi",
            value=f"{stats['clienti_trial']:,}",
            help="Clienti in periodo di prova gratuito"
        )
    
    with col4:
        st.metric(
            label="⏸️ Scaduti",
            value=f"{stats['clienti_scaduti']:,}",
            delta="Da riattivare",
            delta_color="inverse",
            help="Clienti con abbonamento scaduto"
        )

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
    
    # Progress bar
    progress = min(success_rate / 100, 1.0)
    st.progress(progress, text=f"Progresso generazione: {success_rate}%")
    
    # Alert
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
            help="Abbonamenti che scadono oggi - richiedono azione immediata"
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
    
    # Tabella dettaglio
    if stats['dettagli']:
        st.markdown("#### 📋 Dettaglio Scadenze Imminenti")
        
        df = pd.DataFrame(stats['dettagli'])
        
        # Prepara dataframe per visualizzazione
        df_display = df[['name', 'numero', 'end_date', 'tipo_subscription', 'giorni_rimasti']].copy()
        df_display.columns = ['Nome', 'Telefono', 'Data Scadenza', 'Piano', 'Giorni Rimasti']
        
        # Ordina per urgenza
        df_display = df_display.sort_values('Giorni Rimasti')
        
        # Colora le righe in base all'urgenza
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
        
        # Grafico distribuzione
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

def render_footer():
    """Renderizza il footer"""
    st.markdown("---")
    st.caption("💡 **Nota**: I dati vengono aggiornati automaticamente ogni 60 secondi. Usa il pulsante 'Aggiorna Dati' per forzare il refresh immediato.")
    st.caption("🔒 Connesso a Supabase | 🌙 Sistema Oroscopi WhatsApp v1.0")

# ==================== MAIN ====================

def main():
    """Funzione principale dell'applicazione"""
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150x150.png?text=🌙", width=150)
        st.title("Menu")
        st.markdown("---")
        
        page = st.radio(
            "Navigazione",
            ["🏠 Dashboard", "ℹ️ Info Sistema"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### ⚙️ Impostazioni")
        st.caption("Cache automatica: 60s")
        
        if st.button("🗑️ Pulisci Cache", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache pulita!")
    
    # Routing delle pagine
    if page == "🏠 Dashboard":
        render_header()
        
        render_customer_stats()
        st.markdown("---")
        
        render_horoscope_stats()
        st.markdown("---")
        
        render_expiring_subscriptions()
        
        render_footer()
    
    elif page == "ℹ️ Info Sistema":
        st.title("ℹ️ Informazioni Sistema")
        st.markdown("---")
        
        st.markdown("""
        ### 🌙 Sistema Oroscopi WhatsApp
        
        **Versione**: 1.0 Beta  
        **Database**: Supabase (PostgreSQL)  
        **Orchestrazione**: n8n  
        
        #### 📊 Funzionalità Dashboard
        
        - **Statistiche Clienti**: Monitoraggio clienti totali, attivi, trial e scaduti
        - **Oroscopi Giornalieri**: Tracciamento generazione e invio oroscopi
        - **Gestione Scadenze**: Alert su abbonamenti in scadenza
        
        #### 🔄 Aggiornamenti Dati
        
        - **Cache**: 60 secondi
        - **Refresh Manuale**: Disponibile via pulsante
        
        #### 📞 Supporto
        
        Per assistenza tecnica, contattare l'amministratore di sistema.
        """)

if __name__ == "__main__":
    main()