# Nebula Dashboard
## Desafio criar dashboard
### Tabela de conteúdos
=================
<!--ts-->
  * [Tecnologias utilizadas](#Tecnologias)
  * [Arquitetura](#Arquitetura)
  * [Google Sheets](#Google-Sheets)
  * GCP(Ambiente de produção)
    * [Jupyter Notebook](#Jupyter-Notebook)
    * [Cloud Storage](#Cloud-Storage)
    * [BigQuery](#BigQuery) 
    * [Dashboard](#Dashboard)
<!--te-->
### Tecnologias

As seguintes ferramentas foram usadas na resolução dos questionamentos:

- Jupyter
- Anaconda
- Pandas 
- Python
- SQL
- Drawio
- Google Cloud Platform

### Arquitetura
![image](https://user-images.githubusercontent.com/73916591/229174086-f51dd495-410f-48b0-b696-4f8db3353f77.png)

# Google Sheets
criei uma tabela com as metas e o valor investido para utilizar como base de dados no meu dashboard

![image](https://user-images.githubusercontent.com/73916591/229195358-7fa8e852-be6e-4135-836b-413af9f1fa7f.png)


# GCP(Ambiente de produção)

# Jupyter Notebook

Aqui estou importando as bibliotecas que usarei durante o meu código e a chave de autenticação do google cloud
```python
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
```
Agora estou criando um código para me informar que horas o meu script começou
```python
# -*- coding:utf-8 -*-
#Gera a data e hora de São Paulo Brasil
tz_BR = pytz.timezone('America/Sao_Paulo')
#Gera a data atual em formato Timestamp
start = DT.datetime.strftime(DT.datetime.now(tz_BR),'%Y-%m-%d %H:%M:%S')
print("Processo iniciado em: "+start)
```

Pego minha database que está em csv e transformo em um dataframe pandas para manipular os dados depois chamo a função dtypes para saber
o formato das minhas colounas

```python
df_dealslist = pd.read_csv('C:/Users/caior_op46gft/Desktop/teste seazone/Teste BD - deals list.csv')
df_dealslist.dtypes
```
![image](https://user-images.githubusercontent.com/73916591/229186590-749d50cc-7889-4415-97cd-d2f8b33eb4de.png)

Como visto na imagem todas as colunas estão em formato string, então agora terei que transformar as colunas com datas para o formato ideal

```python
#converte as colunas que continham datas no formato string para o formato data
df_dealslist['Data de MQL'] = pd.to_datetime(df_dealslist['Data de MQL'])
df_dealslist['Data de SQL'] = pd.to_datetime(df_dealslist['Data de SQL'])
df_dealslist['Data de Opp'] = pd.to_datetime(df_dealslist['Data de Opp'])
df_dealslist['Data de Won'] = pd.to_datetime(df_dealslist['Data de Won'])
df_dealslist.dtypes
```
Aqui faço um fitlro através de uma query para selecionar somente os leads que iniciaram em fevereiro 
do dia 01/02 até 21/02

```python
query = '''
   SELECT * FROM df_dealslist WHERE strftime('%Y', [Data de MQL]) = '2023' AND strftime('%m', [Data de MQL]) = '02'
   AND strftime('%d', [Data de MQL]) <= '21'
'''
resultado = sqldf(query)
df_dealslist = resultado
```

crio uma query para fazer o calculo das metricas solicitadas: tx de progressão, custo p/ lead, mtd e realizado após isso 
armazeno os resultados em um dataframe

```python
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
```
Depois de criar os meus dataframes dealslist e metricas eu irei armazena-los em um repositorio na minha maquina local

```python
PATH = r"\fevereiro_20230221"
if not os.path.exists(PATH):
    os.makedirs(PATH)

# Salva o arquivo na pasta
df_dealslist.to_csv(os.path.join(PATH, "dealslist.csv"), index=False)
df_metricas.to_csv(os.path.join(PATH, "metricas.csv"), index=False)
```

![image](https://user-images.githubusercontent.com/73916591/229191207-81fe8956-3d53-4960-9fba-70ec24318781.png)

como visto na imagem acima o código funcionou!

Agora armazenarei esses dataframes em um bucket no cloud storage do gcp (google cloud plataform)


```python
# Define o nome do bucket e o prefixo da pasta
bucket_name = "teste-seazone"
PATH_SAVE = "leads_midia_paga/fevereiro/20230221/"
file_names = [f"{PATH}\dealslist.csv", f"{PATH}\metricas.csv"]

# Cria um cliente do Cloud Storage
client = storage.Client()

# Define o bucket
bucket = client.bucket(bucket_name)

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
```

Depois crio uma tabela no Big Query do gcp com os meus dataframes para depois utilizar como fonte de dados na minha dashboard

```python
#Cria tb_dealslist no Big Query
PROJECT_ID = "projetinhos-382019"
DATASET = "core_seazone"
TB_DEALSLIST = "tb_dealslist"
table_id = PROJECT_ID+"."+DATASET+"."+TB_DEALSLIST
print("==== Criando e Carregando Tabela "+table_id+" no bigquery ====")
pandas_gbq.to_gbq(df, table_id, project_id=PROJECT_ID, if_exists='replace') #Se existir, usar "replace" or "append" 
print("==== "+table_id+" Criada e carregada com sucesso! ====")

#Cria tb_metricas no Big Query
PROJECT_ID = "projetinhos-382019"
DATASET = "core_seazone"
TB_METRICAS = "tb_metricas"
table_id = PROJECT_ID+"."+DATASET+"."+TB_METRICAS
print("==== Criando e Carregando Tabela "+table_id+" no bigquery ====")
pandas_gbq.to_gbq(df, table_id, project_id=PROJECT_ID, if_exists='replace') #Se existir, usar "replace" or "append" 
print("==== "+table_id+" Criada e carregada com sucesso! ====")   
```

código para me informar que horas o meu script terminou
```python
#Gera a data e hora de São Paulo Brasil
tz_BR = pytz.timezone('America/Sao_Paulo')
#Gera a data atual em formato Timestamp
start = DT.datetime.strftime(DT.datetime.now(tz_BR),'%Y-%m-%d %H:%M:%S')
print("Processo finalizado em: "+start)
```
# Cloud Storage

![image](https://user-images.githubusercontent.com/73916591/229195672-9000fd67-2d12-4708-84eb-20d394563f47.png)

# BigQuery

![image](https://user-images.githubusercontent.com/73916591/229195936-5bfc3330-f048-437d-aa50-de4d833c06fe.png)

# Dashboard

![image](https://github.com/CaioRodSousa/nebula_dashboard/assets/73916591/106ecffb-8de3-4807-8314-c5a34f0d37f2)

Nota-se que utilizo a planiliha criada no google sheets e os dataframes importados para o bigquery anteriormente como base de dados

![image](https://github.com/CaioRodSousa/nebula_dashboard/assets/73916591/defd14ac-9a91-4a9e-b555-4cc8877c76eb)

https://lookerstudio.google.com/reporting/0980d664-09c8-40e7-a5cc-1854c4a3ec00
