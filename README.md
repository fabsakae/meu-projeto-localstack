# Meu Projeto LocalStack
## Setup de Ambiente
1. Iniciar LocalStack: localstack start
2. Configurar credenciais (awslocal configure): use 'test' e 'us-east-1'
# meu-projeto-localstack
##  Setup e Configuração do LocalStack (Emulador AWS)

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
<img width="990" height="405" alt="gravadb2" src="https://github.com/user-attachments/assets/3a203b45-53af-49b7-9e3c-2376a8f7f8e4" />

Passo C: Compactar a Lambda
Arquivo ZIP que será enviado no deploy:

```Bash

zip lambda_function.zip grava_db.py
```
<img width="888" height="686" alt="lambdafunction" src="https://github.com/user-attachments/assets/dc68341a-2021-4495-958a-5446bd5d4f9b" />


9. Deploy da função Lambda
Código de criação da função, ele irá carregar o lambda_function.zip e associá-lo ao IAM role.

```bash
awslocal lambda create-function \
    --function-name ProcessarNotasFiscais \
    --runtime python3.9 \
    --role arn:aws:iam::000000000000:role/lambda-role \
    --handler grava_db.lambda_handler \
    --zip-file fileb://lambda_function.zip \
    --endpoint-url http://localhost:4566
```
<img width="1351" height="688" alt="lambdapermission" src="https://github.com/user-attachments/assets/0c456da0-28a9-4156-8821-5a1f9a6f589f" />

10. Configurar o Trigger S3
Após o deploy da Lambda (que deve retornar um JSON grande de confirmação), configurar o S3 para chamar a Lambda:

A) Adicionar Permissão de Invocação
```bash
awslocal lambda add-permission --function-name ProcessarNotasFiscais --statement-id s3-trigger-permission \
    --action "lambda:InvokeFunction" --principal s3.amazonaws.com \
    --source-arn "arn:aws:s3:::notas-fiscais-upload" --endpoint-url http://localhost:4566
```
<img width="1341" height="80" alt="invocação" src="https://github.com/user-attachments/assets/a2972d83-d1c1-45a8-b659-df4ae10f645c" />

B) Configurar o Evento de Notificação (O Trigger)
```bash
awslocal s3api put-bucket-notification-configuration \
    --bucket notas-fiscais-upload \
    --notification-configuration '{"LambdaFunctionConfigurations": [
        {
            "Id": "s3-to-lambda-trigger",
            "LambdaFunctionArn": "arn:aws:lambda:us-east-1:000000000000:function:ProcessarNotasFiscais",
            "Events": ["s3:ObjectCreated:*"]
        }
    ]}' \
    --endpoint-url http://localhost:4566
```
<img width="977" height="193" alt="trigger" src="https://github.com/user-attachments/assets/e5f1647a-263f-4173-a3bc-86ed35059d84" />

11.  Gerar o Arquivo de Teste
criará o arquivo notas_fiscais.json no diretório.
```bash
python gerar_dados.py
```
12. Enviar o Arquivo para o S3 (Trigger)
```bash
awslocal s3 cp notas_fiscais.json s3://notas-fiscais-upload/notas_fiscais.json --endpoint-url http://localhost:4566
```
<img width="1347" height="685" alt="verificadadosdb" src="https://github.com/user-attachments/assets/dbc38201-008b-4e47-8f04-3697419ded76" />

13. Verificar os Resultados
DynamoDB: Verifica os 10 registros fictícios inseridos na tabela NotasFiscais.
```bash
awslocal dynamodb scan --table-name NotasFiscais --endpoint-url http://localhost:4566
```
<img width="1360" height="768" alt="verificadadosdn2" src="https://github.com/user-attachments/assets/516c4f1c-4710-4f34-9bda-f9999b8f6457" />

14. Criar a API
```bash
awslocal apigateway create-rest-api --name "NotasFiscaisAPI" --endpoint-url=http://localhost:4566
```
15. Criar o Recurso /notas
```bash
awslocal apigateway create-resource \
    --rest-api-id htdk2mzlhb \
    --parent-id yztdbq9eng \
    --path-part "notas" \
    --endpoint-url=http://localhost:4566
```

16. Configurar os Métodos POST e GET
## Implementar o Método POST: Configurar o método POST para enviar dados (que a Lambda processará ou salvará diretamente).


```bash
awslocal apigateway put-method \
    --rest-api-id htdk2mzlhb \
    --resource-id tzvlgl1y6w \
    --http-method POST \
    --authorization-type "NONE" \
    --endpoint-url=http://localhost:4566
```
A- Integrar o Método POST com a Lambda, este comando conecta o método POST à sua função Lambda ProcessarNotasFiscais.:

```bash
awslocal apigateway put-integration \
    --rest-api-id htdk2mzlhb \
    --resource-id tzvlgl1y6w \
    --http-method POST \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:000000000000:function:ProcessarNotasFiscais/invocations" \
    --endpoint-url=http://localhost:4566
```
## Implementar o Método GET: Configurar o método GET para buscar dados da tabela DynamoDB via Lambda.

```bash

awslocal apigateway put-method \
    --rest-api-id htdk2mzlhb \
    --resource-id tzvlgl1y6w \
    --http-method GET \
    --authorization-type "NONE" \
    --endpoint-url=http://localhost:4566
```
A-  Integrar o Método GET com a Lambda. A integração é a mesma do POST, pois a Lambda lidará com o roteamento
 ```bash
awslocal apigateway put-integration \
    --rest-api-id htdk2mzlhb \
    --resource-id tzvlgl1y6w \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:000000000000:function:ProcessarNotasFiscais/invocations" \
    --endpoint-url=http://localhost:4566
```
B- Conceder Permissão à API Gateway
Para que o API Gateway possa realmente chamar a sua função Lambda, precisa conceder a ele a permissão IAM necessária.

```Bash

awslocal lambda add-permission --function-name ProcessarNotasFiscais --statement-id apigateway-access-post \
    --action "lambda:InvokeFunction" \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:us-east-1:000000000000:htdk2mzlhb/*/POST/notas" \
    --endpoint-url=http://localhost:4566
```


C- Permissão de Invocação para o GET
```baSH
awslocal lambda add-permission --function-name ProcessarNotasFiscais --statement-id apigateway-access-get \
    --action "lambda:InvokeFunction" \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:us-east-1:000000000000:htdk2mzlhb/*/GET/notas" \
    --endpoint-url=http://localhost:4566
```
d- Implementar o Deploy da API
criar o deployment para tornar a API acessível publicamente (no LocalStack) no stage dev.

```Bash

awslocal apigateway create-deployment \
    --rest-api-id htdk2mzlhb \
    --stage-name dev \
    --endpoint-url=http://localhost:4566
```
17.  Testar o Método POST
```bash
curl -X POST \
     -H 'Content-Type: application/json' \
     -d '{"Id": "NF-API-01", "cliente": "Cliente Via API", "valor": 555.55, "data_emissao": "2025-09-30"}' \
     http://localhost:4566/restapis/htdk2mzlhb/dev/_user_request_/notas
```

