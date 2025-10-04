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