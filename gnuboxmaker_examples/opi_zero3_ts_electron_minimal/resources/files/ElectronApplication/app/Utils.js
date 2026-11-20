export function degToRad(degrees) {
    return degrees * (Math.PI / 180);
}

export function createAudioFromBuffer(mp3Data) {
    const blob = new Blob([mp3Data], {
        type: 'audio/mpeg'
    });

    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio._blobUrl = url;
    return audio;
}

export function playAudio(audio) {
    audio.addEventListener("ended", () => stopAudio(audio))

    audio.loop = false;
    audio.play();
}

export function audioFromUrl(url) {
    return new Audio(new URL(url, import.meta.url).href);
}


export function stopAudio(audio) {
    audio.pause();
    audio.currentTime = 0;
    audio.removeAttribute('src');
    audio.load();
    if (audio._blobUrl) URL.revokeObjectURL(audio._blobUrl);
}

export function randomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

export function randomFloat(min, max) {
    return Math.random() * (max - min) + min;
}
