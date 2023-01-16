class Config :
    HOST = 'yh-db.cy1i4s2uewlm.ap-northeast-2.rds.amazonaws.com'
    DATABASE = 'posting_db'
    DB_USER = 'posting_db_user'
    DB_PASSWORD = 'yh1234db'
    SALT = 'dskj29jcdn12jn'

    # JWT 관련 변수 셋팅
    JWT_SECRET_KEY = 'yhacdemy20230105##hello'
    JWT_ACCESS_TOKEN_EXPIRES = False
    PROPAGATE_EXCEPTIONS = True

    # AWS 관련 키
    ACCESS_KEY = 'AKIAYYISOLC4B2GI7F7B'
    SECRET_ACCESS = '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'

    # S3 버킷
    S3_BUCKET = 'hyunsung-posting-app'
    # S3 Location
    S3_LOCATION = 'https://hyunsung-posting-app.s3.ap-northeast-2.amazonaws.com/'