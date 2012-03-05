#!/usr/bin/env python
#-*- coding: utf-8 -*-

import random

__all__ = [
	'ABTestError', 'DummyStorage', 'BaseAB',
	'SimpleAB', 'ConfigurableAB', 'quick_test',
]


class ABTestError(Exception):
	pass


class DummyStorage(object):
	'''
	Dummy AB Test storage. Provides interface to persist test state and
	associate sides/results with user.

	NOTE: This class used mostly for demonstration.
	'''
	def create(self, name, sides):
		'''
		Creates or updates existen test data.

		`name` - name of AB test.
		`sides` - allowed sides for current test.
		'''
		pass

	def set_side(self, identity, name, side):
		'''
		Associates AB side with user for current test. So it can be accessed
		later when user come back.

		`identity` - user identifier, can be None.
		`name` - name of AB test.
		`side` - AB side that will be saved for user.
		'''
		pass

	def get_side(self, identity, name):
		'''
		Returns side previously associated with user or None if no sides have
		been associated.

		`identity` - user identifier, can be None.
		`name` - name of AB test.
		'''
		pass

	def record(self, identity, name, side=None):
		'''
		Saves test result for optional side.

		`identity` - user identifier, can be None.
		`name` - name of AB test.
		`side` - AB side that was successfuly conversed.
		'''
		pass


class BaseAB(object):
	'''
	This class provides gineric AB Test implementation. Each test should have
	unique `name` and provide `allowed_sides` (aka alternatives/variants)
	'''
	name = None
	allowed_sides = None

	def __init__(self, identity=None, storage=None):
		'''
		All parameters are optional. `identity` parameter used to identify a
		user (or wenewer you want) to associalte it with AB test. `storage`
		used to persist AB test state/results across user sessions or for
		later analitics.
		'''
		self.identity = identity
		self.storage = storage
		self._side = None
		if self.storage:
			self.storage.create(self.name, self.allowed_sides)

	@property
	def current_side(self):
		'''
		Returns last selected side.
		'''
		return self._side

	def select_side(self, *args, **kwargs):
		'''
		This method provides necessary logic to select AB side (alternative).
		It can be some deterministic or stohastic algorithm depends on your
		needs.
		The method should be implement in specific subclass.
		'''
		raise NotImplementedError

	def apply_side(self, side, *args, **kwargs):
		'''
		This methos provides logic to associate AB `side` with its value.
		Returns AB side value.
		The method should be implement in specific subclass.
		'''
		raise NotImplementedError

	def test(self, *args, **kwargs):
		'''
		This method implements validation and selection flow. If optional
		parameter `force_side` is given it will be used to get alternative
		value. If `storage` is specified it will be user to load the side
		previously associated with the user (identity value).
		Returns alternative value according with selection algorithm.
		'''
		# check that test instance properly configured
		if not self.name:
			raise ABTestError('Test should be named')
		if not self.allowed_sides:
			raise ABTestError('Sides not given for "%s" test' % self.name)

		# select AB side, use forced value if given
		side = kwargs.pop('force_side', None)
		if not side and self.storage:
				# trying to load side associated later
				side = self.storage.get_side(self.identity, self.name)
		if not side:
				# if no luck, select new one
				side = self.select_side(*args, **kwargs)
		if not side or side not in self.allowed_sides:
			raise ABTestError('Unknown side "%s" for "%s" test' % (side, self.name))

		# ok, we know side, let's save it and get its value
		self._side = side
		if self.storage:
			self.storage.set_side(self.identity, self.name, side)
		value = self.apply_side(side, *args, **kwargs)
		return value

	def record(self, side=None):
		'''
		Saves test result for optional side. Used when success side can be
		detected during user flow.
		'''
		if self.storage:
			self.storage.record(self.identity, self.name, side)

	def __repr__(self):
		return '<%s [name: %s, sides: %s]>' % \
			(self.__class__.__name__, self.name, self.allowed_sides)


class SimpleAB(BaseAB):
	'''
	This implementation of AB Test provides way to implement alternatives as
	methods with names A, B, ..., Z. You should inherit this class to provide
	appropriated side.
	Example:

		>>> class MyTest(SimpleAB):
		... 	name = 'MyTest'
		...     def A(self): return 'Side A'
		...     def B(self): return 'Side B'
		...     def C(self): return 'Side C'
		...
		>>> myab = MyTest()
		>>> myab.test()
		'Side A'
		>>> myab.current_side
		'A'
		>>> myab.test(force_side='C')
		'Side C'
	'''
	@property
	def allowed_sides(self):
		return [x for x in dir(self) if len(x) == 1 and ('A' <= x <= 'Z')]

	def select_side(self, *args, **kwargs):
		return random.choice(self.allowed_sides)

	def apply_side(self, side, *args, **kwargs):
		method = getattr(self, side, None)
		if not callable(method):
			raise ABTestError('Side "%s" is not implemented for "%s" test' % \
				(side, self.name))
		return method(*args, **kwargs)


class ConfigurableAB(BaseAB):
	'''
	This implementation of AB Test provides way to configure test name, sides and
	selector instance. If selector isn't specified random selection will be used.
	Example:

		>>> import random as r
		>>> myab = ConfigurableAB(name='MyTest',
		... 					sides={'A': 'Side A', 'B': 'Side B'},
		... 					selector=lambda: r.choice(['A','B']))
		>>> myab
		<ConfigurableAB [name: MyTest, sides: ['A', 'B']]>
		>>> myab.test()
		'Side A'
		>>> myab.current_side
		'A'
	'''
	def __init__(self, identity=None, storage=None,
			name=None, sides=None, selector=None):
		'''
		Configures AB Test.
		`name` - nane of current AB Test.
		`sides` - non empty dict where key it's side name and value it's side
		value.
		`selector` - optional, callable object that implements appropriated
		selection logic.
		'''
		super(ConfigurableAB, self).__init__(identity, storage)
		self.name = name
		self.sides = sides
		self.selector = selector

	@property
	def allowed_sides(self):
		if self.sides:
			return self.sides.keys()
		return []

	def select_side(self, *args, **kwargs):
		if self.selector:
			return self.selector(*args, **kwargs)
		return random.choice(self.allowed_sides)

	def apply_side(self, side, *args, **kwargs):
		return self.sides[side]


def quick_test(name, sides, selector=None, **kwargs):
	'''
	Shortcut to perform quick AB test. For example:

	>>> quick_test('MyTest', sides={'A': 'Side A', 'B': 'Side B'})
	'Side B'

	See ConfigurableAB class for details.
	'''
	return ConfigurableAB(name=name, sides=sides, selector=selector, **kwargs).test()
