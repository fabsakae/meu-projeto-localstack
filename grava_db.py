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

