from flask import request
from flask_restful import Resource

from mysql_connection import get_connection
from mysql.connector import Error
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity
from datetime import datetime
import boto3
from config import Config

class LikeResource(Resource) :
    @jwt_required()
    def post(self,posting_id) :
        user_id=get_jwt_identity()

        try :
            connection = get_connection()
            query = '''insert into `like`
                    (userId,postingId)
                    values
                    (%s,%s);'''
            record = (user_id,posting_id)
            cursor = connection.cursor()
            cursor.execute(query,record)
            connection.commit()
            cursor.close()
            connection.close()
        except Error as e :
            print(e)        
            cursor.close()
            connection.close()
            return{'error':str(e)},500


        return {'result':'success'},200
    
    @jwt_required()
    def delete(self,posting_id) :

        user_id=get_jwt_identity()

        try :
            connection = get_connection()
            query = '''delete from `like`
                    where userId=%s and postingId=%s;'''
            record = (user_id,posting_id)
            cursor = connection.cursor()
            cursor.execute(query,record)
            connection.commit()
            cursor.close()
            connection.close()
        except Error as e :
            print(e)        
            cursor.close()
            connection.close()
            return{'error':str(e)},500


        return {'result':'success'},200