#!/bin/bash

# =======================
# Colors using tput
# =======================
RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
CYAN=$(tput setaf 6)
MAGENTA=$(tput setaf 5)
WHITE=$(tput setaf 7)
NC=$(tput sgr0)

# =======================
# Animated typing
# =======================
type_text() {
  text="$1"
  speed=${2:-0.02}
  for ((i=0;i<${#text};i++)); do
    echo -n "${text:$i:1}"
    sleep $speed
  done
  echo ""
}

# =======================
# Fancy loading bar
# =======================
fancy_bar() {
  msg="$1"
  duration="$2"
  steps=30
  sleep_per_step=$(awk "BEGIN {print $duration/$steps}")
  echo -ne "${CYAN}[!]${NC} $msg [>------------------------------] 0%"
  for ((i=1;i<=steps;i++)); do
    bar=$(printf "%0.s=" $(seq 1 $i))
    empty=$(printf "%0.s-" $(seq 1 $((steps-i))))
    percent=$((i*100/steps))
    echo -ne "\r${CYAN}[!]${NC} $msg [${bar}${empty}] ${percent}%"
    sleep $sleep_per_step 2>/dev/null || sleep 0.1
  done
  echo -ne "\r${GREEN}[√]${NC} $msg [${bar}] DONE\n"
}

# =======================
# Clear screen and start
# =======================
clear
type_text "${MAGENTA}✤ Initializing environment...${NC}" 0.04
fancy_bar "Scanning system" 1
fancy_bar "Checking Python installation" 0.5

# =======================
# Install dependencies
# =======================
type_text "${YELLOW}📦 Installing required modules...${NC}" 0.03
pkg install python -y
pip install -r requirements.txt >/dev/null 2>&1
fancy_bar "Dependencies installed" 2

# =======================
# Check main file
# =======================
if [ ! -f "junn.py" ]; then
    echo -e "${RED}[ERROR]${NC} junn.py not found!"
    exit 1
fi

# =======================
# Interactive explanation
# =======================
clear
echo -e "${MAGENTA}══════════════════════════════════════════════${NC}"
type_text "${YELLOW}📌 IMPORTANT INFORMATION:${NC}" 0.03
echo "- You will need to input your ${GREEN}Telegram number${NC}"
echo "- Then input ${GREEN}OTP code${NC}"
echo "- Then input ${GREEN}2FA password (if any)${NC}\n"
echo "${RED}⚠️ Your inputs will be hidden as you type.${NC}"
echo "Type carefully and press ENTER."
type_text "Press ${CYAN}y${NC} to continue." 0.03
echo -e "${MAGENTA}══════════════════════════════════════════════${NC}\n"
read -p "✅ Type 'y' to proceed: " confirm

# =======================
# Execute according to choice
# =======================
if [[ "$confirm" =~ ^[yY]$ ]]; then
    clear
    type_text "${CYAN}✨ Preparing Userbot...${NC}" 0.04
    fancy_bar "Loading modules" 3
    fancy_bar "Initializing bot" 2
    type_text "${GREEN}✅ All set! Running Userbot...${NC}" 0.03
    python bot.py
else
    type_text "${RED}❌ Cancelled.${NC}" 0.03
    exit 0
fi