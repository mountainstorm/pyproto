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
import ctypes
import sys




class StreamReader(object):
	def __init__(self, stream):
		self._stream = stream
		self._peekahead = bytes()

	def _into_(self, buf, obj):
		o = obj
		if inspect.isclass(obj):
			o = obj()
		ctypes.memmove(ctypes.addressof(o), buf, len(buf))
		return o

	def peekinto(self, obj):
		buf = self.peek(ptypes.sizeof(obj))
		return self._into_(buf, obj)

	def readinto(self, obj):
		buf = self.read(ptypes.sizeof(obj))
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
	def __init__(self, type):
		self._type_ = type
		self._order_ = [] # used for printing

	def __setattr__(self, name, value):
		if name[0] != u'_':
			# save the order as we add subelements, so we can print in order
			self._order_.append(name)
		super(Scatter, self).__setattr__(name, value)

	def __repr__(self):
		return u'<%s=%s>' % (type(self).__name__, self)

	def __str__(self):
		return unicode(self)

	def __unicode__(self):
		content = StringIO()
		content.write(u'{\n')
		for name in self._order_:
			a = getattr(self, name)
			content.write(u'%s%s %s = ' % (ptypes.TAB, type(a).__name__, name))
			content.write(ptypes._indent(unicode(a)))
		content.write(u'}')
		return content.getvalue()


def unpack(stream, type):
	sct = Scatter(type)
	sct._type_._from_stream_(stream, sct)
	return sct

def pack(sct, stream):
	sct._type_._to_stream_(sct, stream)




if __name__ == u'__main__':
	class SS(ptypes.Struct):
		_pack_ = 4
		_fields_ = [
			('ptr', ptypes.Pointer),
			('len', ptypes.Int8)
		]

		@classmethod
		def _from_stream_(cls, stream, sct):
			sct.hdr = stream.readinto(SS)

		@classmethod
		def _to_stream_(cls, sct, stream):
			stream.write(sct.hdr)


	s = StreamReader(sys.stdin)
	sct = unpack(s, SS)
	print repr(sct)
	b = BytesIO()
	pack(sct, b)
	print b.getvalue()


