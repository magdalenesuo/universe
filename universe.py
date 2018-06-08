# -*- coding: utf-8 -*-

from flask import Flask
from flask_rest_jsonapi import Api, ResourceDetail, ResourceList, ResourceRelationship
from flask import request, jsonify, abort, make_response
from flask_rest_jsonapi.exceptions import ObjectNotFound, BadRequest
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
from marshmallow_jsonapi.flask import Schema, Relationship
from marshmallow_jsonapi import fields
from flask import request, jsonify, abort, make_response, Blueprint
 
 
# Create the Flask application
app = Flask(__name__)
app.config['DEBUG'] = True


# Initialize SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://mms:medo@127.0.0.1:5432/universe'
db = SQLAlchemy(app)


# Create data storage
class Person(db.Model):
    """Person object table"""

    __tablename__ = 'people'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    power= db.Column(db.Integer)
    family_id = db.Column(db.Integer, db.ForeignKey('families.id', ondelete='CASCADE'))
    family = db.relationship('Family', backref='person')

class Family(db.Model):
    """Family object table"""

    __tablename__ = 'families'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fam_power= db.Column(db.Integer, default=0)
    name_identifier = db.Column(db.Integer, nullable=False)
    universe_id = db.Column(db.Integer, db.ForeignKey('universes.id', ondelete='CASCADE'))    
    #people = db.relationship('Person', backref='family')
    universe = db.relationship('Universe', backref='families')

class Universe(db.Model):
    """Universe object table"""

    __tablename__ = 'universes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    family = db.relationship('Family', backref='uiverse')

class UnbalancedFamilies(db.Model):
    """Unbalanced_families object table"""

    __tablename__ = 'unbalanced_families'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    family_id = db.Column(db.Integer, db.ForeignKey('families.id', ondelete='CASCADE'))

db.create_all()



## Schema
class PersonSchema(Schema):
    """
    Api Schema for person
    """

    class Meta:
        """
        Meta class for person Api Schema
        """
        type_ = 'person'
        self_view = 'person_detail'
        self_view_kwargs = {'id': '<id>'}        
        self_view_many = 'person_list'

    id = fields.Str(dump_only=True)
    power = fields.Integer(required=True)
    family = Relationship(attribute='family',
                          self_view='person_family',
                          self_view_kwargs={'id': '<id>'},
                          related_view='family_detail',
                          related_view_kwargs={'id': '<id>'},
                          schema='FamilySchema',
                          type_='family')


class FamilySchema(Schema):
    """
    Api Schema for family
    """

    class Meta:
        """
        Meta class for family Api Schema
        """
        type_ = 'family'
        self_view = 'family_detail'
        self_view_kwargs = {'id': '<id>'}
        self_view_many = 'family_list'

    id = fields.Str(dump_only=True)
    fam_power = fields.Integer(default=0)
    name_identifier = fields.Integer(required=True,nullable=False)
    people = Relationship(attribute='person',
                          self_view='family_person',
                          self_view_kwargs={'id': '<id>'},
                          related_view='person_list',
                          related_view_kwargs={'id': '<id>'},
                          many=True,
                          schema='PersonSchema',
                          type_='person')
    universe = Relationship(attribute='universe',
                            self_view='family_universe',
                            self_view_kwargs={'id': '<id>'},
                            related_view='universe_detail',
                            related_view_kwargs={'id': '<id>'},
                            schema='UniverseSchema',
                            type_='universe')


class UniverseSchema(Schema):
    """
    Api Schema for universe
    """

    class Meta:
        """
        Meta class for universe Api Schema
        """
        type_ = 'universe'
        self_view = 'universe_detail'
        self_view_kwargs = {'id': '<id>'}

    id = fields.Str(dump_only=True)
    name = fields.Str()
    families = Relationship(attribute='family',
                          self_view='universe_family',
                          self_view_kwargs={'id': '<id>'},
                          related_view='family_list',
                          related_view_kwargs={'universe_id': '<id>'},
                          schema='FamilySchema',
                          many=True,
                          type_='family')



# Resources
class PersonList(ResourceList):

    """
    List and create people
    """
    def before_create_object(self, data, view_kwargs):
        if view_kwargs.get('family_id') is not None:
            data['family_id'] = view_kwargs['family_id']

    def after_create_object(self, family, data, view_kwargs):
        if view_kwargs.get('family_id') is not None:
            family = self.session.query(Family).filter_by(id=view_kwargs['family_id']).one()
            family.fam_power = family.fam_power + data['power']
            db.session.add(family)
            db.session.commit()

    def query(self, view_kwargs):
        """
        query method for People class
        :param view_kwargs:
        :return:
        """
        query_ = self.session.query(Person)
        if view_kwargs.get('family_id') is not None:
            family = self.session.query(Family).filter_by(id=view_kwargs['family_id']).one()
            query_ = query_.join(Family).filter(Family.id == family.id)

        return query_

    schema = PersonSchema
    methods = ['GET', 'POST']
    data_layer = {'session': db.session,
                  'model': Person,
                  'methods': {'after_create_object': after_create_object,
                              'before_create_object': before_create_object,
                              'query': query
                              }}


class PersonDetail(ResourceDetail):
    """
    Person detail by id
    """

    schema = PersonSchema
    methods = ['GET', 'PATCH', 'DELETE']
    data_layer = {'session': db.session,
                  'model': Person}


class PersonRelationship(ResourceRelationship):
    """
    Person Relationship
    """
    schema = PersonSchema
    data_layer = {'session': db.session,
                  'model': Person}



class FamilyList(ResourceList):

    """
    List and create family
    """

    def before_create_object(self, data, view_kwargs):
        if view_kwargs.get('universe_id') is not None:
            data['universe_id'] = view_kwargs['universe_id']
    

    def query(self, view_kwargs):
        query_ = self.session.query(Family)
        if view_kwargs.get('universe_id') is not None:
            try:
                self.session.query(Universe).filter_by(id=view_kwargs['universe_id']).one()
            except NoResultFound:
                raise ObjectNotFound({'parameter': 'id'}, "Universe: {} not found".format(view_kwargs['universe_id']))
            else:
                query_ = query_.join(Universe).filter(Universe.id == view_kwargs['universe_id'])

        if view_kwargs.get('family_id') is not None:
            try:
              self.session.query(Family).filter_by(name_identifier=view_kwargs['family_id'])
            except NoResultFound:
              raise ObjectNotFound({'parameter': 'id'}, "Family: {} not found".format(view_kwargs['family_id']))
            else:
              query_ = self.session.query(Family).filter_by(name_identifier=view_kwargs['family_id'])
              
        return query_

    schema = FamilySchema
    methods = ['GET', 'POST']
    data_layer = {'session': db.session,
                  'model': Family,
                  'methods': {'before_create_object':before_create_object,
                              'query':query
                  }}


class FamilyDetail(ResourceDetail):
    """
    Family detail by id
    """
    schema = FamilySchema
    methods = ['GET', 'PATCH', 'DELETE']
    data_layer = {'session': db.session,
                  'model': Family}


class FamilyRelationship(ResourceRelationship):
    """
    Family Relationship
    """
    schema = FamilySchema
    data_layer = {'session': db.session,
                  'model': Family}


class UniverseList(ResourceList):

    """
    List and create uiverse
    """
    schema = UniverseSchema
    methods = ['GET', 'POST']
    data_layer = {'session': db.session,
                  'model': Universe}


class UniverseDetail(ResourceDetail):
    """
    Universe detail by id
    """
    schema = UniverseSchema
    methods = ['GET', 'PATCH', 'DELETE']
    data_layer = {'session': db.session,
                  'model': Universe}


class UniverseRelationship(ResourceRelationship):
    """
    Universe Relationship
    """
    schema = UniverseSchema
    data_layer = {'session': db.session,
                  'model': Universe}


@app.route('/families/check/<int:family_identifier>', methods=['GET'])
def check_family(family_identifier):
    family = Family.query.filter_by(name_identifier=family_identifier)
    power = family[0].fam_power
    for i in family:
      if i.fam_power is not power:
          result=jsonify(result="Power for the given Family is NOT EQUAL in all universe (Unbalanced)"
          )
      else:
          result = jsonify(
            result="Power for the given Family is EQUAL in all universe (Balanced)"
          )
    return result

@app.route('/families/fix', methods=['GET'])
def fix_family():
    family = Family.query.all()
    total = dict()
    howmany = dict()
    initial = dict()
    balanced = []
    unbalanced = []
    sumtotal = 0

    for f in family:
        total[f.name_identifier] = 0
        howmany[f.name_identifier] = 0
        initial[f.name_identifier] = f.fam_power
    for f in family:
        total[f.name_identifier] = total[f.name_identifier]+f.fam_power
        howmany[f.name_identifier] = howmany[f.name_identifier]+1

    for k in howmany:
        total[k] = total[k]/howmany[k]
        for f in family:
            if f.name_identifier == k and initial[f.name_identifier] is not total[k]:
              f.fam_power = total[f.name_identifier]
              if f.name_identifier not in unbalanced:
                unbalanced.append(f.name_identifier)

            elif f.name_identifier == k and initial[f.name_identifier] == total[k]:
              f.fam_power = total[f.name_identifier]
              if f.name_identifier not in balanced:
                balanced.append(f.name_identifier)
        
    db.session.add(f)
    db.session.commit()
    print unbalanced

    result=jsonify(balanced_families=balanced,
                   unbalanced_families=unbalanced)
    return result


##endpoints
api = Api(app)
# people
api.route(PersonList, 'person_list', '/people','/family/<int:family_id>/people')
api.route(PersonDetail, 'person_detail', '/person/<int:id>')
api.route(PersonRelationship, 'person_family', '/people/<int:id>/relationships/family')

# family
api.route(FamilyList, 'family_list', '/families','/universe/<int:universe_id>/families')
api.route(FamilyDetail, 'family_detail', '/family/<int:id>')
api.route(FamilyRelationship, 'family_person',
          '/family/<int:id>/relationships/people')
api.route(FamilyRelationship, 'family_universe',
          '/family/<int:id>/relationships/universe')
# universe
api.route(UniverseList, 'universe_list', '/universes')
api.route(UniverseDetail, 'universe_detail', '/universe/<int:id>')
api.route(UniverseRelationship, 'universe_family',
          '/universe/<int:id>/relationships/families')

if __name__ == '__main__':
    # Start application
    app.run(debug=True)
