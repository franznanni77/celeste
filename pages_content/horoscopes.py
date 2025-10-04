"""
Pagina Visualizzazione Oroscopi
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from utils.database import get_all_horoscopes, get_horoscopes_by_date
from utils.helpers import go_back_to_dashboard

def render():
    """Renderizza la pagina degli oroscopi"""
    
    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("📜 Archivio Oroscopi Generati")
    
    with col2:
        if st.button("⬅️ Torna alla Dashboard", use_container_width=True, type="secondary"):
            go_back_to_dashboard()
    
    st.markdown("---")
    
    # Filtri superiori
    st.subheader("🔍 Filtri")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Selezione periodo
        period_options = {
            "Oggi": 0,
            "Ultimi 3 giorni": 3,
            "Ultimi 7 giorni": 7,
            "Ultimi 14 giorni": 14,
            "Ultimi 30 giorni": 30
        }
        selected_period = st.selectbox("📅 Periodo", list(period_options.keys()))
        days = period_options[selected_period]
    
    with col2:
        # Data specifica
        specific_date = st.date_input(
            "📆 Oppure seleziona una data specifica",
            value=datetime.now().date(),
            max_value=datetime.now().date()
        )
        use_specific_date = st.checkbox("Usa data specifica")
    
    with col3:
        # Filtro per segno zodiacale
        all_signs = ["Tutti", "Ariete", "Toro", "Gemelli", "Cancro", "Leone", "Vergine",
                     "Bilancia", "Scorpione", "Sagittario", "Capricorno", "Acquario", "Pesci"]
        selected_sign = st.selectbox("♈ Filtra per Segno", all_signs)
    
    st.markdown("---")
    
    # Carica dati
    with st.spinner("Caricamento oroscopi..."):
        if use_specific_date:
            df = get_horoscopes_by_date(specific_date.isoformat())
        else:
            df = get_all_horoscopes(days=days)
    
    # Verifica se ci sono dati
    if df.empty:
        st.warning("📭 Nessun oroscopo trovato per i criteri selezionati")
        return
    
    # Applica filtro per segno
    if selected_sign != "Tutti":
        df = df[df['segno'] == selected_sign]
    
    if df.empty:
        st.warning(f"📭 Nessun oroscopo trovato per il segno {selected_sign}")
        return
    
    # Statistiche riepilogo
    st.subheader("📊 Statistiche")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📝 Totale Oroscopi", len(df))
    
    with col2:
        unique_dates = df['data_oroscopo'].nunique()
        st.metric("📅 Giorni Coperti", unique_dates)
    
    with col3:
        unique_signs = df['segno'].nunique()
        st.metric("♈ Segni Unici", unique_signs)
    
    with col4:
        unique_ascendants = df['ascendente'].nunique()
        st.metric("🌟 Ascendenti Unici", unique_ascendants)
    
    st.markdown("---")
    
    # Opzioni visualizzazione
    view_mode = st.radio(
        "📋 Modalità Visualizzazione",
        ["Tabella Completa", "Vista per Data", "Vista per Segno"],
        horizontal=True
    )
    
    st.markdown("---")
    
    # Rendering basato sulla modalità
    if view_mode == "Tabella Completa":
        render_table_view(df)
    
    elif view_mode == "Vista per Data":
        render_date_view(df)
    
    elif view_mode == "Vista per Segno":
        render_sign_view(df)
    
    # Footer con azioni
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Esporta in CSV", use_container_width=True):
            csv = df.to_csv(index=False)
            st.download_button(
                label="⬇️ Scarica CSV",
                data=csv,
                file_name=f"oroscopi_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        if st.button("📊 Mostra Grafici", use_container_width=True):
            st.session_state.show_charts = not st.session_state.get('show_charts', False)
    
    with col3:
        if st.button("🔄 Aggiorna Dati", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Grafici statistici (opzionale)
    if st.session_state.get('show_charts', False):
        render_charts(df)

def render_table_view(df):
    """Renderizza la vista tabella completa"""
    st.subheader("📋 Tabella Completa Oroscopi")
    
    # Filtri aggiuntivi
    col1, col2 = st.columns(2)
    with col1:
        search_text = st.text_input("🔎 Cerca nel testo dell'oroscopo", placeholder="Inserisci parole chiave...")
    with col2:
        ascendants = ["Tutti"] + sorted(df['ascendente'].dropna().unique().tolist())
        selected_ascendant = st.selectbox("🌟 Filtra per Ascendente", ascendants)
    
    # Applica filtri
    df_filtered = df.copy()
    if search_text:
        df_filtered = df_filtered[df_filtered['oroscopo_generale'].str.contains(search_text, case=False, na=False)]
    if selected_ascendant != "Tutti":
        df_filtered = df_filtered[df_filtered['ascendente'] == selected_ascendant]
    
    st.info(f"📊 Visualizzati **{len(df_filtered)}** oroscopi su **{len(df)}** totali")
    
    # Prepara dataframe per visualizzazione
    df_display = df_filtered[['data_oroscopo', 'segno', 'ascendente', 'oroscopo_generale']].copy()
    df_display.columns = ['Data', 'Segno', 'Ascendente', 'Oroscopo']
    
    # Formatta data
    df_display['Data'] = pd.to_datetime(df_display['Data']).dt.strftime('%d/%m/%Y')
    
    # Ordina per data decrescente
    df_display = df_display.sort_values('Data', ascending=False)
    
    # Mostra tabella
    st.dataframe(
        df_display,
        use_container_width=True,
        height=600,
        hide_index=True,
        column_config={
            "Oroscopo": st.column_config.TextColumn(
                "Oroscopo",
                help="Testo completo dell'oroscopo",
                width="large"
            )
        }
    )

def render_date_view(df):
    """Renderizza la vista raggruppata per data"""
    st.subheader("📅 Oroscopi Raggruppati per Data")
    
    # Raggruppa per data
    dates = sorted(df['data_oroscopo'].unique(), reverse=True)
    
    for date in dates:
        df_date = df[df['data_oroscopo'] == date]
        
        # Formatta data per titolo
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        date_formatted = date_obj.strftime('%d/%m/%Y')
        day_name = date_obj.strftime('%A')
        
        # Traduzione giorni
        day_translation = {
            'Monday': 'Lunedì', 'Tuesday': 'Martedì', 'Wednesday': 'Mercoledì',
            'Thursday': 'Giovedì', 'Friday': 'Venerdì', 'Saturday': 'Sabato', 'Sunday': 'Domenica'
        }
        day_it = day_translation.get(day_name, day_name)
        
        with st.expander(f"📆 {day_it} {date_formatted} - {len(df_date)} oroscopi", expanded=(date == dates[0])):
            for _, row in df_date.iterrows():
                st.markdown(f"**♈ {row['segno']} - Ascendente {row['ascendente']}**")
                st.write(row['oroscopo_generale'])
                st.markdown("---")

def render_sign_view(df):
    """Renderizza la vista raggruppata per segno zodiacale"""
    st.subheader("♈ Oroscopi Raggruppati per Segno")
    
    # Raggruppa per segno
    signs = sorted(df['segno'].unique())
    
    for sign in signs:
        df_sign = df[df['segno'] == sign]
        
        with st.expander(f"♈ {sign} - {len(df_sign)} oroscopi"):
            # Mostra gli ultimi 3 oroscopi per questo segno
            df_sign_sorted = df_sign.sort_values('data_oroscopo', ascending=False).head(3)
            
            for _, row in df_sign_sorted.iterrows():
                date_formatted = datetime.strptime(row['data_oroscopo'], '%Y-%m-%d').strftime('%d/%m/%Y')
                st.markdown(f"**📅 {date_formatted} - Ascendente {row['ascendente']}**")
                st.write(row['oroscopo_generale'])
                st.markdown("---")

def render_charts(df):
    """Renderizza grafici statistici"""
    st.markdown("---")
    st.subheader("📊 Analisi Grafiche")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribuzione per segno
        st.markdown("#### Distribuzione per Segno Zodiacale")
        sign_counts = df['segno'].value_counts()
        fig = px.bar(
            x=sign_counts.index,
            y=sign_counts.values,
            title='Numero di Oroscopi per Segno',
            labels={'x': 'Segno', 'y': 'Numero Oroscopi'},
            color=sign_counts.values,
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Distribuzione temporale
        st.markdown("#### Distribuzione Temporale")
        date_counts = df.groupby('data_oroscopo').size().reset_index(name='count')
        date_counts['data_oroscopo'] = pd.to_datetime(date_counts['data_oroscopo'])
        
        fig = px.line(
            date_counts,
            x='data_oroscopo',
            y='count',
            title='Oroscopi Generati per Data',
            labels={'data_oroscopo': 'Data', 'count': 'Numero Oroscopi'},
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Heatmap combinazioni segno/ascendente
    st.markdown("#### Heatmap Combinazioni Segno/Ascendente")
    pivot = df.pivot_table(
        index='segno',
        columns='ascendente',
        values='id',
        aggfunc='count',
        fill_value=0
    )
    
    fig = px.imshow(
        pivot,
        labels=dict(x="Ascendente", y="Segno", color="Numero Oroscopi"),
        title='Combinazioni Segno/Ascendente Generate',
        color_continuous_scale='Viridis'
    )
    st.plotly_chart(fig, use_container_width=True)