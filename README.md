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

