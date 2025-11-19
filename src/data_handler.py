import pandas as pd
import unicodedata
import os


def remove_acentos(txt):
    if pd.isna(txt):
        return None
    return ''.join(
        c for c in unicodedata.normalize('NFD', str(txt))
        if unicodedata.category(c) != 'Mn'
    )


def load_nome_base(data_path):
    """
    Carrega nomes.csv e cria mapa: primeiro_nome_sem_acentos → F/M
    """

    try:
        nome_arquivo = os.path.join(data_path, "nomes.csv")
        df_nomes = pd.read_csv(nome_arquivo)

        df_nomes["first_name"] = (
            df_nomes["first_name"]
            .astype(str)
            .str.lower()
            .str.strip()
            .apply(remove_acentos)
        )

        mapa_nomes = dict(zip(df_nomes["first_name"], df_nomes["classification"]))

        return mapa_nomes

    except Exception as e:
        print("⚠ Erro ao carregar nomes.csv:", e)
        return {}

def inferir_genero_por_nome(nome, mapa):
    if pd.isna(nome):
        return None

    primeiro = str(nome).split()[0].lower()
    primeiro = remove_acentos(primeiro)

    genero = mapa.get(primeiro)

    if genero == "M":
        return "Masculino"
    if genero == "F":
        return "Feminino"

    return None

def normalizar_genero(df, mapa_nomes):

    df["Gênero"] = df["Gênero"].replace({
        "Masculino": "Masculino",
        "Feminino": "Feminino",
        "M": "Masculino",
        "F": "Feminino",
        "m": "Masculino",
        "f": "Feminino"
    })

    df["Genero_Inferido"] = df["Nome"].apply(
        lambda x: inferir_genero_por_nome(x, mapa_nomes)
    )

    def resolver(row):
        if row["Genero_Inferido"] and row["Genero_Inferido"] != row["Gênero"]:
            return row["Genero_Inferido"]
        return row["Gênero"]

    df["Gênero"] = df.apply(resolver, axis=1)

    df.drop(columns=["Genero_Inferido"], inplace=True)

    return df

def load_data():
    data_path = os.getcwd()

    df_atendimento = pd.read_excel(os.path.join(data_path, 'base_atendimento_ecomove.xlsx'))
    df_clientes = pd.read_excel(os.path.join(data_path, 'base_clientes_ecomove.xlsx'))
    df_financeiro = pd.read_excel(os.path.join(data_path, 'base_financeiro_ecomove.xlsx'), decimal=',')
    df_marketing = pd.read_excel(os.path.join(data_path, 'base_marketing_ecomove.xlsx'))
    df_vendas = pd.read_excel(os.path.join(data_path, 'base_vendas_ecomove.xlsx'))

    df_atendimento['Data_Abertura'] = pd.to_datetime(df_atendimento['Data_Abertura'], errors='coerce')
    df_clientes['Data_Cadastro'] = pd.to_datetime(df_clientes['Data_Cadastro'], errors='coerce')
    df_financeiro['Mês'] = pd.to_datetime(df_financeiro['Mês'], errors='coerce')
    df_marketing['Data_Campanha'] = pd.to_datetime(df_marketing['Data_Campanha'], errors='coerce')
    df_vendas['Data_Venda'] = pd.to_datetime(df_vendas['Data_Venda'], errors='coerce')

    mapa_nomes = load_nome_base(data_path)
    df_clientes = normalizar_genero(df_clientes, mapa_nomes)

    return df_atendimento, df_clientes, df_financeiro, df_marketing, df_vendas
