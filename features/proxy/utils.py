
import random
import string


def random_ip():
    first = random.choice([i for i in range(1, 224) if i != 127])
    return f"{first}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"


def random_port():
    return random.choice([8080, 3128, 8000, 8888, 1080, 9050, 9051, 4145, 10808, 10809, 7890, 7891])


def random_user():
    prefixes = ["user", "proxy", "node", "srv", "gw", "nat", "vpn", "relay", "edge"]
    return f"{random.choice(prefixes)}{random.randint(100, 9999)}"


def random_pass(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%&*"
    return "".join(random.choices(chars, k=length))


def generate_random_ips(count=20):
    return [random_ip() for _ in range(count)]


def generate_socks5_proxies(count=20):
    proxies = []
    for _ in range(count):
        ip = random_ip()
        port = random_port()
        user = random_user()
        pw = random_pass()
        proxies.append({"host": ip, "port": port, "user": user, "pass": pw})
    return proxies


def generate_http_proxies(count=20):
    proxies = []
    for _ in range(count):
        ip = random_ip()
        port = random_port()
        proxies.append({"host": ip, "port": port})
    return proxies


def generate_mixed_proxies(count=30):
    formats = ["socks5", "http", "bare"]
    proxies = []
    for _ in range(count):
        ip = random_ip()
        port = random_port()
        fmt = random.choice(formats)
        if fmt == "socks5":
            user = random_user()
            pw = random_pass(8)
            proxies.append({"host": ip, "port": port, "user": user, "pass": pw, "format": "socks5"})
        elif fmt == "http":
            proxies.append({"host": ip, "port": port, "format": "http"})
        else:
            proxies.append({"host": ip, "port": port, "format": "bare"})
    return proxies
