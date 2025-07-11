import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import time

# ---------------------------------------------
# 1. Funciones para obtener los datos de acciones
# ---------------------------------------------

def obtener_datos_acciones(tickers):
    """
    Obtiene las métricas clave de las acciones usando Yahoo Finance y las muestra en una tabla comparativa.
    """
    datos = []
    
    for ticker in tickers:
        try:
            empresa = yf.Ticker(ticker)
            time.sleep(1)  # Evitar bloqueos

            # Obtener datos clave
            info = empresa.info
            wacc, roic, diferencia_roic_wacc, creando_valor = calcular_wacc_y_roic(ticker)

            datos.append({
                'Ticker': ticker,
                'Compañía': info.get('longName', 'N/A'),
                'Sector': info.get('sector', 'N/A'),
                'Industria': info.get('industry', 'N/A'),
                'País': info.get('country', 'N/A'),
                'P/E': info.get('trailingPE', 0),  # Asegurarse de que sea un valor numérico
                'P/B': info.get('priceToBook', 0),  # Asegurarse de que sea un valor numérico
                'P/FCF': info.get('priceToFreeCashFlows', 0),  # Asegurarse de que sea un valor numérico
                'Dividendo': info.get('dividendRate', 0),  # Asegurarse de que sea un valor numérico
                'Payout Ratio': info.get('payoutRatio', 0),  # Asegurarse de que sea un valor numérico
                'ROA': info.get('returnOnAssets', 0),  # Asegurarse de que sea un valor numérico
                'ROE': info.get('returnOnEquity', 0),  # Asegurarse de que sea un valor numérico
                'Current Ratio': info.get('currentRatio', 0),  # Asegurarse de que sea un valor numérico
                'LTDebt/Eq': info.get('longTermDebtToEquity', 0),  # Asegurarse de que sea un valor numérico
                'Debt/Eq': info.get('debtToEquity', 0),  # Asegurarse de que sea un valor numérico
                'Oper Margin': info.get('operatingMargins', 0),  # Asegurarse de que sea un valor numérico
                'Profit Margin': info.get('profitMargins', 0),  # Asegurarse de que sea un valor numérico
                'WACC': wacc,
                'ROIC': roic,
                'Creación de Valor (WACC vs ROIC)': 'Creando valor' if creando_valor else 'No creando valor'
            })
        except Exception as e:
            print(f"Error al obtener datos para {ticker}: {e}")
    
    return pd.DataFrame(datos)


# ---------------------------------------------
# 2. Función para calcular WACC y ROIC
# ---------------------------------------------

def calcular_wacc_y_roic(ticker):
    """
    Calcula el WACC y el ROIC de una empresa usando únicamente datos de yfinance,
    e incluye una evaluación de si la empresa está creando valor (Relación ROIC-WACC).
    """
    try:
        empresa = yf.Ticker(ticker)
        
        # Pausa para evitar bloqueos de Yahoo Finance
        time.sleep(1)  # Esperamos 1 segundo entre las solicitudes
        
        # Información básica
        market_cap = empresa.info.get('marketCap', 0)  # Capitalización de mercado (valor de mercado del patrimonio)
        beta = empresa.info.get('beta', 1)  # Beta de la empresa
        rf = 0.02  # Tasa libre de riesgo (asumida como 2%)
        equity_risk_premium = 0.05  # Prima de riesgo del mercado (asumida como 5%)
        ke = rf + beta * equity_risk_premium  # Costo del capital accionario (CAPM)
        
        balance_general = empresa.balance_sheet
        deuda_total = balance_general.loc['Total Debt'].iloc[0] if 'Total Debt' in balance_general.index else 0
        efectivo = balance_general.loc['Cash And Cash Equivalents'].iloc[0] if 'Cash And Cash Equivalents' in balance_general.index else 0
        patrimonio = balance_general.loc['Common Stock Equity'].iloc[0] if 'Common Stock Equity' in balance_general.index else 0
        
        estado_resultados = empresa.financials
        gastos_intereses = estado_resultados.loc['Interest Expense'].iloc[0] if 'Interest Expense' in estado_resultados.index else 0
        ebt = estado_resultados.loc['Ebt'].iloc[0] if 'Ebt' in estado_resultados.index else 0
        impuestos = estado_resultados.loc['Income Tax Expense'].iloc[0] if 'Income Tax Expense' in estado_resultados.index else 0
        ebit = estado_resultados.loc['EBIT'].iloc[0] if 'EBIT' in estado_resultados.index else 0

        # Pausa después de obtener datos financieros
        time.sleep(1)
        
        # Calcular Kd (costo de la deuda)
        kd = gastos_intereses / deuda_total if deuda_total != 0 else 0

        # Calcular tasa de impuestos efectiva
        tasa_impuestos = impuestos / ebt if ebt != 0 else 0.21  # Asume 21% si no hay datos
        
        # Calcular WACC
        total_capital = market_cap + deuda_total
        wacc = ((market_cap / total_capital) * ke) + ((deuda_total / total_capital) * kd * (1 - tasa_impuestos))
        
        # Calcular ROIC
        nopat = ebit * (1 - tasa_impuestos)  # NOPAT
        capital_invertido = patrimonio + (deuda_total - efectivo)  # Capital Invertido
        roic = nopat / capital_invertido if capital_invertido != 0 else 0
        
        # Calcular Relación ROIC-WACC
        diferencia_roic_wacc = roic - wacc
        creando_valor = roic > wacc  # Determina si está creando valor

        return wacc, roic, diferencia_roic_wacc, creando_valor
        
    except Exception as e:
        print(f"Error al calcular WACC y ROIC para {ticker.upper()}: {e}")
        return 0, 0, 0, False


# ---------------------------------------------
# 3. Función para crear los gráficos de análisis
# ---------------------------------------------

def crear_graficos(df):
    """
    Genera gráficos comparativos de Rentabilidad, Eficiencia, Apalancamiento, Crecimiento, etc.
    """
    # Comparativa de Ratios de Valoración
    if 'P/E' in df.columns and 'P/B' in df.columns and 'P/FCF' in df.columns:
        df.plot(x='Ticker', y=['P/E', 'P/B', 'P/FCF'], kind='bar', figsize=(10, 6))
        plt.title('Comparativa de Ratios de Valoración')
        plt.ylabel('Valor')
        st.pyplot()
    else:
        st.warning("Algunos datos de valoración no están disponibles.")

    # Rendimiento de Dividendos
    if 'Dividendo' in df.columns and 'Payout Ratio' in df.columns:
        df.plot(x='Ticker', y=['Dividendo', 'Payout Ratio'], kind='bar', figsize=(10, 6))
        plt.title('Rendimiento de Dividendos')
        plt.ylabel('Valor')
        st.pyplot()
    else:
        st.warning("Algunos datos de dividendos no están disponibles.")

    # Rentabilidad: ROE vs ROA
    if 'ROE' in df.columns and 'ROA' in df.columns:
        df.plot(x='Ticker', y=['ROE', 'ROA'], kind='bar', figsize=(10, 6))
        plt.title('Rentabilidad: ROE vs ROA')
        plt.ylabel('Porcentaje')
        st.pyplot()
    else:
        st.warning("Algunos datos de rentabilidad no están disponibles.")

    # Eficiencia: WACC vs ROIC
    if 'WACC' in df.columns and 'ROIC' in df.columns:
        df.plot(x='Ticker', y=['WACC', 'ROIC'], kind='bar', figsize=(10, 6))
        plt.title('Eficiencia: WACC vs ROIC')
        plt.ylabel('Porcentaje')
        st.pyplot()
    else:
        st.warning("Algunos datos de eficiencia no están disponibles.")


# ---------------------------------------------
# 4. Interfaz de Usuario con Streamlit
# ---------------------------------------------

st.title("Análisis Financiero Avanzado")
st.subheader("Bienvenido al Dashboard de Análisis Financiero usando Streamlit")

# Ingreso de tickers
tickers_input = st.text_input("Ingresa los tickers de las empresas (separados por coma)", "AAPL, MSFT, GOOGL")
tickers = [ticker.strip() for ticker in tickers_input.split(",")]

if tickers:
    # Cargar datos de las acciones
    st.subheader("Comparador de Acciones")
    df_comparativo = obtener_datos_acciones(tickers)
    st.dataframe(df_comparativo)

    # Análisis de valoración
    st.subheader("Análisis de Valoración")
    crear_graficos(df_comparativo)
