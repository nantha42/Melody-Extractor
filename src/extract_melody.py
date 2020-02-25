from melotract import *
import os

if __name__ == '__main__':
    dr = "../midis/"
    midis = os.listdir(dr)

    for midi in midis:
        if(midi[-3:]=="mid"):
            print(midi)
            pyrolls = read_midi(dr + midi)
            identify_melody_tracks(pyrolls,midi[:-3])

