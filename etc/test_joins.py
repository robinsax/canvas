import canvas as cv

CREATE = True

@cv.model('a_stuff', {
	'id': cv.Column('uuid', primary_key=True),
	'text': cv.Column('text')
})
class A:

	def __init__(self, text):
		self.text = text

@cv.model('b_stuff', {
	'id': cv.Column('uuid', primary_key=True),
	'name': cv.Column('text'),
	'a_id': cv.Column('fk:a_stuff.id')
})
class B:

	def __init__(self, name, a):
		self.name = name
		self.a_id = a.id

cv.initialize()

s = cv.create_session()

if CREATE:
	a = A("I'm another a")
	s.save(a).commit()

	b1 = B("I'm b 1 - 1", a)
	s.save(b1)

	b2 = B("I'm b 1- 2", a)
	s.save(b2)

	s.commit()

from pprint import pprint

join = B.join(A.onto('a'))
#	Should be 2 bs
bs = s.query(join)
print('read %d bs'%len(bs))
for b in bs:
	print(b.name, '-', b.a.text)

join = A.join(B.onto('bs'))
as_ = s.query(join)
for a in as_:
	print(a.text, '-', [b.name for b in a.bs])


A.join(B.onto('b_instances'), C.onto('c_instances'))
