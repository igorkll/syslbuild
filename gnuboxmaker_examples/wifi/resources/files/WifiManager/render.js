{

const wifiList = document.getElementById("wifi-list")

function addWifiNetwork(name) {
    const wifiItem = document.createElement("div")
    wifiItem.classList.add("wifi-item")
    wifiItem.textContent = name

    wifiList.appendChild(wifiItem)

    wifiItem.addEventListener("pointerup", event => {
        
    })
}

let requestId = 0
function refreshWifiNetworks() {
    wifiList.innerHTML = ''
    const currentRequest = ++requestId

    getWiFiList().then(list => {
        if (currentRequest !== requestId) return
        
        console.log(list)
        list.forEach(name => addWifiNetwork(name))
        
        if (list.lenght == 0) {
            let splashBox = document.createElement("div")
            splashBox.classList.add("splash-box")
            wifiList.appendChild(splashBox)
        }
    }).catch(err => console.error(err))
}

setWifiEnabled(true)
refreshWifiNetworks()

document.getElementById("refresh-button").addEventListener("pointerup", event => {
    refreshWifiNetworks()
})

}