import subprocess

def block_user_network_access(username):
    cmd = ["sudo", "iptables", "-A", "OUTPUT", "-m", "owner", "--uid-owner", username, "-j", "REJECT"]
    subprocess.run(cmd, check=True)

def unblock_user_network_access(username):
    cmd = ["sudo", "iptables", "-D", "OUTPUT", "-m", "owner", "--uid-owner", username, "-j", "REJECT"]
    subprocess.run(cmd, check=True)

unblock_user_network_access("temuulen")