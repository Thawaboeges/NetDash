
   # 📊 NetDash: Dashboard de Tráfego de Servidor em Tempo Real (CSV + Excel)
   
   Este projeto captura pacotes de rede de um servidor específico (`SERVER_IP`), agrega o tráfego em janelas de 5 segundos e salva em um arquivo CSV.  
   O arquivo pode ser consumido no Excel para montar um dashboard interativo com **drill-down**.
   
   ---
   
   ## ⚙️ 1. Instalação do Python
   
   ### Windows
   1. Baixe e instale o **Python 3.10+** em: [python.org/downloads](https://www.python.org/downloads)
   2. Durante a instalação, marque a opção **“Add Python to PATH”**.
   3. Para confirmar, abra o Prompt de Comando e digite:
      ```bash
      python --version
   ### Linux/Mac
   Normalmente o Python já vem instalado. Para confirmar:
     
     python3 --version**
   
      
   ## 📦 2. Instalação das Bibliotecas
   No terminal/prompt, execute dentro da pasta do projeto:
   
  
   pip install scapy pandas tqdm
   ⚠️ Windows: instale também o Npcap em modo compatível com WinPcap para permitir captura de pacotes.
   
   ### 🛠️ 3. Configuração do Script
   Arquivo principal: traffic_capture.py
   
   No início do código, existe esta linha:
   
   SERVER_IP = " "
   ➡️ Troque " " pelo IP do servidor que você deseja monitorar.
   
   Ajuste o tamanho da janela em segundos (opcional):
   
   python
   Copiar código
   WINDOW_SIZE = 5
   ### ▶️ 4. Executando o Script
   No terminal/prompt, vá até a pasta do projeto e rode:
   

   python traffic_capture.py
   Windows: abra o Prompt de Comando como Administrador
   
   Linux/Mac: rode com sudo se necessário
   
   O script irá:
   
   Capturar pacotes relacionados ao SERVER_IP
   
   Agregar em janelas de 5 segundos
   
   Salvar os resultados no arquivo traffic.csv
   
   Para encerrar, use Ctrl + C.
   
   ### 📂 5. Estrutura do CSV
   Cada linha do traffic.csv terá as colunas:
   
 
   window_start, window_end, client_ip, direction, total_bytes, http_bytes, ftp_bytes, tcp_bytes, udp_bytes, other_bytes
   window_start / window_end: início e fim da janela (timestamp legível)
   
   client_ip: IP do cliente conectado ao servidor
   
   direction: "in" (entrada) ou "out" (saída)
   
   *_bytes: quantidade de bytes por protocolo
   
   ### 📈 6. Criando o Dashboard no Excel
   Passo 1: Importar o CSV
   Abra o Excel
   
   Vá em Dados → Obter Dados → De Arquivo → De Texto/CSV
   
   Selecione traffic.csv e clique em Carregar
   
  # Passo 2: Criar uma Tabela Dinâmica
   Inserir → Tabela Dinâmica
   
   Configure assim:
   
   Linhas: window_start
   
   Colunas: client_ip (ou protocolo)
   
   Valores: total_bytes
   
   # Passo 3: Gráfico Empilhado
   Selecione a Tabela Dinâmica
   
   Vá em Inserir → Gráfico de Colunas → Coluna Empilhada
   
   Cada barra representará o tráfego total, dividido por protocolo
   
   # Passo 4: Drill-down com Slicers
   Clique na Tabela Dinâmica
   
   Vá em Analisar → Inserir Segmentação de Dados
   
   Escolha client_ip e/ou direction
   
   Agora você pode clicar em um cliente e ver apenas os dados dele (drill-down)
   
   # Passo 5: Atualizar Dados
   Clique com o botão direito na Tabela Dinâmica → Atualizar
   
   O Excel vai recarregar os dados mais recentes do traffic.csv
   
   ### 🧪 7. Testes e Solução de Problemas Comuns
   🔹 Como Testar Rapidamente
   Configure o IP local no arquivo traffic_capture.py:
   

   SERVER_IP = "127.0.0.1"
   Execute o script:
   ```bash
      python traffic_capture.py
```

Em outro terminal, gere tráfego de teste com um ping contínuo:
   

   ping 127.0.0.1 -t   # Windows
   ping 127.0.0.1      # Linux/Mac (Ctrl+C para parar)
   Verifique o traffic.csv: os pacotes de ping aparecerão no protocolo "OTHER"
   
   ⚠️ Problemas Comuns
   O script não captura nenhum pacote / CSV vazio:
   
   Permissões: execute como Administrador (Windows) ou com sudo (Linux/Mac)
   
   IP do servidor configurado incorretamente
   
   Firewall bloqueando a captura de pacotes
   
   Erro ModuleNotFoundError:
   
   As bibliotecas não foram instaladas corretamente
   
   Rode novamente:
   
   pip install scapy pandas tqdm
   Erro de Permissão ao salvar traffic.csv:
   
   O arquivo pode estar aberto no Excel
   
   Feche o arquivo e o script continuará gravando normalmente
   
   ### ✅ Padrões Adotados
   PEP 8: estilo de código Python
   
   PEP 257: docstrings completas
   
   Producer-Consumer Pattern:
   
   Producer: process_packet()
   
   Consumer: writer_thread()










