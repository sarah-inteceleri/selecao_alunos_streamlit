import streamlit as st
import pandas as pd
import numpy as np

st.title("Sistema de Seleção de Alunos - Olimpíada e Paralimpíada (CSV)")

uploaded_file = st.file_uploader("Envie o arquivo .csv", type=["csv"])

# Nomes reais das colunas enviadas por você
col_ano        = "Ano escolar do aluno:"
col_nome       = "Nome do aluno"
col_escola     = "Nome da escola onde você atua"
col_pontos     = "Quantos pontos o aluno fez?"
col_tempo      = "Quanto tempo de realização?"
col_def        = "Se for aluno com deficiência/transtorno, escolha a categoria da Olimpíada que o(a) aluno(a) se encaixa:"
col_prof       = "Escreva o nome do professor representante"
col_municipio  = "Qual o município?"

# ------------ DEIXAR APENAS AS COLUNAS FINAIS ----------
colunas_final = [
    col_ano,
    col_nome,
    col_escola,
    col_municipio,  
    col_pontos,
    col_tempo,
    col_def,
    col_prof
]

# Função para converter tempo em segundos
def tempo_para_segundos(x):
    """Tenta converter várias formas de tempo para segundos.
       Se não conseguir, retorna np.nan (tratado como 'infinito' no sort)."""
    if pd.isna(x):
        return np.nan
    s = str(x).strip()
    if s == "":
        return np.nan
    # se formato mm:ss ou m:ss
    if ":" in s:
        parts = s.split(":")
        try:
            m = int(parts[0])
            sec = int(parts[1])
            return m * 60 + sec
        except:
            return np.nan
    # se for número (segundos já)
    try:
        return float(s)
    except:
        return np.nan

# Função para selecionar alunos por escola e ano
def selecionar_alunos(df):
    df = df.copy()
    df["_tempo_segundos"] = df[col_tempo].apply(tempo_para_segundos)

    final_lista = []

    # groupby por escola e ano
    for (escola, ano), grupo in df.groupby([col_escola, col_ano]):
        grupo = grupo.copy()
        # ordenar por pontos desc, tempo asc (np.nan fica no final)
        grupo = grupo.sort_values(
            by=[col_pontos, "_tempo_segundos"],
            ascending=[False, True],
            na_position='last'
        )

        if len(grupo) <= 2:
            final_lista.append(grupo)
        else:
            top2 = grupo.head(2)

            # referência para checar empates
            pontos_ref = top2[col_pontos].min()
            tempo_ref = top2["_tempo_segundos"].max()

            # pega todos que empataram exatamente nesses valores
            empatados = grupo[
                (grupo[col_pontos] == pontos_ref) &
                (grupo["_tempo_segundos"] == tempo_ref)
            ]

            resultado = pd.concat([top2, empatados]).drop_duplicates()
            final_lista.append(resultado)

    if not final_lista:
        return pd.DataFrame(columns=df.columns)
    return pd.concat(final_lista)

# Processamento do CSV
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Verifica se todas as colunas esperadas existem
        faltam = [c for c in colunas_final if c not in df.columns]
        if faltam:
            st.error(f"As seguintes colunas estão faltando no CSV: {faltam}")
        else:
            st.success("Arquivo carregado!")

            # separar paralimp/olimp com base na coluna de deficiência
            df_paralimp = df[df[col_def].fillna("") != "Não possui deficiência/transtorno"]
            df_olimp = df[df[col_def].fillna("") == "Não possui deficiência/transtorno"]

            # manter apenas as colunas finais
            df_paralimp = df_paralimp[colunas_final]
            df_olimp = df_olimp[colunas_final]

            # aplicar seleção
            par_final = selecionar_alunos(df_paralimp)
            olimp_final = selecionar_alunos(df_olimp)

            # exportar somente colunas desejadas e na ordem
            par_final_out = par_final[colunas_final].copy()
            olimp_final_out = olimp_final[colunas_final].copy()

            # Substituir NaN na coluna de tempo por string vazia
            par_final_out[col_tempo] = par_final_out[col_tempo].fillna("")
            olimp_final_out[col_tempo] = olimp_final_out[col_tempo].fillna("")

            # MOSTRAR NA TELA
            st.subheader("Alunos selecionados - Paralimpíada")
            st.dataframe(par_final_out.reset_index(drop=True), use_container_width=True)

            st.subheader("Alunos selecionados - Olimpíada")
            st.dataframe(olimp_final_out.reset_index(drop=True), use_container_width=True)

            # BOTÕES DE DOWNLOAD (CSV)
            par_csv = par_final_out.to_csv(index=False, encoding="utf-8").encode("utf-8")
            olimp_csv = olimp_final_out.to_csv(index=False, encoding="utf-8").encode("utf-8")

            st.download_button("Baixar Paralimpíada.csv", data=par_csv, file_name="Paralimpiada.csv", mime="text/csv")
            st.download_button("Baixar Olimpíada.csv", data=olimp_csv, file_name="Olimpiada.csv", mime="text/csv")

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
