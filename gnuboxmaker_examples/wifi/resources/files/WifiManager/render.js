{

const wifiList = document.getElementById("wifi-list")

function addWifiNetwork(name) {
    const wifiItem = document.createElement("div")
    wifiItem.classList.add("wifi-item")
    wifiItem.textContent = name

    wifiList.appendChild(wifiItem)
}

function refreshWifiNetworks() {
    wifiList.htmlContent = ''

    getWiFiList().then(list => {
        list.forEach(name => {
            addWifiNetwork(name)
        });
    }).catch(console.error);
}

refreshWifiNetworks()

}