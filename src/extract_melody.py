from melotract import *
import os

if __name__ == '__main__':
    dr = "midis/"
    midis = os.listdir(dr)
    total = len(midis)
    i = 0
    for midi in midis:
        if (midi[-3:] == "mid"):
            # print(midi)
            pyrolls = read_midi(dr + midi)
            if pyrolls is not None:
                identify_melody_tracks(pyrolls, midi[:-3],save_numpy=True)
            print(i, "/", total - 1)
            i += 1
