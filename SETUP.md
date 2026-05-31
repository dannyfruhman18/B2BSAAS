# SETUP.md — Phase 1: Your free cloud server + automation engine

**Goal of this phase:** get a free, always-on computer in the cloud (Oracle),
and install the "automation engine" (n8n) on it. When you finish, you'll open a
web page on your iPad and see your own n8n dashboard. **Then you stop and tell
me** — we build the actual lead-gen workflows in the next phase.

**Trading name:** Brightwick · **Budget so far:** £0 (no charges in this phase).

> **How to use this doc:** do it in order, top to bottom. Every command tells you
> *what it does* and *what could break*. Don't skip the checkpoints (✅) — they
> confirm each part worked before you move on. If anything looks different from
> what's written here (Oracle changes its website often), **stop and send me a
> screenshot** rather than guessing.

---

## Glossary (terms you'll meet — skim now, refer back later)

- **Cloud VM (Virtual Machine):** a computer you rent that lives in a data
  centre and runs 24/7, even when your iPad is off. "VM" and "server" mean the
  same thing here.
- **Region:** which city's data centre your VM lives in. We'll use **London**.
- **OCPU / RAM / storage:** the VM's processing power / memory / disk space.
- **Image / OS:** the operating system on the VM. We'll use **Ubuntu** (a free
  version of Linux — a keyboard-driven OS with no desktop).
- **SSH:** "Secure Shell" — the secure way to log in to your VM and type
  commands. Think of it as a private remote-control line to the server.
- **SSH key:** a pair of files that act as your password for SSH — a *public*
  key (lives on the server) and a *private* key (stays secret on your device).
  Anyone with the private key can log in, so guard it.
- **Terminal:** the black text screen where you type commands to the VM.
- **Docker:** software that runs apps inside sealed boxes called **containers**,
  so they "just work" without messy installation. 
- **Docker Compose:** a way to describe one or more containers in a single text
  file (`docker-compose.yml`) and start them with one command.
- **Port:** a numbered door on the server for network traffic. SSH uses door
  **22**; we'll run n8n on door **5678**.
- **Firewall / Security List:** rules deciding which doors (ports) are open.
  Oracle blocks everything except 22 by default — we'll open 5678.
- **n8n:** the automation engine — a visual tool where "nodes" connect to build
  workflows (e.g. *call Companies House → score → write email*).

---

## What you need before starting

- Your iPad (primary). A laptop works too but isn't required.
- A **payment card** — Oracle requires one to verify you're human. **Always Free
  resources do not charge it.** (We never enable paid billing without asking.)
- A phone number for a verification text.
- ~45–60 minutes. Oracle signup can occasionally be fiddly; that's normal.

---

## Part A — Create your Oracle Cloud account (free)

1. On your iPad, open Safari and go to **https://www.oracle.com/cloud/free/**.
2. Tap **Start for free**. Fill in your details. **Country: United Kingdom.**
3. **Home Region — choose "UK South (London)".** ⚠️ *This cannot be changed
   later.* London gives you UK data residency and good availability.
4. Verify your email, then your phone (you'll get a code by text).
5. Add your card when asked. **You will see "we won't charge you for Always Free
   services."** A tiny temporary authorisation (often £0–£1) may appear and
   reverse itself — that's the bank checking the card is real, not a charge.
6. Finish. You'll land in the **Oracle Cloud Console** (your control panel).

**✅ Checkpoint A:** You can see the Oracle Cloud Console dashboard. If signup
fails (some cards/regions get declined), stop and tell me — there are known
workarounds and I'll walk you through them.

---

## Part B — Create your free ARM server (the VM)

We're creating the **Ampere A1** machine: 4 OCPU + 24 GB RAM + ~50 GB disk,
which is the free allowance.

1. In the Console, tap the **☰ menu** (top-left) → **Compute** → **Instances**.
2. Tap **Create instance**.
3. **Name:** `brightwick-vm` (anything is fine).
4. **Image and shape** → tap **Edit**:
   - **Image:** choose **Canonical Ubuntu** → version **22.04** (or 24.04).
   - **Shape:** tap **Change shape** → **Ampere** → **VM.Standard.A1.Flex** →
     set **OCPUs = 4** and **Memory = 24 GB**. Tap **Select shape**.
   - These exact numbers are the free limit. Don't exceed them.
5. **Networking:** leave the defaults (Oracle creates a network for you). Make
   sure **"Assign a public IPv4 address" = Yes** — you need this to reach it.
6. **Add SSH keys:** choose **Generate a key pair for me**. Tap **Save private
   key** (downloads to your **Files** app) and **Save public key** too. 
   ⚠️ **The private key is your only way in. If you lose it, you lose the server.**
   Keep it in Files; don't share it.
7. Tap **Create**. Wait ~1–2 minutes until status turns **green / RUNNING**.
8. On the instance page, **copy the "Public IP address"** (looks like
   `141.147.x.x`). Write it down — you'll use it constantly.

> **If you see "Out of host capacity":** the free ARM machines are popular. Just
> tap Create again every few minutes — London usually frees up quickly. If it
> stays stuck for an hour, tell me and we'll try a different availability domain
> or Frankfurt.

**✅ Checkpoint B:** Instance is RUNNING and you have its Public IP + the saved
private key file.

---

## Part C — Log in to the server from your iPad (SSH)

We'll use **Termius**, a free SSH app that works well on iPad/iPhone.

1. Install **Termius** from the App Store (free tier is enough).
2. **Import your key:** Termius → **Keychain** (or **Keys**) → **+** → **Import
   key** → pick the private key file you saved in Files (Part B step 6).
3. **New host:** Termius → **Hosts** → **+** → **New Host**:
   - **Address:** your Public IP from Checkpoint B.
   - **Username:** `ubuntu`  *(this is the default login for Ubuntu on Oracle)*.
   - **Key:** select the key you just imported.
4. Tap the host to connect. The first time, it asks to trust the server — say
   yes. You should land at a prompt like `ubuntu@brightwick-vm:~$`.

> **What could break:** wrong username (`ubuntu`, not `root`), or the key not
> selected. "Connection refused/timed out" usually means the IP is wrong or the
> VM is still booting — wait a minute and retry.

**✅ Checkpoint C:** You see the `ubuntu@...:~$` prompt. You're *inside* your
server. Everything below is typed here.

---

## Part D — Update the server & install Docker

Copy-paste these **one block at a time**. I'll explain each before you run it.

**D1 — Update the system's software list and upgrade it.**
*What it does:* fetches the latest security/software updates. *What could break:*
nothing serious; if it asks a yes/no question, answer `Y`.
```bash
sudo apt update && sudo apt -y upgrade
```

**D2 — Install Docker (the container engine) via the official script.**
*What it does:* downloads and runs Docker's own installer. *What could break:*
rare network hiccups — just re-run it.
```bash
curl -fsSL https://get.docker.com | sudo sh
```

**D3 — Let yourself run Docker without typing `sudo` every time.**
*What it does:* adds your `ubuntu` user to the `docker` group. *Note:* you must
**disconnect and reconnect** (close the Termius session, tap the host again)
for this to take effect.
```bash
sudo usermod -aG docker ubuntu
```
Now disconnect and reconnect in Termius, then verify:
```bash
docker run --rm hello-world
```
*What it does:* downloads a tiny test container and runs it. You should see
**"Hello from Docker!"**.

**✅ Checkpoint D:** "Hello from Docker!" appeared. Docker works.

---

## Part E — Open the door for n8n (port 5678)

Two layers block port 5678 by default: Oracle's **Security List** (cloud-side)
and Ubuntu's **iptables** (server-side). Open both.

**E1 — Server-side: allow incoming traffic on 5678.**
*What it does:* inserts a firewall rule and saves it. *What could break:*
nothing here; this only *adds* an allow rule.
```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 5678 -j ACCEPT
sudo netfilter-persistent save
```

**E2 — Cloud-side: add an Ingress Rule in Oracle.**
In the Oracle Console: **☰ → Networking → Virtual Cloud Networks** → click your
VCN → **Security Lists** → the default list → **Add Ingress Rules**:
- **Source CIDR:** `0.0.0.0/0`  *(means "from anywhere" — fine for now; we'll
  tighten this when we add a proper domain + HTTPS later)*
- **IP Protocol:** TCP
- **Destination Port Range:** `5678`
- Save.

**✅ Checkpoint E:** Both rules added. (No visible change yet — we test in Part F.)

---

## Part F — Install and start n8n

We'll run n8n with Docker Compose, with a login so it isn't open to the world.

**F1 — Make a folder and a data volume for n8n** (so your work survives
restarts).
```bash
mkdir -p ~/n8n && cd ~/n8n && docker volume create n8n_data
```

**F2 — Create the Compose file.** This command writes a file called
`docker-compose.yml` describing the n8n container. **Change the two passwords**
(`CHANGE_ME_USER` and `CHANGE_ME_PASSWORD`) to your own before pasting — keep
them somewhere safe.
*What it does:* creates the config file. *What could break:* if you forget to
change the password placeholders, anyone could log in — so don't skip that.
```bash
cat > ~/n8n/docker-compose.yml <<'YAML'
services:
  n8n:
    image: n8nio/n8n:latest
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=CHANGE_ME_USER
      - N8N_BASIC_AUTH_PASSWORD=CHANGE_ME_PASSWORD
      - N8N_SECURE_COOKIE=false
      - GENERIC_TIMEZONE=Europe/London
    volumes:
      - n8n_data:/home/node/.n8n
YAML
```
> After pasting, open the file to set your real username/password:
> ```bash
> nano ~/n8n/docker-compose.yml
> ```
> Edit the two `CHANGE_ME_...` lines, then press **Ctrl+O, Enter** to save and
> **Ctrl+X** to exit. (`nano` is a simple text editor.)

**F3 — Start n8n.**
*What it does:* downloads the n8n container and starts it in the background.
*What could break:* first download takes a minute or two; that's normal.
```bash
cd ~/n8n && docker compose up -d
```
Check it's running:
```bash
docker compose ps
```
You should see the n8n service with state **Up / running**.

**✅ Checkpoint F (the big one):** On your iPad, open Safari and go to:
```
http://YOUR_PUBLIC_IP:5678
```
(replace `YOUR_PUBLIC_IP` with the IP from Checkpoint B). You should get an n8n
login prompt — enter the username/password you set in F2 — and then the **n8n
workflow dashboard**. 🎉

> **If the page won't load:** 9 times out of 10 it's Part E (a firewall rule
> missing or the wrong port). Re-check E1 and E2. Still stuck? Send me a
> screenshot and the output of `docker compose logs --tail 50`.

---

## 🛑 STOP HERE

That's Phase 1. You now have:
- A free, always-on cloud server (Oracle ARM A1).
- Docker installed.
- n8n running and reachable from your iPad — **£0 spent.**

**Tell me when you've reached Checkpoint F** (or if you got stuck at any ✅).
Next phase, we'll register you as a sole trader, sort the ICO fee, choose and
buy the domain, and wire up Companies House — and only then start scraping.

> **Security note (so it's not a surprise later):** right now n8n is reachable
> over plain `http://` with a basic password. That's fine to get going. Before
> any real outreach we'll put it behind your domain with **HTTPS** (encryption)
> and lock the firewall down. Until then, don't put anything sensitive in n8n.
