import pandas as pd
import requests


def get_bcb_series(codigo_serie, data_inicio="01/01/2015", data_fim="31/12/2026"):
    """Busca dados na API pública do Banco Central do Brasil."""
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo_serie}/dados?formato=json&dataInicial={data_inicio}&dataFinal={data_fim}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
            df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
            df.sort_values("data", inplace=True)

            df["ano"] = df["data"].dt.year
            df["variacao_pct"] = (df["valor"].pct_change() * 100).fillna(0.0)

            return df
        return pd.DataFrame()
    except Exception as e:
        print(f"Erro ao conectar com API BCB: {e}")
        return pd.DataFrame()


def load_all_indicators(data_inicio="01/01/2015", data_fim="31/12/2026"):
    """Carrega as séries de Selic, IPCA e Dólar."""
    df_selic = get_bcb_series(432, data_inicio, data_fim)
    df_ipca = get_bcb_series(433, data_inicio, data_fim)
    df_dolar = get_bcb_series(10813, data_inicio, data_fim)

    if not df_selic.empty:
        df_selic["indicador"] = "Taxa SELIC (% a.a.)"
    if not df_ipca.empty:
        df_ipca["indicador"] = "IPCA - Inflação Mensal (%)"
    if not df_dolar.empty:
        df_dolar["indicador"] = "Cotação do Dólar (R$)"

    full_df = pd.concat([df_selic, df_ipca, df_dolar], ignore_index=True)
    return full_df