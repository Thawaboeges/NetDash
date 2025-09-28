fastapi
uvicorn[standard]
scapy
pydantic
python-multipart
pytest

import os

# IP do servidor alvo (o tráfego de/para esse IP é monitorado)
SERVER_IP = os.getenv("SERVER_IP", "192.168.0.10")

# Interface de rede para capturar (ex: "eth0"). Se vazio, scapy tenta autodetect.
IFACE = os.getenv("IFACE", "")

# Se quiser rodar a partir de um pcap em vez de sniffing ao vivo:
PCAP_FILE = os.getenv("PCAP_FILE", "")

# Janela em segundos
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", "5"))

# Quantas janelas manter em memória (p.ex. 60 -> 5min se window=5s)
KEEP_WINDOWS = int(os.getenv("KEEP_WINDOWS", "60"))

# Host/Port para o FastAPI
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
import time
import threading
from collections import defaultdict, OrderedDict, Counter
from typing import Dict, Any, Tuple
from config import WINDOW_SIZE, KEEP_WINDOWS

def window_index_for_ts(ts: float) -> int:
    """Return integer window index for timestamp (seconds)."""
    return int(ts // WINDOW_SIZE)

def window_start_ts_from_index(idx: int) -> int:
    """Start timestamp (epoch seconds) for a given window index."""
    return idx * WINDOW_SIZE

class Aggregator:
    """
    Mantém agregações por janela (tumbling windows).
    Estrutura interna: OrderedDict[window_index -> data]
    data: {
      'by_client': { ip: {'in_bytes': int, 'out_bytes': int, 'protocols': Counter({...}) } },
      'total': {...}
    }
    """

    def __init__(self, keep_windows: int = KEEP_WINDOWS):
        self.lock = threading.RLock()
        self.windows: "OrderedDict[int, Dict]" = OrderedDict()
        self.keep_windows = keep_windows

    def _ensure_window(self, idx: int):
        with self.lock:
            if idx not in self.windows:
                self.windows[idx] = {'by_client': {}, 'total_bytes': 0}
                # prune if too many windows
                while len(self.windows) > self.keep_windows:
                    self.windows.popitem(last=False)

    def add_packet(self, ts: float, src: str, dst: str, size: int, proto: str, server_ip: str):
        """
        Adiciona um pacote à janela correta.
        size: tamanho em bytes (incluindo payload/header estimado)
        proto: string (e.g., "TCP", "UDP", "ICMP", "HTTP")
        server_ip: ip do servidor alvo para decidir direção
        """
        idx = window_index_for_ts(ts)
        self._ensure_window(idx)
        with self.lock:
            w = self.windows[idx]
            # identificar cliente (o outro endpoint)
            if src == server_ip:
                client = dst
                direction = 'out_bytes'
            elif dst == server_ip:
                client = src
                direction = 'in_bytes'
            else:
                # não é tráfego com servidor alvo; ignorar
                return

            client_entry = w['by_client'].setdefault(client, {'in_bytes': 0, 'out_bytes': 0, 'protocols': Counter()})
            client_entry[direction] += size
            client_entry['protocols'][proto] += size
            w['total_bytes'] = w.get('total_bytes', 0) + size

    def get_latest_window(self) -> Tuple[int, Dict]:
        """Retorna (window_start_ts, data) da maior janela disponível."""
        with self.lock:
            if not self.windows:
                return (0, {})
            idx = next(reversed(self.windows))
            return (window_start_ts_from_index(idx), self.windows[idx])

    def get_window_by_ts(self, window_start_ts: int) -> Dict:
        idx = window_index_for_ts(window_start_ts)
        with self.lock:
            return self.windows.get(idx, {})

    def get_client_protocols_latest(self, client_ip: str) -> Dict:
        _, w = self.get_latest_window()
        if not w:
            return {}
        client = w['by_client'].get(client_ip)
        if not client:
            return {}
        # return dict of protocols -> bytes
        return dict(client['protocols'])

    def get_clients_summary_latest(self):
        start_ts, w = self.get_latest_window()
        if not w:
            return {'start_ts': start_ts, 'clients': []}
        clients = []
        for ip, data in w['by_client'].items():
            clients.append({
                'ip': ip,
                'in_bytes': data['in_bytes'],
                'out_bytes': data['out_bytes'],
                'total_bytes': data['in_bytes'] + data['out_bytes']
            })
        # sort by total bytes desc
        clients.sort(key=lambda x: x['total_bytes'], reverse=True)
        return {'start_ts': start_ts, 'clients': clients}
      import time
import logging
from scapy.all import sniff, Raw, IP, TCP, UDP, ICMP, Ether
from aggregator import Aggregator
from config import IFACE, PCAP_FILE
from typing import Optional

logger = logging.getLogger("capture")

def _guess_proto(pkt) -> str:
    # heuristics: use scapy layers to guess protocol
    if pkt.haslayer(TCP):
        # could check ports for HTTP/HTTPS/FTP etc. but we'll return "TCP" and probe ports
        sport = pkt.sport if hasattr(pkt, 'sport') else None
        dport = pkt.dport if hasattr(pkt, 'dport') else None
        # basic port-based protocol hints
        if sport in (80, 8080) or dport in (80, 8080):
            return "HTTP"
        if sport in (443, ) or dport in (443, ):
            return "HTTPS"
        if sport in (21, ) or dport in (21, ):
            return "FTP"
        return "TCP"
    if pkt.haslayer(UDP):
        if getattr(pkt, "dport", None) in (53,) or getattr(pkt, "sport", None) in (53,):
            return "DNS"
        return "UDP"
    if pkt.haslayer(ICMP):
        return "ICMP"
    return "OTHER"

def start_sniffing(aggregator: Aggregator, server_ip: str, iface: Optional[str] = IFACE, pcap_file: Optional[str] = PCAP_FILE):
    """
    Inicia captura. Se pcap_file estiver configurado, chamamos sniff(offline=pcap_file), útil para testes.
    Caso contrário, sniff ao vivo (precisa ser root).
    """
    logger.info("Starting packet capture, server_ip=%s iface=%s pcap=%s", server_ip, iface, pcap_file)

    def _process_pkt(pkt):
        try:
            # só processamos pacotes IPv4/IPv6 com camadas IP
            if not pkt.haslayer(IP):
                return
            ip_layer = pkt[IP]
            src = ip_layer.src
            dst = ip_layer.dst
            ts = pkt.time if hasattr(pkt, 'time') else time.time()
            # estimate size: if Ether present use len(pkt). Fallback to 0
            try:
                size = len(pkt)
            except Exception:
                size = 0
            proto = _guess_proto(pkt)
            aggregator.add_packet(ts=ts, src=src, dst=dst, size=size, proto=proto, server_ip=server_ip)
        except Exception as e:
            logger.exception("Error processing packet: %s", e)

    sniff_kwargs = {
        "prn": _process_pkt,
        "store": False,
    }
    if pcap_file:
        sniff_kwargs["offline"] = pcap_file
    else:
        if iface:
            sniff_kwargs["iface"] = iface
        # Otherwise scapy chooses a default interface

    # Threaded sniff (blocking) — caller should run this in a separate thread
    sniff(**sniff_kwargs)
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from aggregator import Aggregator
import threading
import logging
import time
from capture import start_sniffing
from config import SERVER_IP, HOST, PORT, PCAP_FILE

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="Server Traffic Dashboard API")

aggregator = Aggregator()

# start capture in a background thread
def _start_capture_thread():
    try:
        # start_sniffing blocks; run in daemon thread
        t = threading.Thread(target=start_sniffing, args=(aggregator, SERVER_IP), kwargs={"pcap_file": PCAP_FILE}, daemon=True)
        t.start()
        logger.info("Capture thread started (daemon).")
    except Exception as e:
        logger.exception("Failed to start capture thread: %s", e)

@app.on_event("startup")
def startup_event():
    logger.info("API startup: starting capture")
    _start_capture_thread()

@app.get("/health")
def health():
    return {"status": "ok", "server_ip": SERVER_IP, "time": int(time.time())}

@app.get("/traffic/latest")
def traffic_latest():
    summary = aggregator.get_clients_summary_latest()
    return summary

@app.get("/traffic/window/{window_start_ts}")
def traffic_window(window_start_ts: int):
    data = aggregator.get_window_by_ts(window_start_ts)
    if not data:
        raise HTTPException(status_code=404, detail="window not found")
    # format into clients list similar to latest
    clients = []
    for ip, d in data.get('by_client', {}).items():
        clients.append({
            "ip": ip,
            "in_bytes": d['in_bytes'],
            "out_bytes": d['out_bytes'],
            "protocols": dict(d['protocols'])
        })
    return {"start_ts": window_start_ts, "clients": clients, "total_bytes": data.get('total_bytes', 0)}

@app.get("/traffic/{client_ip}/protocols")
def client_protocols(client_ip: str):
    prot = aggregator.get_client_protocols_latest(client_ip)
    if not prot:
        # pode retornar vazio -> 204 ou 404; usaremos 404 para sinalizar que não há dados
        raise HTTPException(status_code=404, detail="no data for client in latest window")
    return {"client": client_ip, "protocols": prot}

if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)
import time
from aggregator import Aggregator, window_index_for_ts

def test_simple_aggregation():
    agg = Aggregator(keep_windows=10)
    server_ip = "10.0.0.5"
    ts = time.time()
    # packet from client -> server (inbound)
    agg.add_packet(ts=ts, src="10.0.0.2", dst=server_ip, size=100, proto="TCP", server_ip=server_ip)
    # packet from server -> client (outbound)
    agg.add_packet(ts=ts+0.1, src=server_ip, dst="10.0.0.2", size=150, proto="TCP", server_ip=server_ip)
    start_ts, window = agg.get_latest_window()
    clients = agg.get_clients_summary_latest()['clients']
    assert len(clients) == 1
    c = clients[0]
    assert c['ip'] == "10.0.0.2"
    assert c['in_bytes'] == 100
    assert c['out_bytes'] == 150
    # protocol summary
    prot = agg.get_client_protocols_latest("10.0.0.2")
    assert prot.get("TCP", 0) == 250
