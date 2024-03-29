from flask import request
from flask_restful import Resource

from mysql_connection import get_connection
from mysql.connector import Error
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity
from datetime import datetime
import boto3
from config import Config


class PostingListResource(Resource) :
    @jwt_required()
    def post(self):

        # 1. 클라이언트가 보낸 데이터를 받아온다.
        if 'photo' not in request.files :
            return {'error':'파일을 업로드 하십시오.'}
        if 'content' not in request.form :
            return {'error':'내용을 입력 하세요.'}
        file = request.files['photo']
        content = request.form['content']

        user_id=get_jwt_identity()

        


        # 2. 사진을 S3에 저장한다.
        ### 2-1. aws 콘솔로 가서 IAM 유저 만든다. ( 없으면 )
        ### 2-2. s3로 가서 이 프로젝트의 버킷을 만든다.
        ### 2-3. config.py파일에 변수로 저장한다.

        ### 2-4. 파일명을 유니크하게 만든다.
        current_time=datetime.now()
        new_file_name=str(user_id)+current_time.isoformat().replace(':','_')+'.jpg'
        file.filename=new_file_name

        ### 2-5.  S3에 파일을 업로드한다.
        ###       파일 업로드하는 코드는 boto3 라이브리를 이용해서 업로드한다.
        ###       라이브러리가 설치 되어있지 않으면 설치 => pip install boto3
        client = boto3.client('s3',aws_access_key_id=Config.ACCESS_KEY,aws_secret_access_key=Config.SECRET_ACCESS)

        try :
            client.upload_fileobj(file,Config.S3_BUCKET,new_file_name,
                                    ExtraArgs ={'ACL':'public-read','ContentType':file.content_type})

        except Exception as e :
            return {'error':str(e)}, 500


        # 3. S3에 저장된 사진을 Object Detection한다. ( AWS의 Rekognition 이용 )
        #  (AWS Rekognition 이용)
        #  Labels안에 있는 Name만 가져온다.

        client=boto3.client('rekognition',
                    'ap-northeast-2',
                    aws_access_key_id=Config.ACCESS_KEY,
                    aws_secret_access_key=Config.SECRET_ACCESS)
        response=client.detect_labels(Image={'S3Object':{'Bucket':Config.S3_BUCKET,'Name':new_file_name}},
                            MaxLabels= 5 )

        # print(response)
        name_list = []
        for row in response['Labels'] :
            name_list.append(row['Name'])
        

        # 4. 위에서 나온 결과인, imgURL과 태그로 저장할 Labels 이름을 가지고
        #   DB에 저장한다.
        
        imgUrl = Config.S3_LOCATION+new_file_name

        try :
            connection = get_connection()
            

            # 4-1. imgUrl과 Content를 posting 테이블에 insert
            query = '''insert into posting
                    (userId,imgUrl,content)
                    values
                    (%s,%s,%s);'''
            record = (user_id,imgUrl,content)

            cursor = connection.cursor()
            cursor.execute(query,record)
            posting_id = cursor.lastrowid
            print(posting_id)
            # 4-2. tag_name과 tag 테이블에 insert.
            # 4-2-1. name_list에 있는 문자열이 tag_name테이블에 들어있는지 확인
            #        있으면 그 tag_name의 아이디를 가져오고 없으면 tag_name에 넣어준다.
            for name in name_list :
                query = '''select * 
                        from tag_name
                        where name = %s;'''
                record = (name,)
                cursor = connection.cursor(dictionary=True)
                cursor.execute(query,record)
                result_list=cursor.fetchall()
                if len(result_list) == 0 :
                    query = '''insert into tag_name
                            (name)
                            values
                            (%s);'''
                    record=(name,)
                    cursor.execute(query,record)
                    tag_id = cursor.lastrowid
                else :
                    tag_id=result_list[0]['id']

                # tag 테이블에 postingId와 tagId를 저장한다.
                query = '''insert into tag
                        (postingId,tagId)
                        values
                        (%s,%s);'''
                record = (posting_id,tag_id)
                cursor.execute(query,record)
            connection.commit()
            cursor.close()
            connection.close()


        except Error as e:
            print(e)
            cursor.close()
            connection.close()
            return {'error':str(e)}, 500

        # 5. 결과를 클라이언트에 보내준다.

        return {'result':'success'}

    @jwt_required()
    def get(self) :
        user_id = get_jwt_identity()
        offset=request.args.get('offset')
        limit=request.args.get('limit')

        try :
            connection = get_connection()
            query = '''select f.followeeId,u.email,p.id as postingId,p.imgUrl,p.content,p.createdAt,
                    if(l.userId is null,0,1) as isLike
                    from follow f
                    join user u
                    on u.id = f.followeeId
                    join posting p
                    on p.userId = f.followeeId
                    left join `like` l
                    on p.id = l.postingId
                    where followerId=%s
                    order by p.createdAt desc
                    limit '''+offset+''','''+limit+''';'''
            record = (user_id,)
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query,record)
            result_list = cursor.fetchall()

            print(result_list)
            i = 0
            for row in result_list :
                result_list[i]['createdAt']=row['createdAt'].isoformat()
                i = i+1


            cursor.close()
            connection.close()
        except Error as e :
            print(e)
            cursor.close()
            connection.close()
            return{'error':str(e)},500

        return {'result':'success','items':result_list,'count':len(result_list)},200


class PostingTagResource(Resource) :

    @jwt_required()
    def get(self) :
        name=request.args.get('name')
        offset=request.args.get('offset')
        limit=request.args.get('limit')
        user_id = get_jwt_identity()

        
        try :
            connection = get_connection()

            query = '''select u.email,p.imgUrl,p.content,p.createdAt,
                    if(l.userId is null,0,1) as isLike ,t.postingId
                    from tag_name tn
                    join tag t
                    on tn.id = t.tagId
                    join posting p
                    on p.id = t.postingId
                    join user u
                    on p.userId = u.id
                    left join `like` l
                    on l.userId=%s and p.id = l.postingId
                    where name = %s
                    limit '''+offset+''','''+limit+''';'''
            record = (user_id,name)
            cursor=connection.cursor(dictionary=True)
            cursor.execute(query,record)
            result_list=cursor.fetchall()

            print(result_list)

            i = 0
            for row in result_list :
                result_list[i]['createdAt']=row['createdAt'].isoformat()
                i = i+1

            cursor.close()
            connection.close()
        except Error as e :
            print(e)
            cursor.close()
            connection.close()
            return{'error':str(e)},500

        
        return {'result':'success','items':result_list,'count':len(result_list)},200