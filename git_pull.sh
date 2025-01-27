NETWORK1="eduroam"
NETWORK2="GalaxyA52"

TARGET_DIR="~/Drinking_Machine"

connect_to_network() {
    SSID=$1
    echo "Connecting to $SSID..."
    

    if command -v nmcli &> /dev/null; then
        nmcli dev wifi connect "$SSID"
    fi
    sleep 20
}

connect_to_network "$NETWORK1"

cd "$TARGET_DIR"
git pull

connect_to_network "$NETWORK2"

echo "Script completed."