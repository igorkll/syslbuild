import { Dexie } from './dexie.mjs'

// ----------------------------------------- init database

const db = new Dexie("Music")

db.version(1).stores({
    musics: '++id'
})

// -----------------------------------------

export async function getMusicCount() {
    try {
        return await db.musics.count()
    } catch (error) {
        console.error('Failed to get music count:', error)
        return null
    }
}

export async function musicList() {
    try {
        return await db.musics.toArray()
    } catch (error) {
        console.error('Failed to get musics:', error)
        return null
    }
}

export async function getMusicFromId(id) {
    try {
        const music = await db.musics.where('id').equals(id).first()
        return music || null
    } catch (error) {
        console.error('Failed to find music:', error)
        return null
    }
}

export async function saveMusic(music, forceNew=false) {
    try {
        let existing
        if (forceNew) {
            existing = false
        } else {
            existing = await db.musics.where('id').equals(music.id).first()
        }

        if (existing) {
            await db.musics.put(music)
            console.log(`Music "${music.id}" saved`)
            return music
        } else {
            const id = await db.musics.add(music)
            music.id = id
            console.log(`Music "${music.id}" created`)
            return music
        }
    } catch (error) {
        console.error('Failed saving music:', error)
    }
}

export async function deleteMusic(id) {
    try {
        await db.musics.delete(id);
        console.log(`Music with ID ${id} deleted`);
    } catch (error) {
        console.error('Delete failed:', error);
        throw error;
    }
}
