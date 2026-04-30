const { exec } = require('child_process')

function isWifiExists() {
    return new Promise((resolve, reject) => {
        exec('nmcli -t device status', (error, stdout, stderr) => {
            if (error) {
                reject(error)
                return
            }
            if (stderr) {
                reject(new Error(stderr))
                return
            }

            const lines = stdout.trim().split('\n')
            for (const line of lines) {
                const fields = line.split(':')
                const type = fields[1]
                if (type === 'wifi') {
                    resolve(true)
                    return
                }
            }
            resolve(false)
        })
    })
}

function isWifiAvailable() {
    return new Promise((resolve, reject) => {
        exec('nmcli -t device status', (error, stdout, stderr) => {
            if (error) {
                reject(error)
                return
            }
            if (stderr) {
                reject(new Error(stderr))
                return
            }

            const lines = stdout.trim().split('\n')
            for (const line of lines) {
                const fields = line.split(':')
                const type = fields[1]
                const state = fields[2] // STATE — третье поле
                
                if (type === 'wifi' && state !== 'unavailable') {
                    resolve(true)
                    return
                }
            }
            resolve(false)
        })
    })
}

function isWifiEnabled() {
    return new Promise((resolve, reject) => {
        exec('nmcli radio wifi', (error, stdout, stderr) => {
            if (error) {
                reject(error)
                return
            }
            if (stderr) {
                reject(new Error(stderr))
                return
            }
            
            const status = stdout.trim().toLowerCase()
            resolve(status === 'enabled')
        })
    })
}

function setWifiEnabled(enable) {
    return new Promise((resolve, reject) => {
        let state
        if (enable) {
            state = 'on'
        } else {
            state = 'off'
        }

        exec('nmcli radio wifi ' + state, (error, stdout, stderr) => {
            if (error) {
                reject(error)
                return
            }
            if (stderr) {
                reject(new Error(stderr))
                return
            }
            resolve()
        })
    })
}

const wifiObjectFormatter = 'SSID,SIGNAL,SECURITY'
function getWifiObject(line) {
    const [ssid, signal, security] = line.split(':')
    return {
        ssid,
        signal: parseInt(signal, 10),
        security: security || 'Open'
    }
}

function getWiFiList() {
    return new Promise((resolve, reject) => {
        exec(`nmcli -t -f ${wifiObjectFormatter} dev wifi list`, (err, stdout, stderr) => {
            if (err) return reject(err)
            if (stderr) return reject(stderr)
            
            const networks = []
            const lines = stdout.trim().split('\n')
            
            for (const line of lines) {
                const wifiObject = getWifiObject(line)
                networks.push(wifiObject)
            }
            resolve(networks)
        })
    })
}

function getCurrentWifiSSID() {
    return new Promise((resolve, reject) => {
        exec('nmcli -t -f NAME,TYPE connection show --active', (error, stdout, stderr) => {
            if (error) {
                reject(error)
                return
            }

            const lines = stdout.trim().split('\n')
            for (const line of lines) {
                const [name, type] = line.split(':')
                if (type === 'wifi') {
                    resolve(name)
                    return
                }
            }
            resolve(null)
        })
    })
}
