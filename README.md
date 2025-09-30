# Meu Projeto LocalStack
## Setup de Ambiente
1. Iniciar LocalStack: localstack start
2. Configurar credenciais (awslocal configure): use 'test' e 'us-east-1'
# meu-projeto-localstack
## 🚀 Setup e Configuração do LocalStack (Emulador AWS)

Este projeto utiliza o LocalStack para emular os serviços da AWS localmente via Docker no WSL/Ubuntu.

### Pré-requisitos
Certifique-se de que o **Docker Engine** e o **WSL Ubuntu** estão instalados e em execução.

### 1. Instalação do LocalStack CLI e Ferramentas AWS
Usamos o LocalStack CLI e o `awslocal` (um wrapper do AWS CLI) para interagir com o emulador.

1.  **Baixar e Instalar o LocalStack CLI:**
    ```bash
    # Baixa o binário
    curl --output localstack-cli-4.8.1-linux-amd64-onefile.tar.gz \
         --location [https://github.com/localstack/localstack-cli/releases/download/v4.8.1/localstack-cli-4.8.1-linux-amd64-onefile.tar.gz](https://github.com/localstack/localstack-cli/releases/download/v4.8.1/localstack-cli-4.8.1-linux-amd64-onefile.tar.gz)

    # Extrai o binário para o PATH
    sudo tar xvzf localstack-cli-4.8.1-linux-*-onefile.tar.gz -C /usr/local/bin
    ```
<img width="1360" height="768" alt="baixar_localSTACK" src="https://github.com/user-attachments/assets/3f938a1e-8cfd-459c-8cf4-0e9959fcfa15" />

2.  **Instalar o AWS CLI e o awslocal via pipx:**
    Instalamos o `pipx` e as ferramentas CLI do Python em um ambiente isolado:
    ```bash
    # Instala pipx e garante que ele está no PATH
    sudo apt install pipx python3-pip -y
    pipx ensurepath 

    # Instala o AWS CLI (binário 'aws')
    pipx install awscli

    # Instala o awslocal (binário 'awslocal')
    pipx install awscli-local
    ```
<img width="1360" height="768" alt="awslocal" src="https://github.com/user-attachments/assets/9d21b5d6-585b-420d-ba61-6c8ae7ac8e3e" />

### 2. Iniciando o LocalStack

Inicie o emulador LocalStack em uma aba do terminal. Ele fará o download da imagem Docker e iniciará os serviços.

```bash
localstack start
```
3. Configuração Inicial do AWS CLI Local
Configure o awslocal para usar credenciais de mock, necessárias para o emulador:
```bash
awslocal configure


 AWS Access Key ID: test
 AWS Secret Access Key: test
 Default region name: us-east-1
 Default output format: json
```
4. Testando a Conexão
Confirme que a conexão com o S3 está ativa:
<img width="1328" height="587" alt="localstakc_running" src="https://github.com/user-attachments/assets/c49b8313-15b6-44bc-81e4-8cbdc325a93b" />

Bash

5. Criar o Bucket notas-fiscais-upload
Será usado para receber os arquivos, acionando o Lambda.

```bash
awslocal s3 mb s3://notas-fiscais-upload
awslocal s3 ls
```
6. DynamoDB - Criar a Tabela NotasFiscais
Esta tabela armazenará os dados processados.

```bash
awslocal dynamodb create-table \
    --endpoint-url=http://localhost:4566 \
    --table-name NotasFiscais \
    --attribute-definitions AttributeName=Id,AttributeType=S \
    --key-schema AttributeName=Id,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```
**Verifica a criação da tabela**
```bash
awslocal dynamodb list-tables --endpoint-url=http://localhost:4566
```
7. Criar o IAM Role (Permissão)
```bash
awslocal iam create-role \
    --role-name lambda-role \
    --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
```

8. Criar e Compactar os Arquivos Python, arquivos grava_db.py, gerar_dados.py

Passo A: Criar o Script Auxiliar (gerar_dados.py)
Este script é usado apenas para criar o arquivo JSON de teste que será enviado ao S3.
```bash
cat << EOF > gerar_dados.py
import json
import random
from random import randint, uniform, choice
from datetime import datetime, timedelta

def random_date():
    today = datetime.now()
    days_ago = randint(1, 30)
    random_date = today - timedelta(days=days_ago)
    return random_date.strftime("%Y-%m-%d")

clientes = ["João Silva", "Maria Oliveira", "Carlos Santos", "Ana Costa", "Pedro Lima"]

registros = []
for i in range(10):
    registro = {
        "Id": f"NF-{i+1}",
        "cliente": choice(clientes),
        "valor": round(uniform(100.0, 5000.0), 2),
        "data_emissao": random_date()
    }
    registros.append(registro)

with open("notas_fiscais.json", "w", encoding="utf-8") as f:
    json.dump(registros, f, indent=4, ensure_ascii=False)

print("Arquivo 'notas_fiscais.json' gerado com sucesso!")
EOF
```
Passo B: Criar a Função Lambda (grava_db.py)
```bash
at << EOF > grava_db.py
import json
import boto3
import logging
from datetime import datetime

 # Configuração do Logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

	# Configuração da Tabela DynamoDB
TABLE_NAME = 'NotasFiscais'
 # Adicionando a região para garantir que não procure no DNS global
dynamodb = boto3.resource('dynamodb')
     # Garante o endpoint para Boto3 resource

 #Funções auxiliares (validação e mover arquivo)
def validar_registro(registro):
    # Simplificado: no código do professor, esta função faz validações
    if 'Id' in registro and 'cliente' in registro:
        return True, "Registro válido"
    return False, "Registro inválido: falta Id ou cliente"

def mover_arquivo_s3(s3_client, bucket, key, destino):
    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        # Extrai somente o nome do arquivo sem o caminho
        nome_arquivo = key.split('/')[-1]
        novo_key = f"{destino}/{timestamp}_{nome_arquivo}"
        logger.info(f"Movendo arquivo para: s3://{bucket}/{novo_key}")

        # Copia e deleta o arquivo original
        s3_client.copy_object(
            Bucket=bucket,
            CopySource={'Bucket': bucket, 'Key': key},
            Key=novo_key
        )
        s3_client.delete_object(Bucket=bucket, Key=key)
    except Exception as e:
        logger.error(f"Erro ao mover o arquivo no S3: {str(e)}")

 #Função principal do Lambda
def lambda_handler(event, context):
    # CLIENTE S3:
    s3 = boto3.client('s3')    
    table = dynamodb.Table(TABLE_NAME)
    
    for record in event.get('Records', []):
        s3_bucket = record['s3']['bucket']['name']
        s3_key = record['s3']['object']['key']
        
        logger.info(f"Processando arquivo: s3://{s3_bucket}/{s3_key}")
        
        try:
            # 1. Ler o arquivo do S3
            response = s3.get_object(Bucket=s3_bucket, Key=s3_key)
            file_content = response['Body'].read().decode('utf-8')
            
            # 2. Carregar o conteúdo como JSON
            try:
                registros = json.loads(file_content)
                logger.info(f"Arquivo JSON carregado com sucesso. Total de registros: {len(registros)}")
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao decodificar o JSON: {str(e)}")
                mover_arquivo_s3(s3, s3_bucket, s3_key, "erro")
                continue # Pula para o próximo registro S3

            # 3. Processar e Inserir no DynamoDB
            for registro in registros:
                valido, mensagem = validar_registro(registro)
                if not valido:
                    logger.warning(f"Registro inválido: {mensagem}")
                    continue

                try:
                    logger.info(f"Inserindo registro no DynamoDB: {registro}")
        
                     # **CORREÇÃO CRÍTICA: Converta o float para String**
                    if 'valor' in registro and not isinstance(registro['valor'], str):
                        registro['valor'] = str(registro['valor'])
        
                    table.put_item(Item=registro)
                    logger.info("Registro inserido com sucesso!")
                except Exception as e:
                    logger.error(f"Erro ao inserir registro no DynamoDB: {str(e)}")
                    mover_arquivo_s3(s3, s3_bucket, s3_key, "erro")
                    break # Interrompe o processamento deste arquivo

            # 4. Mover arquivo para pasta de sucesso
            mover_arquivo_s3(s3, s3_bucket, s3_key, "sucesso")

        except Exception as e:
            logger.error(f"Erro inesperado ao processar o arquivo: {str(e)}")
            mover_arquivo_s3(s3, s3_bucket, s3_key, "erro")
            continue
            
    return {
        'statusCode': 200,
        'body': json.dumps('Processamento concluído com sucesso!')
    }

 # Configuração do Logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

 # Configuração da Tabela DynamoDB
TABLE_NAME = 'NotasFiscais'
dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:4566') # Garante o endpoint para Boto3 resource

 # Funções auxiliares (validação e mover arquivo)
def validar_registro(registro):
    # Simplificado: no código do professor, esta função faz validações
    if 'Id' in registro and 'cliente' in registro:
        return True, "Registro válido"
    return False, "Registro inválido: falta Id ou cliente"

def mover_arquivo_s3(s3_client, bucket, key, destino):
    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        # Extrai somente o nome do arquivo sem o caminho
        nome_arquivo = key.split('/')[-1]
        novo_key = f"{destino}/{timestamp}_{nome_arquivo}"
        logger.info(f"Movendo arquivo para: s3://{bucket}/{novo_key}")

        # Copia e deleta o arquivo original
        s3_client.copy_object(
            Bucket=bucket,
            CopySource={'Bucket': bucket, 'Key': key},
            Key=novo_key
        )
        s3_client.delete_object(Bucket=bucket, Key=key)
    except Exception as e:
        logger.error(f"Erro ao mover o arquivo no S3: {str(e)}")

 # Função principal do Lambda
def lambda_handler(event, context):
    s3 = boto3.client('s3', endpoint_url='http://localhost:4566') # Garante o endpoint para Boto3 client
    table = dynamodb.Table(TABLE_NAME)
    
    for record in event.get('Records', []):
        s3_bucket = record['s3']['bucket']['name']
        s3_key = record['s3']['object']['key']
        
        logger.info(f"Processando arquivo: s3://{s3_bucket}/{s3_key}")
        
        try:
            # 1. Ler o arquivo do S3
            response = s3.get_object(Bucket=s3_bucket, Key=s3_key)
            file_content = response['Body'].read().decode('utf-8')
            
            # 2. Carregar o conteúdo como JSON
            try:
                registros = json.loads(file_content)
                logger.info(f"Arquivo JSON carregado com sucesso. Total de registros: {len(registros)}")
            except json.JSONDecodeError as e:
                logger.error(f"Erro ao decodificar o JSON: {str(e)}")
                mover_arquivo_s3(s3, s3_bucket, s3_key, "erro")
                continue # Pula para o próximo registro S3

            # 3. Processar e Inserir no DynamoDB
            for registro in registros:
                valido, mensagem = validar_registro(registro)
                if not valido:
                    logger.warning(f"Registro inválido: {mensagem}")
                    continue

                try:
                    logger.info(f"Inserindo registro no DynamoDB: {registro}")
                    table.put_item(Item=registro)
                    logger.info("Registro inserido com sucesso!")
                except Exception as e:
                    logger.error(f"Erro ao inserir registro no DynamoDB: {str(e)}")
                    mover_arquivo_s3(s3, s3_bucket, s3_key, "erro")
                    break # Interrompe o processamento deste arquivo

            # 4. Mover arquivo para pasta de sucesso
            mover_arquivo_s3(s3, s3_bucket, s3_key, "sucesso")

        except Exception as e:
            logger.error(f"Erro inesperado ao processar o arquivo: {str(e)}")
            mover_arquivo_s3(s3, s3_bucket, s3_key, "erro")
            continue
            
    return {
        'statusCode': 200,
        'body': json.dumps('Processamento concluído com sucesso!')
    }

EOF
```

Passo C: Compactar a Lambda
Arquivo ZIP que será enviado no deploy:

```Bash

zip lambda_function.zip grava_db.py
```


9. Gerar o Arquivo de Teste
```bash
python gerar_dados.py
```

