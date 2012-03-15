from ctypes import *
from sys import argv
import ossaudiodev

from espeak._espeak import *

dsp = ossaudiodev.open('w')

f = ossaudiodev.AFMT_S16_LE

if argv[1:]:
    text = argv[1].encode() + b'\0'
else:
    text = b"Hello, World!\0"
def check(ret_val):
    try:
        assert(ret_val >= 0)
    except Exception as err:
        print("There was and error %s %s" % (err, ret_val))
    
    return ret_val

def speak_callback(wav, numsamples, events):
    print(events.contents.type)
    if wav:
        dsp.write(string_at(wav, numsamples * sizeof(c_short)))
    return 0
t = POINTER(c_ulong)(c_ulong(0))
espeak_callback = t_espeak_callback(speak_callback)
rate = check(espeak_Initialize(AUDIO_OUTPUT_RETRIEVAL, 4096, None, 0))
dsp.setparameters(f, 1, rate, True)
espeak_SetSynthCallback(espeak_callback)
check(espeak_SetParameter(espeakRANGE, 100, 0))
check(espeak_SetParameter(espeakRATE, 150, 0))
check(espeak_SetParameter(espeakPITCH, 10, 0))
voices = espeak_ListVoices(None)
print("%-21s %-22s %s" % ("Language", "Name", "Identifier"))
print('-'*55)
for voice in voices:
    if voice:
        voice = voice.contents
        lang = voice.languages.decode()
        name = voice.name.decode()
        ident = voice.identifier.decode()
        print("%-22s %-22s %s" % (lang, name, ident))
        #print(lang, lang.strip('\x05').encode('ascii'))
        #check(espeak_SetVoiceByName(lang.strip('\x05').encode()))
        #check(espeak_Key(name.encode()))
        #input()
    else:
        break
check(espeak_SetVoiceByName(b"en-us"))
#check(espeak_Key(text))
check(espeak_Synth(text, len(text), 0, POS_CHARACTER, 0, espeakCHARS_UTF8, None, None))
#input()
check(espeak_Cancel())
check(espeak_Terminate())
