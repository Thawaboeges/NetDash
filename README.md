
#  📊 Dashboard de Tráfego de Servidor em Tempo Real (CSV + Excel)
Este projeto captura pacotes de rede de um servidor específico (SERVER_IP), agrega o tráfego em janelas de 5 segundos e salva em um arquivo CSV.
O arquivo pode ser consumido no Excel para montar um dashboard interativo com drill-down.

#  ⚙️ 1. Instalação do Python
#  Windows
1. Baixe e instale o Python 3.10+ em: python.org/downloads
2. Durante a instalação, marque a opção “Add Python to PATH”.
3. Para confirmar, abra o Prompt de Comando e digite:
python --version

#  Linux/Mac
Normalmente o Python já vem instalado. Para confirmar:

python3 --version
#  📦 2. Instalação das Bibliotecas
No terminal/prompt, execute dentro da pasta do projeto:

pip install scapy pandas tqdm
⚠️ Windows: instale também o Npcap em modo compatível com WinPcap para permitir captura de pacotes.

# 🛠️ 3. Configuração do Script
Arquivo principal: traffic_capture.py

Existe essa linha no início do código:

SERVER_IP = "  "
➡️ Troque " " pelo IP do servidor que você deseja monitorar.

Ajuste o tamanho da janela em segundos (opcional):

WINDOW_SIZE = 5
▶️ 4. Executando o Script
No terminal/prompt, vá até a pasta do projeto e rode:

python traffic_capture.py
No Windows: abra o Prompt de Comando como Administrador

No Linux/Mac: rode com sudo se necessário

O script irá:

Capturar pacotes relacionados ao SERVER_IP

Agregar em janelas de 5 segundos

Salvar os resultados no arquivo traffic.csv

Para encerrar, use Ctrl + C.

📂 5. Estrutura do CSV
Cada linha do traffic.csv terá as colunas:

window_start, window_end, client_ip, direction, total_bytes, http_bytes, ftp_bytes, tcp_bytes, udp_bytes, other_bytes
window_start / window_end: início e fim da janela (timestamp legível)

client_ip: IP do cliente conectado ao servidor

direction: "in" (entrada) ou "out" (saída)

*_bytes: quantidade de bytes por protocolo

📈 6. Criando o Dashboard no Excel
Passo 1: Importar o CSV

Abra o Excel

Vá em Dados → Obter Dados → De Arquivo → De Texto/CSV

Selecione traffic.csv e clique em Carregar

Passo 2: Criar uma Tabela Dinâmica

Inserir → Tabela Dinâmica

Configure assim:

Linhas: window_start

Colunas: client_ip (ou protocolo)

Valores: total_bytes

Passo 3: Gráfico Empilhado

Selecione a Tabela Dinâmica

Inserir → Gráfico de Colunas → Coluna Empilhada

Cada barra representa o tráfego total, dividido por protocolo
Passo 4: Drill-down com Slicers

Clique na Tabela Dinâmica

Vá em Analisar → Inserir Segmentação de Dados

Escolha client_ip e/ou direction

Agora você pode clicar em um cliente e ver apenas os dados dele (drill-down)
Passo 5: Atualizar Dados

Clique com o botão direito na Tabela Dinâmica → Atualizar

O Excel vai recarregar os dados mais recentes do traffic.csv

🧪 7. Testes e Solução de Problemas Comuns
Esta seção oferece um guia rápido para validar o funcionamento do script e solucionar os erros mais comuns.

Como Testar Rapidamente: Se você quer apenas validar se o script está funcionando corretamente no seu ambiente, pode fazer um teste local simples sem precisar de uma rede complexa.

Configure o IP local No arquivo traffic_capture.py, altere o SERVER_IP para o endereço de localhost, que aponta para a sua própria máquina: SERVER_IP = "127.0.0.1"

Execute o script Abra o Prompt de Comando como Administrador, navegue até a pasta do projeto e inicie o script normalmente: python traffic_capture.py

Gere tráfego de teste Abra uma segunda janela do Prompt de Comando (não precisa ser como Administrador) e inicie um comando de ping contínuo para a sua própria máquina: ping 127.0.0.1 -t

Verifique o resultado Deixe os dois terminais rodando. No terminal onde o script de captura está sendo executado, você verá mensagens informando que linhas estão sendo gravadas no arquivo traffic.csv. Após alguns segundos, você pode abrir o arquivo traffic.csv e verá os dados do tráfego de ping (protocolo "OTHER") sendo registrados.

⚠️ Problemas Comuns

O script não captura nenhum pacote ou o CSV fica vazio:

Permissões: Verifique se você executou o Prompt de Comando como Administrador no Windows.

IP do Servidor: Confirme se o SERVER_IP no topo do script está preenchido corretamente.

Firewall: Verifique se nenhum firewall está bloqueando a captura de pacotes.

Erro ModuleNotFoundError ao executar o script:

Isso indica que as bibliotecas não foram instaladas corretamente. Execute novamente o comando pip install scapy pandas tqdm no terminal, dentro da pasta do projeto.

Erro de Permissão ao Salvar o traffic.csv:

Se o script mostrar um PermissionError, verifique se o arquivo traffic.csv não está aberto no Excel ou em outro programa. O Windows muitas vezes acaba "travando" o arquivo enquanto ele está em uso, impedindo que o script escreva nele. Feche o arquivo e o script continuará a salvar os dados na próxima janela de tempo.

✅ Padrões Adotados
PEP 8: estilo de código Python

PEP 257: docstrings completas

Producer-Consumer Pattern:

Producer: process_packet()
Consumer: writer_thread()

