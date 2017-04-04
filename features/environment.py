from behave import *
import server


def before_all(context):
    context.app = server.app.test_client()
    server.initialize_testmysql()
    server.initialize_index()
    context.server = server
