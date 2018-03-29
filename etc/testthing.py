import canvas as cv

@cv.model('aaa', {
    'id': cv.Column('uuid', primary_key=True),
    'text': cv.Column('text')
})
class A: pass

@cv.model('bbb', {
    'id': cv.Column('serial', primary_key=True),
    'texy': cv.Column('text')
})
class B: pass

@cv.model('ccc', {
    'id': cv.Column('serial', primary_key=True),
    'aref': cv.Column('fk:aaa.id'),
    'bref': cv.Column('fk:bbb.id')
})
class C: pass

cv.initialize()
s = cv.create_session()

a = A()
a.text = 'aaaaaaaaaaaaaAAAAA'

s.save(a).commit()

b = B()
b.texy = 'tex!boi'

s.save(b).commit()

c = C()
c.aref = a.id
c.bref = b.id

s.save(c).commit()

print(['%s=%s'%pair for pair in s.query(C.join(A.text, B.texy), one=True).__dict__.items()])
