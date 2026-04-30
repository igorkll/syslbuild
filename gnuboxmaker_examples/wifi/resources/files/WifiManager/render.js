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

    for (let i = 0; i < 10; i++) {
        addWifiNetwork("test12")
        addWifiNetwork("test2")
    }
}

refreshWifiNetworks()

}