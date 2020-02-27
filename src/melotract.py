from pypianoroll import Track, Multitrack
import numpy as np
import time


def read_midi(name):
    """
    :param name: mid file name
    :return: a list of pianorolls for the tracks in the midi file
    """
    try:
        multitrack = Multitrack(name)
        pyrolls = []
        for track in multitrack.tracks:
            pyrolls.append(track.pianoroll)
        return pyrolls
    except:
        print("Error in Midi file, likes corrupt")


def parse_track(roll):
    """
    Parses the midi file and converts it into the format
    required for my pianoroll function.
    :param roll:
    :return:
    """
    shortened_track = []
    for i in range(128):
        range_array = get_notes(roll[:, i])
        if len(range_array) > 0:
            shortened_track.append([i, range_array])
    shortened_track = np.array(shortened_track)
    modified_track = []

    for each_note_row in shortened_track:
        n = each_note_row[0]  # note number
        ranges = np.array(each_note_row[1])  # range(pos,dur)
        # print("ranges: ", ranges)
        ranges[:, 0] = ranges[:, 0] / 3
        modified_track.append([n, ranges])
    # print(modified_track)
    return modified_track


def load_track(parsed_track, measure_limit):
    """
    Converts the parsed track and loads into the pianoroll
    numpy array. parsed_track is divided by 3 so the basic time
    unit is 32nd note.
    """
    notes_index = []

    array = np.ones([48, int(measure_limit)]) * -1
    for note_index, notes_track in parsed_track:
        note_index = note_index - 36
        if note_index >= 0 and note_index < 48:
            for pos, dura in notes_track:
                if int(pos) < array.shape[1]:
                    # print(47 - note_index, int(pos), array.shape, np.log2(dura))
                    array[47 - note_index][int(pos)] = np.log2(dura)
                    notes_index.append([47 - note_index, int(pos)])
    notes = array

    return [notes, notes_index]


def find_closer(x):
    """
    Returns the closest resemblance of the note type
    such as whole(96),half(48),half+quarter.
    Currently ex_dura feature is turned off, because of
    reducing complexity
    :param x:
    :return:
    """
    # ex_dura = [96,72,48,36,24,18,12,9,6,4,3]
    measure_length = 91
    dura = [measure_length, measure_length / 2, measure_length / 4, measure_length / 8,
            measure_length / 16, measure_length / 32]
    dura.reverse()
    dura = np.array(dura)
    my_dura = [0.125, 0.25, 0.5, 1, 2, 4]
    my_dura = np.array(my_dura)
    duration = my_dura[np.argmin(np.abs(x - dura))] * 8
    # print(duration)
    return duration


def get_notes(key_row):
    """
    Returns a list of list of starting position
    and duration of a particular note in the entire track
    :param key_row:
    :return:
    """
    nonzeros = np.nonzero(key_row)[0]
    # print("Nonzeros1",nonzeros)
    notes = []
    if len(nonzeros) > 0:
        start = int(nonzeros[0])
        prestart = start
        length = 0
        # tuple stores length start,length
        for i in range(1, len(nonzeros)):
            if start + 1 == nonzeros[i] and i < len(nonzeros) - 1:
                length += 1
                start += 1
            else:
                notes.append([prestart, find_closer(length)])
                length = 0
                prestart = int(nonzeros[i])
                start = prestart
            pass
        # print("Notes", notes)
        return notes
    else:
        return []
    # print(nonzeros.shape)


def dura_to_timecell(x):
    return {0: 2, 1: 4, 2: 10, 3: 21, 4: 44, 5: 90}[x]


def play_notes(roll, loc, trackname):
    """
    Converts the notes array to pypianoroll format
    and then using MultiTrack object, the midi file
    is written to the file system
    :return:
    """

    pianoroll = np.zeros((roll.shape[1] * 3, 128))

    for i in range(roll.shape[0]):
        note_track = np.array(roll[i, :])
        note_track += 1

        notes_pos = np.nonzero(note_track)
        f = 3
        for pos in notes_pos[0]:
            # print("Error", f * pos, f * pos + self.dura_to_timecell(note_track[pos] - 1),self.dura_to_timecell(note_track[pos] - 1))
            pianoroll[f * pos:f * pos + dura_to_timecell(note_track[pos] - 1) + 1, 83 - i] = 90

    tracks = []
    tracker = Track(pianoroll=pianoroll, program=1)
    tracks.append(tracker)
    multitrack = Multitrack(tracks=tracks)

    # print(save_time, )
    if len(np.nonzero(pianoroll)[0]) > 0:
        # for preventing writing empty midi tracks
        multitrack.write(loc + trackname)


def is_chord(pyroll):
    mul_notes_count = 0.0
    sin_notes_count = 0.0
    # print(pyroll.shape)
    for i in range(pyroll.shape[1]):
        time_row = pyroll[:, i]  # vertical scale
        pos = np.nonzero(time_row + 1)[0]
        if len(pos) > 1:
            mul_notes_count += 1.0
        elif len(pos) == 1:
            sin_notes_count += 1.0

    ratio = 0
    # print(sin_notes_count, mul_notes_count)
    if sin_notes_count > 0:
        ratio = mul_notes_count / sin_notes_count

    if ratio > 0.9:
        # print("ratio", ratio)
        return True
    else:
        return False


def max_keys_used(pyroll, maxkeys, notes_count):
    """
    Counts the number of notes in the
    pyroll and also the number of types of keys used
    :param pyroll:
    :param maxkeys:
    :return:
    """
    notes_used = set()
    notes = []
    note_count = 0
    for i in range(pyroll.shape[1]):
        time_row = pyroll[:, i]
        pos = np.nonzero(time_row + 1)[0]
        if len(pos) > 0:
            notes_used.add(pos[0])
            notes.append(pos[0])
            note_count += 1
    # print("Notes Used", notes_used)
    # print(len(notes))

    if maxkeys > len(notes_used):
        return False
    else:
        if note_count > notes_count:
            return True


def split_track(roll, keyrange):
    startindex = 0
    splitted = []
    # finding first note start
    for i in range(roll.shape[1]):
        time_row = roll[:, i][keyrange[0]:keyrange[1]]
        non_zeros = np.nonzero(time_row + 1)[0]
        if len(non_zeros) > 0:
            startindex = i
            break
    # print("StartIndex",startindex)
    splits = []
    i = startindex
    gap = False
    gap_started = 0
    # print(roll.shape[1])
    while i < roll.shape[1]:
        # print(roll,i)
        # print(splits)
        i = int(i)
        time_row = roll[:, i]
        q = time_row + 1
        # print(keyrange[0],keyrange[1])
        q = q[keyrange[0]:keyrange[1]]
        non_zeros = np.nonzero(q)[0]
        # print(q,non_zeros)
        # print(time_row)
        # print(i)
        if len(non_zeros) > 0:
            # print("If Executed",i,non_zeros,gap,gap_started)
            if gap:
                if i - gap_started < 2 * 32:
                    splits.pop(len(splits) - 1)
                    # print("Popped")
                else:
                    # print("Started again")
                    startindex = i
                gap = False
                gap_started = 0
            # print("before",i,time_row[non_zeros[0]])
            i += 2 ** time_row[keyrange[0] + non_zeros[0]]
            # print("after", i)

        else:
            # print("Else executed",i)
            if not gap:
                gap = True
                splits.append([startindex, i])
                gap_started = i
                i += 1
            elif gap == True:
                i += 1

    if len(splits) == 0:
        if startindex != i:
            # print(startindex,i-startindex)
            splits.append([startindex, i - startindex])
    # print("Splitted Length", len(splits))
    for split in splits:
        j = np.array(roll[:, int(split[0]):int(split[1])])
        # j[24:48] = -1
        splitted.append(j)
    # print(len(splitted))
    return splitted


def identify_melody_tracks(pyrolls, track_name, nnotes=5, max_cons=4, filter_chords=True, max_cons_duration=(5, 3),
                           save_numpy=False):
    """
    :param pyrolls:
    :param nnotes:
    :param max_cons:
    :param filter_chords:
    :param max_cons_duration:

   Takes list of pianorolls and finds the melody
   in that list

    :return: pianoroll

    """
    filtered_rolls = []
    # print(len(pyrolls))
    index = 0
    for roll in pyrolls:
        # print(index)
        # print("Roll",index)
        index += 1
        chord = True
        modified_track = parse_track(roll)
        roll = load_track(modified_track, measure_limit=32 * 200)[0]

        # print(roll[0])
        if not is_chord(roll):

            filtered_rolls.append(roll)
            chord = False

            splitted1 = split_track(roll, [0, 24])
            splitted2 = split_track(roll, [24, 48])

            for splits in splitted1:
                if max_keys_used(splits, maxkeys=8, notes_count=5):
                    timed = str(time.time())[-5:]
                    save_roll_as_mid(splits, "extracted/melody/high/", track_name + str(timed))
                    if save_numpy == True:
                        np.savez_compressed("extracted/melody/high_npy/" + track_name + timed, splits)

            for splits in splitted2:
                if max_keys_used(splits, maxkeys=8, notes_count=5):
                    timed = str(time.time())[-5:]
                    save_roll_as_mid(splits, "extracted/melody/low/", track_name + timed)
                    if save_numpy == True:
                        np.savez_compressed("extracted/melody/low_npy/" + track_name + timed, splits)

        if chord:
            # save_roll_as_mid(roll, "extracted/chords/")
            pass


def identify_recurring_patterns(track):
    pass


def save_pattern(pyroll):
    pass


def save_roll_as_mid(roll, loc, track_name):
    play_notes(roll, loc, track_name)


def save_as_mid(dirname):
    pass
