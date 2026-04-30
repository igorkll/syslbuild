const { exec } = require('child_process');

function isWifiEnabled() {
    return new Promise((resolve, reject) => {
        exec('nmcli radio wifi', (error, stdout, stderr) => {
            if (error) {
                reject(error);
                return;
            }
            if (stderr) {
                reject(new Error(stderr));
                return;
            }
            
            const status = stdout.trim().toLowerCase();
            resolve(status === 'enabled');
        });
    });
}

function getWiFiList() {
    return new Promise((resolve, reject) => {
        exec('nmcli -t -f SSID,SIGNAL,SECURITY dev wifi list', (err, stdout, stderr) => {
            if (err) return reject(err);
            if (stderr) return reject(stderr);
            
            const networks = [];
            const lines = stdout.trim().split('\n');
            
            for (const line of lines) {
                const [ssid, signal, security] = line.split(':');
                if (ssid && ssid !== '--') {
                    networks.push({ ssid, signal: parseInt(signal, 10), security: security || 'Open' });
                }
            }
            resolve(networks);
        });
    });
}
