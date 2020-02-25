# Melody-Extractor
Extracts melody from provided midi files without harmony notes.

Dependancies
------------
1. pypianoroll
2. numpy

How to Use
-----------
Place the midi files "midis" directory in 
the created directory structure 



    +extracted/
        + extracted/
            + melody/
                + high/
                + low /
    
    + midis/
    
    + src/
         +extract_melody.py
         +melotract.py
         
Run extract_melody.py, the melody will appear in the extracted/melody/high directory.