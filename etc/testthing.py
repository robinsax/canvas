import canvas as cv

@cv.model('thing1s', {
    'id': cv.Column('uuid', primary_key=True),
    'text': cv.Column('text')
})
class Thing1: pass

@cv.model('thing2s', {
    'id': cv.Column('serial', primary_key=True),
    'ref': cv.Column('fk:thing1s.id')
})
class Thing2: pass

cv.initialize()

s = cv.create_session()

what_is_this = s.query(Thing2.join(Thing1.text), one=True)
print(what_is_this.text, what_is_this.id)

what_is_this.text = 'Thing2 changed me'
s.commit()
