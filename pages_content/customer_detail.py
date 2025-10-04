"""
Pagina Dettaglio Singolo Cliente
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from utils.database import (
    get_customer_by_id,
    get_customer_subscriptions_history,
    get_customer_horoscopes_history,
    get_customer_timeline,
    update_customer,
    cancel_subscription,
    create_manual_subscription,
    get_available_service_plans
)
from utils.helpers import navigate_to

def render(customer_id):
    """
    Renderizza la pagina di dettaglio cliente
    Args:
        customer_id: str - UUID del cliente
    """
    
    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("👤 Dettaglio Cliente")
    
    with col2:
        if st.button("⬅️ Torna ai Clienti", use_container_width=True, type="secondary"):
            navigate_to('customers', 'totale')
    
    st.markdown("---")
    
    # Carica dati cliente
    with st.spinner("Caricamento dati cliente..."):
        customer = get_customer_by_id(customer_id)
    
    if not customer:
        st.error("❌ Cliente non trovato")
        return
    
    # Tab per organizzare le informazioni
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Informazioni", 
        "💳 Abbonamenti", 
        "📜 Oroscopi", 
        "📅 Timeline", 
        "⚙️ Azioni"
    ])
    
    with tab1:
        render_customer_info(customer)
    
    with tab2:
        render_subscriptions_history(customer_id)
    
    with tab3:
        render_horoscopes_history(customer_id, customer)
    
    with tab4:
        render_timeline(customer_id)
    
    with tab5:
        render_actions(customer, customer_id)

def render_customer_info(customer):
    """Renderizza le informazioni del cliente"""
    st.subheader("📋 Dati Anagrafici")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Informazioni Personali")
        st.text_input("Nome", value=customer.get('name', 'N/A'), disabled=True, key="view_name")
        st.text_input("Telefono", value=customer.get('phone_number', 'N/A'), disabled=True, key="view_phone")
        st.text_input("Data di Nascita", value=customer.get('birth_date', 'N/A'), disabled=True, key="view_birth")
        st.text_input("Luogo di Nascita", value=customer.get('birth_place', 'N/A'), disabled=True, key="view_place")
        st.text_input("Genere", value=customer.get('gender', 'N/A'), disabled=True, key="view_gender")
    
    with col2:
        st.markdown("##### Dati Astrologici")
        st.text_input("Segno Zodiacale", value=customer.get('zodiac_sign', 'N/A'), disabled=True, key="view_sign")
        st.text_input("Ascendente", value=customer.get('ascendant', 'N/A'), disabled=True, key="view_asc")
        st.text_input("Gruppo Energia", value=customer.get('gruppo_energia', 'N/A'), disabled=True, key="view_energy")
        st.text_input("Fase Lunare", value=customer.get('fase_lunare', 'N/A'), disabled=True, key="view_moon")
        
        pianeti = customer.get('pianeti_rilevanti', [])
        if pianeti and isinstance(pianeti, list):
            st.text_area("Pianeti Rilevanti", value=", ".join(pianeti), disabled=True, key="view_planets", height=100)
        else:
            st.text_input("Pianeti Rilevanti", value="N/A", disabled=True, key="view_planets")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        created = customer.get('created_at', 'N/A')
        if created != 'N/A':
            created = pd.to_datetime(created).strftime('%d/%m/%Y %H:%M')
        st.metric("📅 Data Registrazione", created)
    
    with col2:
        updated = customer.get('updated_at', 'N/A')
        if updated != 'N/A':
            updated = pd.to_datetime(updated).strftime('%d/%m/%Y %H:%M')
        st.metric("🔄 Ultimo Aggiornamento", updated)

def render_subscriptions_history(customer_id):
    """Renderizza lo storico abbonamenti"""
    st.subheader("💳 Storico Abbonamenti")
    
    with st.spinner("Caricamento abbonamenti..."):
        df_subs = get_customer_subscriptions_history(customer_id)
    
    if df_subs.empty:
        st.info("📭 Nessun abbonamento trovato")
        return
    
    # Evidenzia abbonamento attivo
    for idx, row in df_subs.iterrows():
        is_active = row['is_active']
        
        with st.expander(
            f"{'🟢 ATTIVO' if is_active else '⚪'} {row['piano']} - Dal {row['data_inizio']} al {row['data_fine']}",
            expanded=is_active
        ):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Piano", row['piano'])
                st.metric("Tipo", "Trial Gratuito" if row['is_trial'] else "Abbonamento Pagante")
            
            with col2:
                st.metric("Stato", row['stato'].upper())
                st.metric("Pagamento", row['payment_status'].upper())
            
            with col3:
                st.metric("Durata", f"{row['durata_giorni']} giorni")
                if not row['is_trial']:
                    st.metric("Prezzo", f"€ {row['prezzo']:.2f}")
            
            if row['payment_reference'] and row['payment_reference'] != 'N/A':
                st.text_input("Riferimento Pagamento", value=row['payment_reference'], disabled=True, key=f"pay_ref_{idx}")
            
            if row['notes']:
                st.text_area("Note", value=row['notes'], disabled=True, key=f"notes_{idx}")
            
            # Pulsante cancella (solo se attivo)
            if is_active:
                st.markdown("---")
                if st.button(f"🗑️ Cancella Abbonamento", key=f"cancel_{row['id']}", type="secondary"):
                    st.session_state[f'confirm_cancel_{row["id"]}'] = True
                
                if st.session_state.get(f'confirm_cancel_{row["id"]}', False):
                    st.warning("⚠️ Sei sicuro di voler cancellare questo abbonamento?")
                    reason = st.text_input("Motivo cancellazione", key=f"reason_{row['id']}")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✅ Conferma", key=f"confirm_yes_{row['id']}"):
                            if cancel_subscription(row['id'], reason):
                                st.success("Abbonamento cancellato con successo!")
                                st.cache_data.clear()
                                st.rerun()
                    with col_b:
                        if st.button("❌ Annulla", key=f"confirm_no_{row['id']}"):
                            st.session_state[f'confirm_cancel_{row["id"]}'] = False
                            st.rerun()

def render_horoscopes_history(customer_id, customer):
    """Renderizza lo storico oroscopi"""
    st.subheader("📜 Oroscopi Ricevuti (Ultimi 30 giorni)")
    
    with st.spinner("Caricamento oroscopi..."):
        df_horoscopes = get_customer_horoscopes_history(customer_id, days=30)
    
    if df_horoscopes.empty:
        st.info("📭 Nessun oroscopo trovato per questo cliente")
        st.caption(f"Combinazione: {customer.get('zodiac_sign', 'N/A')} + Ascendente {customer.get('ascendant', 'N/A')}")
        return
    
    st.info(f"✅ Trovati **{len(df_horoscopes)}** oroscopi per la combinazione **{customer.get('zodiac_sign')} + Ascendente {customer.get('ascendant')}**")
    
    # Mostra oroscopi
    for idx, row in df_horoscopes.iterrows():
        date_formatted = pd.to_datetime(row['data_oroscopo']).strftime('%d/%m/%Y')
        
        with st.expander(f"📅 {date_formatted}", expanded=(idx == 0)):
            st.markdown(f"**Segno:** {row['segno']} | **Ascendente:** {row['ascendente']}")
            st.markdown("---")
            st.write(row['oroscopo_generale'])

def render_timeline(customer_id):
    """Renderizza la timeline eventi"""
    st.subheader("📅 Timeline Eventi")
    
    with st.spinner("Caricamento timeline..."):
        timeline = get_customer_timeline(customer_id)
    
    if not timeline:
        st.info("📭 Nessun evento trovato")
        return
    
    # Mostra timeline
    for event in timeline:
        date_formatted = pd.to_datetime(event['data']).strftime('%d/%m/%Y %H:%M')
        
        col1, col2 = st.columns([1, 5])
        
        with col1:
            st.markdown(f"### {event['icona']}")
            st.caption(date_formatted)
        
        with col2:
            st.markdown(f"**{event['descrizione']}**")
            st.caption(event['dettagli'])
        
        st.markdown("---")

def render_actions(customer, customer_id):
    """Renderizza le azioni disponibili"""
    st.subheader("⚙️ Azioni Disponibili")
    
    # Modifica dati anagrafici
    with st.expander("✏️ Modifica Dati Anagrafici"):
        render_edit_customer(customer, customer_id)
    
    # Crea nuovo abbonamento
    with st.expander("💳 Crea Nuovo Abbonamento"):
        render_create_subscription(customer_id)
    
    # Invio messaggio
    with st.expander("💬 Invia Messaggio Personalizzato"):
        st.text_area("Messaggio", placeholder="Scrivi il messaggio da inviare...", key="custom_message")
        if st.button("📤 Invia Messaggio", key="send_message"):
            st.info("🚧 Funzionalità in sviluppo - Integrazione WhatsApp API")
    
    # Invio oroscopo manuale
    with st.expander("📜 Invia Oroscopo Manuale"):
        st.text_area("Testo Oroscopo", placeholder="Scrivi l'oroscopo personalizzato...", key="manual_horoscope")
        if st.button("📤 Invia Oroscopo", key="send_horoscope"):
            st.info("🚧 Funzionalità in sviluppo - Integrazione WhatsApp API")

def render_edit_customer(customer, customer_id):
    """Form per modificare i dati del cliente"""
    st.markdown("##### Modifica Informazioni")
    
    with st.form("edit_customer_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_name = st.text_input("Nome", value=customer.get('name', ''))
            new_phone = st.text_input("Telefono", value=customer.get('phone_number', ''))
            new_birth_place = st.text_input("Luogo di Nascita", value=customer.get('birth_place', ''))
        
        with col2:
            new_ascendant = st.text_input("Ascendente", value=customer.get('ascendant', ''))
            
            # FIX: Gestione sicura del gender
            current_gender = customer.get('gender', 'M')
            gender_options = ['M', 'F', 'Other']
            
            # Se il valore corrente non è nella lista, usa 'M' come default
            if current_gender not in gender_options:
                current_gender = 'M'
            
            gender_index = gender_options.index(current_gender)
            
            new_gender = st.selectbox(
                "Genere", 
                options=gender_options,
                index=gender_index
            )
        
        submitted = st.form_submit_button("💾 Salva Modifiche", type="primary")
        
        if submitted:
            updates = {
                'name': new_name,
                'phone_number': new_phone,
                'birth_place': new_birth_place,
                'ascendant': new_ascendant,
                'gender': new_gender
            }
            
            if update_customer(customer_id, updates):
                st.success("✅ Dati aggiornati con successo!")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("❌ Errore nell'aggiornamento")

def render_create_subscription(customer_id):
    """Form per creare un nuovo abbonamento"""
    st.markdown("##### Nuovo Abbonamento")
    
    # Carica piani disponibili
    plans = get_available_service_plans()
    
    if plans.empty:
        st.warning("Nessun piano disponibile")
        return
    
    with st.form("create_subscription_form"):
        selected_plan = st.selectbox(
            "Seleziona Piano",
            options=plans['id'].tolist(),
            format_func=lambda x: f"{plans[plans['id']==x]['name'].values[0]} - €{plans[plans['id']==x]['price'].values[0]:.2f} ({plans[plans['id']==x]['duration_days'].values[0]} giorni)"
        )
        
        payment_ref = st.text_input("Riferimento Pagamento (opzionale)")
        
        submitted = st.form_submit_button("✅ Crea Abbonamento", type="primary")
        
        if submitted:
            if create_manual_subscription(customer_id, selected_plan, payment_ref):
                st.success("✅ Abbonamento creato con successo!")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("❌ Errore nella creazione abbonamento")