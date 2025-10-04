"""
Pagina Dashboard Principale
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.database import (
    get_customer_stats,
    get_horoscopes_today,
    get_expiring_subscriptions
)
from utils.helpers import navigate_to

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
    
    col1, col2, col3, col4 = st.columns(4)
    
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
    
    with col4:
        # Pulsante per visualizzare tutti gli oroscopi
        st.metric(
            label="📋 Archivio",
            value="Vedi tutti",
            help="Visualizza tutti gli oroscopi generati"
        )
        if st.button("🔍 Visualizza", key="btn_horoscopes", use_container_width=True):
            navigate_to('horoscopes')
    
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
    
    # Tabella dettaglio
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

def render():
    """Funzione principale per renderizzare la dashboard"""
    render_header()
    render_customer_stats()
    st.markdown("---")
    render_horoscope_stats()
    st.markdown("---")
    render_expiring_subscriptions()