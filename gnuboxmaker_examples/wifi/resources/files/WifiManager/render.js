{

const wifiList = document.getElementById("wifi-list")

function addWifiNetwork(name) {
    const wifiItem = document.createElement("div")
    wifiItem.classList.add("wifi-item")
    wifiItem.textContent = name

    wifiList.appendChild(wifiItem)
}

let requestId = 0
function refreshWifiNetworks() {
    wifiList.innerHTML = ''
    const currentRequest = ++requestId

    getWiFiList().then(list => {
        if (currentRequest !== requestId) return
        list.forEach(name => addWifiNetwork(name))
    }).catch(err => console.error(err))
}

refreshWifiNetworks()

document.getElementById("refresh-button").addEventListener("pointerup", event => {
    refreshWifiNetworks()
})

}