"""
Pagina Dettaglio Clienti
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.database import get_filtered_customers
from utils.helpers import go_back_to_dashboard

def render(filter_type):
    """
    Renderizza la pagina di dettaglio clienti
    Args:
        filter_type: str - tipo di filtro (totale, attivi, trial, scaduti)
    """
    
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
            st.session_state.show_stats = not st.session_state.get('show_stats', False)
    
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