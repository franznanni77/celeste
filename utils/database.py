"""
Funzioni per l'accesso al database Supabase
Tutte le query sono cached per migliorare le performance
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.config import supabase

# ==================== STATISTICHE GENERALI ====================

@st.cache_data(ttl=60)
def get_customer_stats():
    """
    Ottiene statistiche aggregate sui clienti
    Returns: dict con totale_clienti, clienti_trial, clienti_attivi, clienti_scaduti
    """
    try:
        # Totale clienti
        all_customers = supabase.table('customers').select('id', count='exact').execute()
        total_customers = all_customers.count if hasattr(all_customers, 'count') else len(all_customers.data)
        
        # Abbonamenti attivi
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
        
        # Abbonamenti scaduti
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
    """
    Ottiene statistiche sugli oroscopi generati oggi
    Returns: dict con generati, necessari, percentuale_successo
    """
    today = datetime.now().date().isoformat()
    
    try:
        # Oroscopi generati oggi
        horoscopes = supabase.table('daily_horoscopes')\
            .select('*', count='exact')\
            .eq('data_oroscopo', today)\
            .execute()
        
        generated_count = horoscopes.count if hasattr(horoscopes, 'count') else len(horoscopes.data)
        
        # Combinazioni necessarie
        try:
            active_combinations = supabase.table('active_customers_zodiac_combinations')\
                .select('*', count='exact')\
                .execute()
            
            total_needed = active_combinations.count if hasattr(active_combinations, 'count') else len(active_combinations.data)
        except:
            # Fallback: conta combinazioni uniche manualmente
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
        
        # Calcola percentuale
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
    """
    Ottiene abbonamenti in scadenza nei prossimi 7 giorni
    Returns: dict con oggi, tre_giorni, sette_giorni, dettagli
    """
    try:
        # Usa la vista esistente
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

# ==================== DETTAGLI CLIENTI ====================

@st.cache_data(ttl=60)
def get_all_customers_details():
    """
    Ottiene tutti i clienti con dettagli completi
    Returns: DataFrame con tutti i dati dei clienti
    """
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
    """
    Ottiene clienti filtrati per tipo (totale, attivi, trial, scaduti)
    Args:
        filter_type: str - tipo di filtro da applicare
    Returns: DataFrame filtrato
    """
    df = get_all_customers_details()
    
    if df.empty:
        return df
    
    today = datetime.now().date()
    
    if filter_type == 'totale':
        return df
    
    elif filter_type == 'attivi':
        filtered = df[
            (df['is_active'] == True) & 
            (df['stato_abbonamento'] == 'active') & 
            (df['is_trial'] == False)
        ].copy()
        
    elif filter_type == 'trial':
        filtered = df[
            (df['is_active'] == True) & 
            (df['stato_abbonamento'] == 'active') & 
            (df['is_trial'] == True)
        ].copy()
        
    elif filter_type == 'scaduti':
        filtered = df[df['stato_abbonamento'] == 'expired'].copy()
    
    else:
        return df
    
    # Calcola giorni rimanenti per abbonamenti attivi
    if filter_type in ['attivi', 'trial']:
        filtered['giorni_rimanenti'] = filtered['data_scadenza'].apply(
            lambda x: (datetime.strptime(x, '%Y-%m-%d').date() - today).days if x != 'N/A' else 0
        )
    
    return filtered

# ==================== OROSCOPI ====================

@st.cache_data(ttl=60)
def get_all_horoscopes(days=7):
    """
    Ottiene tutti gli oroscopi degli ultimi N giorni
    Args:
        days: int - numero di giorni da recuperare
    Returns: DataFrame con gli oroscopi
    """
    try:
        cutoff_date = (datetime.now().date() - timedelta(days=days)).isoformat()
        
        response = supabase.table('daily_horoscopes')\
            .select('*')\
            .gte('data_oroscopo', cutoff_date)\
            .order('data_oroscopo', desc=True)\
            .execute()
        
        if not response.data:
            return pd.DataFrame()
        
        df = pd.DataFrame(response.data)
        return df
        
    except Exception as e:
        st.error(f"Errore nel recupero oroscopi: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_horoscopes_by_date(date_str):
    """
    Ottiene tutti gli oroscopi per una data specifica
    Args:
        date_str: str - data in formato YYYY-MM-DD
    Returns: DataFrame con gli oroscopi
    """
    try:
        response = supabase.table('daily_horoscopes')\
            .select('*')\
            .eq('data_oroscopo', date_str)\
            .execute()
        
        if not response.data:
            return pd.DataFrame()
        
        df = pd.DataFrame(response.data)
        return df
        
    except Exception as e:
        st.error(f"Errore nel recupero oroscopi per data: {str(e)}")
        return pd.DataFrame()
# ==================== DETTAGLIO SINGOLO CLIENTE ====================

@st.cache_data(ttl=60)
def get_customer_by_id(customer_id):
    """
    Ottiene tutti i dettagli di un singolo cliente
    Args:
        customer_id: str - UUID del cliente
    Returns: dict con tutti i dati del cliente
    """
    try:
        response = supabase.table('customers')\
            .select('*')\
            .eq('id', customer_id)\
            .single()\
            .execute()
        
        return response.data if response.data else None
        
    except Exception as e:
        st.error(f"Errore nel recupero cliente: {str(e)}")
        return None

@st.cache_data(ttl=60)
def get_customer_subscriptions_history(customer_id):
    """
    Ottiene lo storico completo degli abbonamenti di un cliente
    Args:
        customer_id: str - UUID del cliente
    Returns: DataFrame con storico abbonamenti
    """
    try:
        response = supabase.table('subscriptions')\
            .select('*, service_plans(name, price, duration_days, is_trial)')\
            .eq('customer_id', customer_id)\
            .order('created_at', desc=True)\
            .execute()
        
        if not response.data:
            return pd.DataFrame()
        
        subs_list = []
        for sub in response.data:
            subs_list.append({
                'id': sub.get('id'),
                'piano': sub.get('service_plans', {}).get('name', 'N/A'),
                'is_trial': sub.get('service_plans', {}).get('is_trial', False),
                'prezzo': sub.get('service_plans', {}).get('price', 0),
                'durata_giorni': sub.get('service_plans', {}).get('duration_days', 0),
                'data_inizio': sub.get('start_date', 'N/A'),
                'data_fine': sub.get('end_date', 'N/A'),
                'stato': sub.get('status', 'N/A'),
                'is_active': sub.get('is_active', False),
                'payment_status': sub.get('payment_status', 'N/A'),
                'payment_reference': sub.get('payment_reference', 'N/A'),
                'created_at': sub.get('created_at', 'N/A'),
                'notes': sub.get('notes', '')
            })
        
        return pd.DataFrame(subs_list)
        
    except Exception as e:
        st.error(f"Errore nel recupero storico abbonamenti: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_customer_horoscopes_history(customer_id, days=30):
    """
    Ottiene gli oroscopi inviati al cliente negli ultimi N giorni
    Args:
        customer_id: str - UUID del cliente
        days: int - numero di giorni da recuperare
    Returns: DataFrame con storico oroscopi
    """
    try:
        # Prima recupera il cliente per avere segno e ascendente
        customer = get_customer_by_id(customer_id)
        if not customer:
            return pd.DataFrame()
        
        segno = customer.get('zodiac_sign')
        ascendente = customer.get('ascendant')
        
        if not segno or not ascendente:
            return pd.DataFrame()
        
        # Calcola data cutoff
        cutoff_date = (datetime.now().date() - timedelta(days=days)).isoformat()
        
        # Recupera oroscopi per quella combinazione
        response = supabase.table('daily_horoscopes')\
            .select('*')\
            .eq('segno', segno)\
            .eq('ascendente', ascendente)\
            .gte('data_oroscopo', cutoff_date)\
            .order('data_oroscopo', desc=True)\
            .execute()
        
        if not response.data:
            return pd.DataFrame()
        
        return pd.DataFrame(response.data)
        
    except Exception as e:
        st.error(f"Errore nel recupero storico oroscopi: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_customer_timeline(customer_id):
    """
    Genera una timeline degli eventi del cliente
    Args:
        customer_id: str - UUID del cliente
    Returns: list di eventi ordinati cronologicamente
    """
    try:
        timeline = []
        
        # 1. Recupera cliente
        customer = get_customer_by_id(customer_id)
        if customer:
            timeline.append({
                'data': customer.get('created_at', ''),
                'tipo': 'registrazione',
                'icona': '👋',
                'descrizione': f"Registrazione cliente: {customer.get('name')}",
                'dettagli': f"Segno: {customer.get('zodiac_sign')}, Ascendente: {customer.get('ascendant')}"
            })
        
        # 2. Recupera abbonamenti
        subs = get_customer_subscriptions_history(customer_id)
        if not subs.empty:
            for _, sub in subs.iterrows():
                # Evento inizio abbonamento
                timeline.append({
                    'data': sub['created_at'],
                    'tipo': 'abbonamento_inizio',
                    'icona': '🎁' if sub['is_trial'] else '💳',
                    'descrizione': f"Inizio {'Trial' if sub['is_trial'] else 'Abbonamento'}: {sub['piano']}",
                    'dettagli': f"Dal {sub['data_inizio']} al {sub['data_fine']} - Stato: {sub['stato']}"
                })
                
                # Evento fine abbonamento (se scaduto)
                if sub['stato'] == 'expired':
                    timeline.append({
                        'data': sub['data_fine'],
                        'tipo': 'abbonamento_scaduto',
                        'icona': '⏸️',
                        'descrizione': f"Scadenza abbonamento: {sub['piano']}",
                        'dettagli': 'Abbonamento terminato'
                    })
        
        # Ordina per data decrescente
        timeline.sort(key=lambda x: x['data'], reverse=True)
        
        return timeline
        
    except Exception as e:
        st.error(f"Errore nella generazione timeline: {str(e)}")
        return []

# ==================== AZIONI SUI CLIENTI ====================

def update_customer(customer_id, data):
    """
    Aggiorna i dati di un cliente
    Args:
        customer_id: str - UUID del cliente
        data: dict - dati da aggiornare
    Returns: bool - True se successo, False altrimenti
    """
    try:
        response = supabase.table('customers')\
            .update(data)\
            .eq('id', customer_id)\
            .execute()
        
        return True
        
    except Exception as e:
        st.error(f"Errore nell'aggiornamento cliente: {str(e)}")
        return False

def cancel_subscription(subscription_id, reason=""):
    """
    Cancella un abbonamento
    Args:
        subscription_id: str - UUID dell'abbonamento
        reason: str - motivo della cancellazione
    Returns: bool - True se successo
    """
    try:
        response = supabase.table('subscriptions')\
            .update({
                'is_active': False,
                'status': 'cancelled',
                'cancelled_at': datetime.now().isoformat(),
                'cancelled_reason': reason
            })\
            .eq('id', subscription_id)\
            .execute()
        
        return True
        
    except Exception as e:
        st.error(f"Errore nella cancellazione abbonamento: {str(e)}")
        return False

def create_manual_subscription(customer_id, service_plan_id, payment_reference=""):
    """
    Crea un nuovo abbonamento manualmente
    Args:
        customer_id: str - UUID del cliente
        service_plan_id: str - UUID del piano di servizio
        payment_reference: str - riferimento pagamento
    Returns: bool - True se successo
    """
    try:
        # Recupera il piano per calcolare end_date
        plan = supabase.table('service_plans')\
            .select('*')\
            .eq('id', service_plan_id)\
            .single()\
            .execute()
        
        if not plan.data:
            st.error("Piano non trovato")
            return False
        
        duration = plan.data.get('duration_days', 30)
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=duration)
        
        # Crea abbonamento
        response = supabase.table('subscriptions')\
            .insert({
                'customer_id': customer_id,
                'service_plan_id': service_plan_id,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'is_active': True,
                'status': 'active',
                'payment_status': 'paid',
                'payment_reference': payment_reference,
                'renewal_enabled': False
            })\
            .execute()
        
        return True
        
    except Exception as e:
        st.error(f"Errore nella creazione abbonamento: {str(e)}")
        return False

@st.cache_data(ttl=300)
def get_available_service_plans():
    """
    Ottiene tutti i piani di servizio disponibili
    Returns: DataFrame con i piani
    """
    try:
        response = supabase.table('service_plans')\
            .select('*')\
            .eq('is_active', True)\
            .order('price')\
            .execute()
        
        if not response.data:
            return pd.DataFrame()
        
        return pd.DataFrame(response.data)
        
    except Exception as e:
        st.error(f"Errore nel recupero piani: {str(e)}")
        return pd.DataFrame()