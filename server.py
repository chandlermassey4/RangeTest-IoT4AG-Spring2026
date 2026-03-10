import serial
import time

# ── Configuration ─────────────────────────────────────────────────────────────
SERVER_BOARD_PORT = "COM14"
SERVER_ID         = 39
CHANNEL           = 530
BAND              = 4
TX_POWER          = 19        
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


print("Connecting to server board...")
board = serial.Serial(SERVER_BOARD_PORT, 115200, timeout=2, write_timeout=5)
time.sleep(2)
send(board, "", 1)
send(board, f"dect sett -t {SERVER_ID}", 2)
board.reset_input_buffer()

# --- Set band and max power --- CHANGE FOR BANDS
#send(board, f"dect sett -b {BAND}", 1)        # select 900 MHz band
send(board, f"dect sett --tx_pwr {TX_POWER}" , 1) # set TX power to max
print("Ready\n")

while True:
    cmd = input("Command (ping / perf / stop / q): ").strip().lower()

    if cmd == "q":
        break
    elif cmd == "ping":
        send(board, f"dect ping -s --channel {CHANNEL}", 5)
        print("Ping server running — tell client to go")
    elif cmd == "perf":
        send(board, f"dect perf -s -t -1 --channel {CHANNEL}", 5)
        print("Perf server running — tell client to go")
    elif cmd == "stop":
        send(board, "dect ping stop", 2)
        send(board, "dect perf stop", 2)
        print("Stopped")
    else:
        print("Unknown command")

board.close()
print("Finished")