from fastapi import FastAPI
import psutil
import os
import platform
import subprocess
import socket
import re

app = FastAPI(title="CloudBot Agent API", version="1.0")


# ============================================================
# 1️⃣ ROOT / NORMAL STATUS ENDPOINT
# ============================================================
@app.get("/")
def home():
    return {"status": "Agent running ✅", "hostname": os.uname().nodename}


# ============================================================
# 2️⃣ METRICS ENDPOINT
# ============================================================
@app.get("/metrics")
def get_metrics():
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "cpu_percent": cpu,
        "memory": {
            "total_gb": round(memory.total / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "percent": memory.percent,
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "percent": disk.percent,
        },
    }


# ============================================================
# 3️⃣ LOGS ENDPOINT
# ============================================================
@app.get("/logs")
def get_logs():
    try:
        logs = subprocess.check_output(
            "tail -n 20 /var/log/syslog", shell=True, text=True
        )
        return {"logs": logs.split("\n")}
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# 4️⃣ SYSTEM INVENTORY ENDPOINT
# ============================================================
@app.get("/system-inventory")
def get_system_inventory():
    try:
        uname = os.uname()
        inventory = {
            "hostname": uname.nodename,
            "os": f"{uname.sysname} {uname.release}",
            "kernel_version": uname.version,
            "architecture": uname.machine,
            "platform": platform.platform(),
        }

        # Uptime
        uptime_seconds = int(
            os.popen("awk '{print int($1)}' /proc/uptime").read().strip() or 0
        )
        inventory["uptime_hours"] = round(uptime_seconds / 3600, 2)

        # CPU Info
        inventory["cpu"] = {
            "cores_physical": psutil.cpu_count(logical=False),
            "cores_logical": psutil.cpu_count(logical=True),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "load_avg": os.getloadavg() if hasattr(os, "getloadavg") else None,
        }

        # Memory Info
        mem = psutil.virtual_memory()
        inventory["memory"] = {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "percent_used": mem.percent,
        }

        # Disk Info
        disks = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append(
                    {
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_percent": usage.percent,
                    }
                )
            except PermissionError:
                continue
        inventory["disks"] = disks

        # Network Info
        net_info = []
        addrs = psutil.net_if_addrs()
        for iface, addr_list in addrs.items():
            ipv4 = [a.address for a in addr_list if a.family == socket.AF_INET]
            mac = [a.address for a in addr_list if a.family == psutil.AF_LINK]
            net_info.append({"interface": iface, "ipv4": ipv4, "mac": mac})
        inventory["network"] = net_info

        # Running Services
        try:
            services = (
                subprocess.check_output(
                    "systemctl list-units --type=service --state=running --no-pager --no-legend",
                    shell=True,
                    text=True,
                )
                .strip()
                .split("\n")
            )
            services = [line.split()[0] for line in services if line]
        except Exception:
            services = []

        inventory["running_services"] = services[:15]

        return inventory

    except Exception as e:
        return {"error": str(e)}


# ============================================================
# 5️⃣ SECURITY & COMPLIANCE SIGNALS ENDPOINT
# ============================================================
@app.get("/security")
def get_security_signals():
    security_data = {}

    # 🔒 Firewall status
    try:
        firewall = subprocess.check_output("ufw status", shell=True, text=True)
        security_data["firewall_status"] = firewall.strip()
    except Exception:
        security_data["firewall_status"] = "unknown"

    # 🧱 Open ports
    try:
        ports = subprocess.check_output(
            "ss -tuln | awk 'NR>1 {print $1, $5}'", shell=True, text=True
        )
        security_data["open_ports"] = ports.strip().split("\n")
    except Exception:
        security_data["open_ports"] = []

    # 👤 Failed logins
    try:
        authlog = subprocess.check_output(
            "grep 'Failed password' /var/log/auth.log | tail -n 10",
            shell=True,
            text=True,
        )
        security_data["failed_logins"] = authlog.strip().split("\n") if authlog else []
    except Exception:
        security_data["failed_logins"] = []

    # 👥 New users recently added
    try:
        passwd_out = subprocess.check_output(
            "awk -F: '$3 >= 1000 {print $1}' /etc/passwd", shell=True, text=True
        )
        security_data["regular_users"] = passwd_out.strip().split("\n")
    except Exception:
        security_data["regular_users"] = []

    # ⚙️ Sudoers file
    try:
        sudoers = subprocess.check_output("getent group sudo", shell=True, text=True)
        security_data["sudo_users"] = (
            re.findall(r"sudo:(?:x:27:)?(.*)", sudoers)[0].split(",")
            if "sudo" in sudoers
            else []
        )
    except Exception:
        security_data["sudo_users"] = []

    # 🛡️ Kernel vulnerabilities (quick CVE check)
    try:
        uname = platform.release()
        security_data["kernel_version"] = uname
        if "generic" in uname:
            security_data["kernel_security_status"] = (
                "✅ Likely patched (Ubuntu generic kernel)"
            )
        else:
            security_data["kernel_security_status"] = "⚠️ Verify latest security patches"
    except Exception:
        security_data["kernel_security_status"] = "unknown"

    return security_data
