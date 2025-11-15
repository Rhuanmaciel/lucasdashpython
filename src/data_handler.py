import pandas as pd
import os

def load_data():
    data_path = os.path.join(os.getcwd())
    
    df_atendimento = pd.read_excel(os.path.join(data_path, 'base_atendimento_ecomove.xlsx'))
    df_clientes = pd.read_excel(os.path.join(data_path, 'base_clientes_ecomove.xlsx'))
    df_financeiro = pd.read_excel(os.path.join(data_path, 'base_financeiro_ecomove.xlsx'), decimal=',')
    df_marketing = pd.read_excel(os.path.join(data_path, 'base_marketing_ecomove.xlsx'))
    df_vendas = pd.read_excel(os.path.join(data_path, 'base_vendas_ecomove.xlsx'))

    # Convert date columns to datetime objects
    df_atendimento['Data_Abertura'] = pd.to_datetime(df_atendimento['Data_Abertura'])
    df_clientes['Data_Cadastro'] = pd.to_datetime(df_clientes['Data_Cadastro'])
    df_financeiro['Mês'] = pd.to_datetime(df_financeiro['Mês'])
    df_marketing['Data_Campanha'] = pd.to_datetime(df_marketing['Data_Campanha'])
    df_vendas['Data_Venda'] = pd.to_datetime(df_vendas['Data_Venda'])

    return df_atendimento, df_clientes, df_financeiro, df_marketing, df_vendas
