import streamlit as st
import pandas as pd
import plotly.express as px
import re
import random

def render_analyse():
    st.header("🧠 Centre d'Intelligence Analytique")
    st.markdown("Exploration **flexible, globale et intelligente** de vos datasets (TUNEPS, RNE, JORT, ou fichiers externes).")
    
    # 1. Vérification si des données ont été transmises par le Hub TUNEPS
    df_ana = None
    
    if 'data_to_analyse' in st.session_state and st.session_state['data_to_analyse'] is not None:
        df_ana = st.session_state['data_to_analyse']
        st.info("💡 Données prêtes pour l'**Analyse Globale & Intelligente** (en provenance du Hub TUNEPS).")
        if st.button("🗑️ Effacer et charger un autre fichier", key="clear_ana"):
            st.session_state['data_to_analyse'] = None
            st.rerun()
    else:
        file_ana = st.file_uploader("Importer une base de données", type=["csv", "xlsx"], key="uploader_ana")
        if file_ana:
            try:
                if file_ana.name.endswith('.csv'):
                    df_ana = pd.read_csv(file_ana)
                else:
                    df_ana = pd.read_excel(file_ana)
            except Exception as e:
                st.error(f"Erreur de lecture : {e}")
                return
    
    if df_ana is not None:
        if df_ana.empty:
            st.warning("Le fichier est vide.")
            return

        st.success(f"Base de données importée : {len(df_ana)} enregistrements.")
        
        # Nettoyage et détection automatique
        df_ana = _auto_clean_df(df_ana)
        col_types = _detect_column_types(df_ana)
        
        # Tabs pour l'organisation
        tab1, tab2, tab3 = st.tabs(["💡 Vue d'ensemble", "📈 Exploration Libre", "📋 Données Brutes"])
        
        with tab1:
            # Vérification si c'est un format connu pour analyses spéciales
            cols = df_ana.columns.tolist()
            if "Montant HT" in cols and "Lien Source" in cols:
                _render_tuneps_analytics(df_ana)
            elif "Numéro RNE" in cols and "Capital Social" in cols:
                _render_rne_analytics(df_ana)
            elif "URL Annonce" in cols and "Catégorie" in cols:
                _render_jort_analytics(df_ana)
            else:
                _render_smart_generic_analytics(df_ana, col_types)
                
        with tab2:
            _render_exploration_libre(df_ana, col_types)
            
        with tab3:
            st.dataframe(df_ana, width='stretch', key="raw_data_view")

def _auto_clean_df(df):
    """Tente de convertir les colonnes de montants et de dates automatiquement."""
    for col in df.columns:
        if df[col].dtype == 'object':
            sample = df[col].dropna().astype(str).str.strip().head(20)
            if sample.empty: continue
            
            try:
                if any(sample.str.contains(r'\d{2}/\d{2}/\d{4}')):
                    df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
                    continue
            except: pass

            # Test Argent ou Nombre Pur (TND, DT, €, $, ou juste des chiffres bien formés)
            # On cherche si au moins 50% du sample ressemble à un nombre après nettoyage basique
            num_matches = 0
            for s_val in sample:
                cleaned = re.sub(r'[^\d.,]', '', s_val)
                if len(cleaned) > 0 and any(c.isdigit() for c in cleaned):
                    num_matches += 1
            
            if num_matches > len(sample) * 0.5:
                # C'est probablement une colonne de mesures
                df[col] = pd.to_numeric(df[col].apply(_clean_numeric_string), errors='coerce')
    return df

def _clean_numeric_string(val):
    if pd.isna(val) or str(val).strip() in ["Non défini", "Inconnu", ""]: return 0.0
    s = str(val).replace(' ', '')
    s = re.sub(r'[^\d.,]', '', s)
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    try: return float(s)
    except: return 0.0

def _detect_column_types(df):
    types = {'categorical': [], 'numerical': [], 'temporal': [], 'text': []}
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            types['temporal'].append(col)
        elif pd.api.types.is_numeric_dtype(df[col]):
            if df[col].nunique() < 10 and len(df) > 50:
                types['categorical'].append(col)
            else:
                types['numerical'].append(col)
        else:
            n_unique = df[col].nunique()
            if n_unique <= 30:
                types['categorical'].append(col)
            else:
                types['text'].append(col)
    return types

def _render_smart_generic_analytics(df, types):
    st.subheader("💡 Analyse Automatique du Dataset")
    cols_kpi = st.columns(min(len(types['numerical']) + 1, 4))
    cols_kpi[0].metric("Total Lignes", f"{len(df):,}")
    
    for idx, num_col in enumerate(types['numerical'][:3]):
        sum_val = df[num_col].sum()
        if (idx + 1) < len(cols_kpi):
            cols_kpi[idx + 1].metric(f"Total {num_col}", f"{sum_val:,.3f}")

    st.divider()
    c1, c2 = st.columns(2)
    if types['categorical']:
        with c1:
            target_cat = types['categorical'][0]
            st.markdown(f"**Répartition : {target_cat}**")
            counts = df[target_cat].value_counts().reset_index()
            counts.columns = [target_cat, 'Nombre']
            fig = px.pie(counts, names=target_cat, values='Nombre', hole=0.4)
            st.plotly_chart(fig, width='stretch', key="gen_pie")
            
    if len(types['categorical']) > 1 or types['text']:
        with c2:
            target = types['categorical'][1] if len(types['categorical']) > 1 else types['text'][0]
            st.markdown(f"**Top 10 : {target}**")
            top10 = df[target].value_counts().head(10).reset_index()
            top10.columns = [target, 'Compte']
            fig = px.bar(top10, x='Compte', y=target, orientation='h', color='Compte')
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, width='stretch', key="gen_bar")

    if types['temporal']:
        st.divider()
        st.markdown(f"**Évolution temporelle ({types['temporal'][0]})**")
        t_col = types['temporal'][0]
        period = "ME" if len(df) > 100 else "D"
        time_data = df.groupby(df[t_col].dt.to_period(period)).size().reset_index(name='Volume')
        time_data[t_col] = time_data[t_col].dt.to_timestamp()
        fig_time = px.line(time_data, x=t_col, y='Volume', markers=True, line_shape='spline')
        st.plotly_chart(fig_time, width='stretch', key="gen_time")

def _render_exploration_libre(df, types):
    st.subheader("📈 Exploration Multi-Dimensionnelle")
    st.markdown("Croisez les colonnes pour découvrir des corrélations.")
    
    c1, c2, c3 = st.columns(3)
    x_axis = c1.selectbox("Axe X (Dimensions)", types['categorical'] + types['temporal'] + types['numerical'], key="explor_x")
    y_axis = c2.selectbox("Axe Y (Mesures)", ["Nombre de lignes"] + types['numerical'], key="explor_y")
    chart_type = c3.selectbox("Type de Graphique", [
        "Barres", "Lignes", "Aires", "Points (Nuage)", "Boxplot", "Violon", "Histogramme", "Camembert"
    ], key="explor_type")
    
    y_format = ".3f"
    if y_axis == "Nombre de lignes":
        plot_df = df.groupby(x_axis).size().reset_index(name='Nombre')
        y_col = 'Nombre'
        y_format = ".0f"
    else:
        agg_func = st.radio("Agrégation", ["Somme", "Moyenne"], horizontal=True, key="explor_agg")
        if agg_func == "Somme":
            plot_df = df.groupby(x_axis)[y_axis].sum().reset_index()
        else:
            plot_df = df.groupby(x_axis)[y_axis].mean().reset_index()
        y_col = y_axis

    # Validation Sécurité
    is_distribution_chart = chart_type in ["Points (Nuage)", "Boxplot", "Violon", "Histogramme"]
    if is_distribution_chart and y_axis == "Nombre de lignes":
        st.error(f"❌ Le graphique en **{chart_type}** nécessite une mesure numérique réelle pour l'axe Y.")
        return
    
    if chart_type == "Barres":
        fig = px.bar(plot_df, x=x_axis, y=y_col, color=y_col, text_auto=y_format)
    elif chart_type == "Lignes":
        fig = px.line(plot_df, x=x_axis, y=y_col, markers=True)
    elif chart_type == "Aires":
        fig = px.area(plot_df, x=x_axis, y=y_col)
    elif chart_type == "Points (Nuage)":
        fig = px.scatter(df, x=x_axis, y=y_axis, color=types['categorical'][0] if types['categorical'] else None)
    elif chart_type == "Boxplot":
        fig = px.box(df, x=x_axis, y=y_axis, color=x_axis)
    elif chart_type == "Violon":
        fig = px.violin(df, x=x_axis, y=y_axis, color=x_axis, box=True, points="all")
    elif chart_type == "Histogramme":
        fig = px.histogram(df, x=y_axis, color=x_axis, marginal="box")
    elif chart_type == "Camembert":
        fig = px.pie(plot_df, names=x_axis, values=y_col, hole=0.4)
    else:
        fig = px.bar(plot_df, x=x_axis, y=y_col)
        
    st.plotly_chart(fig, width='stretch', key="explor_chart_final")

def _render_tuneps_analytics(df):
    st.subheader("🔍 Analyse des Marchés Publics (TUNEPS)")
    if 'Montant Calc HT' not in df.columns:
        df['Montant Calc HT'] = df.get('Montant HT', df.get('Montant TTC', '0')).apply(_clean_numeric_string)
    
    total_ht = df['Montant Calc HT'].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Volume Total (Marchés)", f"{len(df):,}")
    c2.metric("Enveloppe Globale", f"{total_ht:,.3f} TND")
    if 'PME' in df.columns:
        parts_pme = len(df[df['PME'].astype(str).str.lower() == 'oui'])
        c3.metric("Remportés par PME", f"{parts_pme} marchés")
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Top 10 Acheteurs Publics**")
        buyers = df['Acheteur Public'].value_counts().head(10).reset_index()
        buyers.columns = ['Acheteur', 'Nombre']
        fig = px.bar(buyers, x='Nombre', y='Acheteur', orientation='h', color='Nombre')
        st.plotly_chart(fig, width='stretch', key="tuneps_buyers")
        
    with col2:
        st.markdown("**Top 10 Entreprises**")
        df_winners = df[~df['Attributaire (Gagnant)'].isin(["Non défini", "", None])]
        winners = df_winners['Attributaire (Gagnant)'].value_counts().head(10).reset_index()
        winners.columns = ['Entreprise', 'Marchés']
        fig2 = px.bar(winners, x='Marchés', y='Entreprise', orientation='h', color='Marchés')
        st.plotly_chart(fig2, width='stretch', key="tuneps_winners")

def _render_rne_analytics(df):
    st.subheader("🔍 Analyse du Registre National (RNE)")
    df = df.fillna("Non renseigné")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Forme Juridique**")
        df_forme = df['Forme Juridique'].value_counts().reset_index()
        df_forme.columns = ['Forme Juridique', 'Nombre']
        fig = px.pie(df_forme, names='Forme Juridique', values='Nombre', hole=0.4)
        st.plotly_chart(fig, width='stretch', key="rne_forme_pie")
        
    with c2:
        st.markdown("**État d'Activité**")
        if 'État' in df.columns:
            df_etat = df['État'].value_counts().reset_index()
            df_etat.columns = ['État', 'Nombre']
            fig2 = px.pie(df_etat, names='État', values='Nombre', color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig2, width='stretch', key="rne_etat_pie")

def _render_jort_analytics(df):
    st.subheader("🔍 Analyse des Annonces Légales (JORT)")
    df = df.fillna("Non renseigné")
    cat = df['Catégorie'].value_counts().reset_index()
    cat.columns = ['Catégorie', 'Volume']
    fig = px.pie(cat, names='Catégorie', values='Volume', hole=0.3)
    st.plotly_chart(fig, width='stretch', key="jort_cat_pie")
