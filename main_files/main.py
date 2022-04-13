import sqlalchemy
from flask import Flask, jsonify, request, make_response, json
from flask_marshmallow import Marshmallow
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import Column, Integer, String, ForeignKey

app = Flask(__name__)

engine = sqlalchemy.create_engine('sqlite:///main.db', echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
ma = Marshmallow(app)

HTTP_RES_SUCCESSFUL = 201
HTTP_RES_CLIENT_ERROR = 400


# TABLE CREATION ON MYSQL - FUNCIONÁRIOS (EMPLOYEES)
class Employee(Base):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True, nullable=False)
    employee_name = Column(String(50), nullable=False)

    team_id = Column(Integer, ForeignKey('teams.id'))
    teams = relationship('Team', back_populates='employees')

    recommendation_id = Column(Integer, ForeignKey('recommendations.id'))
    recommendations = relationship('Recommendation', back_populates='employees')

    def __repr__(self) -> str:
        return f'ID: {self.id} , Employee Name: {self.employee_name}'


# TABLE CREATION ON MYSQL - EQUIPES  (TEAMS)
class Team(Base):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True, nullable=False)
    team_name = Column(String(50), nullable=False)

    employees = relationship('Employee', back_populates='teams')  # Employee --> references Class Employee

    def __repr__(self) -> str:
        return f'ID: {self.id}, Team Name: {self.team_name}, Employees: {self.employees}'


# TABLE CREATION ON MYSQL - INDICACOES (RECOMMENDATIONS)
class Recommendation(Base):
    __tablename__ = 'recommendations'

    id = Column(Integer, primary_key=True, nullable=False)
    recommendation = Column(String(50), nullable=False)

    employees = relationship('Employee', back_populates='recommendations')  # Employee --> references Class Employee


Base.metadata.create_all(engine)


# SERIALIZED TABLE "TEAM" SCHEMA
class TeamSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Team


# SERIALIZED TABLE "RECOMMENDATION" SCHEMA
class RecoSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Recommendation


# NESTED SCHEMAS
class EmployeeTeamSchemaNested(SQLAlchemyAutoSchema):
    class Meta:
        model = Team
        include_relationships = True


# NESTED SCHEMAS
class EmployeesRecoSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Recommendation
        include_relationships = True


# REGISTRAR EQUIPES (TIMES)
@app.route('/teams', methods=['POST'])
def register_teams():
    # DATA GOTTEN FROM POST BODY JSON - POSTMAN
    request_data = request.get_json()

    try:
        # CHECK IF TEAM NAME WAS GIVEN
        if "team_name" not in request_data:
            session.close()
            return make_response({"status": HTTP_RES_CLIENT_ERROR, "message": "Team Name is a mandatory field"},
                                 HTTP_RES_CLIENT_ERROR)

        else:
            teams = Team(id=request_data["id"], team_name=request_data["team_name"])

            # INSERT DATA INTO MYSQL TABLE
            session.add(teams)
            session.commit()
            session.close()

            # RETURN POST ON POSTMAN
            return make_response(jsonify({"status": HTTP_RES_SUCCESSFUL, "message": "Team added successfully :)"},
                                         request_data), HTTP_RES_SUCCESSFUL)

    # CHECK IF VALUE IS NULL
    except Exception:
        session.rollback()
        return make_response(jsonify({"status": HTTP_RES_CLIENT_ERROR, "message": "Column 'TEAM_NAME' cannot be null"}),
                             HTTP_RES_CLIENT_ERROR)


# REGISTRAR FUNCIONÁRIOS (EMPLOYEES)
@app.route('/employees', methods=['POST'])
def register_employees():
    # DATA GOTTEN FROM POST BODY JSON - POSTMAN
    request_data = request.get_json()

    try:
        # CHECK IF EMPLOYEE NAME EXISTS
        if "employee_name" not in request_data:
            session.close()
            return make_response({"status": HTTP_RES_CLIENT_ERROR, "message": "Employee Name is a mandatory field"},
                                 HTTP_RES_CLIENT_ERROR)

        else:
            employee = Employee(id=request_data["id"], employee_name=request_data["employee_name"],
                                team_id=request_data["team_id"], recommendation_id=request_data["recommendation_id"])

            # INSERT DATA INTO MYSQL TABLE
            session.add(employee)
            session.commit()
            session.close()

            # RETURN POST ON POSTMAN
            return make_response(jsonify({"status": HTTP_RES_SUCCESSFUL, "message": "Employee added successfully :)"},
                                         request_data), HTTP_RES_SUCCESSFUL)

    # CHECK IF VALUE IS NULL
    except Exception:
        session.rollback()
        return make_response(jsonify({"status": HTTP_RES_CLIENT_ERROR,
                                      "message": "Column 'EMPLOYEE NAME' cannot be null"}), HTTP_RES_CLIENT_ERROR)


# REGISTRAR INDICAÇÕES (RECOMMENDATIONS)
@app.route('/recommendations', methods=['POST'])
def register_recommendations():
    # DATA GOTTEN FROM POST BODY JSON - POSTMAN
    request_data = request.get_json()

    try:
        if "recommendation" not in request_data:
            session.close()
            return make_response({"status": HTTP_RES_CLIENT_ERROR, "message": "Recommendation is a mandatory field"},
                                 HTTP_RES_CLIENT_ERROR)

        else:
            recommendations = Recommendation(id=request_data["id"], recommendation=request_data["recommendation"])

            # INSERT DATA INTO MYSQL TABLE
            session.add(recommendations)
            session.commit()
            session.close()

            # RETURN POST ON POSTMAN
            return make_response(
                jsonify({"status": HTTP_RES_SUCCESSFUL, "message": "Recommendation added successfully :)"},
                        request_data), HTTP_RES_SUCCESSFUL)

    # CHECK IF VALUE IS NULL
    except Exception:
        session.rollback()
        return make_response(jsonify({"status": HTTP_RES_CLIENT_ERROR, "message": "Column 'RECOMMENDATION' cannot be "
                                                                                  "null"}), HTTP_RES_CLIENT_ERROR)


# Retornar uma lista de equipes e respectivos funcionários
@app.route('/teams', methods=['GET'])
def get_all_teams():

    if request.args.get('id'):
        req = request.args.get('id')
        res = session.query(Team).join(Employee).filter(Team.id == req).order_by(Team.id).all()
        res_json = json.dumps(res, default=str)
        return make_response(jsonify(res_json), 200)

    else:
        res = session.query(Team).join(Employee).filter(Team.id == Employee.team_id).order_by(Team.id).all()
        res_json = json.dumps(res, default=str)
        return make_response(jsonify(res_json), 200)


# Retornar uma lista de indicações
@app.route('/recommendations', methods=['GET'])
def get_all_recommendations():
    reco_schema = RecoSchema()

    if request.args.get('id'):
        req = request.args.get('id')
        res = session.query(Recommendation).filter(Recommendation.id == req).all()
        res_json = reco_schema.dump(res, many=True)
        return make_response(jsonify(res_json), 200)

    else:
        res = session.query(Recommendation).order_by(Recommendation.id).all()
        res_json = reco_schema.dump(res, many=True)
        return make_response(jsonify(res_json), 200)


# Retornar quais funcionários realizaram indicações
@app.route('/recommendations/employees', methods=['GET'])
def get_all_employees_with_recommendations():
    employees_reco = EmployeesRecoSchema()

    if request.args.get('id'):
        req = request.args.get('id')
        res = session.query(Recommendation).join(Employee).filter(Recommendation.id == req).all()
        res_json = employees_reco.dump(res, many=True)
        return make_response(jsonify(res_json), 200)

    else:
        res = session.query(Recommendation).join(Employee).filter(Recommendation.id == Employee.team_id).all()
        res_json = employees_reco.dump(res, many=True)
        return make_response(jsonify(res_json), 200)


if __name__ == "__main__":
    app.run(debug=True)
