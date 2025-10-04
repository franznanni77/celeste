"""
Pagina Statistiche e Analytics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from utils.database import (
    get_stats_registrations,
    get_stats_payments,
    get_stats_expired_not_renewed,
    get_mrr,
    get_arr,
    get_revenue_by_period,
    get_arpu,
    get_revenue_projection,
    get_stats_summary
)
from utils.helpers import go_back_to_dashboard

def render():
    """Renderizza la pagina statistiche"""
    
    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("📊 Statistiche e Analytics")
        st.caption(f"Dati aggiornati al {datetime.now().strftime('%d/%m/%Y alle %H:%M')}")
    
    with col2:
        if st.button("⬅️ Torna alla Dashboard", use_container_width=True, type="secondary"):
            go_back_to_dashboard()
    
    st.markdown("---")
    
    # Carica tutte le statistiche
    with st.spinner("Caricamento statistiche..."):
        stats = get_stats_summary()
    
    # Sezione 1: KPI Principali
    render_main_kpis(stats)
    
    st.markdown("---")
    
    # Sezione 2: Selettore Periodo + Metriche Clienti
    render_customer_metrics(stats)
    
    st.markdown("---")
    
    # Sezione 3: Metriche Revenue
    render_revenue_metrics(stats)
    
    st.markdown("---")
    
    # Footer azioni
    render_footer()

def render_main_kpis(stats):
    """Renderizza i KPI principali in cards"""
    st.subheader("🎯 KPI Principali")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 MRR (Monthly Recurring Revenue)",
            value=f"€ {stats.get('mrr', 0):,.2f}",
            help="Revenue mensile ricorrente - tutti gli abbonamenti attivi normalizzati a 30 giorni"
        )
    
    with col2:
        st.metric(
            label="📈 ARR (Annual Recurring Revenue)",
            value=f"€ {stats.get('arr', 0):,.2f}",
            delta="MRR × 12",
            help="Revenue annuale proiettata"
        )
    
    with col3:
        st.metric(
            label="👤 ARPU (Avg Revenue Per User)",
            value=f"€ {stats.get('arpu', 0):,.2f}",
            help="Revenue medio per utente attivo al mese"
        )
    
    with col4:
        projection = stats.get('revenue_projection', 0)
        st.metric(
            label="🔮 Proiezione Revenue Mensile",
            value=f"€ {projection:,.2f}",
            help="Basata su trend ultimi 7 giorni × 30"
        )

def render_customer_metrics(stats):
    """Renderizza le metriche clienti con selettore periodo"""
    st.subheader("👥 Metriche Clienti")
    
    # Selettore periodo
    col1, col2, col3 = st.columns(3)
    
    with col1:
        show_today = st.checkbox("📅 Oggi", value=True)
    with col2:
        show_week = st.checkbox("📅 Settimana (7gg)", value=True)
    with col3:
        show_month = st.checkbox("📅 Mese (30gg)", value=True)
    
    st.markdown("---")
    
    # Tabella comparativa
    data = []
    
    if show_today:
        data.append({
            'Periodo': '📅 Oggi',
            'Nuovi Iscritti': stats.get('registrations_today', 0),
            'Hanno Pagato': stats.get('payments_today', 0),
            'Scaduti Non Rinnovati': stats.get('expired_today', 0)
        })
    
    if show_week:
        data.append({
            'Periodo': '📅 Ultimi 7 giorni',
            'Nuovi Iscritti': stats.get('registrations_week', 0),
            'Hanno Pagato': stats.get('payments_week', 0),
            'Scaduti Non Rinnovati': stats.get('expired_week', 0)
        })
    
    if show_month:
        data.append({
            'Periodo': '📅 Ultimi 30 giorni',
            'Nuovi Iscritti': stats.get('registrations_month', 0),
            'Hanno Pagato': stats.get('payments_month', 0),
            'Scaduti Non Rinnovati': stats.get('expired_month', 0)
        })
    
    if data:
        df = pd.DataFrame(data)
        
        # Mostra tabella
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Nuovi Iscritti": st.column_config.NumberColumn(
                    "✅ Nuovi Iscritti",
                    help="Clienti registrati nel periodo",
                    format="%d"
                ),
                "Hanno Pagato": st.column_config.NumberColumn(
                    "💳 Hanno Pagato",
                    help="Clienti che hanno attivato abbonamento pagante",
                    format="%d"
                ),
                "Scaduti Non Rinnovati": st.column_config.NumberColumn(
                    "⏸️ Scaduti Non Rinnovati",
                    help="Clienti scaduti che non hanno rinnovato",
                    format="%d"
                )
            }
        )
        
        # Grafici
        if st.checkbox("📊 Mostra Grafici Comparativi", value=False):
            render_customer_charts(df)

def render_customer_charts(df):
    """Renderizza grafici per metriche clienti"""
    st.markdown("#### 📊 Visualizzazione Grafica")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Grafico a barre - Nuovi Iscritti
        fig1 = px.bar(
            df,
            x='Periodo',
            y='Nuovi Iscritti',
            title='Nuovi Iscritti per Periodo',
            labels={'Nuovi Iscritti': 'Numero Clienti'},
            color='Nuovi Iscritti',
            color_continuous_scale='Blues'
        )
        fig1.update_layout(showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Grafico a barre - Hanno Pagato
        fig2 = px.bar(
            df,
            x='Periodo',
            y='Hanno Pagato',
            title='Clienti che Hanno Pagato',
            labels={'Hanno Pagato': 'Numero Pagamenti'},
            color='Hanno Pagato',
            color_continuous_scale='Greens'
        )
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Grafico a barre - Scaduti Non Rinnovati
    fig3 = px.bar(
        df,
        x='Periodo',
        y='Scaduti Non Rinnovati',
        title='Clienti Scaduti Non Rinnovati',
        labels={'Scaduti Non Rinnovati': 'Numero Clienti'},
        color='Scaduti Non Rinnovati',
        color_continuous_scale='Reds'
    )
    fig3.update_layout(showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)

def render_revenue_metrics(stats):
    """Renderizza le metriche revenue"""
    st.subheader("💰 Metriche Revenue")
    
    # Tabella revenue per periodo
    revenue_data = [
        {
            'Periodo': '📅 Oggi',
            'Revenue': f"€ {stats.get('revenue_today', 0):,.2f}",
            'Numero Pagamenti': stats.get('payments_today', 0)
        },
        {
            'Periodo': '📅 Ultimi 7 giorni',
            'Revenue': f"€ {stats.get('revenue_week', 0):,.2f}",
            'Numero Pagamenti': stats.get('payments_week', 0)
        },
        {
            'Periodo': '📅 Ultimi 30 giorni',
            'Revenue': f"€ {stats.get('revenue_month', 0):,.2f}",
            'Numero Pagamenti': stats.get('payments_month', 0)
        }
    ]
    
    df_revenue = pd.DataFrame(revenue_data)
    
    st.dataframe(
        df_revenue,
        use_container_width=True,
        hide_index=True
    )
    
    # Info box con calcoli
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"""
        **💡 Info MRR/ARR**
        
        - **MRR**: € {stats.get('mrr', 0):,.2f} (revenue mensile ricorrente)
        - **ARR**: € {stats.get('arr', 0):,.2f} (MRR × 12)
        - **ARPU**: € {stats.get('arpu', 0):,.2f} (revenue medio per utente)
        
        Il MRR è calcolato normalizzando tutti gli abbonamenti attivi a 30 giorni.
        """)
    
    with col2:
        projection = stats.get('revenue_projection', 0)
        revenue_month = stats.get('revenue_month', 0)
        
        if revenue_month > 0:
            trend = ((projection - revenue_month) / revenue_month) * 100
            trend_text = f"+{trend:.1f}%" if trend > 0 else f"{trend:.1f}%"
            trend_emoji = "📈" if trend > 0 else "📉" if trend < 0 else "➡️"
        else:
            trend_text = "N/A"
            trend_emoji = "➡️"
        
        st.success(f"""
        **🔮 Proiezione Mensile**
        
        - **Proiezione**: € {projection:,.2f}
        - **Ultimo mese**: € {revenue_month:,.2f}
        - **Trend**: {trend_emoji} {trend_text}
        
        Basata sulla media giornaliera degli ultimi 7 giorni × 30.
        """)
    
    # Grafico revenue
    if st.checkbox("📊 Mostra Grafico Revenue", value=False):
        render_revenue_chart(stats)

def render_revenue_chart(stats):
    """Renderizza grafico revenue"""
    st.markdown("#### 💰 Revenue per Periodo")
    
    revenue_values = [
        stats.get('revenue_today', 0),
        stats.get('revenue_week', 0),
        stats.get('revenue_month', 0)
    ]
    
    periods = ['Oggi', 'Settimana', 'Mese']
    
    fig = go.Figure(data=[
        go.Bar(
            x=periods,
            y=revenue_values,
            text=[f"€ {v:,.2f}" for v in revenue_values],
            textposition='auto',
            marker_color=['#1f77b4', '#2ca02c', '#ff7f0e']
        )
    ])
    
    fig.update_layout(
        title='Revenue Totale per Periodo',
        xaxis_title='Periodo',
        yaxis_title='Revenue (€)',
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_footer():
    """Renderizza footer con azioni"""
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Aggiorna Statistiche", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    with col2:
        if st.button("📥 Esporta Report (Coming Soon)", use_container_width=True, disabled=True):
            st.info("🚧 Funzionalità in sviluppo")
    
    st.caption("💡 Le statistiche vengono aggiornate automaticamente ogni 5 minuti.")