#!/usr/bin/env python
# vim: sw=4:ts=4:sts=4:fdm=indent:fdl=0:
# -*- coding: UTF8 -*-
#
# A TTS module using the espeak library.
# Copyright (C) 2012 Josiah Gordon <josiahg@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


""" A TTS module using the espeak library.

"""

from functools import wraps as functools_wraps
from sys import stderr as sys_stderr

from espeak import _espeak

def redirect_cstd():
    """ Redirect ctypes stderr.

    """

    import sys
    import os
    sys.stdout.flush()
    oldstderr = os.dup(2)
    r, w = os.pipe()
    os.dup2(w, 2)
    os.close(w)
    os.close(r)
    sys.stderr = os.fdopen(oldstderr, 'w')


class Espeak(object):
    """ Espeak wrapper for text to speech synthesis

    """

    def __init__(self, output=_espeak.AUDIO_OUTPUT_PLAYBACK):
        """ Espeak tts object.

        """

        self._output = output
        self._position = 0
        self._data_buffer = b''
        self._speaking = False
        self._buffer_size = 4096

        self._rate = self._err_check(_espeak.espeak_Initialize(output, 0,
                                                               None, 0))
        if output == _espeak.AUDIO_OUTPUT_RETRIEVAL:
            espeak_synth_callback = _espeak.t_espeak_callback(self)
            _espeak.espeak_SetSynthCallback(espeak_synth_callback)
        else:
            self.write = self.speak_text

    def __call__(self, wav, numsamples, events):
        """ Make the class callable so it can be called as the espeak synth
        callback.

        """

        # Stop if the end of the synthesis is reached.
        if not wav: return 1

        # Append the data to the buffer.
        self._data_buffer += _espeak.string_at(wav, numsamples *
                                               _espeak.sizeof(_espeak.c_short))

        # Return value 0 means to keep playing 1 means to stop.
        return 0 if self._speaking else 1

    def __enter__(self):
        """ Provides the ability to use pythons with statement.

        """

        try:
            return self
        except Exception as err:
            print(err)
            return None

    def __exit__(self, exc_type, exc_value, traceback):
        """ Close the file when finished.

        """

        try:
            self.close()
            return not bool(exc_type)
        except Exception as err:
            print(err)
            return False

    def __iter__(self):
        """ Returns an iter of this object.

        """

        return self

    def __next__(self) -> bytes:
        """ Return the next buffer.

        """

        data = self.read(self._buffer_size)

        if not data:
            raise StopIteration
        else:
            return data

    def _err_check(self, ret_val):
        """ Checks the 'ret_val' for error status (<0) and prints and error
        message.  Returns 'ret_val' for the calling function to use.

        """
        try:
            assert(ret_val >= 0)
        except Exception as err:
            print("There was and error %s %s" % (err, ret_val), file=sys_stderr)

        return ret_val

    @property
    def range(self):
        """ The current inflection range.

        """

        return _espeak.espeak_GetParameter(_espeak.espeakRANGE, 1)

    @range.setter
    def range(self, value):
        """ Set the inflection range.

        """

        self._err_check(_espeak.espeak_SetParameter(_espeak.espeakRANGE, value,
                                                    0))

    @property
    def pitch(self):
        """ The current pitch.

        """

        return _espeak.espeak_GetParameter(_espeak.espeakPITCH, 1)

    @pitch.setter
    def pitch(self, value):
        """ Set the pitch.

        """

        self._err_check(_espeak.espeak_SetParameter(_espeak.espeakPITCH, value,
                                                    0))

    @property
    def volume(self):
        """ The current volume.

        """

        return _espeak.espeak_GetParameter(_espeak.espeakVOLUME, 1)

    @volume.setter
    def volume(self, value):
        """ Set the pitch.

        """

        self._err_check(_espeak.espeak_SetParameter(_espeak.espeakVOLUME,
                                                    value, 0))

    @property
    def rate(self):
        """ The current rate.

        """

        return _espeak.espeak_GetParameter(_espeak.espeakRATE, 1)

    @rate.setter
    def rate(self, value):
        """ Set the rate.

        """

        self._err_check(_espeak.espeak_SetParameter(_espeak.espeakRATE, value,
                                                    0))

    @property
    def voice(self):
        """ The current voice.

        """

        voice = _espeak.espeak_GetCurrentVoice()
        return voice.contents.languages[1:].decode()

    @voice.setter
    def voice(self, value):
        """ Set the espeak voice.

        """

        if not isinstance(value, bytes):
            value = value.encode()
        self._err_check(_espeak.espeak_SetVoiceByName(value))

    @property
    def sample_rate(self):
        """ The sample rate of the espeak instance.

        """

        return self._rate

    @property
    def isspeaking(self):
        """ Is it speaking.

        """

        if self._output == _espeak.AUDIO_OUTPUT_RETRIEVAL:
            return self._speaking
        else:
            return bool(_espeak.espeak_IsPlaying())

    def list_voices(self):
        """ Print a list of available voices.

        """

        voices = _espeak.espeak_ListVoices(None)
        print("%-21s %-22s %s" % ("Language", "Name", "Identifier"))
        print('-'*55)
        for voice in voices:
            if not voice:
                break
            voice = voice.contents
            lang = voice.languages.decode()
            name = voice.name.decode()
            ident = voice.identifier.decode()
            print("%-22s %-22s %s" % (lang, name, ident))

    def _update_speaking(func):
        """ Update the speaking variable.

        """

        @functools_wraps(func)
        def wrapper(self, *args):
            """ Wraps the function.

            """

            if func.__name__ != 'close':
                self._position = 0
                self._speaking = True
            else:
                self._speaking = False

            ret_val = func(self, *args)

            return ret_val

        return wrapper

    @_update_speaking
    def speak_text(self, text: str) -> int:
        """ Speak the text to the audio buffer.

        """

        text = text.strip().encode() + b'\0'
        text_length = len(text)

        if self._output != _espeak.AUDIO_OUTPUT_RETRIEVAL:
            redirect_cstd()

        self._err_check(_espeak.espeak_Synth(text, text_length, 0,
                                             _espeak.POS_CHARACTER, 0,
                                             _espeak.espeakCHARS_UTF8, None,
                                             None))

        return text_length

    @_update_speaking
    def close(self):
        """ Stop speaking.

        """

        #self._err_check(_espeak.espeak_Synchronize())
        self._err_check(_espeak.espeak_Cancel())
        self._err_check(_espeak.espeak_Terminate())

    def read(self, size=4096) -> bytes:
        """ Read from the data buffer.

        """

        data = self._data_buffer[self._position:self._position + size]
        self._position += len(data)

        return data


if __name__ == '__main__':
    import sys

    if sys.argv[1:]:
        text = sys.argv[1]
    else:
        text = "Hello, World!"

    with Espeak(_espeak.AUDIO_OUTPUT_RETRIEVAL) as espeak:
        espeak.range = 100
        espeak.voice = 'en-us'
        espeak.rate = 200
        espeak.volume = 100
        espeak.speak_text(text)

        import ossaudiodev
        dsp = ossaudiodev.open('w')
        f = ossaudiodev.AFMT_S16_LE
        dsp.setparameters(f, 1, espeak.sample_rate, True)

        for data in espeak:
            dsp.write(data)
