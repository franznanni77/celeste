"""
Pagina Dettaglio Clienti con filtri avanzati
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.database import get_filtered_customers
from utils.helpers import go_back_to_dashboard, navigate_to

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
    render_summary_stats(df, filter_type)
    
    st.markdown("---")
    
    # Filtri avanzati
    df_filtered = render_advanced_filters(df, filter_type)
    
    st.markdown("---")
    
    # Tabella principale con azioni
    render_customer_table(df_filtered, filter_type)
    
    # Footer con azioni
    render_actions_footer(df_filtered, filter_type)

def render_summary_stats(df, filter_type):
    """Renderizza le statistiche di riepilogo"""
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

def render_advanced_filters(df, filter_type):
    """Renderizza i filtri avanzati"""
    st.subheader("🔍 Filtri e Ricerca")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search_name = st.text_input("🔎 Cerca per nome", placeholder="Nome cliente...")
    
    with col2:
        search_phone = st.text_input("📱 Cerca per telefono", placeholder="Numero telefono...")
    
    with col3:
        signs = ['Tutti'] + sorted(df['segno'].dropna().unique().tolist())
        selected_sign = st.selectbox("♈ Segno Zodiacale", signs)
    
    with col4:
        ascendants = ['Tutti'] + sorted(df['ascendente'].dropna().unique().tolist())
        selected_ascendant = st.selectbox("🌟 Ascendente", ascendants)
    
    # Riga 2 di filtri
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'tipo_abbonamento' in df.columns:
            plans = ['Tutti'] + sorted(df['tipo_abbonamento'].dropna().unique().tolist())
            selected_plan = st.selectbox("💳 Piano Abbonamento", plans)
        else:
            selected_plan = 'Tutti'
    
    with col2:
        if 'stato_abbonamento' in df.columns:
            statuses = ['Tutti'] + sorted(df['stato_abbonamento'].dropna().unique().tolist())
            selected_status = st.selectbox("📊 Stato", statuses)
        else:
            selected_status = 'Tutti'
    
    with col3:
        # Filtro per data registrazione
        date_options = ['Tutti', 'Ultima settimana', 'Ultimo mese', 'Ultimo anno']
        selected_date_range = st.selectbox("📅 Registrati", date_options)
    
    with col4:
        # Filtro per giorni rimanenti (solo per attivi/trial)
        if 'giorni_rimanenti' in df.columns:
            days_options = ['Tutti', '<7 giorni', '<14 giorni', '<30 giorni', '>30 giorni']
            selected_days = st.selectbox("⏰ Giorni Rimanenti", days_options)
        else:
            selected_days = 'Tutti'
    
    # Applica filtri
    df_filtered = df.copy()
    
    if search_name:
        df_filtered = df_filtered[df_filtered['nome'].str.contains(search_name, case=False, na=False)]
    
    if search_phone:
        df_filtered = df_filtered[df_filtered['telefono'].str.contains(search_phone, case=False, na=False)]
    
    if selected_sign != 'Tutti':
        df_filtered = df_filtered[df_filtered['segno'] == selected_sign]
    
    if selected_ascendant != 'Tutti':
        df_filtered = df_filtered[df_filtered['ascendente'] == selected_ascendant]
    
    if selected_plan != 'Tutti':
        df_filtered = df_filtered[df_filtered['tipo_abbonamento'] == selected_plan]
    
    if selected_status != 'Tutti':
        df_filtered = df_filtered[df_filtered['stato_abbonamento'] == selected_status]
    
    # Filtro data registrazione
    if selected_date_range != 'Tutti':
        today = datetime.now().date()
        if selected_date_range == 'Ultima settimana':
            cutoff = today - pd.Timedelta(days=7)
        elif selected_date_range == 'Ultimo mese':
            cutoff = today - pd.Timedelta(days=30)
        else:  # Ultimo anno
            cutoff = today - pd.Timedelta(days=365)
        
        df_filtered['data_reg_dt'] = pd.to_datetime(df_filtered['data_registrazione'])
        df_filtered = df_filtered[df_filtered['data_reg_dt'].dt.date >= cutoff]
        df_filtered = df_filtered.drop('data_reg_dt', axis=1)
    
    # Filtro giorni rimanenti
    if 'giorni_rimanenti' in df_filtered.columns and selected_days != 'Tutti':
        if selected_days == '<7 giorni':
            df_filtered = df_filtered[df_filtered['giorni_rimanenti'] < 7]
        elif selected_days == '<14 giorni':
            df_filtered = df_filtered[df_filtered['giorni_rimanenti'] < 14]
        elif selected_days == '<30 giorni':
            df_filtered = df_filtered[df_filtered['giorni_rimanenti'] < 30]
        else:  # >30 giorni
            df_filtered = df_filtered[df_filtered['giorni_rimanenti'] >= 30]
    
    st.info(f"📊 Visualizzati **{len(df_filtered)}** clienti su **{len(df)}** totali")
    
    return df_filtered

def render_customer_table(df, filter_type):
    """Renderizza la tabella clienti con pulsante dettaglio"""
    st.subheader("📋 Elenco Clienti")
    
    # Prepara colonne
    if filter_type in ['attivi', 'trial']:
        columns_to_show = ['nome', 'telefono', 'segno', 'ascendente', 'tipo_abbonamento', 
                          'data_scadenza', 'giorni_rimanenti']
        column_names = ['Nome', 'Telefono', 'Segno', 'Ascendente', 'Piano', 'Scadenza', 'Giorni Rimasti']
    elif filter_type == 'scaduti':
        columns_to_show = ['nome', 'telefono', 'segno', 'ascendente', 'tipo_abbonamento', 'data_scadenza']
        column_names = ['Nome', 'Telefono', 'Segno', 'Ascendente', 'Piano', 'Data Scadenza']
    else:  # totale
        columns_to_show = ['nome', 'telefono', 'segno', 'ascendente', 'stato_abbonamento', 'data_registrazione']
        column_names = ['Nome', 'Telefono', 'Segno', 'Ascendente', 'Stato', 'Registrato il']
    
    # Crea dataframe per visualizzazione
    df_display = df[['id'] + columns_to_show].copy()
    
    # Formatta date
    for col in columns_to_show:
        if 'data' in col.lower() or 'scadenza' in col.lower():
            df_display[col] = pd.to_datetime(df_display[col], errors='coerce').dt.strftime('%d/%m/%Y')
            df_display[col] = df_display[col].fillna('N/A')
    
    # Mostra intestazioni tabella
    header_cols = st.columns(len(column_names) + 1)
    for i, col_name in enumerate(column_names):
        with header_cols[i]:
            st.markdown(f"**{col_name}**")
    with header_cols[-1]:
        st.markdown("**Azioni**")
    
    st.markdown("---")
    
    # Mostra righe (max 50 per performance)
    display_limit = 50
    total_rows = len(df_display)
    
    if total_rows > display_limit:
        st.warning(f"⚠️ Visualizzate prime {display_limit} righe su {total_rows}. Usa i filtri per restringere la ricerca.")
        df_to_show = df_display.head(display_limit)
    else:
        df_to_show = df_display
    
    # Mostra righe con pulsanti
    for idx, row in df_to_show.iterrows():
        cols = st.columns(len(column_names) + 1)
        
        # Mostra i dati
        for i, col_name in enumerate(columns_to_show):
            with cols[i]:
                value = str(row[col_name])
                # Tronca valori lunghi
                if len(value) > 20:
                    value = value[:17] + "..."
                st.text(value)
        
        # Pulsante azioni
        with cols[-1]:
            if st.button("👁️", key=f"view_{row['id']}", help="Visualizza dettaglio", use_container_width=True):
                navigate_to('customer_detail', row['id'])
        
        # Linea separatrice leggera
        st.markdown('<hr style="margin: 5px 0; opacity: 0.3;">', unsafe_allow_html=True)

def render_actions_footer(df, filter_type):
    """Renderizza le azioni disponibili"""
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Esporta CSV",
            data=csv,
            file_name=f"clienti_{filter_type}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        if st.button("📊 Mostra Statistiche", use_container_width=True):
            st.session_state.show_customer_stats = not st.session_state.get('show_customer_stats', False)
    
    with col3:
        if st.button("🔄 Aggiorna Dati", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Statistiche dettagliate
    if st.session_state.get('show_customer_stats', False):
        render_detailed_stats(df)

def render_detailed_stats(df):
    """Renderizza statistiche dettagliate"""
    st.markdown("---")
    st.subheader("📈 Statistiche Dettagliate")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if 'segno' in df.columns:
            st.markdown("#### Distribuzione per Segno Zodiacale")
            sign_counts = df['segno'].value_counts()
            fig = px.pie(
                values=sign_counts.values,
                names=sign_counts.index,
                title='Distribuzione Segni Zodiacali'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'tipo_abbonamento' in df.columns:
            st.markdown("#### Distribuzione per Piano")
            plan_counts = df['tipo_abbonamento'].value_counts()
            fig = px.bar(
                x=plan_counts.index,
                y=plan_counts.values,
                title='Distribuzione Piani di Abbonamento',
                labels={'x': 'Piano', 'y': 'Numero Clienti'}
            )
            st.plotly_chart(fig, use_container_width=True)