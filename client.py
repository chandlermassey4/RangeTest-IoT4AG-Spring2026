import serial
import time
import csv
import os
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────────────────
CLIENT_BOARD_PORT = "COM13"
SERVER_ID         = 39
CHANNEL           = 530
BAND              = 4
TX_POWER          = 19    # dB
# ─────────────────────────────────────────────────────────────────────────────

def send(board, command, wait=2):
    board.reset_input_buffer()
    board.write((command + "\r\n").encode())
    time.sleep(wait)
    output = ""
    while board.in_waiting:
        chunk = board.read(board.in_waiting).decode(errors="replace")
        output += chunk
        time.sleep(0.1)
    return output


def wait_for(board, keyword, timeout=90):
    start_time = time.time()
    output = ""
    while time.time() - start_time < timeout:
        if board.in_waiting:
            chunk = board.read(board.in_waiting).decode(errors="replace")
            output += chunk
            if keyword in output:
                return output
        time.sleep(0.1)
    return output


def find_between(text, before, after):
    start = text.find(before)
    if start == -1:
        return ""
    start += len(before)
    end = text.find(after, start)
    if end == -1:
        return ""
    return text[start:end].strip()


def find_all_rtts(text):
    rtts = []
    pos = 0
    while True:
        found = text.find("RTT: ", pos)
        if found == -1:
            break
        num_start = found + 5
        num_end = text.find(" msec", num_start)
        if num_end == -1:
            break
        rtts.append(int(text[num_start:num_end]))
        pos = num_end
    return rtts


def run_ping(board, channel, server_id):
    input("Start PING on server, then press Enter...")
    cmd = f"dect ping -c --s_tx_id {server_id} --channel {channel} --c_count 10"
    send(board, cmd, 1)
    output = wait_for(board, "ping command done", 90)
    input("Tell server to STOP, then press Enter...")

    rtts = find_all_rtts(output)
    if rtts:
        received     = len(rtts)
        avg_rtt      = sum(rtts) // len(rtts)
        rssi_weak    = find_between(output, "min RSSI ", ",")
        rssi_strong  = find_between(output, "max RSSI ", "\n")
        header_err   = find_between(output, "PCC CRC error count:", "\n")
        data_err     = find_between(output, "PDC CRC error count:", "\n")

        print("PING:")
        print(f"  Received: {received}/10")
        print(f"  Round trip time: {avg_rtt} ms")
        print(f"  Signal (weak/strong): {rssi_weak} / {rssi_strong} dBm")
        print(f"  Header errors: {header_err}")
        print(f"  Data errors:   {data_err}")

        return {
            "received": received,
            "avg_rtt_ms": avg_rtt,
            "rssi_weak_dBm": rssi_weak,
            "rssi_strong_dBm": rssi_strong,
            "header_errors": header_err,
            "data_errors": data_err,
        }
    else:
        print("PING: no responses")
        return None


def run_throughput(board, channel, server_id, test_name, mcs, slots, extra=""):
    cmd = (f"dect perf -c --s_tx_id {server_id}"
           f" -t 10 --c_tx_mcs {mcs} --c_slots {slots}"
           f"{extra} --channel {channel}")
    send(board, cmd, 1)
    output = wait_for(board, "perf command done", 45)

    srv          = output[output.find("Server results received:"):]
    speed        = find_between(srv, "data rates:", "kbits") or find_between(srv, "data rate:", "kbits")
    pkts_rx      = find_between(srv, "packet count:", "\n")
    pkts_tx      = find_between(output, "packet count:", "\n")
    rssi_weak    = find_between(srv, "RSSI: min:", ",")
    rssi_strong  = find_between(srv, "max:", "dBm")
    header_err   = find_between(srv, "PCC CRC errors:", "\n")
    data_err     = find_between(srv, "PDC CRC errors:", "\n")

    print(f"{test_name}:")
    print(f"  Speed: {speed} kbps")
    print(f"  Packets received/sent: {pkts_rx} / {pkts_tx}")
    print(f"  Signal (weak/strong): {rssi_weak} / {rssi_strong} dBm")
    print(f"  Header errors: {header_err}")
    print(f"  Data errors:   {data_err}")

    return {
        "speed_kbps": speed,
        "packets_rx": pkts_rx,
        "packets_tx": pkts_tx,
        "rssi_weak_dBm": rssi_weak,
        "rssi_strong_dBm": rssi_strong,
        "header_errors": header_err,
        "data_errors": data_err,
    }


def write_csv(csv_path, rows):
    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


# ── Main ──────────────────────────────────────────────────────────────────────

csv_path = f"range_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
print(f"Results will be saved to: {csv_path}\n")

print("Connecting to client board...")
board = serial.Serial(CLIENT_BOARD_PORT, 115200, timeout=2, write_timeout=5)
time.sleep(2)
send(board, "", 1)
board.reset_input_buffer()

# --- Set band and max power --- CHANGE FOR BANDS
#send(board, f"dect sett -b {BAND}", 1)        # select 900 MHz band
send(board, f"dect sett --tx_pwr {TX_POWER}" , 1) # set TX power to max
print("Ready\n")

while True:
    distance = input("Distance in meters (q to quit): ").strip()
    if distance == "q":
        break
    print()

    rows = []

    # Ping
    ping = run_ping(board, CHANNEL, SERVER_ID)
    print()
    if ping:
        rows.append({
            "distance_m":       distance,
            "test":             "ping",
            "mcs":              "",
            "speed_kbps":       "",
            "packets_rx":       ping["received"],
            "packets_tx":       10,
            "avg_rtt_ms":       ping["avg_rtt_ms"],
            "rssi_weak_dBm":    ping["rssi_weak_dBm"],
            "rssi_strong_dBm":  ping["rssi_strong_dBm"],
            "header_errors":    ping["header_errors"],
            "data_errors":      ping["data_errors"],
        })

    # Throughput
    input("Start PERF on server, then press Enter...")
    time.sleep(3)

    for test_name, mcs, slots, extra in [
        ("MCS 0 (reliable)", 0, 2, ""),
        ("MCS 1 (balanced)", 1, 2, ""),
        ("MCS 4 (fast)",     4, 4, " --c_gap_subslots 3"),
    ]:
        perf = run_throughput(board, CHANNEL, SERVER_ID, test_name, mcs, slots, extra)
        rows.append({
            "distance_m":       distance,
            "test":             "perf",
            "mcs":              mcs,
            "speed_kbps":       perf["speed_kbps"],
            "packets_rx":       perf["packets_rx"],
            "packets_tx":       perf["packets_tx"],
            "avg_rtt_ms":       "",
            "rssi_weak_dBm":    perf["rssi_weak_dBm"],
            "rssi_strong_dBm":  perf["rssi_strong_dBm"],
            "header_errors":    perf["header_errors"],
            "data_errors":      perf["data_errors"],
        })
        time.sleep(3)

    input("Tell server to STOP, then press Enter...")

    write_csv(csv_path, rows)
    print(f"\nDone with {distance}m — saved to {csv_path}")

board.close()
print("Finished")