import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_calendar import calendar
import os

# --- Configuración inicial ---
st.set_page_config(page_title="Gestor de reservas de coches arada", layout="wide")
st.title("🚗 Gestor de reservas de coches arada")

# --- Datos base ---
empleados = ["Seleccionar"] + sorted([
    "Antonio José", "Antonio Miguel", "Berta", "Encar", "Felipe",
    "Jose David", "Juanjo", "Juanma Fdez.", "Juanma Pelegrín", "Justa",
    "Mari Huertas", "Mayca", "Miguel Ángel", "Pedro", "Raúl"
])

vehiculos = ["Seleccionar", "Micra", "Sandero", "Duster"]
colores_vehiculo = {"Micra": "#1f77b4", "Sandero": "#2ca02c", "Duster": "#ff7f0e"}

# --- Cargar datos persistentes desde CSV ---
if os.path.exists("reservas.csv"):
    reservas_df = pd.read_csv("reservas.csv", parse_dates=["Inicio", "Fin"])
else:
    reservas_df = pd.DataFrame(columns=["Empleado", "Vehículo", "Inicio", "Fin", "Motivo"])

if os.path.exists("mantenimiento.csv"):
    mantenimiento_df = pd.read_csv("mantenimiento.csv", parse_dates=["Inicio", "Fin"])
else:
    mantenimiento_df = pd.DataFrame(columns=["Vehículo", "Inicio", "Fin", "Motivo"])

# --- Formulario de reserva ---
st.header("📅 Nueva reserva")
with st.form("form_reserva"):
    empleado = st.selectbox("Empleado", empleados, index=0)
    vehiculo = st.selectbox("Vehículo", vehiculos, index=0)
    inicio_fecha = st.date_input("Fecha de inicio de la reserva")
    inicio_hora = st.time_input("Hora de inicio de la reserva", value=None)
    fin_fecha = st.date_input("Fecha de fin de la reserva")
    fin_hora = st.time_input("Hora de fin de la reserva", value=None)
    motivo = st.text_input("Motivo (opcional)")
    submitted = st.form_submit_button("Reservar")

    if submitted:
        if empleado == "Seleccionar" or vehiculo == "Seleccionar" or not inicio_hora or not fin_hora:
            st.error("Debes completar todos los campos de la reserva.")
        else:
            inicio = datetime.combine(inicio_fecha, inicio_hora)
            fin = datetime.combine(fin_fecha, fin_hora)
            if inicio >= fin:
                st.error("La fecha/hora de inicio debe ser anterior a la de fin.")
            else:
                reservas_vehiculo = reservas_df[reservas_df["Vehículo"] == vehiculo]
                conflicto_reserva = reservas_vehiculo[
                    ((reservas_vehiculo["Inicio"] < fin) & (reservas_vehiculo["Fin"] > inicio))
                ]
                mantenimiento_vehiculo = mantenimiento_df[mantenimiento_df["Vehículo"] == vehiculo]
                conflicto_mantenimiento = mantenimiento_vehiculo[
                    ((mantenimiento_vehiculo["Inicio"] < fin) & (mantenimiento_vehiculo["Fin"] > inicio))
                ]
                if not conflicto_reserva.empty:
                    st.error("⚠️ Conflicto con otra reserva existente para este vehículo.")
                elif not conflicto_mantenimiento.empty:
                    st.error("🔧 El vehículo está reservado por mantenimiento en ese horario.")
                else:
                    nueva_reserva = pd.DataFrame([{
                        "Empleado": empleado,
                        "Vehículo": vehiculo,
                        "Inicio": inicio,
                        "Fin": fin,
                        "Motivo": motivo
                    }])
                    reservas_df = pd.concat([reservas_df, nueva_reserva], ignore_index=True)
                    reservas_df.to_csv("reservas.csv", index=False)
                    st.success("🚀 Reserva realizada con éxito.")

# --- Gestión de mantenimiento ---
st.header("🔧 Bloquear vehículo por mantenimiento")
with st.form("form_mantenimiento"):
    vehiculo_m = st.selectbox("Vehículo", vehiculos[1:], key="mant_vehiculo")
    inicio_fecha_m = st.date_input("Fecha inicio mantenimiento", key="mant_inicio_fecha")
    inicio_hora_m = st.time_input("Hora inicio mantenimiento", key="mant_inicio_hora", value=None)
    fin_fecha_m = st.date_input("Fecha fin mantenimiento", key="mant_fin_fecha")
    fin_hora_m = st.time_input("Hora fin mantenimiento", key="mant_fin_hora", value=None)
    motivo_m = st.text_input("Motivo mantenimiento", key="mant_motivo")
    submit_m = st.form_submit_button("Añadir bloqueo")

    if submit_m:
        if not inicio_hora_m or not fin_hora_m:
            st.error("Debes indicar la hora de inicio y fin del mantenimiento.")
        else:
            inicio_m = datetime.combine(inicio_fecha_m, inicio_hora_m)
            fin_m = datetime.combine(fin_fecha_m, fin_hora_m)
            if inicio_m >= fin_m:
                st.error("La fecha/hora de inicio debe ser anterior a la de fin.")
            else:
                nuevo_bloqueo = pd.DataFrame([{
                    "Vehículo": vehiculo_m,
                    "Inicio": inicio_m,
                    "Fin": fin_m,
                    "Motivo": motivo_m
                }])
                mantenimiento_df = pd.concat([mantenimiento_df, nuevo_bloqueo], ignore_index=True)
                mantenimiento_df.to_csv("mantenimiento.csv", index=False)
                st.success("🛠️ Bloqueo de mantenimiento añadido.")

# --- Visualización en calendario tipo agenda ---
st.header("📊 Agenda de reservas y mantenimiento")

if reservas_df.empty and mantenimiento_df.empty:
    st.info("No hay registros para mostrar.")
else:
    calendar_events = []

    for _, row in reservas_df.iterrows():
        color = colores_vehiculo.get(row["Vehículo"], "#1f77b4")
        calendar_events.append({
            "title": f"{row['Vehículo']} - {row['Empleado']}",
            "start": row['Inicio'].isoformat(),
            "end": row['Fin'].isoformat(),
            "color": color
        })

    for _, row in mantenimiento_df.iterrows():
        calendar_events.append({
            "title": f"Mantenimiento - {row['Vehículo']}",
            "start": row['Inicio'].isoformat(),
            "end": row['Fin'].isoformat(),
            "color": "#808080"
        })

    calendar(
        events=calendar_events,
        options={
            "initialView": "timeGridWeek",
            "locale": "es",
            "slotMinTime": "07:00:00",
            "slotMaxTime": "21:00:00",
            "height": 600
        },
        custom_css=".fc-event-title { font-size: 14px; }"
    )

# --- Anular reservas y exportar historial ---
st.header("❌ Anular reserva")
if not reservas_df.empty:
    reservas_df["Resumen"] = reservas_df.apply(lambda row: f"{row['Empleado']} - {row['Vehículo']} ({row['Inicio'].strftime('%d/%m/%Y %H:%M')} - {row['Fin'].strftime('%d/%m/%Y %H:%M')})", axis=1)
    reserva_seleccionada = st.selectbox("Selecciona una reserva para anular", ["Seleccionar"] + reservas_df["Resumen"].tolist())
    if reserva_seleccionada != "Seleccionar":
        if st.button("Anular reserva"):
            reservas_df = reservas_df[reservas_df["Resumen"] != reserva_seleccionada].drop(columns=["Resumen"])
            reservas_df.to_csv("reservas.csv", index=False)
            st.success("Reserva anulada correctamente.")
else:
    st.info("No hay reservas disponibles para anular.")

with st.expander("Exportar historial"):
    col1, col2 = st.columns(2)
    with col1:
        csv_reservas = reservas_df.to_csv(index=False).encode('utf-8')
        st.download_button("Descargar CSV reservas", csv_reservas, "reservas_coches.csv", "text/csv")
    with col2:
        csv_mantenimiento = mantenimiento_df.to_csv(index=False).encode('utf-8')
        st.download_button("Descargar CSV mantenimiento", csv_mantenimiento, "mantenimiento_coches.csv", "text/csv")
