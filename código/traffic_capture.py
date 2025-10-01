"""
Traffic Capture and Aggregation Tool
------------------------------------
Este script captura pacotes de rede relacionados a um servidor específico,
agrega os dados em janelas de tempo discretas (5s) e exporta para um arquivo CSV.

Padrões adotados:
- PEP 8: estilo de código Python.
- PEP 257: docstrings.
- Producer-Consumer Pattern:
    - Producer: captura pacotes em tempo real (process_packet).
    - Consumer: thread que escreve periodicamente no CSV (writer_thread).
"""

from scapy.all import sniff
import pandas as pd
import time
from collections import defaultdict
import threading

# ==============================
# Configurações globais
# ==============================
SERVER_IP = "  "   # <<< troque pelo IP do servidor alvo
WINDOW_SIZE = 5               # janela em segundos
OUTPUT_FILE = "traffic.csv"

# Estrutura de dados compartilhada entre producer e consumer
traffic_data = defaultdict(lambda: defaultdict(int))
lock = threading.Lock()


def classify_protocol(pkt):
    """
    Classifica o protocolo do pacote capturado.

    Parâmetros:
    -----------
    pkt : scapy.Packet
        Pacote de rede capturado pelo Scapy.

    Retorna:
    --------
    str
        Nome do protocolo: "HTTP", "FTP", "TCP", "UDP", "OTHER"
    """
    if pkt.haslayer("TCP"):
        sport, dport = pkt["TCP"].sport, pkt["TCP"].dport
        if sport == 80 or dport == 80:
            return "HTTP"
        elif sport == 21 or dport == 21:
            return "FTP"
        else:
            return "TCP"
    elif pkt.haslayer("UDP"):
        return "UDP"
    else:
        return "OTHER"


def process_packet(pkt):
    """
    Processa cada pacote capturado e agrega os dados em janelas de tempo.

    Parâmetros:
    -----------
    pkt : scapy.Packet
        Pacote capturado pelo Scapy.

    Retorna:
    --------
    None
    """
    try:
        if not pkt.haslayer("IP"):
            return

        src, dst = pkt["IP"].src, pkt["IP"].dst
        length = len(pkt)
        ts = int(time.time())
        window_start = ts - (ts % WINDOW_SIZE)

        if src == SERVER_IP:
            client = dst
            direction = "out"
        elif dst == SERVER_IP:
            client = src
            direction = "in"
        else:
            return

        protocol = classify_protocol(pkt)
        key = (window_start, client, direction)

        with lock:
            traffic_data[key][protocol] += length
            traffic_data[key]["total"] += length

    except Exception as e:
        print(f"[ERRO] Falha ao processar pacote: {e}")


def writer_thread():
    """
    Thread que periodicamente grava os dados agregados no arquivo CSV.

    Executa continuamente a cada WINDOW_SIZE segundos.
    """
    while True:
        time.sleep(WINDOW_SIZE)
        rows = []

        with lock:
            for (window_start, client, direction), proto_dict in list(traffic_data.items()):
                window_end = window_start + WINDOW_SIZE
                row = {
                    "window_start": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(window_start)),
                    "window_end": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(window_end)),
                    "client_ip": client,
                    "direction": direction,
                    "total_bytes": proto_dict.get("total", 0),
                    "http_bytes": proto_dict.get("HTTP", 0),
                    "ftp_bytes": proto_dict.get("FTP", 0),
                    "tcp_bytes": proto_dict.get("TCP", 0),
                    "udp_bytes": proto_dict.get("UDP", 0),
                    "other_bytes": proto_dict.get("OTHER", 0)
                }
                rows.append(row)

            # limpa buffer para não duplicar na próxima janela
            traffic_data.clear()

        if rows:
            df = pd.DataFrame(rows)
            # append no CSV, cria cabeçalho se não existir
            df.to_csv(OUTPUT_FILE, mode="a", header=not pd.io.common.file_exists(OUTPUT_FILE), index=False)
            print(f"[INFO] {len(rows)} linhas gravadas no {OUTPUT_FILE}")


def main():
    """
    Função principal que inicia a captura de pacotes e a thread de gravação.

    Executa o sniffing em tempo real usando Scapy e lança a thread writer_thread.
    """
    print(f"[INFO] Iniciando captura de tráfego para {SERVER_IP}...")
    t = threading.Thread(target=writer_thread, daemon=True)
    t.start()
    sniff(prn=process_packet, store=False)


if __name__ == "__main__":
    main()
