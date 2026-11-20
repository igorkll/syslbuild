import * as Modals from './Modals.js';
import * as Utils from './Utils.js';
import * as Game from './Game.js';
import * as MusicList from './music/MusicList.js';
import * as MusicManager from './MusicManager.js';
import * as Main from './Main.js';
import * as Consts from './Consts.js';

const gui_base = document.getElementById("gui_base")
const gui_music_list = document.getElementById("gui_music_list")

let _audio;

function hideCursor(state) {
    Main.canvasItem.style.cursor = state ? "none" : "";
}

function stopGame() {
    if (_audio) {
        Utils.stopAudio(_audio);
        _audio = null;
    }

    Game.stop();

    gui_base.classList.remove("gui_base_hide");
    hideCursor(false);
}

function startGame(musicItem) {
    stopGame();

    let audio;
    if (musicItem.url) {
        console.log(musicItem.url, new URL(musicItem.url, import.meta.url).href)
        audio = Utils.audioFromUrl(musicItem.url);
    } else if (musicItem.mp3data) {
        audio = Utils.createAudioFromBuffer(musicItem.mp3data);
    }

    audio.volume = 0.1;
    audio.loop = true;
    audio.play();

    Game.setData(musicItem);
    Game.start();

    _audio = audio;

    gui_base.classList.add("gui_base_hide");
    hideCursor(true);
}

export function gameover() {
    stopGame();
    Utils.playAudio(Utils.audioFromUrl("./sounds/gameover.mp3"));
}

document.addEventListener('visibilitychange', () => {
    if (_audio) {
        if (document.hidden) {
            _audio.pause();
        } else {
            _audio.play();
        }
    }
});

function addSeekBarForMusicValue(container, musicItem, field, defVal, min, max, saveCallback) {
    let seekbar = Modals.addSeekBar(container, musicItem[field] ?? defVal, null, (val) => {
        musicItem[field] = val;
        saveCallback();
    }, min, max);
    seekbar.style.alignSelf = 'stretch';

    return () => {
        seekbar.value = musicItem[field];
    };
}

function editMusic(musicItem) {
    const modal = Modals.createBaseModal("Edit music settings")
    Modals.addModalDescription(modal, musicItem.title)

    let saveOnDone = false;
    const saveCallback = () => {
        saveOnDone = true;
    };

    let forceUpdateValues = [];

    let container = Modals.addVContainer(modal);
    Modals.addSubTitle(container, "Rhythm");
    forceUpdateValues.push(
        addSeekBarForMusicValue(container, musicItem, "rhythm", Consts.DEFAULT_TRACK_RHYTHM, Consts.RHYTHM_MIN, Consts.RHYTHM_MAX, saveCallback)
    );

    container = Modals.addVContainer(modal);
    Modals.addSubTitle(container, "Platform width");
    forceUpdateValues.push(
        addSeekBarForMusicValue(container, musicItem, "platform_width_mul", Consts.DEFAULT_TRACK_PLATFORM_WIDTH_MUL, Consts.TRACK_SETS_MUL_MIN, Consts.TRACK_SETS_MUL_MAX, saveCallback)
    );

    container = Modals.addVContainer(modal);
    Modals.addSubTitle(container, "Ball diameter");
    forceUpdateValues.push(
        addSeekBarForMusicValue(container, musicItem, "ball_diameter_mul", Consts.DEFAULT_TRACK_BALL_DIAMETER_MUL, Consts.TRACK_SETS_MUL_MIN, Consts.TRACK_SETS_MUL_MAX, saveCallback)
    );

    container = Modals.addVContainer(modal);
    Modals.addSubTitle(container, "Platform speed");
    forceUpdateValues.push(
        addSeekBarForMusicValue(container, musicItem, "platform_speed_mul", Consts.DEFAULT_TRACK_PLATFORM_SPEED_MUL, Consts.TRACK_SETS_MUL_MIN, Consts.TRACK_SETS_MUL_MAX, saveCallback)
    );

    container = Modals.addContainer(modal, false);
    const saveButton = Modals.addButton(container, "Save");
    saveButton.style.flex = "1";
    container.appendChild(saveButton)

    const randomButton = Modals.addButton(container, "Random");
    container.appendChild(randomButton)

    const resetButton = Modals.addButton(container, "Reset");
    container.appendChild(resetButton)

    randomButton.addEventListener("click", async () => {
        musicItem.rhythm = Utils.randomFloat(Consts.RHYTHM_MIN, Consts.RHYTHM_MAX);
        musicItem.platform_width_mul = Utils.randomFloat(Consts.TRACK_SETS_MUL_MIN, Consts.TRACK_SETS_MUL_MAX);
        musicItem.ball_diameter_mul = Utils.randomFloat(Consts.TRACK_SETS_MUL_MIN, Consts.TRACK_SETS_MUL_MAX);
        musicItem.platform_speed_mul = Utils.randomFloat(Consts.TRACK_SETS_MUL_MIN, Consts.TRACK_SETS_MUL_MAX);

        forceUpdateValues.forEach(forceUpdateValue => {
            forceUpdateValue();
        });

        await MusicManager.saveMusic(musicItem);
        refreshMusicList();
    });

    resetButton.addEventListener("click", async () => {
        musicItem.rhythm = Consts.DEFAULT_TRACK_RHYTHM;
        musicItem.platform_width_mul = Consts.DEFAULT_TRACK_PLATFORM_WIDTH_MUL;
        musicItem.ball_diameter_mul = Consts.DEFAULT_TRACK_BALL_DIAMETER_MUL;
        musicItem.platform_speed_mul = Consts.DEFAULT_TRACK_PLATFORM_SPEED_MUL;

        forceUpdateValues.forEach(forceUpdateValue => {
            forceUpdateValue();
        });

        await MusicManager.saveMusic(musicItem);
        refreshMusicList();
    });

    saveButton.addEventListener("click", async () => {
        Modals.closeModal()
        if (saveOnDone) {
            await MusicManager.saveMusic(musicItem);
            refreshMusicList();
        }
    });

    Modals.openModalWindow(modal)
}

function deleteMusic(musicItem) {
    Modals.modalYesno("Delete music?", musicItem.title).then(accept => {
        if (accept) {
            MusicManager.deleteMusic(musicItem.id);
            refreshMusicList();
        }
    })
}

function addMusicToList(musicItem, editable=false) {
    const item = document.createElement("div")
    item.classList.add("gui_music_item")
    item.textContent = musicItem.title;
    item.addEventListener("click", () => startGame(musicItem));

    const flexItem = document.createElement("div");
    flexItem.classList.add("flex");
    item.appendChild(flexItem);

    if (editable) {
        let itemButton = document.createElement("div");
        itemButton.classList.add("gui_music_item_button");
        itemButton.innerHTML = "<img class=\"button-img\" src=\"textures/rename.png\"></img>";
        itemButton.addEventListener("click", (e) => {
            e.stopPropagation();
            editMusic(musicItem);
        });
        item.appendChild(itemButton);

        itemButton = document.createElement("div");
        itemButton.classList.add("gui_music_item_button");
        itemButton.innerHTML = "<img class=\"button-img\" src=\"textures/delete.png\"></img>";
        itemButton.addEventListener("click", (e) => {
            e.stopPropagation();
            deleteMusic(musicItem);
        });
        item.appendChild(itemButton);
    }

    gui_music_list.appendChild(item);
}

function refreshMusicList() {
    gui_music_list.innerHTML = "";

    MusicList.list.forEach(musicItem => addMusicToList(musicItem));
    MusicManager.musicList().then((musicItems) => {
        musicItems.forEach(musicItem => {
            addMusicToList(musicItem, true);
        })
    })
}

export function init() {
    document.getElementById("import").addEventListener("click", () => {
        Modals.windowSelectFile("mp3", true).then(mp3data => {
            let importTbl = {
                mp3data,
                rhythm: Consts.DEFAULT_TRACK_RHYTHM,
                platform_width_mul: Consts.DEFAULT_TRACK_PLATFORM_WIDTH_MUL,
                ball_diameter_mul: Consts.DEFAULT_TRACK_BALL_DIAMETER_MUL,
                platform_speed_mul: Consts.DEFAULT_TRACK_PLATFORM_SPEED_MUL,
                title: "unknown"
            };
            MusicManager.saveMusic(importTbl, true).then(refreshMusicList);
        });
    })

    refreshMusicList()
}

export function setupCanvas(canvas) {
    const callback = (event) => {
        let pos = (event.offsetX / canvas.clientWidth) - 0.5;
        if (pos < -0.5) { pos = -0.5; }
        else if (pos > 0.5) { pos = 0.5; }
        Game.setPos(pos);
    };

    canvas.addEventListener('pointermove', callback);
    canvas.addEventListener('pointerdown', callback);
}
