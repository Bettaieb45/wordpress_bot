import subprocess

def reconnect_to_nordvpn():
    try:
        subprocess.run(["nordvpn", "disconnect"], check=True)
        subprocess.run(["nordvpn", "connect"], check=True)
        print("Reconnected to NordVPN successfully.")
    except Exception as e:
        print(f"Error reconnecting to NordVPN: {e}")
