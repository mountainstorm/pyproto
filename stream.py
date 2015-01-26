#!/usr/bin/python
# coding: utf-8

# Copyright (c) 2014 Mountainstorm
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from io import *
import inspect
import ptypes
import sys




class StreamReader(object):
	def __init__(self, stream):
		self._stream = stream
		self._peekahead = bytes()

	def _into_(self, buf, obj):
		o = obj
		if inspect.isclass(obj):
			o = obj()
		ctypes.memmove(addressof(o), buf, sizeof(buf))
		return o

	def peekinto(self, obj):
		buf = self.peek(pstruct.sizeof(obj))
		return self._into_(buf, obj)

	def readinto(self, obj):
		buf = self.read(pstruct.sizeof(obj))
		return self._into_(buf, obj)

	def peek(self, length):
		peekahead = self.read(length)
		self._peekahead = peekahead + self._peekahead
		return peekahead

	def read(self, length):
		retval = b''
		if length <= len(self._peekahead):
			retval = self._peekahead[:length] # return some peeked data
		else:
			buf = self._stream.read(length - len(self._peekahead))
			retval = self._peekahead + buf
		self._peekahead = self._peekahead[length:]
		return retval


class StreamWriter(object):
	def __init__(self, stream):
		self._stream = stream

	def write(self, buf):
		return self._stream.write(buf)


class Scatter(object):
	pass




if __name__ == u'__main__':
	s = StreamReader(sys.stdin)
	#s.readinto(Packet)
	# Packet.unpack(s)
	#     stream.readinto(self)
	#     stream.peekinto(self)
	#     stream.read(128)


