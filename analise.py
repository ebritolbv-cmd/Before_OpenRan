import sys
import re
import argparse
import pandas as pd
import matplotlib.pyplot as plt

def parse_logs(log_file):
    """
    Realiza o parsing dos logs do Open5GS seguindo a lógica do analise.sh.
    Suporta logs multi-linha (ISO8601) e linha-a-linha.
    """
    packets = []
    current_packet = []
    
    # Regex para identificar o início de um novo bloco de log (formato ISO8601)
    iso_regex = re.compile(r'^\d{4}-\d{2}-\d{2}T')
    # Regex para extrair o evento entre colchetes no início da mensagem
    event_regex = re.compile(r'^\S+ \[([^\]]+)\]')

    try:
        with open(log_file, 'r') as f:
            for line in f:
                if iso_regex.match(line):
                    if current_packet:
                        packets.append("\n".join(current_packet))
                    current_packet = [line.strip()]
                else:
                    current_packet.append(line.strip())
            
            if current_packet:
                packets.append("\n".join(current_packet))
    except FileNotFoundError:
        print(f"Erro: Arquivo {log_file} não encontrado.")
        sys.exit(1)

    parsed_data = []
    for pkt in packets:
        first_line = pkt.split('\n')[0]
        match = event_regex.match(first_line)
        if match:
            event = match.group(1).strip()
            # Extrair timestamp (primeira parte da linha)
            timestamp = first_line.split(' ')[0]
            parsed_data.append({'timestamp': timestamp, 'event': event, 'content': pkt})
            
    return pd.DataFrame(parsed_data)

def list_events(df):
    """Lista eventos e suas contagens, ordenados alfabeticamente."""
    if df.empty:
        print("Nenhum evento encontrado.")
        return
    summary = df['event'].value_counts().sort_index()
    print(f"{'EVENTO':<15} {'CONTAGEM'}")
    for event, count in summary.items():
        print(f"{event:<15} {count}")

def filter_event(df, event_name):
    """Filtra e imprime blocos de um evento específico."""
    filtered = df[df['event'] == event_name]
    if filtered.empty:
        print(f"Nenhum evento '{event_name}' encontrado.")
        return
    for _, row in filtered.iterrows():
        print(row['content'])
        print("---")

def plot_events(df, output_file='events_chart.png'):
    """Gera um gráfico de barras com a contagem de eventos."""
    if df.empty:
        return
    summary = df['event'].value_counts().sort_index()
    plt.figure(figsize=(10, 6))
    summary.plot(kind='bar', color='skyblue')
    plt.title('Contagem de Eventos por Tipo (Logs Open5GS)')
    plt.xlabel('Tipo de Evento')
    plt.ylabel('Frequência')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_file)
    print(f"Gráfico salvo em: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Versão Python do analise.sh para logs Open5GS")
    parser.add_argument("--list", action="store_true", help="Lista e contagem de eventos")
    parser.add_argument("--plot", action="store_true", help="Gera gráfico de eventos")
    parser.add_argument("arg1", help="Nome do evento (se não usar --list) ou caminho do log")
    parser.add_argument("arg2", nargs="?", help="Caminho do log (se arg1 for o evento)")

    args = parser.parse_args()

    if args.list:
        log_path = args.arg1
        df = parse_logs(log_path)
        list_events(df)
        if args.plot:
            plot_events(df)
    else:
        if not args.arg2:
            print("Erro: Forneça o nome do evento e o caminho do arquivo de log.")
            sys.exit(1)
        event_name = args.arg1
        log_path = args.arg2
        df = parse_logs(log_path)
        filter_event(df, event_name)
