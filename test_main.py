from app import create_app_with_test
import pymysql
pymysql.install_as_MySQLdb()

n_app = create_app_with_test()

if __name__ == '__main__':
    with n_app.app_context():
        n_app.run(host="0.0.0.0", port=3002)