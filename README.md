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

Bash

# Cria um bucket de teste
awslocal s3 mb s3://s3

# Lista os buckets existentes
awslocal s3 ls
