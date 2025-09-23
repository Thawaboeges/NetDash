# NetDash
# Dashboard de Análise de Tráfego de Servidor em Tempo Real

## 📌 Contexto
Este projeto tem como objetivo monitorar a carga de um servidor específico em tempo real.  
O sistema captura pacotes de rede, processa os dados e apresenta um **dashboard interativo** com gráficos dinâmicos de tráfego por cliente e por protocolo.

---

## 🚀 Funcionalidades
- Captura de tráfego em janelas de **5 segundos**.
- Exibição de volume de tráfego **entrada/saída por cliente (IP)**.
- **Drill down**: ao clicar em um cliente, mostra os protocolos utilizados.
- Interface moderna e responsiva.
- API RESTful para servir os dados de séries temporais.
- Tratamento de erros para evitar travamentos.

---

## 🛠️ Tecnologias Utilizadas
- **Backend**: Python (Scapy / FastAPI) ou outra linguagem à escolha.  
- **Frontend**: React + Recharts (ou outra lib de gráficos).  
- **Banco/Cache**: Redis ou memória local para agregação.  

---

## 📂 Estrutura do Projeto
- `backend/`: responsável pela captura e processamento dos pacotes.  
- `frontend/`: interface web para visualização.  
- `tests/`: testes unitários e integração.  
- `docs/`: relatório técnico e documentação adicional.  

---
