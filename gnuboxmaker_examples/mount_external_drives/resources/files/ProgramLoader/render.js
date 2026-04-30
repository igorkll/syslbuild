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

function wifiSplash(text) {
    let splashBox = document.createElement("div")
    splashBox.classList.add("splash-box")
    splashBox.textContent = text
    wifiList.appendChild(splashBox)
}

async function refreshWifiNetworks() {
    wifiList.innerHTML = ''

    if (await isWifiExists()) {
        if (await isWifiAvailable()) {
            let list = await getWiFiList()
            
            console.log(list)
            list.forEach(name => addWifiNetwork(name))
            
            if (list.length == 0) {
                wifiSplash('There are no wifi networks available')
            }
        } else {
            wifiSplash('Problems with the wifi driver')
        }
    } else {
        wifiSplash('Your device does not support wifi')
    }
}

setWifiEnabled(true).then(_ => refreshWifiNetworks())

document.getElementById("refresh-button").addEventListener("pointerup", event => {
    refreshWifiNetworks()
})

}