#!/usr/bin/env python
# coding: utf-8

# In[2]:


# -*- coding:utf-8 -*-
import pandas as pd
import pytz
import datetime as DT
import os
import pandas_gbq
from pandasql import sqldf
from datetime import datetime
from google.cloud import storage
from google.cloud import bigquery

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="C:/Users/caior_op46gft/Desktop/teste seazone/projetinhos-382019-7575362a8e96.json"


# In[232]:


#Gera a data e hora de São Paulo Brasil
tz_BR = pytz.timezone('America/Sao_Paulo')
#Gera a data atual em formato Timestamp
start = DT.datetime.strftime(DT.datetime.now(tz_BR),'%Y-%m-%d %H:%M:%S')
print("Processo iniciado em: "+start)


# In[233]:


#Pego minha database que está em csv e transformo em um dataframe pandas para manipular os dados
df_dealslist = pd.read_csv('C:/Users/caior_op46gft/Desktop/teste seazone/Teste BD - deals list.csv')
df_dealslist


# In[234]:


df_dealslist.dtypes


# In[235]:


#converte as colunas que continham datas no formato string para o formato data
df_dealslist['Data de MQL'] = pd.to_datetime(df_dealslist['Data de MQL'])
df_dealslist['Data de SQL'] = pd.to_datetime(df_dealslist['Data de SQL'])
df_dealslist['Data de Opp'] = pd.to_datetime(df_dealslist['Data de Opp'])
df_dealslist['Data de Won'] = pd.to_datetime(df_dealslist['Data de Won'])
df_dealslist.dtypes


# In[236]:


#Aqui faço um fitlro através de uma query para selecionar somente os leads que iniciaram em fevereiro 
#do dia 01/02 até 21/02

query = '''
   SELECT * FROM df_dealslist WHERE strftime('%Y', [Data de MQL]) = '2023' AND strftime('%m', [Data de MQL]) = '02'
   AND strftime('%d', [Data de MQL]) <= '21'
'''
resultado = sqldf(query)
df_dealslist = resultado


# In[247]:


#crio uma query para fazer o calculo das metricas solicitadas: tx de progressão, custo p/ lead, mtd e realizado após isso 
#armazeno os resultados em um dataframe

query = '''
   SELECT COUNT("Data de MQL") AS "Total de MQL",
          COUNT("Data de SQL") AS "Total de SQL",
          COUNT("Data de Opp") AS "Total de Opp",
          COUNT("Data de Won") AS "Total de Won",
          
          COUNT("Data de MQL") * 100 / 350 AS "Porcentagem de MQL",
          COUNT("Data de SQL") * 100 / 120 AS "Porcentagem de SQL",
          COUNT("Data de Opp") * 100 / 102 AS "Porcentagem de Opp",
          COUNT("Data de Won") * 100 / 20  AS "Porcentagem de Won",
          
          COUNT("Data de SQL") * 100 / COUNT("Data de MQL") AS "tx% de conversao MQL",
          COUNT("Data de Opp") * 100 / COUNT("Data de SQL") AS "tx% de conversao SQL",
          COUNT("Data de Won") * 100 / COUNT("Data de Opp") AS "tx% de conversao Opp",
          
          6000.0 / COUNT("Data de MQL") AS "custo por lead MQL",
          6000.0 /  COUNT("Data de SQL") AS "custo por lead SQL",
          6000.0 / COUNT("Data de Opp") AS "custo por lead Opp",
          6000.0 / COUNT("Data de Won") AS "custo por lead Won"
   
   FROM df_dealslist
'''
resultado = sqldf(query)
df_metricas = resultado


# In[248]:


df_metricas


# In[224]:


df_dealslist


# In[225]:


PATH = r"\fevereiro_20230221"
if not os.path.exists(PATH):
    os.makedirs(PATH)

# Salva o arquivo na pasta
df_dealslist.to_csv(os.path.join(PATH, "dealslist.csv"), index=False)
df_metricas.to_csv(os.path.join(PATH, "metricas.csv"), index=False)


# In[226]:


# Define o nome do bucket e o prefixo da pasta
bucket_name = "teste-seazone"
PATH_SAVE = "leads_midia_paga/fevereiro/20230221/"
file_names = [f"{PATH}\dealslist.csv", f"{PATH}\metricas.csv"]


# In[227]:


# Cria um cliente do Cloud Storage
client = storage.Client()

# Define o bucket
bucket = client.bucket(bucket_name)


# In[228]:


# Loop através da lista de nomes de arquivos
for file_name in file_names:
    if file_name == f"{PATH}\dealslist.csv":
        # Cria um blob (arquivo) na pasta do bucket
        blob = bucket.blob(PATH_SAVE + "dealslist.csv")
    else:
        blob = bucket.blob(PATH_SAVE + "metricas.csv")
    
    # Carrega o arquivo CSV em um DataFrame
    df = pd.read_csv(file_name)

    # Salva o DataFrame como um arquivo CSV em um objeto bytes
    data = df.to_csv(index=False).encode()

    # Envia o objeto bytes para o blob
    blob.upload_from_string(data)


# In[ ]:


#Cria tb_dealslist no Big Query
PROJECT_ID = "projetinhos-382019"
DATASET = "core_seazone"
TB_DEALSLIST = "tb_dealslist"
table_id = PROJECT_ID+"."+DATASET+"."+TB_DEALSLIST
print("==== Criando e Carregando Tabela "+table_id+" no bigquery ====")
pandas_gbq.to_gbq(df, table_id, project_id=PROJECT_ID, if_exists='replace') #Se existir, usar "replace" or "append" 
print("==== "+table_id+" Criada e carregada com sucesso! ====")   


# In[ ]:


#Cria tb_metricas no Big Query
PROJECT_ID = "projetinhos-382019"
DATASET = "core_seazone"
TB_METRICAS = "tb_metricas"
table_id = PROJECT_ID+"."+DATASET+"."+TB_METRICAS
print("==== Criando e Carregando Tabela "+table_id+" no bigquery ====")
pandas_gbq.to_gbq(df, table_id, project_id=PROJECT_ID, if_exists='replace') #Se existir, usar "replace" or "append" 
print("==== "+table_id+" Criada e carregada com sucesso! ====")   


# In[3]:


#Gera a data e hora de São Paulo Brasil
tz_BR = pytz.timezone('America/Sao_Paulo')
#Gera a data atual em formato Timestamp
start = DT.datetime.strftime(DT.datetime.now(tz_BR),'%Y-%m-%d %H:%M:%S')
print("Processo finalizado em: "+start)


# In[ ]:




