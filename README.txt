Simple but flexible python library for A/B or split testing.

================
    Examples
================

1. SimpleAB test. This implementation of AB Test provides way to implement
alternatives as methods with names A, B, ..., Z.

	>>> import simpleab
	>>> class MyTest(simpleab.SimpleAB):
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


2. ConfigurableAB test. This implementation of AB Test provides way to configure
test name, sides and selector instance. If selector isn't specified random selection
will be used.

	>>> improt simpleab
	>>> import random
	>>> myab = simpleab.ConfigurableAB(name='MyTest',
	... 			sides={'A': 'Side A', 'B': 'Side B'},
	... 			selector=lambda: random.choice(['A','B']))
	>>> myab
	<ConfigurableAB [name: MyTest, sides: ['A', 'B']]>
	>>> myab.test()
	'Side A'
	>>> myab.current_side
	'A'

3. Super short version, quick AB test:

	>>> improt simpleab
	>>> simpleab.quick_test('MyTest', sides={'A': 'Side A', 'B': 'Side B'})
	'Side B'