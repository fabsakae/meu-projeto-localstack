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
# NO ARQUIVO grava_db.py (Adicione esta lógica antes da função lambda_handler)
# Certifique-se de manter as importações no topo (json, boto3, etc.)

# Funções Auxiliares para API Gateway (Adicione estas ao arquivo)
def handle_get_request(event):
    # LÓGICA DE GET: SCAN no DynamoDB para retornar todos os itens
    try:
        # Nota: O Boto3 precisa ser inicializado localmente se não for global
        dynamodb = boto3.resource('dynamodb', endpoint_url='http://host.docker.internal:4566', region_name='us-east-1')
        table = dynamodb.Table('NotasFiscais')
        
        response = table.scan()
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response['Items']) # Retorna os dados do DynamoDB
        }
    except Exception as e:
        logger.error(f"Erro ao consultar DynamoDB: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Erro interno ao consultar dados.'})
        }

def handle_post_request(event):
    # LÓGICA DE POST: Insere um único registro do payload JSON
    try:
        dynamodb = boto3.resource('dynamodb', endpoint_url='http://host.docker.internal:4566', region_name='us-east-1')
        table = dynamodb.Table('NotasFiscais')

        # O payload do API Gateway vem como uma string JSON no 'body'
        data = json.loads(event['body'])
        
        # O campo 'valor' é float, precisamos convertê-lo para String/Decimal (Serialização)
        if 'valor' in data and not isinstance(data['valor'], str):
            data['valor'] = str(data['valor'])
        
        table.put_item(Item=data)

        return {
            'statusCode': 201,
            'body': json.dumps({'message': 'Nota fiscal registrada via API com sucesso.'})
        }
    except Exception as e:
        logger.error(f"Erro no POST API: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Erro ao processar o POST.'})
        }


# Modifique a função principal lambda_handler para incluir o roteamento:
def lambda_handler(event, context):
    
    # ----------------------------------------------------
    # LÓGICA DE ROTEAMENTO: Verifica se é uma chamada HTTP
    # ----------------------------------------------------
    if 'httpMethod' in event:
        http_method = event['httpMethod']
        
        if http_method == 'GET':
            return handle_get_request(event)
        
        elif http_method == 'POST':
            return handle_post_request(event)
            
        else:
            return {'statusCode': 405, 'body': json.dumps({'message': f'Método {http_method} não suportado!'})}

    # ----------------------------------------------------
    # LÓGICA DE PROCESSAMENTO S3 (Se a chamada NÃO for HTTP)
    # ----------------------------------------------------
    
    # ... O restante do seu código S3 que você já tem (leitura, loop, put_item) deve vir aqui ...
    
    # Se for um evento S3, você deve retornar a resposta padrão
    return {
        'statusCode': 200,
        'body': json.dumps('Processamento concluído com sucesso!')
    }
