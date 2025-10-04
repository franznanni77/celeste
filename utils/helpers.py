"""
Funzioni helper e utilità generiche
"""

import streamlit as st
from datetime import datetime

def format_date(date_str, format="%d/%m/%Y"):
    """
    Formatta una stringa data nel formato desiderato
    Args:
        date_str: str - data in formato ISO (YYYY-MM-DD)
        format: str - formato di output desiderato
    Returns: str - data formattata
    """
    try:
        if date_str == 'N/A' or not date_str:
            return 'N/A'
        date_obj = datetime.strptime(date_str.split('T')[0], '%Y-%m-%d')
        return date_obj.strftime(format)
    except:
        return date_str

def format_phone(phone):
    """
    Formatta un numero di telefono
    Args:
        phone: str - numero di telefono
    Returns: str - numero formattato
    """
    if not phone or phone == 'N/A':
        return 'N/A'
    # Rimuovi spazi
    phone = phone.replace(' ', '')
    return phone

def navigate_to(page, filter_type=None):
    """
    Naviga a una pagina specifica
    Args:
        page: str - nome della pagina
        filter_type: str - tipo di filtro (opzionale)
    """
    st.session_state.current_page = page
    st.session_state.filter_type = filter_type
    st.rerun()

def go_back_to_dashboard():
    """Torna alla dashboard principale"""
    st.session_state.current_page = 'dashboard'
    st.session_state.filter_type = None
    st.rerun()

def highlight_urgency(row):
    """
    Applica colori di sfondo basati sull'urgenza
    Args:
        row: DataFrame row - riga da colorare
    Returns: list - stili CSS da applicare
    """
    if 'Giorni Rimasti' in row.index:
        giorni = row['Giorni Rimasti']
        if giorni == 0:
            return ['background-color: #ffcccc; font-weight: bold'] * len(row)
        elif giorni <= 3:
            return ['background-color: #fff4cc'] * len(row)
        else:
            return ['background-color: #e8f4f8'] * len(row)
    return [''] * len(row)