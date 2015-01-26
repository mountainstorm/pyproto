#!/usr/bin/python
# coding: utf-8

# Copyright (c) 2015 Mountainstorm
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

import ctypes
from io import StringIO




#
# Utility functions
#

TAB = u'    '

def _indent(str):
	u"""Internal function for indenting all lines by TAB (except first)"""
	retval = StringIO()
	first = True
	for line in str.split(u'\n'):
		if first == False:
			retval.write(TAB + line + u'\n')
		else:
			retval.write(line + u'\n')
		first = False
	return retval.getvalue()




#
# Type meta classes
#

class TypeMetaMixin(object):
	u"""Metaclass mixin, used internally to hook __mul__ so that we can add
		our ArrayMixin (and rename) any array types
	"""
	def __rmul__(cls, other):
		return cls * other

	def __mul__(cls, other):
		# override mul so we add the ArrayMixin
		bt = super(TypeMetaMixin, cls).__mul__(5)
		# create derrived type with new name and ArrayMixin
		t = type(cls.__name__+'*%d' % other, (ArrayMixin, bt), dict(
			_length_=other,
			_type_=cls
		))
		return t


def new_type(name, mixin, base_type, d=dict()):
	u"""Low level helper method for creating new types.  Automatically creates 
		a suitable copy of the meta type TypeMeta, derrived from the correct base

		Arguments:
			name: the name (non unicode) of the type
			mixin: the mixing (functionality) for the type
			base_type: the base type - the one used for rooting the meta
			d: optional dictionary of members for the new instance

		Return:
			None; adds class name to the global namespace
	"""
	meta = type(name+'Meta', (TypeMetaMixin, type(base_type),), dict())
	cls = meta(name, (mixin, base_type), d)
	globals()[name] = cls # add to namespace
	return cls



#
# Array type
#

class ArrayMixin(object):
	u"""Array mixin, provides display routines"""
	def __repr__(self):
		return u'<%s> = %s' % (type(self).__name__, self)

	def __str__(self):
		return unicode(self)

	def __unicode__(self):
		retval = None
		if hasattr(self, u'_format_') and hasattr(self._format_, u'__call__'):
			try:
				retval = self._format_(self)
			except:
				# something went wrong; try calling it on each entry
				content = StringIO()
				for value in self:
					content.write(self._format_(value))
				retval = content.getvalue()
		else:
			content = StringIO()
			first = True
			for val in self:
				if not first:
					content.write(u', ')
				s = _indent(unicode(val))
				if s[-1] == u'\n':
					s = s[:-1]
				# XXX dump all type info .. hmmm
				content.write(s)
				first = False
			retval = u'[%s]' % (content.getvalue())
		return retval




#
# Structure mixin
#

class StructMixin(object):
	u"""Struct mixin, provides display routines"""
	def __repr__(self):
		return u'<%s> = %s' % (type(self).__name__, self)

	def __str__(self):
		return unicode(self)

	def __unicode__(self):
		# XXX: anonymous members
		MEMBER_STR = u'%s '
		MEMBER_TYPE_STR = u'%s'
		MEMBER_OFF_STR = u'%xh: '

		retval = StringIO()
		retval.write(u'{\n')
		# figure out the largest offset & largest delta to the '='
		moffsize = 0
		mtsize = 0
		msize = 0
		members = []
		off = 0
		i = 0
		for field in self._fields_:
			m = MEMBER_STR % field[0]
			mt = MEMBER_TYPE_STR % field[1].__name__
			mo = MEMBER_OFF_STR % off
			val = _indent(str(getattr(self, field[0])))

			members.append((mo, mt, u' ' + m, u'= ' + val))
			msize = max(msize, len(m))
			mtsize = max(mtsize, len(mt))
			moffsize = max(moffsize, len(mo))
			off += ctypes.sizeof(field[1])
			i += 1
		# calc end of struct marker - don't use off as it wont include any padding
		mo = MEMBER_OFF_STR % ctypes.sizeof(self)
		moffsize = max(moffsize, len(mo))
		# now do the actual display
		for member in members:
			retval.write(
				  TAB 
				+ u'+'
				+ member[0].rjust(moffsize, u'0') 
				+ member[1]#.ljust(mtsize, u' ')
				+ member[2]#.ljust(msize, u' ')
				+ member[3] 
			)
		retval.write(TAB + u'+' + mo.rjust(moffsize, u'0') + u'^^^')
		retval.write(u'\n}')
		return str(retval.getvalue())

	def __unpack__(self, stream, tree):
		# tree = TREE(PacketInitResponse, {
		# 	TREE(WdH2C, {
		# 		CapHdr,
		# 		CapEntry[]
		# 	)
		# }
		tree = [
			(pkt, PacketInitResponse, [
				(mod, WdH2C, [
					(caphdr, CapHdr,),
					(CapEntry,),
					(CapEntry,),
					(CapEntry,),
					(CapEntry,),
				])
			]),
		]


#
# Simple type mixins
#

class SimpleTypeMixin(object):
	u"""Simple type routines, provides display and base type operations"""
	def __repr__(self):
		return u'<%s> = %s' % (type(self).__name__, self)

	def __str__(self):
		return unicode(self)

	def __unicode__(self):
		retval = None
		if hasattr(self._format_, u'__call__'):
			retval = self._format_(self.value)
		else:
			if self.value is None:
				retval = u'NULL'
			else:
				retval = self._format_ % self.value
		return retval

	def __int__(self):
		return int(self.value)

	def __long__(self):
		return long(self.value)

	def __float__(self):
		return float(self.value)

	def __hash__(self):
		return hash(self.value)		

	def __eq__(self, other):
		return self.value == other.value

	def __gt__(self, other):
		return self.value > other.value

	def __lt__(self, other):
		return self.value < other.value

	def __ge__(self, other):
		return self.value >= other.value

	def __le__(self, other):
		return self.value <= other.value

	def __ne__(self, other):
		return self.value != other.value


class IntTypeMixin(SimpleTypeMixin):
	U"""Adds default _format_ to integer types"""
	_format_ = u'%d'


class FloatTypeMixin(SimpleTypeMixin):
	U"""Adds default _format_ to float types"""
	_format_ = u'%f'




#
# Enumeration meta class
#

class EnumTypeMeta(TypeMetaMixin):
	u"""Meta class for Enum types; takes _values_ and creates mapping tables"""
	def __init__(cls, name, bases, dict):
		if u'_values_' in dict:
			# create the mapping arrays
			cls._name_by_value = {}
			cls._value_by_name = {}
			val = 0
			if u'_start_' in dict:
				val = cls._start_
			for value in cls._values_:
				name = value
				if isinstance(value, tuple):
					name = value[0]
					val = value[1] 
				# store into name_by and value_by
				cls._name_by_value[val] = name
				cls._value_by_name[name] = val
				val += 1
		return super(EnumTypeMeta, cls).__init__(name, bases, dict)

	def __contains__(cls, value):
		retval = None
		if not (isinstance(value, str) and value.startswith(u'_')):
			if value in cls._name_by_value:
				retval = cls._name_by_value[value]
		return retval

	def __iter__(cls):
		for value in sorted(cls._name_by_value.keys()):
			name = cls._name_by_value[value]
			if isinstance(name, str) or isinstance(name, unicode):
				yield (name, value)
			else:
				for n in name:
					yield (n, value)

	def __getattr__(cls, name):
		retval = None
		if not name.startswith(u'_') and u'_values_' in cls.__dict__:
			if name in cls._value_by_name:
				retval = cls._value_by_name[name]
		return retval

	def __getitem__(cls, value):
		retval = None
		if value in cls._name_by_value:
			retval = cls._name_by_value[value]
		return retval




#
# Enumeration mixin and helper
#

class EnumMixin(object):
	u"""Enum mixin, used to provide display and attr access"""
	# XXX add bitfield support
	def __repr__(self):
		return u'<%s> = %s' % (type(self).__name__, self)

	def __unicode__(self):
		retval = u'{undefined}'
		if self.value in self.__class__._name_by_value:
			retval = self.__class__._name_by_value[self.value]
		return u'%s(%d)' % (retval, self)

	def __getattr__(self, key):
		retval = None
		if key == u'name':
			if self.value in self.__class__._name_by_value:
				retval = self.__class__._name_by_value[self.value]
		return retval


def Enum(base_type):
	u"""Helper function for creating enumeration types"""
	name = 'Enum'+base_type.__name__
	meta = type(name+'Meta', (EnumTypeMeta, type(base_type),), dict())
	return meta(name, (EnumMixin, base_type), dict())

# XXX Union support



#
# Structure types
#

new_type('LitteEndianStruct', StructMixin, ctypes.LittleEndianStructure)
new_type('BigEndianStruct', StructMixin, ctypes.BigEndianStructure)
new_type('Struct', StructMixin, ctypes.Structure)
new_type('Union', StructMixin, ctypes.Union)




#
# Fixed size simple types
#

new_type('Char', IntTypeMixin, ctypes.c_char)
new_type('WChar', IntTypeMixin, ctypes.c_wchar)

new_type('Int8', IntTypeMixin, ctypes.c_int8)
new_type('UInt8', IntTypeMixin, ctypes.c_uint8)

new_type('Int16', IntTypeMixin, ctypes.c_int16)
new_type('UInt16', IntTypeMixin, ctypes.c_uint16)

new_type('Int32', IntTypeMixin, ctypes.c_int32)
new_type('UInt32', IntTypeMixin, ctypes.c_uint32)

new_type('Int64', IntTypeMixin, ctypes.c_int64)
new_type('UInt64', IntTypeMixin, ctypes.c_uint64)




#
# Variable size simple types
#

new_type('Bool',IntTypeMixin, ctypes.c_bool)

new_type('Short', IntTypeMixin, ctypes.c_short)
new_type('UShort', IntTypeMixin, ctypes.c_short)

new_type('Int', IntTypeMixin, ctypes.c_int)
new_type('UInt', IntTypeMixin, ctypes.c_uint)

new_type('Long', IntTypeMixin, ctypes.c_long)
new_type('ULong', IntTypeMixin, ctypes.c_ulong)

new_type('LongLong', IntTypeMixin, ctypes.c_longlong)
new_type('ULongLong', IntTypeMixin, ctypes.c_ulonglong)

new_type('SizeT', IntTypeMixin, ctypes.c_size_t)
new_type('SSizeT', IntTypeMixin, ctypes.c_ssize_t)

new_type('Float', FloatTypeMixin, ctypes.c_float)
new_type('Double', FloatTypeMixin, ctypes.c_double)
new_type('LongDouble', FloatTypeMixin, ctypes.c_longdouble)

new_type('Pointer', IntTypeMixin, ctypes.c_void_p, dict(
	_format_ = u'%08xh' if ctypes.sizeof(ctypes.c_void_p) == 4 else u'%016xh'
))




#
# Format support
#

def format(t, fmt):
	u"""Returns a copy of type t, with fmt set as its format specifier.

		Arguments:
			t: a type on which to set a format specifier
			fmt: the format specifier; a printf style string or a callable

		Return:
			a copy of type t, with fmt set as it's format specifier
	"""
	nt = type(t.__name__, t.__bases__, dict(t.__dict__))
	nt._format_ = fmt
	return nt

sizeof = ctypes.sizeof




import sys
import binascii

if __name__ == u'__main__':
	class MH_FILETYPE(Enum(UInt32)):
		_start_ = 0
		_values_ = [
			u'MH_UNKNOWN',		# value is 0
			(u'MH_EXECUTE', 2),	# value is 2
			u'MH_FVMLIB'		# value is 3
		]

	# print(MH_FILETYPE.MH_EXECUTE)
	# print((MH_FILETYPE[2]))
	# a = MH_FILETYPE(MH_FILETYPE.MH_EXECUTE)
	# print((a.name))
	# print((a.value))
	# print((2 in MH_FILETYPE))
	# b = MH_FILETYPE()
	# print(b)
	# for k, v in MH_FILETYPE:
	# 	print("    ", k, v)



	# print MH_FILETYPE
	# e = MH_FILETYPE()
	# e.value = 10
	# print repr(e)
	# print u'%s (%d)' % (e, e)


	# tt1 = Int16 * 10
	# tt2 = 5 * Int16

	class SS(Struct):
		_pack_ = 4
		_fields_ = [
			('ptr', Pointer),
			('len', Int8)
		]

	tt1 = SS * 2

	# print tt1
	# print tt1._endian_
	# print tt1._sizeof_

	# t = tt1()

	# print repr(t)
	# print u'%s' % (t)
	# print unicode(t)


	class S(Struct):
		_fields_ = [
			('a', Int16),
			('b', Float),
			('kkk', MH_FILETYPE*2),
			('c', SS),
			('ddsa', tt1),
			('e', format(Int32, u'%08xh')),
			('f', format(Int8 * 10, binascii.hexlify)),
		]

	s = S()
	s.c.ptr = 7
	print(repr(s))

	# sys.stdin.readinto(s)
	# print s

	# i = Int16()
	# print repr(i)
	# print u'%d' % i
	# print unicode(i)

	# f = Float32()
	# print repr(f)
	# print u'%f' % f
	# print unicode(f)

