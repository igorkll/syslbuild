const { exec } = require('child_process');

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

getWiFiList().then(list => console.log(list)).catch(console.error);