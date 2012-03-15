#!/bin/bash
h2xml.py -c -I/usr/include/espeak /usr/include/espeak/speak_lib.h -o espeak.xml -D __STDC_CONSTANT_MACROS
xml2py espeak.xml -o _espeak.py -l/usr/lib/libespeak.so
sed -i 's/\([[:digit:]]\)L\>/\1/g' _espeak.py
