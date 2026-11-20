export function windowSelectFile(ext=null, binary=false) {
    return new Promise((resolve, reject) => {
        const input = document.createElement("input")
        input.type = "file"
        if (ext != null) input.accept = `.${ext}`

        input.onchange = async (event) => {
            const file = event.target.files[0]
            if (!file) return resolve(null)

            try {
                if (binary) {
                    const buffer = await file.arrayBuffer()
                    const bytes = new Uint8Array(buffer)
                    resolve(bytes)
                } else {
                    const text = await file.text()
                    resolve(text)
                }
            } catch (err) {
                console.error('Select failed:', err)
                void modalShow("FAILED TO SELECT FILE", err.message ?? String(err))

                reject(err)
            }
        }

        input.click()
    })
}

const gui_base = document.getElementById("gui_base");
let _modal = null;
let _closeModal = null;

export function openModalWindow(modal) {
    gui_base.classList.add("gui_base_hide");
    document.body.appendChild(modal);

    setTimeout(() => {
        modal.classList.remove("gui_base_hide");
    }, 100);

    let old_modal = _modal;

    if (old_modal) {
        old_modal.classList.add("gui_base_hide")
    }

    _modal = modal;
    _closeModal = () => {
        if (old_modal) {
            old_modal.classList.remove("gui_base_hide")
        } else {
            gui_base.classList.remove("gui_base_hide")
        }

        modal.classList.add("gui_base_hide");
        setTimeout(() => {
            modal.remove();
        }, 1000);

        _modal = old_modal;
    }
}

export function closeModal() {
    if (_closeModal) _closeModal();
}

export function createBaseModal(title) {
    const modal = document.createElement("div")
    modal.classList.add("gui_base")
    modal.classList.add("gui_base_hide");

    const titleObj = document.createElement("div")
    titleObj.classList.add("menu-title")
    titleObj.textContent = title
    modal.appendChild(titleObj)

    return modal
}

export function addModalDescription(modal, description) {
    const descriptionObj = document.createElement("div");
    descriptionObj.classList.add("menu-description");
    descriptionObj.textContent = description;
    modal.appendChild(descriptionObj);
}

export function addContainer(modal, flex=true) {
    const obj = document.createElement("div");
    obj.classList.add("gui_container");
    if (flex) obj.classList.add("gui_container_flex");
    modal.appendChild(obj);
    return obj;
}

export function addVContainer(modal) {
    const obj = document.createElement("div");
    obj.classList.add("gui_container_vertical");
    modal.appendChild(obj);
    return obj;
}

export function addSubTitle(container, subtitle) {
    const obj = document.createElement("div");
    obj.classList.add("menu-subtitle");
    obj.textContent = subtitle;
    container.appendChild(obj);
    return obj;
}

export function addButton(container, text) {
    const obj = document.createElement("div");
    obj.classList.add("gui_music_button");
    obj.textContent = text;
    container.appendChild(obj);
    return obj;
}

export function addSeekBar(container, defaultValue, changeCallback, saveCallback, minVal=0, maxVal=1, step=0.01) {
    const seekbar = document.createElement("input");

    seekbar.type = "range";
    seekbar.min = minVal;
    seekbar.max = maxVal;
    seekbar.step = step;
    seekbar.value = defaultValue;

    seekbar.addEventListener("input", () => {
        changeCallback?.(Number(seekbar.value));
    });

    seekbar.addEventListener("change", () => {
        saveCallback?.(Number(seekbar.value));
    });

    container.appendChild(seekbar);

    return seekbar;
}

export function modalYesno(title, description=null) {
    const modal = createBaseModal(title)
    if (description) addModalDescription(modal, description)

    const container = document.createElement("div")
    container.classList.add("gui_container")
    container.classList.add("gui_container_flex")
    modal.appendChild(container)

    const noButton = document.createElement("div")
    noButton.classList.add("gui_music_button")
    noButton.textContent = "No"
    container.appendChild(noButton)

    const yesButton = document.createElement("div")
    yesButton.classList.add("gui_music_button")
    yesButton.textContent = "Yes"
    container.appendChild(yesButton)

    return new Promise((resolve) => {
        noButton.addEventListener("click", () => {
            closeModal()
            resolve(false)
        })

        yesButton.addEventListener("click", () => {
            closeModal()
            resolve(true)
        })

        openModalWindow(modal)
    });
}
