from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_

from app import db
from app.model.analysis_module import AnalysisModule
from tools.time_util import get_current_timestamp


class AnalysisModuleRepo:
    def __init__(self):
        self.db = db

    def create_analysis_module(self, user_id, service_introduction=None, customer_description=None):
        new_module = AnalysisModule(
            user_id=user_id,
            service_introduction=service_introduction,
            customer_description=customer_description
        )
        try:
            self.db.session.add(new_module)
            self.db.session.commit()
            return new_module
        except SQLAlchemyError as e:
            self.db.session.rollback()
            print(f"Error creating analysis module: {e}")
            return None

    def update_analysis_module(self, module_id, user_id, service_introduction=None, customer_description=None, default=None):
        module = AnalysisModule.query.filter_by(id=module_id, user_id=user_id).first()
        if not module:
            print(f"Analysis module with id {module_id} not found")
            return None

        if service_introduction is not None:
            module.service_introduction = service_introduction
        if customer_description is not None:
            module.customer_description = customer_description
        if default is not None:
            module.default = default
        module.update_time = get_current_timestamp()

        try:
            self.db.session.commit()
            return module
        except SQLAlchemyError as e:
            self.db.session.rollback()
            print(f"Error updating analysis module: {e}")
            return None

    def delete_analysis_module(self, module_id, user_id):
        module = AnalysisModule.query.filter(
            and_(
                AnalysisModule.id == module_id,
                AnalysisModule.user_id == user_id,
                AnalysisModule.delete_time == None
            )).first()
        if not module:
            print(f"Analysis module with id {module_id} not found")
            return False

        module.delete_time = get_current_timestamp()
        try:
            self.db.session.commit()
            return True
        except SQLAlchemyError as e:
            self.db.session.rollback()
            print(f"Error deleting analysis module: {e}")
            return False

    @staticmethod
    def get_analysis_modules_by_user_id(user_id):
        try:
            modules = AnalysisModule.query.filter_by(user_id=user_id, delete_time=None).all()
            return modules
        except SQLAlchemyError as e:
            print(f"Error retrieving analysis modules for user_id {user_id}: {e}")
            return None





