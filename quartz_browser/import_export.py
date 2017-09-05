# -*- coding: utf-8 -*-
import io

def importBookmarks(filename):
    try:
        bmkfile = io.open(filename, 'r', encoding='utf-8')
    except:
        return []
    bmk_lines = bmkfile.readlines()
    bmkfile.close()
    bmk_list = []
    bmk = []
    for line in bmk_lines:
        line = line[:-1]
        bmk.append(line)
        if len(bmk) == 2:
            bmk_list.append(bmk)
            bmk = []
    return bmk_list

def exportBookmarks(filename, bookmarks):
    bmkfile = io.open(filename, 'w', encoding='utf-8')
    for item in bookmarks:
        bmk = item[0] + "\n" + item[1] + "\n"
        bmkfile.write(bmk)
    bmkfile.close()

def importFavourites(filename):
    try:
        favfile = io.open(filename, 'r', encoding='utf-8')
    except:
        return []
    fav_lines = favfile.readlines()
    favfile.close()
    fav_list = []
    fav = []
    for line in fav_lines:
        line = line.rstrip()
        fav.append(line)
        if len(fav) == 3:
            fav_list.append(fav)
            fav = []
    return fav_list

def exportFavourites(filename, favs):
    favfile = io.open(filename, 'w', encoding='utf-8')
    for [title, addr, icon] in favs:
        fav = str(title + "\n" + addr + "\n" + icon + '\n')
        favfile.write(fav)
    favfile.close()

def importDownloads(filename):
    try:
        dwnld_file = io.open(filename, 'r', encoding='utf-8')
    except:
        return []
    dwnld_lines = dwnld_file.readlines()
    dwnld_file.close()
    dwnld_list = []
    dwnld = []
    for line in dwnld_lines:
        line = line[:-1]
        dwnld.append(line)
        if len(dwnld) == 4:
            dwnld_list.append(dwnld)
            dwnld = []
    return dwnld_list

def exportDownloads(filepath, downloads):
    dl_text = ''
    for [filename, url, filesize, timestamp] in downloads:
        dl_text = dl_text + filename+'\n' + url+'\n' + filesize+'\n' + timestamp+'\n'
    dl_file = io.open(filepath, 'w', encoding='utf-8')
    dl_file.write(str(dl_text))
    dl_file.close()

