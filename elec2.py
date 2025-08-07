# -*- coding: utf-8 -*-
"""
Created on Thu Aug  7 10:15:09 2025

@author: marti
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import numpy_financial as npf

# Configuración de la página
st.set_page_config(page_title="Comparador Proyecto Solar", layout="wide")
st.title("☀️ Comparador Financiero Proyecto Solar - Escenario A vs B")

def calcular_escenario(nombre, consumo_kwh, precio_kwh, cobertura_pct, costo_kw,
                       factor_solar, vida_anos, mantencion_pct,
                       tasa_anual, plazo_credito, inflacion_energia_pct):
    """
    Calcula todas las métricas financieras para un escenario de proyecto solar.
    """
    # --- Cálculos iniciales ---
    capacidad_total_kw = consumo_kwh / (factor_solar / 12)
    capacidad_instalada_kw = capacidad_total_kw * (cobertura_pct / 100)
    energia_generada_mensual = capacidad_instalada_kw * (factor_solar / 12)
    inversion_total = capacidad_instalada_kw * costo_kw

    # --- Cálculos financieros ---
    n_credito = plazo_credito * 12
    i_credito = tasa_anual / 100 / 12
    cuota_mensual = npf.pmt(i_credito, n_credito, -inversion_total) if i_credito > 0 else inversion_total / n_credito

    mantencion_anual = inversion_total * (mantencion_pct / 100)
    mantencion_mensual = mantencion_anual / 12
    
    # Tasa de inflación mensual para el precio de la energía
    i_inflacion_mensual = (1 + inflacion_energia_pct / 100)**(1/12) - 1

    # --- Simulación del Flujo de Caja Mensual ---
    meses = vida_anos * 12
    flujo_proyecto = []
    flujos_para_van = [-inversion_total]
    columnas_tabla = ["Gasto Energía ($)", "Ahorro Solar ($)", "Cuota Crédito ($)", "Mantención ($)", "Flujo Neto ($)"]
    tabla_flujo = {col: [] for col in columnas_tabla}

    for m in range(1, meses + 1):
        precio_kwh_ajustado = precio_kwh * ((1 + i_inflacion_mensual) ** (m - 1))
        ahorro_mensual_ajustado = energia_generada_mensual * precio_kwh_ajustado
        gasto_sin_solar = consumo_kwh * precio_kwh_ajustado
        
        cuota_actual = cuota_mensual if m <= n_credito else 0
        flujo_neto = ahorro_mensual_ajustado - cuota_actual - mantencion_mensual
        
        flujo_proyecto.append(flujo_neto)
        flujos_para_van.append(flujo_neto)

        tabla_flujo["Gasto Energía ($)"].append(gasto_sin_solar)
        tabla_flujo["Ahorro Solar ($)"].append(ahorro_mensual_ajustado)
        tabla_flujo["Cuota Crédito ($)"].append(cuota_actual)
        tabla_flujo["Mantención ($)"].append(mantencion_mensual)
        tabla_flujo["Flujo Neto ($)"].append(flujo_neto)

    # --- Métricas de Rentabilidad ---
    tir = npf.irr(flujos_para_van) * 12 if npf.irr(flujos_para_van) else 0
    van = npf.npv(i_credito, flujos_para_van) if i_credito > 0 else sum(flujos_para_van)
    flujo_acumulado = np.cumsum(flujo_proyecto)
    
    payback_mes_array = np.where(flujo_acumulado >= 0)[0]
    payback_mes = payback_mes_array[0] + 1 if len(payback_mes_array) > 0 else -1
    
    df_tabla = pd.DataFrame(tabla_flujo).T
    df_tabla.columns = [f"Mes {i+1}" for i in range(meses)]

    return {
        "nombre": nombre,
        "inversion_total": inversion_total,
        "ahorro_mensual_inicial": energia_generada_mensual * precio_kwh,
        "cuota_mensual": cuota_mensual,
        "mantencion_mensual": mantencion_mensual,
        "flujo_neto_mensual": (energia_generada_mensual * precio_kwh) - cuota_mensual - mantencion_mensual,
        "tir": tir,
        "van": van,
        "payback_mes": payback_mes,
        "flujo_acumulado": flujo_acumulado,
        "meses": list(range(1, meses + 1)),
        "tabla_flujo": df_tabla
    }

def get_scenario_inputs(scenario_key):
    """Crea los widgets de Streamlit para un escenario y devuelve los valores."""
    st.sidebar.header(f" {'🅰' if scenario_key == 'a' else '🅱'} Escenario {scenario_key.upper()}")
    
    default_cobertura = 50 if scenario_key == 'a' else 80
    default_tasa = 6.0 if scenario_key == 'a' else 8.0

    consumo_kwh = st.sidebar.number_input("🔌 Consumo mensual (kWh)", value=50000, key=f"{scenario_key}1")
    precio_kwh = st.sidebar.number_input("💰 Precio energía ($/kWh)", value=0.12, format="%.3f", key=f"{scenario_key}2")
    cobertura_pct = st.sidebar.slider("⚡ % de cobertura solar", 10, 100, default_cobertura, key=f"{scenario_key}3")
    costo_kw = st.sidebar.number_input("🏗️ Costo por kW instalado", value=1000, key=f"{scenario_key}4")
    factor_solar = st.sidebar.number_input("🌞 Factor solar (kWh/kW/año)", value=1600, key=f"{scenario_key}5", help="Producción anual de energía por cada kW de panel instalado. Depende de la ubicación geográfica.")
    vida_anos = st.sidebar.slider("📅 Vida útil (años)", 10, 30, 20, key=f"{scenario_key}6")
    mantencion_pct = st.sidebar.slider("🛠️ Mantención anual (% de inversión)", 0.0, 5.0, 0.5, step=0.1, key=f"{scenario_key}7")
    tasa_anual = st.sidebar.slider("📉 Tasa interés anual (%)", 2.0, 15.0, default_tasa, step=0.5, key=f"{scenario_key}8")
    plazo_credito = st.sidebar.slider("💳 Plazo crédito (años)", 1, vida_anos, 10, key=f"{scenario_key}9")
    
    return (consumo_kwh, precio_kwh, cobertura_pct, costo_kw, factor_solar,
            vida_anos, mantencion_pct, tasa_anual, plazo_credito)

# --- Barra Lateral (Inputs) ---
comparar = st.sidebar.radio("¿Comparar dos escenarios?", ["No", "Sí"]) == "Sí"
st.sidebar.markdown("---")
inflacion_energia_pct = st.sidebar.slider("📈 Aumento anual del precio de la energía (%)", 0.0, 10.0, 3.0, step=0.1, key="inflacion", help="Tasa anual a la que se espera que suba el costo de la energía de la red.")

# --- Cálculos de Escenarios ---
params_a = get_scenario_inputs('a')
escenario_a = calcular_escenario("Escenario A", *params_a, inflacion_energia_pct)

if comparar:
    st.sidebar.markdown("---")
    params_b = get_scenario_inputs('b')
    escenario_b = calcular_escenario("Escenario B", *params_b, inflacion_energia_pct)
else:
    escenario_b = None

# --- Dashboard Principal ---

# 1. Veredicto del Proyecto
st.subheader("✅ Veredicto del Proyecto")
col1, col2 = st.columns(2) if comparar else (st.columns(1)[0], None)

with col1:
    st.markdown("#### 🅰 Escenario A")
    flujo_neto_A = escenario_a['flujo_neto_mensual']
    if flujo_neto_A > 0:
        st.success(f"¡CONVIENE! El proyecto genera un flujo neto positivo inicial de **${flujo_neto_A:,.0f}** mensuales.")
    else:
        st.error(f"¡NO CONVIENE! El proyecto tiene un déficit inicial de **${-flujo_neto_A:,.0f}** mensuales.")

if comparar and escenario_b:
    with col2:
        st.markdown("#### 🅱 Escenario B")
        flujo_neto_B = escenario_b['flujo_neto_mensual']
        if flujo_neto_B > 0:
            st.success(f"¡CONVIENE! El proyecto genera un flujo neto positivo inicial de **${flujo_neto_B:,.0f}** mensuales.")
        else:
            st.error(f"¡NO CONVIENE! El proyecto tiene un déficit inicial de **${-flujo_neto_B:,.0f}** mensuales.")

st.markdown("---")

# 2. KPIs Principales
st.subheader("📌 KPIs del Proyecto")
cols_kpi = st.columns(4)
payback_a_anos = escenario_a['payback_mes'] / 12 if escenario_a['payback_mes'] > 0 else "Nunca"
payback_a_texto = f"{payback_a_anos:.1f} años" if isinstance(payback_a_anos, float) else payback_a_anos

cols_kpi[0].metric("🅰 Inversión Total", f"${escenario_a['inversion_total']:,.0f}")
cols_kpi[1].metric("🅰 Ahorro Mensual (inicial)", f"${escenario_a['ahorro_mensual_inicial']:,.0f}")
cols_kpi[2].metric("🅰 TIR (Tasa Interna Retorno)", f"{escenario_a['tir']:.2%}")
cols_kpi[3].metric("🅰 Payback", payback_a_texto)

if comparar and escenario_b:
    cols_kpi_b = st.columns(4)
    payback_b_anos = escenario_b['payback_mes'] / 12 if escenario_b['payback_mes'] > 0 else "Nunca"
    payback_b_texto = f"{payback_b_anos:.1f} años" if isinstance(payback_b_anos, float) else payback_b_texto
    
    cols_kpi_b[0].metric("🅱 Inversión Total", f"${escenario_b['inversion_total']:,.0f}")
    cols_kpi_b[1].metric("🅱 Ahorro Mensual (inicial)", f"${escenario_b['ahorro_mensual_inicial']:,.0f}")
    cols_kpi_b[2].metric("🅱 TIR (Tasa Interna Retorno)", f"{escenario_b['tir']:.2%}")
    cols_kpi_b[3].metric("🅱 Payback", payback_b_texto)

st.markdown("---")

# 3. Gráfico de Flujo de Caja Acumulado
st.subheader("📈 Flujo de Caja Acumulado")
fig_acumulado = go.Figure()
fig_acumulado.add_trace(go.Scatter(x=escenario_a['meses'], y=escenario_a['flujo_acumulado'], mode='lines', name='Flujo Acumulado A', line=dict(color='#1f77b4')))
if escenario_a['payback_mes'] > 0:
    fig_acumulado.add_vline(x=escenario_a['payback_mes'], line_width=2, line_dash="dash", line_color="green", annotation_text=f"Payback A: Mes {escenario_a['payback_mes']}", annotation_position="top left")

if comparar and escenario_b:
    fig_acumulado.add_trace(go.Scatter(x=escenario_b['meses'], y=escenario_b['flujo_acumulado'], mode='lines', name='Flujo Acumulado B', line=dict(color='#ff7f0e')))
    if escenario_b['payback_mes'] > 0:
        fig_acumulado.add_vline(x=escenario_b['payback_mes'], line_width=2, line_dash="dash", line_color="red", annotation_text=f"Payback B: Mes {escenario_b['payback_mes']}", annotation_position="bottom right")

fig_acumulado.add_hline(y=0, line_width=1, line_color="grey")
fig_acumulado.update_layout(title="Evolución del Retorno de la Inversión", xaxis_title="Mes del Proyecto", yaxis_title="Flujo de Caja Acumulado ($)", height=500, legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
st.plotly_chart(fig_acumulado, use_container_width=True)

st.markdown("---")

# 4. Tabla de Flujo Mensual Detallada
with st.expander("Ver Tabla de Flujo Mensual Detallada - Escenario A"):
    st.dataframe(escenario_a["tabla_flujo"].style.format("{:,.0f}"), use_container_width=True)
    if comparar and escenario_b:
        st.markdown("---")
        st.markdown("#### Tabla de Flujo Mensual - Escenario B")
        st.dataframe(escenario_b["tabla_flujo"].style.format("{:,.0f}"), use_container_width=True)

# 5. Tabla de Sensibilidad de la Cuota
with st.expander("Ver Análisis de Sensibilidad de la Cuota del Crédito (Escenario A)"):
    inversion = escenario_a['inversion_total']
    tasas = np.arange(2.0, 15.5, 1.0)
    plazos = range(5, len(escenario_a['meses']) // 12 + 1, 2)
    
    matriz_cuotas = []
    for plazo in plazos:
        fila = [npf.pmt(tasa / 100 / 12, plazo * 12, -inversion) for tasa in tasas]
        matriz_cuotas.append(fila)
    
    df_cuotas = pd.DataFrame(matriz_cuotas, columns=[f"{t:.1f}%" for t in tasas], index=[f"{p} años" for p in plazos])
    st.dataframe(df_cuotas.style.background_gradient(cmap='viridis_r').format("${:,.0f}"), use_container_width=True)
    st.caption("La tabla muestra la cuota mensual del crédito para diferentes combinaciones de Tasa de Interés y Plazo en años, basada en la inversión del Escenario A.")